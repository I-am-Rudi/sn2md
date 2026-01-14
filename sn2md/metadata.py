import hashlib
import logging
import os
import yaml
from dataclasses import asdict
from .types import ConversionMetadata

logger = logging.getLogger(__name__)


def _load_metadata_unversioned(data) -> list[ConversionMetadata]:
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("Invalid metadata format")

    entries = []
    for entry in data:
        # Remove version if it exists in the entry (old format)
        entry_copy = entry.copy()
        entry_copy.pop("version", None)
        entries.append(ConversionMetadata(**entry_copy))
    return entries


def _load_metadata_v1(data) -> list[ConversionMetadata]:
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("Invalid metadata format")

    entries: list[ConversionMetadata] = []
    for entry in data:
        if entry.get("version") != 1:
            raise ValueError("Unsupported metadata version")

        entry_copy = entry.copy()
        entry_copy.pop("version", None)
        entries.append(ConversionMetadata(**entry_copy))

    return entries


def _load_metadata_entries(metadata_path: str) -> list[ConversionMetadata]:
    with open(metadata_path, "r") as f:
        data = yaml.safe_load(f) or {}

    if isinstance(data, dict) and "version" in data and "files" in data:
        if data["version"] == 1:
            return _load_metadata_unversioned(data["files"])
        raise ValueError("Unsupported metadata version")

    if isinstance(data, list):
        if not data:
            return []

        if all("version" not in entry for entry in data):
            return _load_metadata_unversioned(data)

        if all(entry.get("version") == 1 for entry in data):
            return _load_metadata_v1(data)

        if any("version" in entry for entry in data):
            raise ValueError("Unsupported metadata version")

    if isinstance(data, dict):
        if "version" not in data:
            return _load_metadata_unversioned(data)

        if data.get("version") == 1:
            return _load_metadata_v1(data)

    if isinstance(data, dict) and "version" in data:
        raise ValueError("Unsupported metadata version")

    raise ValueError("Unsupported metadata format or version")


def check_metadata_file(
    metadata_file: str, input_file: str | None = None
) -> ConversionMetadata | None:
    """Check the hashes of the source file against the metadata.

    Raises a ValueError if the source file hasn't been modified.

    Returns the computed source and output hashes.
    """
    metadata_path = os.path.join(metadata_file, ".sn2md.metadata.yaml")
    if os.path.exists(metadata_path):
        metadata_entries = _load_metadata_entries(metadata_path)
        if not metadata_entries:
            return None

        if input_file:
            metadata = next(
                (entry for entry in metadata_entries if entry.input_file == input_file),
                None,
            )
            if metadata is None:
                return None
        else:
            if len(metadata_entries) > 1:
                raise ValueError("Multiple metadata entries found; specify input file")
            metadata = metadata_entries[0]

        if not os.path.exists(metadata.output_file):
            raise ValueError("Output file does not exist anymore!")

        with open(metadata.output_file, "rb") as f:
            output_hash = hashlib.sha1(f.read()).hexdigest()

        if not os.path.exists(metadata.input_file):
            raise ValueError("Input file does not exist anymore!")

        with open(metadata.input_file, "rb") as f:
            source_hash = hashlib.sha1(f.read()).hexdigest()

        if metadata.input_hash == source_hash:
            raise ValueError(f"Input {metadata.input_file} has NOT changed!")

        if metadata.output_hash != output_hash:
            raise ValueError(f"Output {metadata.output_file} HAS been changed!")

        return metadata
    return None


def write_metadata_file(source_file: str, output_file: str) -> None:
    """Write the source hash and path to the metadata file."""
    output_path = os.path.dirname(output_file)
    with open(output_file, "rb") as f:
        output_hash = hashlib.sha1(f.read()).hexdigest()

    with open(source_file, "rb") as f:
        source_hash = hashlib.sha1(f.read()).hexdigest()

    metadata_path = os.path.join(output_path, ".sn2md.metadata.yaml")
    existing_metadata = []
    if os.path.exists(metadata_path):
        existing_metadata = _load_metadata_entries(metadata_path)

    metadata_entries = [entry for entry in existing_metadata if entry.input_file != source_file]

    metadata_entries.append(
        ConversionMetadata(
            input_file=source_file,
            input_hash=source_hash,
            output_file=output_file,
            output_hash=output_hash,
        )
    )

    with open(metadata_path, "w") as f:
        yaml.dump(
            {
                "version": 1,
                "files": [asdict(entry) for entry in metadata_entries],
            },
            f,
        )
