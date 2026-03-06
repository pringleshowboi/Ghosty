#include "Remediator.h"
#include <windows.h>
#include <iostream>

Remediator::Remediator() {}

int Remediator::remediate(const std::vector<SuspiciousActivity>& threats) {
    if (threats.empty()) return 0;

    std::cout << "\n--- Remediation Protocol ---\n";
    int killedCount = 0;

    for (const auto& threat : threats) {
        if (threat.severity == "High") {
            std::cout << "[ATTEMPT] Terminating malicious process: " << threat.process.name 
                      << " (PID: " << threat.process.pid << ")... ";
            
            if (killProcess(threat.process.pid)) {
                std::cout << "SUCCESS." << std::endl;
                killedCount++;
            } else {
                std::cout << "FAILED. (Error Code: " << GetLastError() << ")" << std::endl;
            }
        } else {
            std::cout << "[SKIP] Low severity threat: " << threat.process.name << std::endl;
        }
    }
    
    return killedCount;
}

bool Remediator::killProcess(unsigned long pid) {
    HANDLE hProcess = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (hProcess == NULL) {
        return false;
    }

    bool result = TerminateProcess(hProcess, 1);
    CloseHandle(hProcess);
    return result;
}
