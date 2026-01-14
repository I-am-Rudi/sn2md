import os
import pytest
import yaml
from sn2md.metadata import check_metadata_file, write_metadata_file
from sn2md.types import ConversionMetadata


@pytest.fixture
def temp_files(tmp_path):
    # Create test files
    source_file = tmp_path / "source.txt"
    output_file = tmp_path / "output.md"
    metadata_dir = tmp_path

    # Write initial content
    source_file.write_text("original content")
    output_file.write_text("# Original markdown")

    return {
        "source_file": str(source_file),
        "output_file": str(output_file),
        "metadata_dir": str(metadata_dir),
    }


def test_write_metadata_file(temp_files):
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])

    metadata_path = os.path.join(os.path.dirname(temp_files["output_file"]), ".sn2md.metadata.yaml")
    assert os.path.exists(metadata_path)

    with open(metadata_path) as f:
        data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert data["version"] == 1
        assert "files" in data
        assert data["files"][0]["input_file"] == temp_files["source_file"]
        assert data["files"][0]["output_file"] == temp_files["output_file"]
        assert "input_hash" in data["files"][0]
        assert "output_hash" in data["files"][0]


def test_check_metadata_file_modified_input(temp_files):
    # First write initial metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])

    # Modify source file
    with open(temp_files["source_file"], "w") as f:
        f.write("modified content")

    # Should return metadata since input changed
    metadata = check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])
    assert isinstance(metadata, ConversionMetadata)
    assert metadata.input_file == temp_files["source_file"]


def test_check_metadata_file_unmodified_input(temp_files):
    # Write metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])

    # Should raise error since input hasn't changed
    with pytest.raises(ValueError, match="has NOT changed"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_modified_output(temp_files):
    # Write initial metadata
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])

    # Modify source and output
    with open(temp_files["source_file"], "w") as f:
        f.write("modified content")
    with open(temp_files["output_file"], "w") as f:
        f.write("# Modified markdown")

    # Should raise error since output was modified
    with pytest.raises(ValueError, match="HAS been changed"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_missing(temp_files):
    # No metadata file exists
    result = check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])
    assert result is None


def test_write_multiple_metadata_entries(temp_files):
    write_metadata_file(temp_files["source_file"], temp_files["output_file"])

    second_source = os.path.join(temp_files["metadata_dir"], "second.txt")
    second_output = os.path.join(temp_files["metadata_dir"], "second.md")
    with open(second_source, "w") as f:
        f.write("secondary content")
    with open(second_output, "w") as f:
        f.write("# Secondary markdown")

    write_metadata_file(second_source, second_output)

    # Modify both sources to ensure metadata is considered stale and returned
    with open(temp_files["source_file"], "w") as f:
        f.write("updated content")

    with open(second_source, "w") as f:
        f.write("updated secondary content")

    metadata = check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])
    assert metadata is not None
    assert metadata.output_file == temp_files["output_file"]

    second_metadata = check_metadata_file(temp_files["metadata_dir"], second_source)
    assert second_metadata is not None
    assert second_metadata.output_file == second_output


def test_check_metadata_file_unversioned_backwards_compatibility(temp_files):
    metadata_path = os.path.join(temp_files["metadata_dir"], ".sn2md.metadata.yaml")

    # Get current hashes
    import hashlib

    with open(temp_files["source_file"], "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()
    with open(temp_files["output_file"], "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    # Write legacy list format
    legacy_data = [
        {
            "input_file": temp_files["source_file"],
            "input_hash": source_hash,
            "output_file": temp_files["output_file"],
            "output_hash": output_hash,
        }
    ]

    with open(metadata_path, "w") as f:
        yaml.safe_dump(legacy_data, f)

    with pytest.raises(ValueError, match="Input .* has NOT changed!"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_unknown_version(temp_files):
    metadata_path = os.path.join(temp_files["metadata_dir"], ".sn2md.metadata.yaml")
    with open(metadata_path, "w") as f:
        yaml.dump(
            [
                {
                    "version": 2,
                    "input_file": temp_files["source_file"],
                    "input_hash": "abc",
                    "output_file": temp_files["output_file"],
                    "output_hash": "def",
                }
            ],
            f,
        )

    with pytest.raises(ValueError, match="Unsupported metadata version"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_old_v1_backwards_compatibility(temp_files):
    metadata_path = os.path.join(temp_files["metadata_dir"], ".sn2md.metadata.yaml")

    import hashlib

    with open(temp_files["source_file"], "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()
    with open(temp_files["output_file"], "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    # Write old V1 format (list of entries with version=1)
    old_v1_data = [
        {
            "version": 1,
            "input_file": temp_files["source_file"],
            "input_hash": source_hash,
            "output_file": temp_files["output_file"],
            "output_hash": output_hash,
        }
    ]

    with open(metadata_path, "w") as f:
        yaml.safe_dump(old_v1_data, f)

    with pytest.raises(ValueError, match="Input .* has NOT changed!"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_single_entry_dict_compatibility(temp_files):
    metadata_path = os.path.join(temp_files["metadata_dir"], ".sn2md.metadata.yaml")

    import hashlib

    with open(temp_files["source_file"], "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()
    with open(temp_files["output_file"], "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    # Write single entry dict (no version)
    data = {
        "input_file": temp_files["source_file"],
        "input_hash": source_hash,
        "output_file": temp_files["output_file"],
        "output_hash": output_hash,
    }

    with open(metadata_path, "w") as f:
        yaml.safe_dump(data, f)

    with pytest.raises(ValueError, match="Input .* has NOT changed!"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])


def test_check_metadata_file_single_entry_dict_v1_compatibility(temp_files):
    metadata_path = os.path.join(temp_files["metadata_dir"], ".sn2md.metadata.yaml")

    import hashlib

    with open(temp_files["source_file"], "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()
    with open(temp_files["output_file"], "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    # Write single entry dict with version=1
    data = {
        "version": 1,
        "input_file": temp_files["source_file"],
        "input_hash": source_hash,
        "output_file": temp_files["output_file"],
        "output_hash": output_hash,
    }

    with open(metadata_path, "w") as f:
        yaml.safe_dump(data, f)

    with pytest.raises(ValueError, match="Input .* has NOT changed!"):
        check_metadata_file(temp_files["metadata_dir"], temp_files["source_file"])
