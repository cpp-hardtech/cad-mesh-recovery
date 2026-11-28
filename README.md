<p align="center">
  <img src=".github/branding/logo.png" alt="CAD Mesh Recovery logo" width="160">
</p>

<h1 align="center">CAD Mesh Recovery</h1>

**Convert triangle meshes into STEP solid geometry for mechanical CAD workflows.**

CAD Mesh Recovery reads STL meshes and writes STEP files that a CAD system can open as
boundary representations. It ships as a C++17 library plus a command-line tool, builds on
Open CASCADE Technology (OCCT), and runs on Linux, macOS, and Windows.

The tool exists for the case where the mesh is all that is left of a part: scanning, legacy
exports, or a supplier that only delivered STL. It reconstructs as much structure as the
tessellation supports and says plainly when it could not.

## What it does

- Reads binary and ASCII STL and writes STEP AP203, AP214, or AP242.
- Splits disconnected bodies, welds duplicate vertices, merges coplanar triangles, and
  attempts to repair irregular meshes. Components that cannot close may be written as open
  shells, with warnings.
- Recovers supported analytic surfaces from tessellated mechanical parts in `trueform` mode,
  and can tessellate existing STEP geometry back to binary STL.
- Reports the outcome as machine-readable JSON on standard output.

STL stores coordinates without a unit label, no feature history, and no design tolerances.
State the input units when needed; STEP output is written in millimetres. Freeform, scanned,
and heavily simplified geometry can stay faceted, and some inputs produce open shells or fail
to convert.

## Requirements

- A C++17 compiler and CMake 3.16 or newer. CMake 3.21 or newer is needed for the preset
  workflow.
- OCCT development libraries. The calibrated tests use OCCT 7.9.x as their baseline and
  report a skip on older versions.

Installing OCCT:

| Platform | Command |
| --- | --- |
| macOS (Homebrew) | `brew install opencascade` |
| Debian / Ubuntu | `sudo apt install libocct-foundation-dev libocct-modeling-data-dev libocct-modeling-algorithms-dev libocct-data-exchange-dev` |
| Fedora | `sudo dnf install opencascade-devel` |
| Arch Linux | `sudo pacman -S opencascade` |
| Windows (vcpkg) | `vcpkg install opencascade`, then pass `-DCMAKE_TOOLCHAIN_FILE=<path>` |

Configuration uses the OCCT CMake package or the bundled finder. For a custom installation,
pass `-DOpenCASCADE_ROOT=/path/to/occt` or add its prefix to `CMAKE_PREFIX_PATH`.

## Build

```sh
git clone https://github.com/cpp-hardtech/cad-mesh-recovery.git
cd cad-mesh-recovery
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
./build/cad_mesh_recovery part.stl
```

The last command expects `part.stl` in the working directory and writes `part.step` beside it.
Visual Studio builds place the CLI at `build\Release\cad_mesh_recovery.exe`.

To build the examples and run the tests, use the `dev` preset:

```sh
cmake --preset dev
cmake --build --preset dev --config Release
ctest --preset dev -C Release
```

Build outputs are controlled by `CAD_MESH_RECOVERY_BUILD_CLI`,
`CAD_MESH_RECOVERY_BUILD_EXAMPLES`, `CAD_MESH_RECOVERY_BUILD_TESTS`, and
`CAD_MESH_RECOVERY_INSTALL`.

## Conversion modes

- **Verbatim** (default) builds a boundary representation from the mesh and merges coplanar
  faces where possible. Curved areas keep the input tessellation.
- **TrueForm** attempts analytic recovery of supported geometry — planes, cylinders, chamfers,
  and some rounded transitions. It can reconstruct supported prismatic profiles and export
  DXF sections. Regions where recovery fails keep their facets.

```sh
cad_mesh_recovery part.stl -o part-verbatim.step
cad_mesh_recovery part.stl --engine trueform -o part-analytic.step
cad_mesh_recovery part-in-inches.stl --units in --schema AP242 --threads 4
cad_mesh_recovery --mesh part-analytic.step -o preview.stl --edges preview.edges
```

For a supported prismatic part, add `--dxf profiles` together with `--engine trueform` to
export one DXF per recognised level. `cad_mesh_recovery --help` lists every option. The
geometry and tolerance checks are described in [docs/METHOD.md](docs/METHOD.md).

## Command-line reference

