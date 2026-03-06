#pragma once
#include <vector>
#include <string>
#include <iostream>

struct ProcessInfo {
    unsigned long pid;
    unsigned long parentPid;
    std::string name;
    // Future: Add integrity level, user info, etc. for Contextual Awareness
};

class ProcessScanner {
public:
    ProcessScanner();
    std::vector<ProcessInfo> scan();
    void printProcessList(const std::vector<ProcessInfo>& processes);

private:
    // Helper to get process name from PID
    std::string getProcessName(unsigned long pid);
};
