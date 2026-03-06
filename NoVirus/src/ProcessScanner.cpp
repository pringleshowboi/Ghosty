#include "ProcessScanner.h"
#include <windows.h>
#include <tlhelp32.h>
#include <iostream>

ProcessScanner::ProcessScanner() {}

std::vector<ProcessInfo> ProcessScanner::scan() {
    std::vector<ProcessInfo> processes;
    HANDLE hProcessSnap;
    PROCESSENTRY32 pe32;

    // Take a snapshot of all processes in the system.
    hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcessSnap == INVALID_HANDLE_VALUE) {
        std::cerr << "Error: CreateToolhelp32Snapshot failed." << std::endl;
        return processes;
    }

    pe32.dwSize = sizeof(PROCESSENTRY32);

    if (!Process32First(hProcessSnap, &pe32)) {
        std::cerr << "Error: Process32First failed." << std::endl;
        CloseHandle(hProcessSnap);
        return processes;
    }

    do {
        ProcessInfo info;
        info.pid = pe32.th32ProcessID;
        info.parentPid = pe32.th32ParentProcessID;
        info.name = std::string(pe32.szExeFile);
        processes.push_back(info);
    } while (Process32Next(hProcessSnap, &pe32));

    CloseHandle(hProcessSnap);
    return processes;
}

void ProcessScanner::printProcessList(const std::vector<ProcessInfo>& processes) {
    std::cout << "\n--- Process List (Contextual Foundation) ---\n";
    std::cout << "PID\tPPID\tName\n";
    std::cout << "--------------------------------------------\n";
    for (const auto& proc : processes) {
        std::cout << proc.pid << "\t" << proc.parentPid << "\t" << proc.name << "\n";
    }
    std::cout << "--------------------------------------------\n";
    std::cout << "Total Processes: " << processes.size() << "\n";
}
