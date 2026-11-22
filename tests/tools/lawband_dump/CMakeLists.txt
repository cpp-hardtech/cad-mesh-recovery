# tests/tools/lawband_dump — throwaway dump of lawChainAccept on labeled bands.
cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_lawband_dump LANGUAGES CXX)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "lawband_dump standalone: do not recurse into tests/" FORCE)
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

add_executable(cad_mesh_recovery_lawband_dump lawband_dump.cpp)
target_compile_features(cad_mesh_recovery_lawband_dump PRIVATE cxx_std_17)
set_target_properties(cad_mesh_recovery_lawband_dump PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_link_libraries(cad_mesh_recovery_lawband_dump PRIVATE cad_mesh_recovery::harness)
target_include_directories(cad_mesh_recovery_lawband_dump PRIVATE
    "${_cad_mesh_recovery_root}/src"
    "${_cad_mesh_recovery_root}/tests/harness")
if(MSVC)
    target_compile_definitions(cad_mesh_recovery_lawband_dump PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_lawband_dump)
endif()
unset(_cad_mesh_recovery_root)
