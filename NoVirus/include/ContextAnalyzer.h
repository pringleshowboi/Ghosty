#pragma once
#include <vector>
#include <string>
#include "ProcessScanner.h"

struct SuspiciousActivity {
    ProcessInfo process;
    std::string reason;
    std::string severity; // "High", "Medium", "Low"
};

class ContextAnalyzer {
public:
    ContextAnalyzer(const std::vector<ProcessInfo>& processList);
    std::vector<SuspiciousActivity> analyze();
    void printReport(const std::vector<SuspiciousActivity>& activities);

private:
    std::vector<ProcessInfo> processes;
    
    // Helper to find parent process name
    std::string getProcessNameByPid(unsigned long pid);
    
    // Heuristics
    bool isSuspiciousParent(const ProcessInfo& proc, const std::string& parentName, std::string& outReason);
};
