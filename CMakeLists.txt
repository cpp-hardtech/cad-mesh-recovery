cmake_minimum_required(VERSION 3.16)

# Ad-hoc codesign built executables on macOS: a freshly built unsigned binary
# doing heavy test I/O trips SentinelOne behavioral remediation (2026-08-25).
function(cad_mesh_recovery_adhoc_sign tgt)
  if(APPLE)
    add_custom_command(TARGET ${tgt} POST_BUILD
      COMMAND codesign --force --sign - $<TARGET_FILE:${tgt}>
      COMMENT "ad-hoc codesign ${tgt}" VERBATIM)
  endif()
endfunction()


project(cad_mesh_recovery
    VERSION 1.11.0
    DESCRIPTION "Universal STL (mesh) -> STEP (B-Rep solid) conversion engine"
    LANGUAGES CXX)

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------
option(CAD_MESH_RECOVERY_BUILD_CLI      "Build the cad_mesh_recovery command-line tool" ON)
option(CAD_MESH_RECOVERY_BUILD_EXAMPLES "Build the integration examples"       OFF)
option(CAD_MESH_RECOVERY_BUILD_TESTS    "Register the smoke test with CTest"
       ${PROJECT_IS_TOP_LEVEL})
option(CAD_MESH_RECOVERY_INSTALL        "Generate install + package-config rules"
       ${PROJECT_IS_TOP_LEVEL})

# Default to an optimised build when the caller did not pick one.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

find_package(Threads REQUIRED)
find_package(OpenCASCADE REQUIRED)

# D-I-5 / #8 — expose OCCT version to calibrated tests (one range: >= 7.9.x).
include("${CMAKE_CURRENT_SOURCE_DIR}/tests/support/occt_calibrated.cmake")
set(CAD_MESH_RECOVERY_OCCT_GENERATED_DIR "${CMAKE_BINARY_DIR}/generated")
file(MAKE_DIRECTORY "${CAD_MESH_RECOVERY_OCCT_GENERATED_DIR}")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/support/occt_calibrated.hpp.in"
    "${CAD_MESH_RECOVERY_OCCT_GENERATED_DIR}/occt_calibrated.hpp"
    @ONLY)
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/support/occt_calibrated.py.in"
    "${CAD_MESH_RECOVERY_OCCT_GENERATED_DIR}/occt_calibrated.py"
    @ONLY)

# ---------------------------------------------------------------------------
# Engine library
# ---------------------------------------------------------------------------
add_library(cad_mesh_recovery_core
    src/cad_mesh_recovery.cpp
    src/parallel.cpp
    src/stl_quant.cpp
    src/mesh.cpp
    src/refit_math.cpp
    src/refit_cone_math.cpp
    src/refit_torus_math.cpp
    src/refit_ellipse_math.cpp
    src/refit_cone_bind.cpp
    src/refit_union_census.cpp
    src/refit_ellipse_bind.cpp
    src/refit_grow.cpp
    src/refit_fillet.cpp
    src/refit_chains.cpp
    src/refit_island_absorb.cpp
    src/refit_segment.cpp
    src/refit_build.cpp
    src/refit_lawband.cpp
    src/refit_ngon.cpp
    src/refit_chamfer_cone.cpp
    src/refit_torus.cpp
    src/refit_profile_cert.cpp
    src/refit_anchored_round.cpp
    src/refit_drafted_cone.cpp
    src/refit_relational_extrude.cpp
    src/refit_relational_revolve.cpp
    src/refit_relational_reclaim.cpp
    src/refit_relational_sphere.cpp
    src/refit_relational_ruled.cpp
    src/refit_tesslaw.cpp
    src/refit_plane_circle.cpp
    src/refit_prism.cpp
    src/refit_profile.cpp
    src/refit_prism_build.cpp
    src/dxf_export.cpp)
add_library(cad_mesh_recovery::core ALIAS cad_mesh_recovery_core)

