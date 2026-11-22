# tests/gates/regiondump — RegionSet JSON emitter (lane p1-dump).
#
# Nested (after p0-gates lands tests/gates/CMakeLists.txt):
#   foreach(census regiondump buildtest) add_subdirectory(...)
#
# Standalone (this worktree, no tests/gates/CMakeLists.txt yet):
#   cmake -S tests/gates/regiondump -B build-dump -DCMAKE_BUILD_TYPE=Release
#   cmake --build build-dump -j
#
# Depth from this directory to the repo root is ../../..
# The EXISTS guard on src/refit_segment.cpp compiles stub_segment.cpp only while
# that TU is absent; when it lands, this file does not need to change.

cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_regiondump LANGUAGES CXX)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "regiondump standalone: do not recurse into tests/" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
endif()

if(NOT TARGET cad_mesh_recovery::harness)
    add_subdirectory("${_cad_mesh_recovery_root}/tests/harness"
                     "${CMAKE_CURRENT_BINARY_DIR}/_harness")
endif()

# Reconfigure when any P1 TU appears or disappears so the EXISTS switch below
# is not stale across a no-edit drop-in.
set(_p1_tus
    refit_math.cpp
    refit_grow.cpp
    refit_fillet.cpp
    refit_chains.cpp
    refit_segment.cpp)
foreach(_tu IN LISTS _p1_tus)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${_cad_mesh_recovery_root}/src/${_tu}")
endforeach()

set(_regiondump_sources dump_regionset.cpp)
set(_p1_all_present TRUE)
set(_p1_sources "")
foreach(_tu IN LISTS _p1_tus)
    set(_path "${_cad_mesh_recovery_root}/src/${_tu}")
    if(EXISTS "${_path}")
        list(APPEND _p1_sources "${_path}")
    else()
        set(_p1_all_present FALSE)
    endif()
endforeach()

# refit::segment lives in cad_mesh_recovery::core; cad_mesh_recovery::harness links it PUBLIC.
# Recompiling 1–4 P1 TUs into this executable while also linking core is the
# half-link defect (FINDINGS-0 D1): duplicate segment() symbols, stub winning
# at link, or silent divergence from the in-engine path.
set(_regiondump_use_core_refit FALSE)
if(TARGET cad_mesh_recovery::core AND EXISTS "${_cad_mesh_recovery_root}/src/refit_segment.cpp")
    set(_regiondump_use_core_refit TRUE)
    message(STATUS
        "cad_mesh_recovery_regiondump: refit from cad_mesh_recovery::core (no duplicate P1 compile)")
elseif(_p1_all_present)
    list(APPEND _regiondump_sources ${_p1_sources})
    message(STATUS
        "cad_mesh_recovery_regiondump: compiling 5/5 P1 TUs (no cad_mesh_recovery::core)")
else()
    list(APPEND _regiondump_sources stub_segment.cpp)
    message(WARNING
        "cad_mesh_recovery_regiondump: not all five P1 TUs present; compiling stub_segment.cpp")
endif()

add_executable(cad_mesh_recovery_regiondump ${_regiondump_sources})
target_compile_features(cad_mesh_recovery_regiondump PRIVATE cxx_std_17)
set_target_properties(cad_mesh_recovery_regiondump PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_link_libraries(cad_mesh_recovery_regiondump PRIVATE cad_mesh_recovery::harness)
target_include_directories(cad_mesh_recovery_regiondump PRIVATE
    "${_cad_mesh_recovery_root}/src")

if(NOT _regiondump_use_core_refit AND NOT _p1_all_present)
    target_compile_definitions(cad_mesh_recovery_regiondump PRIVATE CAD_MESH_RECOVERY_REGIONDUMP_STUB=1)
endif()

if(MSVC)
    target_compile_definitions(cad_mesh_recovery_regiondump PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()

# CTest hook lives here (this file is owned). Do not edit tests/CMakeLists.txt.
if(EXISTS "${_cad_mesh_recovery_root}/tests/p1_compose/CMakeLists.txt")
    add_subdirectory("${_cad_mesh_recovery_root}/tests/p1_compose"
                     "${CMAKE_CURRENT_BINARY_DIR}/_p1_compose")
endif()

unset(_regiondump_sources)
unset(_p1_tus)
unset(_p1_sources)
unset(_p1_all_present)
unset(_regiondump_use_core_refit)
unset(_tu)
unset(_path)
unset(_cad_mesh_recovery_root)

# ad-hoc signing (see root helper)
if(TARGET cad_mesh_recovery_regiondump)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_regiondump)
endif()
