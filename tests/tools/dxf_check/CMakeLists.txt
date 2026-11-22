# tests/tools/dxf_check — DXF round-trip reader + writeProfileDxf API probe.
cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_dxf_check LANGUAGES CXX)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "dxf_check standalone: do not recurse into tests/" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
endif()

add_executable(dxf_check dxf_check.cpp dxf_read.cpp)
target_compile_features(dxf_check PRIVATE cxx_std_17)
set_target_properties(dxf_check PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_link_libraries(dxf_check PRIVATE cad_mesh_recovery::core)
target_include_directories(dxf_check PRIVATE
    "${_cad_mesh_recovery_root}/src"
    "${CMAKE_CURRENT_SOURCE_DIR}")
if(MSVC)
    target_compile_definitions(dxf_check PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(dxf_check)
endif()

add_test(NAME dxf_export_api
    COMMAND dxf_check --self-test "${CMAKE_CURRENT_BINARY_DIR}/dxf_self")
set_tests_properties(dxf_export_api PROPERTIES
    LABELS "dxf;unit"
    TIMEOUT 60)

unset(_cad_mesh_recovery_root)
