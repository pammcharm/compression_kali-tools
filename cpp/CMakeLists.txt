cmake_minimum_required(VERSION 3.20)
project(pamm_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(pamm_core STATIC src/pamm_core.cpp)
target_include_directories(pamm_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../include)
target_link_libraries(pamm_core PUBLIC z lzma)

add_executable(pamm_bench src/bench_stub.cpp)
target_link_libraries(pamm_bench PRIVATE pamm_core)