target_compile_features(cad_mesh_recovery_core PUBLIC cxx_std_17)
set_target_properties(cad_mesh_recovery_core PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON)

# On Windows an executable named `cad_mesh_recovery` also emits an import `cad_mesh_recovery.lib`,
# which collides with the static library's `cad_mesh_recovery.lib` (LNK1149). Keep the
# tidy `libcad_mesh_recovery.{a,so,dylib}` name on Unix; fall back to the target name
# (`cad_mesh_recovery_core.lib`) on Windows. CMake consumers link the `cad_mesh_recovery::core`
# target, so the on-disk name is transparent to them either way.
if(NOT WIN32)
    set_target_properties(cad_mesh_recovery_core PROPERTIES OUTPUT_NAME cad_mesh_recovery)
endif()

target_include_directories(cad_mesh_recovery_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)

target_link_libraries(cad_mesh_recovery_core
    PUBLIC  OpenCASCADE::OpenCASCADE
    PRIVATE Threads::Threads)

# ---------------------------------------------------------------------------
# Name every OpenCASCADE toolkit the sources actually use.
#
# `OpenCASCADE::OpenCASCADE` is our own INTERFACE target (cmake/FindOpenCASCADE.cmake),
# so it carries only the toolkits that finder happens to list. Anything it misses
# has to arrive by luck: some other toolkit's INTERFACE_LINK_LIBRARIES dragging it
# in, or a linker that keeps libraries nothing asked for. Debian/Ubuntu remove both
# crutches -- `ld --as-needed` is the distro default, and an OCCT laid out without a
# CMake package config (source install, $CASROOT/{inc,lib}, a vendored tree) reduces
# the finder to bare find_library results that carry no interface deps at all. The
# link line is then literally the list below, and a toolkit missing from it is a
# missing DSO: `BRepAlgoAPI_Fuse` -> TKBO and `BRepPrimAPI_MakePrism` -> TKPrim were
# both reached only transitively before, which is what github issue #1 reported.
#
# The list is the measured minimal cover of libcad_mesh_recovery.a's undefined symbols over
# all 51 OCCT toolkits -- nothing missing, no spares. Ordered most-dependent-first so
# a static OCCT resolves in one pass. OCCT >= 7.8 renamed the data-exchange toolkits
# (TKSTL -> TKDESTL; TKSTEP/TKSTEPBase/TKSTEPAttr/TKSTEP209 -> TKDESTEP); the old
# spellings are kept as alternates and only what this OCCT ships is linked.
# ---------------------------------------------------------------------------
set(_occt_toolkits
    TKDESTL      # StlAPI_Writer, RWStl
    TKDESTEP     # STEPControl_Reader / STEPControl_Writer
    TKXSBase     # Interface_Static, IFSelect_ReturnStatus
    TKMesh       # BRepMesh_IncrementalMesh, IMeshTools_Parameters (--mesh mode)
    TKShHealing  # ShapeFix_*, ShapeUpgrade_UnifySameDomain
    TKBO         # BRepAlgoAPI_Fuse, BOPAlgo_GlueEnum
    TKPrim       # BRepPrimAPI_MakePrism
    TKTopAlgo    # BRepBuilderAPI_*, BRepCheck_*, BRepClass3d_*, BRepGProp
    TKGeomAlgo   # GeomAPI_ProjectPointOnSurf, BRepLib_ValidateEdge
    TKBRep       # TopoDS_*, BRep_*, BRepTools*, BRepAdaptor_*, TopExp, TopTools
    TKGeomBase   # GC_MakeArcOfCircle, GeomProjLib, IntAna_QuadQuadGeo
    TKG3d        # Geom_*, Poly_*
    TKG2d        # Geom2d_*
    TKMath       # gp_*, TColgp_*, Bnd_Box, GProp_*, ElCLib, ElSLib
    TKernel)     # Standard_*, TColStd_*, Message_*, OSD
