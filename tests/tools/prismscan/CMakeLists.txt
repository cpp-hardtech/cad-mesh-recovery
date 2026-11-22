# tests/tools/prismscan — corpus routing census (AC3-P1).
cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_prismscan LANGUAGES CXX)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL
            "prismscan standalone: do not recurse into tests/" FORCE)
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

add_executable(prismscan prismscan.cpp)
target_compile_features(prismscan PRIVATE cxx_std_17)
set_target_properties(prismscan PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_link_libraries(prismscan PRIVATE cad_mesh_recovery::harness)
target_include_directories(prismscan PRIVATE
    "${_cad_mesh_recovery_root}/src"
    "${_cad_mesh_recovery_root}/tests/harness")
if(MSVC)
    target_compile_definitions(prismscan PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(prismscan)
endif()
unset(_cad_mesh_recovery_root)
