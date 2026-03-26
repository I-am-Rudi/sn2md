#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: collect_md_png.sh <source_dir> <markdown_destination_dir> <png_destination_dir>

Recursively finds .md and .png files in <source_dir> (case-insensitive) and moves:
  - .md files to <markdown_destination_dir>
  - .png files to <png_destination_dir>

Behavior:
  - Fails before moving anything if destination filename collisions are detected.
  - Fails if a destination file already exists.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ $# -ne 3 ]]; then
    usage >&2
    exit 1
fi

source_dir=$1
md_dest=$2
png_dest=$3

if [[ ! -d "$source_dir" ]]; then
    echo "Error: source directory does not exist: $source_dir" >&2
    exit 1
fi

mkdir -p "$md_dest" "$png_dest"

declare -a md_files=()
declare -a png_files=()

while IFS= read -r -d '' file; do
    md_files+=("$file")
done < <(find "$source_dir" -type f -iname '*.md' -print0)

while IFS= read -r -d '' file; do
    png_files+=("$file")
done < <(find "$source_dir" -type f -iname '*.png' -print0)

declare -A md_targets=()
declare -A png_targets=()

for file in "${md_files[@]}"; do
    base_name=$(basename -- "$file")
    target_path="${md_dest%/}/$base_name"
    if [[ -e "$target_path" ]]; then
        echo "Error: destination already exists: $target_path" >&2
        exit 1
    fi
    if [[ -n "${md_targets[$target_path]+x}" ]]; then
        echo "Error: destination filename collision for markdown files:" >&2
        echo "  - ${md_targets[$target_path]}" >&2
        echo "  - $file" >&2
        echo "Both map to: $target_path" >&2
        exit 1
    fi
    md_targets["$target_path"]=$file
done

for file in "${png_files[@]}"; do
    base_name=$(basename -- "$file")
    target_path="${png_dest%/}/$base_name"
    if [[ -e "$target_path" ]]; then
        echo "Error: destination already exists: $target_path" >&2
        exit 1
    fi
    if [[ -n "${png_targets[$target_path]+x}" ]]; then
        echo "Error: destination filename collision for png files:" >&2
        echo "  - ${png_targets[$target_path]}" >&2
        echo "  - $file" >&2
        echo "Both map to: $target_path" >&2
        exit 1
    fi
    png_targets["$target_path"]=$file
done

moved_md=0
for file in "${md_files[@]}"; do
    mv -- "$file" "$md_dest/"
    ((moved_md += 1))
done

moved_png=0
for file in "${png_files[@]}"; do
    mv -- "$file" "$png_dest/"
    ((moved_png += 1))
done

echo "Move complete."
echo "Markdown files moved: $moved_md"
echo "PNG files moved: $moved_png"
