# tests/gates/hybrid_validity — D3-8 pre-J4 BRepCheck unit (lane gates-g01).
#
# Standalone C++ against OCCT in the style of prism_unit / lawband_unit.
# Does not compile src/refit_build.cpp (h1-seams owns that TU this wave).

cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_hybrid_validity LANGUAGES CXX)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
endif()

if(NOT TARGET OpenCASCADE::OpenCASCADE)
    list(APPEND CMAKE_MODULE_PATH "${_cad_mesh_recovery_root}/cmake")
    find_package(OpenCASCADE REQUIRED)
endif()

find_package(Threads REQUIRED)

add_executable(cad_mesh_recovery_hybrid_validity_pre_j4 hybrid_validity_pre_j4.cpp)
target_compile_features(cad_mesh_recovery_hybrid_validity_pre_j4 PRIVATE cxx_std_17)
set_target_properties(cad_mesh_recovery_hybrid_validity_pre_j4 PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_link_libraries(cad_mesh_recovery_hybrid_validity_pre_j4 PRIVATE
    OpenCASCADE::OpenCASCADE
    Threads::Threads)
target_compile_definitions(cad_mesh_recovery_hybrid_validity_pre_j4 PRIVATE
    "HYBRID_VALIDITY_SOURCE=\"${CMAKE_CURRENT_SOURCE_DIR}/hybrid_validity_pre_j4.cpp\"")
if(MSVC)
    target_compile_definitions(cad_mesh_recovery_hybrid_validity_pre_j4 PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_hybrid_validity_pre_j4)
endif()

add_test(NAME hybrid_validity_pre_j4
    COMMAND cad_mesh_recovery_hybrid_validity_pre_j4)
set_tests_properties(hybrid_validity_pre_j4 PROPERTIES
    LABELS "gates;hybrid_validity"
    TIMEOUT 60)

add_test(NAME hybrid_validity_pre_j4_selftest
    COMMAND cad_mesh_recovery_hybrid_validity_pre_j4 --self-test)
set_tests_properties(hybrid_validity_pre_j4_selftest PROPERTIES
    LABELS "gates;hybrid_validity"
    TIMEOUT 30)

add_test(NAME hybrid_validity_pre_j4_synthetic
    COMMAND cad_mesh_recovery_hybrid_validity_pre_j4 --synthetic-pass)
set_tests_properties(hybrid_validity_pre_j4_synthetic PROPERTIES
    LABELS "gates;hybrid_validity"
    TIMEOUT 60)

add_test(NAME hybrid_validity_pre_j4_nosameparam
    COMMAND "${CMAKE_COMMAND}" -P "${CMAKE_CURRENT_SOURCE_DIR}/check_no_sameparam.cmake")
set_tests_properties(hybrid_validity_pre_j4_nosameparam PROPERTIES
    LABELS "gates;hybrid_validity"
    TIMEOUT 15)

unset(_cad_mesh_recovery_root)
