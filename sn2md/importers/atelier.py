import io
import logging
import os
import sqlite3

import supernotelib as sn
from PIL import Image

from sn2md.types import ImageExtractor

logger = logging.getLogger(__name__)

TILE_PIXELS = 128
STRIDE = 4096
# Magic number for the upper left tile in an SPD file
START_INDEX = 7976857


def tid_to_row_col(tid):
    offset = tid - START_INDEX
    col = offset % STRIDE
    row = offset // STRIDE
    return row, col


def find_max_x_y(tile_dict: list[dict]) -> tuple[int, int]:
    max_x = 0
    max_y = 0

    for tile_data in tile_dict:
        for tid in tile_data.keys():
            row, col = tid_to_row_col(tid)
            x = row * TILE_PIXELS
            y = col * TILE_PIXELS

            # Update max_x and max_y
            max_x = max(max_x, x + TILE_PIXELS)
            max_y = max(max_y, y + TILE_PIXELS)
    return max_x, max_y


def clean_bad_tids_from_tiles_data(tiles_data):
    # Some files will have tiles that are out of bounds, remove them.
    cleaned_data = [
        {
            k: v for k, v in tiles_dict.items() if (
                row_col := tid_to_row_col(k)
            )[0] < 100 and row_col[1] < 100
        } for tiles_dict in tiles_data
    ]

    for i, cd in enumerate(cleaned_data):
        if len(cd) != len(tiles_data[i]):
            logger.warning("Removed %d tiles from layer %d", len(tiles_data[i]) - len(cd), i)

    return cleaned_data



def read_tiles_data(spd_file_path: str) -> list[dict]:
    conn = sqlite3.connect(spd_file_path)
    cursor = conn.cursor()

    # Check the format version - only version 2 is supported at present
    cursor.execute("select value from config where name='fmt_ver';")
    version = cursor.fetchone()[0].decode("utf-8")
    if version != "2":
        raise ValueError(f"Unsupported SPD format version: {version}")

    cursor.execute("select value from config where name='ls';")
    layers = [v for v in cursor.fetchone()[0].decode("utf-8").split("\n") if len(v) > 0]

    def is_not_visible(x):
        return x.endswith("\x00")

    tiles_data = []
    # Iterate over the layers from the top layer to the bottom layer
    for layer in layers:
        if is_not_visible(layer):
            continue
        # Fetch tiles, ordering them by tid.  Replace with the hardcoded `tids` list
        surface_idx = ord(layer[2])
        cursor.execute(f"SELECT tid, tile FROM surface_{surface_idx} ORDER BY tid ASC;")
        tile_dict = {tid: tile_data for tid, tile_data in cursor.fetchall()}
        tiles_data.append(tile_dict)

    conn.close()

    return clean_bad_tids_from_tiles_data(tiles_data)


def spd_to_png(spd_file_path: str, output_path: str) -> str:
    tiles_data = read_tiles_data(spd_file_path)
    logger.debug("Number of layers: %d", len(tiles_data))

    x_y = find_max_x_y(tiles_data)
    # Ensure that even if the layers are all empty, we create a blank image
    if x_y == (0, 0):
        x_y = (TILE_PIXELS * 12, TILE_PIXELS * 16)
    logger.debug("output size: %s", x_y)
    full_image = Image.new("RGBA", x_y)

    for tile_dict in reversed(tiles_data):
        for tid in tile_dict.keys():
            tile_data = tile_dict[tid]
            tile = Image.open(io.BytesIO(tile_data)).convert("RGBA")

            assert tile.size == (TILE_PIXELS, TILE_PIXELS)

            row, col = tid_to_row_col(tid)
            x = row * TILE_PIXELS
            y = col * TILE_PIXELS

            # Blend the tile image with the full image
            tile_image = Image.new("RGBA", x_y)
            tile_image.paste(tile, (x, y))
            full_image = Image.alpha_composite(full_image, tile_image)

    full_image_with_white_bg = Image.new("RGB", x_y, (255, 255, 255))
    full_image_with_white_bg.paste(full_image, (0, 0), full_image)

    image_path = (
        output_path
        + "/"
        + os.path.splitext(os.path.basename(spd_file_path))[0]
        + ".png"
    )
    full_image_with_white_bg.save(image_path)

    return image_path


class AtelierExtractor(ImageExtractor):
    def extract_images(self, filename: str, output_path: str) -> list[str]:
        return [spd_to_png(filename, output_path)]

    def get_notebook(self, filename: str) -> sn.Notebook | None:
        return None
