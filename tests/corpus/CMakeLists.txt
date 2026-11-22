# tests/corpus — synthetic STL corpus + ground-truth sidecars (lane p0-gen).
#
# Standalone:
#   cmake -S tests/corpus -B build-corpus -DCMAKE_BUILD_TYPE=Release
#   cmake --build build-corpus -j
# Nested: picked up by tests/CMakeLists.txt once cad_mesh_recovery::core exists.

cmake_minimum_required(VERSION 3.16)

if(NOT TARGET cad_mesh_recovery::core)
    project(cad_mesh_recovery_corpus LANGUAGES CXX)
    get_filename_component(_cad_mesh_recovery_root "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
    if(EXISTS "${_cad_mesh_recovery_root}/CMakeLists.txt")
        set(CAD_MESH_RECOVERY_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(CAD_MESH_RECOVERY_INSTALL OFF CACHE BOOL "" FORCE)
        add_subdirectory("${_cad_mesh_recovery_root}" "${CMAKE_CURRENT_BINARY_DIR}/_engine")
    else()
        find_package(cad_mesh_recovery REQUIRED)
    endif()
    unset(_cad_mesh_recovery_root)
endif()

set(_corpus_out_dir "${CMAKE_CURRENT_SOURCE_DIR}")
set(_corpus_stamp "${CMAKE_CURRENT_BINARY_DIR}/corpus.stamp")

add_executable(cad_mesh_recovery_corpus_gen gen_corpus.cpp)
target_compile_features(cad_mesh_recovery_corpus_gen PRIVATE cxx_std_17)
target_link_libraries(cad_mesh_recovery_corpus_gen PRIVATE cad_mesh_recovery::core)
if(MSVC)
    target_compile_definitions(cad_mesh_recovery_corpus_gen PRIVATE _USE_MATH_DEFINES NOMINMAX)
endif()
# Generator uses MakeFillet/MakeChamfer (TKFillet), ThruSections (TKOffset),
# and booleans (TKBool). Those are NOT in the engine's OpenCASCADE::OpenCASCADE
# toolkit list. Resolve them in THIS directory: nested builds see the root
# find_package imported targets; standalone (`cmake -S tests/corpus`) does not,
# because that find_package ran inside add_subdirectory(_engine).
# Graft: re-run find_package HERE so OpenCASCADE_LIBRARY_DIR is populated in
# this directory's scope (standalone) before the find_library fallback.
if(NOT TARGET TKFillet OR NOT TARGET TKOffset OR NOT TARGET TKBool OR NOT TARGET TKMesh)
    find_package(OpenCASCADE REQUIRED)
endif()
# TKMesh: BRepMesh_IncrementalMesh in tessellate(). Homebrew's OCCT config
# links it transitively; Ubuntu's libocct 7.6 does not — name it explicitly.
foreach(_tk IN ITEMS TKFillet TKOffset TKBool TKMesh)
    if(TARGET ${_tk})
        target_link_libraries(cad_mesh_recovery_corpus_gen PRIVATE ${_tk})
    else()
        find_library(_corpus_${_tk}
            NAMES ${_tk}
            HINTS
                "${OpenCASCADE_LIBRARY_DIR}"
                "${OpenCASCADE_BINARY_DIR}"
                "${OpenCASCADE_ROOT}"
                "$ENV{OpenCASCADE_ROOT}"
                "$ENV{CASROOT}"
                ${CASROOT}
            PATH_SUFFIXES lib lib64 win64/vc14/lib
            PATHS
                /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu
                /opt/homebrew/lib /opt/local/lib)
        if(NOT _corpus_${_tk})
            message(FATAL_ERROR
                "cad_mesh_recovery_corpus_gen requires OCCT toolkit ${_tk} (imported target or library)")
        endif()
        target_link_libraries(cad_mesh_recovery_corpus_gen PRIVATE "${_corpus_${_tk}}")
    endif()
endforeach()
set_target_properties(cad_mesh_recovery_corpus_gen PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

add_executable(cad_mesh_recovery_corpus_check check_corpus.cpp)
target_compile_features(cad_mesh_recovery_corpus_check PRIVATE cxx_std_17)
target_link_libraries(cad_mesh_recovery_corpus_check PRIVATE cad_mesh_recovery::core)
set_target_properties(cad_mesh_recovery_corpus_check PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

add_custom_command(
    OUTPUT "${_corpus_stamp}"
    COMMAND cad_mesh_recovery_corpus_gen "${_corpus_out_dir}"
    COMMAND "${CMAKE_COMMAND}" -E touch "${_corpus_stamp}"
    DEPENDS cad_mesh_recovery_corpus_gen gen_corpus.cpp corpus_util.hpp
    COMMENT "Generating synthetic STL corpus fixtures"
    VERBATIM)

add_custom_target(cad_mesh_recovery_corpus_data ALL DEPENDS "${_corpus_stamp}")

# SPEC-fixtures (D-fc-1.12): ids the generator writes after S21. The existing
# corpus loops (corpus_generate, corpus_sidecar_check, and the phase-end
# corpus_engine_convert glob) pick them up from this directory. No new ctest:
# expected-red rows are orchestrator-owned (D-fc-1.14).
set(CAD_MESH_RECOVERY_CORPUS_FC_IDS
    S23_plane_fillet_lowfold
    S24_hem_uturn
    S25_peg_fillet
    S26_funnel_rev
    S27_sphere_corner_fine
    S28_varradius_negative
    S29_hex_law
    S30-open-crack
)

enable_testing()

add_test(NAME corpus_generate
    COMMAND cad_mesh_recovery_corpus_gen "${_corpus_out_dir}")
add_test(NAME corpus_sidecar_check
    COMMAND cad_mesh_recovery_corpus_check "${_corpus_out_dir}")
set_tests_properties(corpus_sidecar_check PROPERTIES
    DEPENDS corpus_generate)

add_test(NAME corpus_determinism
    COMMAND "${CMAKE_COMMAND}"
        -DGEN=$<TARGET_FILE:cad_mesh_recovery_corpus_gen>
        -DDIR_A=${CMAKE_CURRENT_BINARY_DIR}/_det_a
        -DDIR_B=${CMAKE_CURRENT_BINARY_DIR}/_det_b
        -P "${CMAKE_CURRENT_SOURCE_DIR}/check_corpus_determinism.cmake")

    if(TARGET cad_mesh_recovery)
    # A bare .sh has no shebang execution on Windows (ctest "Not Run");
    # invoke through bash when one exists (Git Bash on GitHub runners).
    find_program(CAD_MESH_RECOVERY_BASH bash)
    if(CAD_MESH_RECOVERY_BASH)
        set(_engine_check_cmd "${CAD_MESH_RECOVERY_BASH}"
            "${CMAKE_CURRENT_SOURCE_DIR}/run_engine_check.sh")
    else()
        set(_engine_check_cmd "${CMAKE_CURRENT_SOURCE_DIR}/run_engine_check.sh")
    endif()
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(NAME corpus_engine_convert
        COMMAND ${_engine_check_cmd}
                $<TARGET_FILE:cad_mesh_recovery>)
    # PYTHON: Git Bash `python3` is the Windows Store stub (Permission denied).
    # PYTHONUTF8=1: CMake ENVIRONMENT (not `set X=1 &&`, which poisons the value).
    set_tests_properties(corpus_engine_convert PROPERTIES
        ENVIRONMENT "CORPUS=${_corpus_out_dir};CENSUS=$<TARGET_FILE:cad_mesh_recovery_census>;PYTHON=${Python3_EXECUTABLE};PYTHONUTF8=1"
        DEPENDS corpus_generate)
endif()