set(_occt_alt_TKDESTL  TKSTL)
set(_occt_alt_TKDESTEP TKSTEP TKSTEPBase TKSTEPAttr TKSTEP209)

foreach(_tk IN LISTS _occt_toolkits)
    # The canonical name first, then the pre-7.8 spellings it replaced.
    set(_occt_names ${_tk} ${_occt_alt_${_tk}})
    set(_occt_found FALSE)
    foreach(_name IN LISTS _occt_names)
        if(TARGET ${_name})
            target_link_libraries(cad_mesh_recovery_core PUBLIC ${_name})
            set(_occt_found TRUE)
        endif()
    endforeach()
    if(NOT _occt_found)
        # No imported target: OCCT was found without its config package. Resolve
        # by library name against the finder's own hints -- never a hard-coded path.
        foreach(_name IN LISTS _occt_names)
            find_library(CAD_MESH_RECOVERY_OCCT_${_name} NAMES ${_name}
                HINTS
                    "${OpenCASCADE_LIBRARY_DIR}"
                    "${OpenCASCADE_BINARY_DIR}"
                    ${OpenCASCADE_ROOT} $ENV{OpenCASCADE_ROOT} $ENV{CASROOT} ${CASROOT}
                PATH_SUFFIXES lib lib64 win64/vc14/lib
                PATHS
                    /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu
                    /opt/homebrew/lib /opt/local/lib)
            mark_as_advanced(CAD_MESH_RECOVERY_OCCT_${_name})
            if(CAD_MESH_RECOVERY_OCCT_${_name})
                target_link_libraries(cad_mesh_recovery_core PUBLIC "${CAD_MESH_RECOVERY_OCCT_${_name}}")
            endif()
        endforeach()
    endif()
endforeach()
unset(_occt_toolkits)
unset(_occt_alt_TKDESTL)
unset(_occt_alt_TKDESTEP)
unset(_occt_names)
unset(_occt_found)

if(MSVC)
    target_compile_definitions(cad_mesh_recovery_core PRIVATE _USE_MATH_DEFINES NOMINMAX)
    target_compile_options(cad_mesh_recovery_core PRIVATE /EHsc)
endif()

# Optional sanitizer instrumentation for the engine + anything that links it
# (CLI smoke, unit tests). Clang: ASan+UBSan. MSVC: /fsanitize=address.
# OCCT stays uninstrumented (we only add flags to our targets).
option(CAD_MESH_RECOVERY_SANITIZE "Build with AddressSanitizer (and UBSan on Clang)" OFF)
if(CAD_MESH_RECOVERY_SANITIZE)
    if(MSVC)
        target_compile_options(cad_mesh_recovery_core PUBLIC /fsanitize=address /Zi)
        target_link_options(cad_mesh_recovery_core PUBLIC /INCREMENTAL:NO)
    else()
        target_compile_options(cad_mesh_recovery_core PUBLIC
            -fsanitize=address,undefined -fno-omit-frame-pointer)
        target_link_options(cad_mesh_recovery_core PUBLIC -fsanitize=address,undefined)
    endif()
endif()

# ---------------------------------------------------------------------------
# Command-line tool
# ---------------------------------------------------------------------------
if(CAD_MESH_RECOVERY_BUILD_CLI)
    add_executable(cad_mesh_recovery src/main.cpp)
    target_link_libraries(cad_mesh_recovery PRIVATE cad_mesh_recovery::core)
    set_target_properties(cad_mesh_recovery PROPERTIES OUTPUT_NAME cad_mesh_recovery)
    if(CAD_MESH_RECOVERY_SANITIZE)
        if(MSVC)
            target_compile_options(cad_mesh_recovery PRIVATE /fsanitize=address /Zi)
            target_link_options(cad_mesh_recovery PRIVATE /INCREMENTAL:NO)
        else()
            target_compile_options(cad_mesh_recovery PRIVATE
                -fsanitize=address,undefined -fno-omit-frame-pointer)
            target_link_options(cad_mesh_recovery PRIVATE -fsanitize=address,undefined)
        endif()
    endif()
