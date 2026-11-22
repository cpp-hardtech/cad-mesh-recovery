# tests/harness — weld/split MeshView harness (lane p-meshview-harness).
#
# Nested (after p-cmake-scaffold lands):
#   tests/CMakeLists.txt does add_subdirectory(harness) once cad_mesh_recovery::core exists.
#
# Standalone (this worktree, no tests/CMakeLists.txt yet):
#   cmake -S tests/harness -B build-harness -DCMAKE_BUILD_TYPE=Release
#   cmake --build build-harness -j
# The guard below pulls in the parent engine project when cad_mesh_recovery::core is
# missing, with CAD_MESH_RECOVERY_BUILD_TESTS=OFF so a later root add_subdirectory(tests)
# cannot recurse back into this file.

cmake_minimum_required(VERSION 3.16)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_meshharness LANGUAGES CXX)
    get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "Harness standalone: do not recurse into tests/" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        # CLI stays ON so the same build tree can run engine-vs-harness comparison.
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
    unset(_cad_mesh_recovery_root)
endif()

add_library(cad_mesh_recovery_harness STATIC mesh_harness.cpp)
add_library(cad_mesh_recovery::harness ALIAS cad_mesh_recovery_harness)
target_compile_features(cad_mesh_recovery_harness PUBLIC cxx_std_17)
set_target_properties(cad_mesh_recovery_harness PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF)
target_include_directories(cad_mesh_recovery_harness PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../support")
target_link_libraries(cad_mesh_recovery_harness PUBLIC cad_mesh_recovery::core)

add_executable(cad_mesh_recovery_meshharness mesh_dump.cpp)
target_compile_features(cad_mesh_recovery_meshharness PRIVATE cxx_std_17)
target_link_libraries(cad_mesh_recovery_meshharness PRIVATE cad_mesh_recovery_harness)
set_target_properties(cad_mesh_recovery_meshharness PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

add_executable(cad_mesh_recovery_harness_test mesh_harness_test.cpp)
target_compile_features(cad_mesh_recovery_harness_test PRIVATE cxx_std_17)
target_link_libraries(cad_mesh_recovery_harness_test PRIVATE cad_mesh_recovery_harness)

enable_testing()

set(_harness_deg  "${CMAKE_CURRENT_SOURCE_DIR}/testdata/degenerate.stl")
set(_harness_two  "${CMAKE_CURRENT_SOURCE_DIR}/testdata/two_cubes.stl")
set(_harness_cube "${CMAKE_CURRENT_SOURCE_DIR}/../cube.stl")

add_test(NAME harness_fixtures
    COMMAND cad_mesh_recovery_harness_test
        "${_harness_deg}" "${_harness_two}" "${_harness_cube}")

add_test(NAME harness_dump_cube
    COMMAND cad_mesh_recovery_meshharness "${_harness_cube}")
set_tests_properties(harness_dump_cube PROPERTIES
    PASS_REGULAR_EXPRESSION
    "\"triangles\":12.*\"vertices\":8.*\"tris\":12.*\"vtx\":8.*\"edges\":18.*\"open\":0.*\"conflict\":0.*\"nonManifold\":0.*\"clean\":true")

add_test(NAME harness_determinism
    COMMAND "${CMAKE_COMMAND}"
        -DDUMP=$<TARGET_FILE:cad_mesh_recovery_meshharness>
        -DFILE1=${_harness_cube}
        -DFILE2=${_harness_deg}
        -DFILE3=${_harness_two}
        -P "${CMAKE_CURRENT_SOURCE_DIR}/check_determinism.cmake")

unset(_harness_deg)
unset(_harness_two)
unset(_harness_cube)

# ad-hoc signing (see root helper)
if(TARGET cad_mesh_recovery_meshharness)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_meshharness)
endif()
if(TARGET cad_mesh_recovery_harness_test)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_harness_test)
endif()
