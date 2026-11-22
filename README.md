<p align="center">
  <img src=".github/branding/logo.png" alt="CAD Mesh Recovery logo" width="160">
</p>

<h1 align="center">CAD Mesh Recovery</h1>

**Convert STL meshes into STEP geometry for mechanical CAD workflows.**

CAD Mesh Recovery provides a C++17 library and command-line tool for recovering CAD geometry from triangle meshes. It builds on Open CASCADE Technology (OCCT) and runs locally on Linux, macOS, and Windows.

[Quick start](#quick-start) · [Conversion modes](#conversion-modes) · [C++ integration](#c-integration) · [Roadmap](#roadmap)

## What it does

- Reads binary and ASCII STL files and writes STEP AP203, AP214, or AP242.
- Splits disconnected bodies, welds duplicate vertices, merges coplanar triangles, and attempts to repair irregular meshes. Components that cannot close may be written as open shells with warnings.
- Recovers supported analytic surfaces from tessellated mechanical parts in TrueForm mode. It can also tessellate existing STEP geometry to binary STL.
- Reports conversion outcomes as machine-readable JSON through the CLI and through the C++ API.

STL stores triangle coordinates without a unit label, CAD feature history, or design tolerances. Specify the input units when needed. STEP output uses millimetres. Freeform, scanned, and heavily simplified geometry can remain faceted, and some inputs produce open shells or fail to convert.

## Quick start

Install a C++17 compiler, CMake, and OCCT development libraries. The CMake project declares a minimum of 3.16. Use CMake 3.21 or newer for the preset workflow below. OCCT 7.9.x is the baseline for the calibrated tests.

- **macOS with Homebrew** — `brew install opencascade`
- **Debian or Ubuntu** — `sudo apt install libocct-foundation-dev libocct-modeling-data-dev libocct-modeling-algorithms-dev libocct-data-exchange-dev`
- **Fedora** — `sudo dnf install opencascade-devel`
- **Arch Linux** — `sudo pacman -S opencascade`
- **Windows with vcpkg** — `vcpkg install opencascade`. Pass the vcpkg toolchain file to CMake with `-DCMAKE_TOOLCHAIN_FILE=<path>`.

The configure step uses the OCCT CMake package or the bundled finder. For a custom installation, pass `-DOpenCASCADE_ROOT=/path/to/occt` or add its prefix to `CMAKE_PREFIX_PATH`.

```sh
git clone https://github.com/cpp-hardtech/cad-mesh-recovery.git
cd cad-mesh-recovery
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
./build/stl2step part.stl
```

The final command expects `part.stl` in the current directory and writes `part.step` beside it. Visual Studio builds place the CLI at `build\Release\stl2step.exe`. The remaining examples assume the executable is on your `PATH`.

To build the example programs and run the project tests, use the `dev` preset.

```sh
cmake --preset dev
cmake --build --preset dev --config Release
ctest --preset dev -C Release
```

Tests calibrated for OCCT 7.9.x report a skip on older versions. Use `STL2STEP_BUILD_CLI`, `STL2STEP_BUILD_EXAMPLES`, `STL2STEP_BUILD_TESTS`, and `STL2STEP_INSTALL` to control build outputs.

## Conversion modes

- **Verbatim** is the default. It builds a boundary representation (B-Rep) from the mesh and merges coplanar faces where possible. Curved areas retain the input tessellation.
- **TrueForm** attempts analytic recovery of supported geometry, including planes, cylinders, chamfers, and some rounded transitions. It can reconstruct supported prismatic profiles and export DXF sections. Regions where recovery fails can retain their facets.

```sh
stl2step part.stl -o part-verbatim.step
stl2step part.stl --engine trueform -o part-analytic.step
stl2step part-in-inches.stl --units in --schema AP242 --threads 4
stl2step --mesh part-analytic.step -o preview.stl --edges preview.edges
```

For a supported prismatic part, pass `--dxf profiles` alongside `--engine trueform` to export a DXF per recognized level. Use `--quiet` to suppress progress output and `stl2step --help` to list available options. See the [reconstruction method](docs/METHOD.md) for the geometry and tolerance checks.

### Automation and verification

Conversion prints a final `RESULT {json}` line on standard output and sends diagnostics to standard error. Exit code **0** means conversion completed cleanly, **2** means a STEP file was written with warnings, and **1** means conversion failed. Check `openShells` and `warnings` when a downstream consumer requires closed solids.

By default the engine reopens the generated STEP for a volume check. The reported `volumeDeltaPct` compares the reopened file with the B-Rep sent to the writer. A source-to-output volume comparison can use `meshVolumeMM3` and `stepVolumeMM3`. The B-Rep validity check may be skipped above 50,000 faces, signalled by `"validityCheck":"skipped"`. Use `--no-verify` only when your integration handles verification separately.

Mesh mode accepts STEP input and emits `MESH_RESULT {json}` on standard output. It returns **0** on success and **1** on failure. The optional `--edges` file contains little-endian float32 endpoint pairs for drawing B-Rep edges. Each segment occupies 24 bytes.

## C++ integration

Link against `stl2step::core` and include [the public header](include/stl2step/stl2step.hpp). The public API uses C++ standard library types. OCCT is a build and link dependency.

```cpp
#include <stl2step/stl2step.hpp>

#include <iostream>

int main() {
    stl2step::Options options;
    options.input = "part.stl";
    options.output = "part.step";
    options.smooth = true;

    const auto result = stl2step::convert(options);
    std::cout << result.toJson() << '\n';
    return result.exitCode;
}
```

Use `Result::ok` and `Result::error` to inspect failures. Pass a `LogCallback` to receive progress and diagnostics. [The embedding example](examples/convert_min.cpp) shows how to use the callback and surface warnings.

To install the library and its CMake package, configure with `-DSTL2STEP_INSTALL=ON`, build, and install to your chosen prefix.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DSTL2STEP_INSTALL=ON
cmake --build build --config Release --parallel
cmake --install build --config Release --prefix /path/to/prefix
```

Add that prefix to `CMAKE_PREFIX_PATH` in the consuming project.

```cmake
find_package(stl2step CONFIG REQUIRED)
target_link_libraries(your_app PRIVATE stl2step::core)
```

You can also add the source tree with `add_subdirectory` or CMake's `FetchContent`. Use `stl2step::core` as the link target in either case. For subprocess integrations, see the [CLI integration recipes](AGENTS.md).

## Roadmap

The proposed focus is **offline batch migration of legacy mechanical part libraries**, with geometry QA for deciding which generated STEP files are ready for review or import. The following capabilities are planned.

- **Repeatable batches** — record input hashes, units, conversion options, and engine versions in a manifest so a batch can be resumed and rerun.
- **Geometry comparison** — measure sampled distances from source mesh to STEP surfaces and back, alongside changes in part bounds and volume.
- **Acceptance rules** — apply per-part tolerances, flag open shells and skipped checks, and produce a machine-readable report for review and CI.

## License

Distributed under the MIT License. The original copyright notice and the full
license text are retained in [LICENSE](LICENSE). Provenance and attribution
are documented in [NOTICE](NOTICE).
