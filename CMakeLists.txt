cmake_minimum_required(VERSION 3.18)

project(pandarm LANGUAGES CXX)

# ---------------------------------------------------------------------------
# C++ standard
# ---------------------------------------------------------------------------
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# nanobind
# ---------------------------------------------------------------------------
find_package(Python 3.10 COMPONENTS Interpreter Development.Module NumPy REQUIRED)

# Detect the installed nanobind package and import it into CMake
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)

# Suppress warnings from the vendored CH library (it uses old-style casts and
# signed/unsigned comparisons we don't want to fix right now — matches the
# former -w / /w flags in setup.py).
if(MSVC)
    add_compile_options(/W0)
else()
    add_compile_options(-w)
endif()

# ---------------------------------------------------------------------------
# OpenMP
#
# This replaces the ~40 lines of platform-specific clang/gcc/MSVC detection
# that lived in setup.py. CMake's FindOpenMP handles all of that, including
# the macOS conda/homebrew toolchain quirks.
# ---------------------------------------------------------------------------
find_package(OpenMP QUIET)
if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found — enabling multi-threaded preprocessing")
else()
    message(STATUS "OpenMP not found — building single-threaded fallback")
endif()

# ---------------------------------------------------------------------------
# Contraction-hierarchies library sources
# ---------------------------------------------------------------------------
set(CH_SOURCES
    src/contraction_hierarchies/src/libch.cpp
)

# ---------------------------------------------------------------------------
# pandarm engine sources
# ---------------------------------------------------------------------------
set(PANDARM_SOURCES
    src/accessibility.cpp
    src/graphalg.cpp
)

# ---------------------------------------------------------------------------
# nanobind extension
# ---------------------------------------------------------------------------
nanobind_add_module(
    cyaccess
    NOMINSIZE
    src/cyaccess_nb.cpp
    ${PANDARM_SOURCES}
    ${CH_SOURCES}
)

target_include_directories(cyaccess PRIVATE
    src
    src/contraction_hierarchies/src
    ${Python_NumPy_INCLUDE_DIRS}
)

# Python extension target → install into pandarm/ alongside the pure-Python package
set_target_properties(cyaccess PROPERTIES
    OUTPUT_NAME cyaccess
)

# ---------------------------------------------------------------------------
# Link OpenMP if available
# ---------------------------------------------------------------------------
if(OpenMP_CXX_FOUND)
    target_link_libraries(cyaccess PRIVATE OpenMP::OpenMP_CXX)
endif()

# ---------------------------------------------------------------------------
# Install the extension into the pandarm package directory
# ---------------------------------------------------------------------------
install(TARGETS cyaccess LIBRARY DESTINATION pandarm)