#include "ContextAnalyzer.h"
#include <iostream>
#include <algorithm>

ContextAnalyzer::ContextAnalyzer(const std::vector<ProcessInfo>& processList) 
    : processes(processList) {}

std::string ContextAnalyzer::getProcessNameByPid(unsigned long pid) {
    for (const auto& p : processes) {
        if (p.pid == pid) {
            return p.name;
        }
    }
    return "Unknown";
}

std::vector<SuspiciousActivity> ContextAnalyzer::analyze() {
    std::vector<SuspiciousActivity> suspiciousList;

    for (const auto& proc : processes) {
        std::string parentName = getProcessNameByPid(proc.parentPid);
        std::string reason;

        if (isSuspiciousParent(proc, parentName, reason)) {
            SuspiciousActivity activity;
            activity.process = proc;
            activity.reason = reason;
            activity.severity = "High"; // Default to high for now
            suspiciousList.push_back(activity);
        }
    }

    return suspiciousList;
}

bool ContextAnalyzer::isSuspiciousParent(const ProcessInfo& proc, const std::string& parentName, std::string& outReason) {
    // 1. Check for Command Shells spawned by Non-System/Non-User apps
    // "Living off the Land" detection
    if (proc.name == "cmd.exe" || proc.name == "powershell.exe") {
        
        // Allowed Parents (Allow-list)
        if (parentName == "explorer.exe" || 
            parentName == "Trae.exe" || 
            parentName == "Code.exe" ||
            parentName == "conhost.exe" ||
            parentName == "winlogon.exe") {
            return false;
        }

        // Suspicious Parents (Block-list / Red Flags)
        if (parentName == "winword.exe" || 
            parentName == "excel.exe" || 
            parentName == "outlook.exe" || 
            parentName == "chrome.exe" ||
            parentName == "firefox.exe" ||
            parentName == "acrobat.exe") {
            outReason = "Shell spawned by application (" + parentName + ")";
            return true;
        }

        // Unknown parent spawning shell
        outReason = "Shell spawned by unknown/uncommon parent (" + parentName + ")";
        return true;
    }

    // 2. Check for System Tools spawned by Browsers
    if (proc.name == "net.exe" || proc.name == "whoami.exe" || proc.name == "ipconfig.exe") {
        if (parentName == "chrome.exe" || parentName == "msedge.exe") {
            outReason = "Reconnaissance tool spawned by browser";
            return true;
        }
    }

    return false;
}

void ContextAnalyzer::printReport(const std::vector<SuspiciousActivity>& activities) {
    std::cout << "\n--- Contextual Analysis Report ---\n";
    if (activities.empty()) {
        std::cout << "No suspicious behavioral patterns detected.\n";
    } else {
        std::cout << "DETECTED SUSPICIOUS ACTIVITY:\n";
        for (const auto& act : activities) {
            std::cout << "[!] " << act.severity << ": " << act.process.name 
                      << " (PID: " << act.process.pid << ")\n"
                      << "    Reason: " << act.reason << "\n"
                      << "    Parent PID: " << act.process.parentPid << "\n";
        }
    }
    std::cout << "----------------------------------\n";
}
