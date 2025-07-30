import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sn2md.importers.atelier import read_tiles_data, spd_to_png, tid_to_row_col, START_INDEX

@pytest.mark.parametrize("tid, row, col", [
    (START_INDEX, 0, 0),
    (8009635, 8, 10),
])
def test_tid_to_row_col(tid, row, col):
    assert tid_to_row_col(tid) == (row, col)


@pytest.mark.parametrize(
    "spd_file, tiles_data_length, width, height",
    [
        # old formats don't have width/height metadata
        (str(Path(__file__).parent / "fixtures/20250325_165251-blank.spd"), 0, 0, 0),
        (str(Path(__file__).parent / "fixtures/20250325_165308-Layers.spd"), 3, 0, 0),
        # but newer formats do
        (str(Path(__file__).parent / "fixtures/a3.spd"), 3, 3507, 4960),
        (str(Path(__file__).parent / "fixtures/a4.spd"), 2, 2480, 3507),
        (str(Path(__file__).parent / "fixtures/a5.spd"), 2, 1748, 2480),
    ],
)
def test_read_tiles_data(spd_file, tiles_data_length, width, height):
    tiles_data, w, h = read_tiles_data(spd_file)
    assert len(tiles_data) == tiles_data_length
    assert w == width
    assert h == height


@pytest.mark.parametrize(
    "spd_file",
    [
        (str(Path(__file__).parent / "fixtures/20250325_165251-blank.spd")),
        (str(Path(__file__).parent / "fixtures/20250325_165308-Layers.spd")),
        (str(Path(__file__).parent / "fixtures/a3.spd")),
        (str(Path(__file__).parent / "fixtures/a4.spd")),
        (str(Path(__file__).parent / "fixtures/a5.spd")),
    ],
)
def test_spd_to_png_succeeds(spd_file):
    with TemporaryDirectory() as tmpdir:
        img_path = spd_to_png(spd_file, tmpdir)
        assert os.path.exists(img_path)
