cmake_minimum_required(VERSION 3.10)
project(NoVirus)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_executable(NoVirus 
    src/main.cpp 
    src/ProcessScanner.cpp 
    src/ContextAnalyzer.cpp 
    src/Remediator.cpp
    src/CloudVerifier.cpp
    src/FileScanner.cpp
    src/BehavioralMonitor.cpp
)