endif()

# ---------------------------------------------------------------------------
# Smoke test (converts the committed cube and expects a clean exit 0)
# ---------------------------------------------------------------------------
if(CAD_MESH_RECOVERY_BUILD_TESTS AND CAD_MESH_RECOVERY_BUILD_CLI)
    enable_testing()
    add_test(NAME convert_cube
        COMMAND cad_mesh_recovery "${CMAKE_CURRENT_SOURCE_DIR}/tests/cube.stl"
                         "${CMAKE_CURRENT_BINARY_DIR}/cube.step")
    set_tests_properties(convert_cube PROPERTIES
        PASS_REGULAR_EXPRESSION "\"ok\":true.*\"solids\":1.*\"volumeDeltaPct\":0")
    # Guard: CLI --version must equal the CMake project version (catches
    # CAD_MESH_RECOVERY_VERSION_* macros drifting from project(VERSION ...)).
    add_test(NAME version_matches_project
        COMMAND cad_mesh_recovery --version)
    string(REPLACE "." "\\." _cad_mesh_recovery_version_re "${PROJECT_VERSION}")
    set_tests_properties(version_matches_project PROPERTIES
        PASS_REGULAR_EXPRESSION "^cad_mesh_recovery ${_cad_mesh_recovery_version_re}[\r\n]*$")
    unset(_cad_mesh_recovery_version_re)
endif()

# ---------------------------------------------------------------------------
# Test / gate tree (corpus generator, censuses, region dumps, gate harnesses).
# Each tool owns its own CMakeLists so the lanes that add them never collide
# in this file.
# ---------------------------------------------------------------------------
if(CAD_MESH_RECOVERY_BUILD_TESTS)
    add_subdirectory(tests)
endif()

# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------
if(CAD_MESH_RECOVERY_BUILD_EXAMPLES)
    add_executable(convert_min examples/convert_min.cpp)
    target_link_libraries(convert_min PRIVATE cad_mesh_recovery::core)
endif()

# ---------------------------------------------------------------------------
# Install + package config  (lets downstream projects find_package(cad_mesh_recovery))
# ---------------------------------------------------------------------------
if(CAD_MESH_RECOVERY_INSTALL)
    include(GNUInstallDirs)
    include(CMakePackageConfigHelpers)

    set(_targets cad_mesh_recovery_core)
    if(CAD_MESH_RECOVERY_BUILD_CLI)
        list(APPEND _targets cad_mesh_recovery)
    endif()

    install(TARGETS ${_targets}
        EXPORT cad_mesh_recoveryTargets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})

    install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

    install(EXPORT cad_mesh_recoveryTargets
        NAMESPACE cad_mesh_recovery::
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/cad_mesh_recovery)

    # Ship the OCCT finder so downstream find_package(cad_mesh_recovery) can locate OCCT.
    install(FILES cmake/FindOpenCASCADE.cmake
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/cad_mesh_recovery)

    configure_package_config_file(
        cmake/cad_mesh_recoveryConfig.cmake.in
        "${CMAKE_CURRENT_BINARY_DIR}/cad_mesh_recoveryConfig.cmake"
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/cad_mesh_recovery)

    write_basic_package_version_file(
        "${CMAKE_CURRENT_BINARY_DIR}/cad_mesh_recoveryConfigVersion.cmake"
        VERSION ${PROJECT_VERSION}
        COMPATIBILITY SameMajorVersion)

    install(FILES
        "${CMAKE_CURRENT_BINARY_DIR}/cad_mesh_recoveryConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/cad_mesh_recoveryConfigVersion.cmake"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/cad_mesh_recovery)
endif()

# ad-hoc signing (see root helper)
if(TARGET cad_mesh_recovery)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery)
endif()
if(TARGET convert_min)
  cad_mesh_recovery_adhoc_sign(convert_min)
endif()
