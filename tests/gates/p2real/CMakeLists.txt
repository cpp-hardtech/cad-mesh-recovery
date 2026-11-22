# tests/gates/p2real — live RegionSet re-gate of refit::buildFaces.
# Picked up from tests/gates/p2buildtest/CMakeLists.txt (this lane owns both).
# Do not edit root CMakeLists.txt.

cmake_minimum_required(VERSION 3.16)

find_package(Python3 COMPONENTS Interpreter REQUIRED)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)

set(_p2real_script "${CMAKE_CURRENT_SOURCE_DIR}/run_p2real.py")

if(TARGET cad_mesh_recovery_p2buildtest AND TARGET cad_mesh_recovery_regiondump)
    add_test(NAME p2real_live
        COMMAND ${Python3_EXECUTABLE} ${_p2real_script}
                --repo ${_cad_mesh_recovery_root}
                --build-dir ${CMAKE_BINARY_DIR}
                --dump $<TARGET_FILE:cad_mesh_recovery_regiondump>
                --p2 $<TARGET_FILE:cad_mesh_recovery_p2buildtest>
                --corpus ${_cad_mesh_recovery_root}/tests/corpus
                --cube ${_cad_mesh_recovery_root}/tests/cube.stl
                --dumps-dir ${CMAKE_BINARY_DIR}/p1-dumps
                --sidecars ${_cad_mesh_recovery_root}/tests/corpus
                --compose-dump $<TARGET_FILE:cad_mesh_recovery_regiondump>)
    set_tests_properties(p2real_live PROPERTIES
        LABELS "gates;p2real"
        TIMEOUT 600)
endif()

unset(_cad_mesh_recovery_root)
unset(_p2real_script)
