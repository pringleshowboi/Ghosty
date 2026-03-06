#include <iostream>
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <filesystem>
#include "ProcessScanner.h"
#include "ContextAnalyzer.h"
#include "Remediator.h"
#include "FileScanner.h"
#include "BehavioralMonitor.h"

namespace fs = std::filesystem;

#include <set>

// Directory watcher simulation (in real world use ReadDirectoryChangesW)
void monitorDirectoryChanges(const std::string& path, BehavioralMonitor& monitor) {
    static std::set<std::string> previousFiles;
    std::set<std::string> currentFiles;
    
    try {
        if (fs::exists(path)) {
            for (const auto& entry : fs::recursive_directory_iterator(path)) {
                currentFiles.insert(entry.path().string());
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Directory monitor error: " << e.what() << std::endl;
        return;
    }

    // Check for new files
    for (const auto& file : currentFiles) {
        if (previousFiles.find(file) == previousFiles.end()) {
             monitor.logFileEvent(file, "CREATE");
        }
    }

    // Update state
    previousFiles = currentFiles;
}

void runScanLoop() {
    ProcessScanner procScanner;
    Remediator remediator;
    FileScanner fileScanner;
    BehavioralMonitor behMonitor;
    
    int loopCount = 0;

    while (true) {
        std::cout << "\n=== NoVirus Service Loop [" << ++loopCount << "] ===" << std::endl;

        // 1. Process Scan & Remediation
        std::vector<ProcessInfo> processes = procScanner.scan();
        ContextAnalyzer analyzer(processes);
        std::vector<SuspiciousActivity> alerts = analyzer.analyze();
        
        if (!alerts.empty()) {
            analyzer.printReport(alerts);
            remediator.remediate(alerts);
        }

        // 2. Behavioral Monitoring (Test #2)
        // Monitor test_scan_area for rapid file creation
        monitorDirectoryChanges("./test_scan_area", behMonitor);
        std::vector<std::string> behaviorAlerts = behMonitor.analyzeBehavior();
        for (const auto& alert : behaviorAlerts) {
            std::cout << "[!!!] BEHAVIORAL ALERT: " << alert << std::endl;
        }

        // 3. File Scan (Scanning current directory for demo)
        // Handles Test #1 (EICAR) and Test #3 (Heuristics)
        std::vector<FileThreat> fileThreats = fileScanner.scanDirectory("./test_scan_area");
        
        // Simple remediation for files (Delete)
        for (const auto& threat : fileThreats) {
            std::cout << "[REMEDIATION] Deleting file: " << threat.filePath << std::endl;
            if (std::remove(threat.filePath.c_str()) == 0) {
                std::cout << "SUCCESS: File removed." << std::endl;
            } else {
                std::cout << "FAILED: Could not remove file." << std::endl;
            }
        }

        std::cout << "Service sleeping..." << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}

int main(int argc, char* argv[]) {
    std::cout << "NoVirus Security Engine Starting..." << std::endl;
    
    bool serviceMode = false;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--service") {
            serviceMode = true;
        }
    }

    if (serviceMode) {
        std::cout << "Starting in SERVICE MODE (Continuous Monitoring)..." << std::endl;
        runScanLoop();
    } else {
        std::cout << "Running single pass scan..." << std::endl;
        
        // Single Pass Logic (Existing)
        ProcessScanner procScanner;
        std::cout << "\n[1] Scanning running processes..." << std::endl;
        std::vector<ProcessInfo> processes = procScanner.scan();

        std::cout << "\n[2] Analyzing behavioral context..." << std::endl;
        ContextAnalyzer analyzer(processes);
        std::vector<SuspiciousActivity> alerts = analyzer.analyze();
        analyzer.printReport(alerts);

        if (!alerts.empty()) {
            std::cout << "\n[3] Initiating Remediation..." << std::endl;
            Remediator remediator;
            remediator.remediate(alerts);
        } else {
            std::cout << "\nSystem is Clean. No active threats detected." << std::endl;
        }
    }

    return 0;
}
