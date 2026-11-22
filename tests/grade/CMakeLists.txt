# tests/grade — mesh-oracle recovery grader (D-140-1).
# Standalone graft finds OCCT via the repo module (never CONFIG from here).
cmake_minimum_required(VERSION 3.16)

get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)

list(APPEND CMAKE_MODULE_PATH "${_cad_mesh_recovery_root}/cmake")
if(NOT DEFINED CAD_MESH_RECOVERY_OCCT_SKIP_EXIT_CODE)
    include("${CMAKE_CURRENT_SOURCE_DIR}/../support/occt_calibrated.cmake")
endif()
if(NOT TARGET OpenCASCADE::OpenCASCADE)
    project(cad_mesh_recovery_grade_tool LANGUAGES CXX)
    find_package(OpenCASCADE REQUIRED)
endif()

set(_grade_srcs
    grade_mesh.cpp
    grade_oracle.cpp
    grade_step.cpp
    grade_compare.cpp
    grade_report.cpp
    "${_cad_mesh_recovery_root}/src/stl_quant.cpp")

add_executable(cad_mesh_recovery_grade grade_main.cpp ${_grade_srcs})
target_compile_features(cad_mesh_recovery_grade PRIVATE cxx_std_17)
set_target_properties(cad_mesh_recovery_grade PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_include_directories(cad_mesh_recovery_grade PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${_cad_mesh_recovery_root}/src")
target_link_libraries(cad_mesh_recovery_grade PRIVATE OpenCASCADE::OpenCASCADE)
if(MSVC)
    target_compile_definitions(cad_mesh_recovery_grade PRIVATE _USE_MATH_DEFINES NOMINMAX)
    target_compile_options(cad_mesh_recovery_grade PRIVATE /bigobj /EHsc)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_grade)
endif()

add_executable(cad_mesh_recovery_grade_selftest grade_selftest.cpp ${_grade_srcs})
target_compile_features(cad_mesh_recovery_grade_selftest PRIVATE cxx_std_17)
set_target_properties(cad_mesh_recovery_grade_selftest PROPERTIES
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
target_include_directories(cad_mesh_recovery_grade_selftest PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${_cad_mesh_recovery_root}/src"
    "${CMAKE_BINARY_DIR}/generated")
target_link_libraries(cad_mesh_recovery_grade_selftest PRIVATE OpenCASCADE::OpenCASCADE)
# D-140-7 / D-130-23: recorded-deferral list, resolved from the source tree at
# configure time (the same file run_gates.py's DEFAULT_BASELINE resolves).
target_compile_definitions(cad_mesh_recovery_grade_selftest PRIVATE
    CAD_MESH_RECOVERY_EXPECTED_RED_JSON="${_cad_mesh_recovery_root}/tests/gates/baseline/expected-red.json")
# Synthetic STEPs (cases 5–8) need TKPrim / sewing primitives when present.
foreach(_tk IN ITEMS TKPrim TKBool TKFillet)
    if(TARGET ${_tk})
        target_link_libraries(cad_mesh_recovery_grade_selftest PRIVATE ${_tk})
    endif()
endforeach()
if(MSVC)
    target_compile_definitions(cad_mesh_recovery_grade_selftest PRIVATE _USE_MATH_DEFINES NOMINMAX)
    target_compile_options(cad_mesh_recovery_grade_selftest PRIVATE /bigobj /EHsc)
endif()
if(COMMAND cad_mesh_recovery_adhoc_sign)
    cad_mesh_recovery_adhoc_sign(cad_mesh_recovery_grade_selftest)
endif()

add_test(NAME grade_selftest
    COMMAND cad_mesh_recovery_grade_selftest core "${_cad_mesh_recovery_root}/tests/corpus")
add_test(NAME grade_synthetic
    COMMAND cad_mesh_recovery_grade_selftest synthetic "${_cad_mesh_recovery_root}/tests/corpus")
add_test(NAME grade_selftest_ascii
    COMMAND cad_mesh_recovery_grade_selftest ascii "${_cad_mesh_recovery_root}/tests/corpus")
add_test(NAME grade_independence
    COMMAND "${CMAKE_COMMAND}" -P "${CMAKE_CURRENT_SOURCE_DIR}/check_independence.cmake")
set_tests_properties(grade_selftest
    PROPERTIES
        LABELS "grade"
        # D-train-push-5: hosted windows grade_selftest 1089.46 s (run 35847345961, ce1024b); 1089.46×1.5=1634.19→ceil600→TIMEOUT 1800.
        TIMEOUT 1800
        SKIP_RETURN_CODE ${CAD_MESH_RECOVERY_OCCT_SKIP_EXIT_CODE})
set_tests_properties(grade_synthetic grade_selftest_ascii grade_independence
    PROPERTIES LABELS "grade" TIMEOUT 300)

unset(_grade_srcs)
unset(_cad_mesh_recovery_root)