| Group | Option | Purpose |
| --- | --- | --- |
| Input | `--units <unit>` | Unit of the input coordinates. |
| Input | `--scale <factor>` | Apply a uniform scale factor. |
| Output | `-o <file>` | Output STEP path. |
| Output | `--schema <schema>` | STEP schema: `AP203`, `AP214`, or `AP242`. |
| Engine | `--engine <mode>` | `verbatim` (default) or `trueform`. |
| Mesh | `--mesh <file>` | Tessellate a STEP file instead of converting a mesh. |
| Mesh | `--edges <file>` | Write B-Rep edge segments as little-endian float32 pairs. |
| Repair | `--weld` | Weld duplicate vertices. |
| Repair | `--unify-angle <deg>` | Threshold for unifying faces. |
| Repair | `--force-sew` | Force sewing of the result. |
| Repair | `--sew-tol <tol>` | Sewing tolerance. |
| Repair | `--no-unify` | Skip face unification. |
| Repair | `--no-solid` | Do not require a closed solid. |
| Smoothing | `--smooth` | Enable surface smoothing. |
| Smoothing | `--smooth-angle <deg>` | Angle threshold for smoothing. |
| Smoothing | `--smooth-tol <tol>` | Tolerance for smoothing. |
| Smoothing | `--no-smooth` | Disable smoothing. |
| Smoothing | `--no-smooth-fillets` | Leave fillets unsmoothed. |
| Smoothing | `--refit` | Refit surfaces after smoothing. |
| Performance | `--threads <n>` | Worker thread count. |
| Verification | `--no-verify` | Skip the reopen and volume check. |
| Output | `--dxf <mode>` | Export DXF sections (`profiles`). |
| Output | `--quiet` | Suppress progress output. |
| Info | `-h, --help` | Print usage and exit. |
| Info | `-v, --version` | Print the version and exit. |

## Output contract

Conversion prints a final `RESULT {json}` line on standard output and sends diagnostics to
standard error.

| Exit code | Meaning |
| --- | --- |
| `0` | Conversion completed cleanly. |
| `2` | A STEP file was written, with warnings. |
| `1` | Conversion failed. |

By default the engine reopens the generated STEP for a volume check and reports
`volumeDeltaPct`, which compares the reopened file against the B-Rep that was written. A
source-to-output comparison can use `meshVolumeMM3` and `stepVolumeMM3`. Above 50,000 faces
the B-Rep validity check may be skipped and reports `"validityCheck":"skipped"`. Check
`openShells` and `warnings` when a downstream consumer requires closed solids.

See [Publish verified closed-solid STEP files](docs/VERIFIED-STEP.md) for a
runnable intake workflow that checks the result before publishing the STEP.

Mesh mode accepts STEP input and prints `MESH_RESULT {json}`, returning `0` on success and `1`
on failure. The optional `--edges` file holds 24-byte records: little-endian float32 endpoint
pairs for drawing B-Rep edges.

## C++ integration

Link against `cad_mesh_recovery::core` and include
[the public header](include/cad_mesh_recovery/cad_mesh_recovery.hpp). The public API uses only
C++ standard library types; OCCT remains a build and link dependency.

```cpp
#include <cad_mesh_recovery/cad_mesh_recovery.hpp>

#include <iostream>

int main() {
    cad_mesh_recovery::Options options;
    options.input = "part.stl";
    options.output = "part.step";
    options.smooth = true;

    const auto result = cad_mesh_recovery::convert(options);
    std::cout << result.toJson() << '\n';
    return result.exitCode;
}
```

Inspect failures through `Result::ok` and `Result::error`. Pass a `LogCallback` to receive
progress and diagnostics; [examples/convert_min.cpp](examples/convert_min.cpp) shows the
callback and how to surface warnings.

To install the library and its CMake package:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCAD_MESH_RECOVERY_INSTALL=ON
cmake --build build --config Release --parallel
cmake --install build --config Release --prefix /path/to/prefix
```

Then add that prefix to `CMAKE_PREFIX_PATH` and link the imported target:

```cmake
find_package(cad_mesh_recovery CONFIG REQUIRED)
target_link_libraries(your_app PRIVATE cad_mesh_recovery::core)
```

`add_subdirectory` and CMake's `FetchContent` work as well; the link target is the same. For
subprocess integrations, see the CLI recipes in [AGENTS.md](AGENTS.md).

## Documentation

- [Reconstruction method](docs/METHOD.md)
- [CLI integration recipes](AGENTS.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Distributed under the MIT License. The original copyright notice and the full license text
are retained in [LICENSE](LICENSE).

This software links against Open CASCADE Technology, which is licensed under LGPL-2.1 with an
additional exception. OCCT is a separate dependency and is not bundled with this source tree.
