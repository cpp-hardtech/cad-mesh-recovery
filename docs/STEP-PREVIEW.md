# Read STEP preview artifacts

`cad_mesh_recovery --mesh` tessellates a STEP file into a binary STL preview.
Add `--edges` to write a line-list overlay with endpoints in the same coordinate
system. Use distinct output paths for the STL preview and the edge file.

## Generate a preview

This command previews the bundled cylinder. Run it from the repository root
with `cad_mesh_recovery` on your `PATH`.

```sh
preview_dir=$(mktemp -d) &&
cad_mesh_recovery --mesh tests/mesh/seamed_cylinder.step --quiet \
  -o "$preview_dir/preview.stl" --edges "$preview_dir/preview.edges"
```

Exit code `0` indicates success. Use the `MESH_RESULT` line for the preview
diagnostics. To generate only the STL, omit the `--edges` option and its path.

## Read the files

The binary STL starts with an 80-byte header and a little-endian 32-bit triangle
count. Each triangle record occupies 50 bytes. The Format A edge file consists
of 24-byte records with six little-endian float32 values
`x0, y0, z0, x1, y1, z1`. Draw each record as one independent line segment.

`MESH_RESULT.edges` counts drawable B-Rep edges. A curved edge can contribute
several line segments, so use the number of 24-byte records when building the
overlay. For the bundled cylinder, OCCT 7.9.3 generated 176 triangles and
91 segments from 3 drawable B-Rep edges.

Save this Python 3 example as `read_preview.py`. Its `edge_segments()`
generator provides the two endpoints of each segment for a renderer.

```python
import argparse
import json
import math
import struct
from pathlib import Path


EDGE_RECORD = struct.Struct("<6f")


def triangle_count(path):
    with path.open("rb") as stream:
        header = stream.read(84)
        if len(header) != 84:
            raise ValueError(f"{path}: incomplete binary STL header")
        count, = struct.unpack_from("<I", header, 80)
        if count == 0 or stream.seek(0, 2) != 84 + 50 * count:
            raise ValueError(f"{path}: binary STL length or triangle count is invalid")
    return count


def edge_segments(path):
    with path.open("rb") as stream:
        while True:
            record = stream.read(EDGE_RECORD.size)
            if not record:
                return
            if len(record) != EDGE_RECORD.size:
                raise ValueError(f"{path}: incomplete edge segment")
            coords = EDGE_RECORD.unpack(record)
            if not all(map(math.isfinite, coords)):
                raise ValueError(f"{path}: edge coordinates must be finite")
            yield coords[:3], coords[3:]


def main():
    parser = argparse.ArgumentParser(description="Read CAD Mesh Recovery preview files")
    parser.add_argument("stl", type=Path)
    parser.add_argument("edges", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        summary = {"triangles": triangle_count(args.stl)}
        if args.edges is not None:
            summary["segments"] = sum(1 for _ in edge_segments(args.edges))
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
```

Invoke the reader with the file paths as arguments.

```sh
python3 read_preview.py "$preview_dir/preview.stl" "$preview_dir/preview.edges"
```

For an STL-only preview, pass just the STL path.
