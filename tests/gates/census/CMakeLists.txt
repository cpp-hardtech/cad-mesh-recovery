# tests/gates/census — independent STEP census (lane p0-census).
#
# Nested (after p0-gates lands tests/gates/CMakeLists.txt):
#   tests/gates/CMakeLists.txt does add_subdirectory(census) once cad_mesh_recovery::core
#   (and OpenCASCADE::OpenCASCADE) already exist.
#
# Standalone:
#   cmake -S tests/gates/census -B build-census -DCMAKE_BUILD_TYPE=Release
#   cmake --build build-census -j
# Depth from this directory to the repo root is ../../..

cmake_minimum_required(VERSION 3.16)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_census LANGUAGES CXX)
    get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "Census standalone: do not recurse into tests/" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
    unset(_cad_mesh_recovery_root)
endif()

# OpenCASCADE::OpenCASCADE is an IMPORTED target created without GLOBAL, so a
# subdirectory's copy is invisible here. Nested builds see the root's copy;
# standalone re-runs find_package in this directory (cache hit) to own the alias.
if(NOT TARGET OpenCASCADE::OpenCASCADE)
    get_filename_component(_census_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)
    list(APPEND CMAKE_MODULE_PATH "${_census_root}/cmake")
    find_package(OpenCASCADE REQUIRED)
    unset(_census_root)
endif()

# Link the CAD kernel, not cad_mesh_recovery::core. The census is a witness; sharing
# the defendant's translation units would make G2 / G2.5 circular.
add_executable(cad_mesh_recovery_census step_census.cpp)
target_compile_features(cad_mesh_recovery_census PRIVATE cxx_std_17)
target_link_libraries(cad_mesh_recovery_census PRIVATE OpenCASCADE::OpenCASCADE)
set_target_properties(cad_mesh_recovery_census PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

add_executable(cad_mesh_recovery_census_test census_test.cpp step_census.cpp)
target_compile_features(cad_mesh_recovery_census_test PRIVATE cxx_std_17)
target_compile_definitions(cad_mesh_recovery_census_test PRIVATE CAD_MESH_RECOVERY_CENSUS_NO_MAIN)
target_link_libraries(cad_mesh_recovery_census_test PRIVATE OpenCASCADE::OpenCASCADE)
set_target_properties(cad_mesh_recovery_census_test PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

# BRepPrimAPI_MakeCylinder lives in TKPrim, which the engine's imported
# OpenCASCADE::OpenCASCADE interface does not carry.
if(TARGET TKPrim)
    target_link_libraries(cad_mesh_recovery_census_test PRIVATE TKPrim)
else()
    find_library(CAD_MESH_RECOVERY_CENSUS_TKPRIM NAMES TKPrim)
    if(NOT CAD_MESH_RECOVERY_CENSUS_TKPRIM)
        message(FATAL_ERROR "TKPrim is required for the Seamed360 cylinder fixture")
    endif()
    target_link_libraries(cad_mesh_recovery_census_test PRIVATE "${CAD_MESH_RECOVERY_CENSUS_TKPRIM}")
endif()

if(MSVC)
    target_compile_definitions(cad_mesh_recovery_census PRIVATE _USE_MATH_DEFINES NOMINMAX)
    target_compile_definitions(cad_mesh_recovery_census_test PRIVATE _USE_MATH_DEFINES NOMINMAX)
    target_compile_options(cad_mesh_recovery_census PRIVATE /EHsc)
    target_compile_options(cad_mesh_recovery_census_test PRIVATE /EHsc)
endif()

enable_testing()

add_test(NAME census_cylinder
    COMMAND cad_mesh_recovery_census_test "${CMAKE_CURRENT_BINARY_DIR}")
set_tests_properties(census_cylinder PROPERTIES
    FIXTURES_SETUP census_files)

add_test(NAME census_determinism
    COMMAND "${CMAKE_COMMAND}"
        -DCENSUS=$<TARGET_FILE:cad_mesh_recovery_census>
        -DFILE=${CMAKE_CURRENT_BINARY_DIR}/seamed360.step
        -P "${CMAKE_CURRENT_SOURCE_DIR}/check_determinism.cmake")
set_tests_properties(census_determinism PROPERTIES
    FIXTURES_REQUIRED census_files)

add_test(NAME census_error
    COMMAND "${CMAKE_COMMAND}"
        -DCENSUS=$<TARGET_FILE:cad_mesh_recovery_census>
        -P "${CMAKE_CURRENT_SOURCE_DIR}/check_error.cmake")

# ad-hoc signing (see root helper)
if(TARGET cad_mesh_recovery_census)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_census)
endif()
if(TARGET cad_mesh_recovery_census_test)
  cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_census_test)
endif()
