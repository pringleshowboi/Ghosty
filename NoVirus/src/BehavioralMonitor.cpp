#include "BehavioralMonitor.h"
#include <iostream>
#include <algorithm>

BehavioralMonitor::BehavioralMonitor() {}

void BehavioralMonitor::logFileEvent(const std::string& filePath, const std::string& operation) {
    FileEvent event;
    event.filePath = filePath;
    event.operation = operation;
    event.timestamp = std::chrono::steady_clock::now();
    
    recentEvents.push_back(event);
    
    // Cleanup old events (sliding window)
    auto now = std::chrono::steady_clock::now();
    recentEvents.erase(std::remove_if(recentEvents.begin(), recentEvents.end(),
        [&](const FileEvent& e) {
            return std::chrono::duration_cast<std::chrono::seconds>(now - e.timestamp).count() > TIME_WINDOW_SECONDS;
        }), recentEvents.end());
}

std::vector<std::string> BehavioralMonitor::analyzeBehavior() {
    std::vector<std::string> alerts;
    
    // Check for Ransomware-like behavior (Mass Creation/Modification)
    int creationCount = 0;
    for (const auto& event : recentEvents) {
        if (event.operation == "CREATE" || event.operation == "MODIFY") {
            creationCount++;
        }
    }

    if (creationCount > RANSOMWARE_THRESHOLD) {
        alerts.push_back("Ransomware Behavior Detected: " + std::to_string(creationCount) + " file operations in 60s");
    }

    return alerts;
}
