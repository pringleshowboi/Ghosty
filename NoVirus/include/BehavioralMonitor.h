#pragma once
#include <string>
#include <vector>
#include <map>
#include <chrono>

struct FileEvent {
    std::string filePath;
    std::chrono::steady_clock::time_point timestamp;
    std::string operation; // "CREATE", "MODIFY", "DELETE"
};

class BehavioralMonitor {
public:
    BehavioralMonitor();
    
    void logFileEvent(const std::string& filePath, const std::string& operation);
    std::vector<std::string> analyzeBehavior();

private:
    // PID -> List of file events
    // For simplicity in this demo, we assume single-process monitoring or global monitoring
    std::vector<FileEvent> recentEvents;
    
    // Config
    const int RANSOMWARE_THRESHOLD = 50; // Files per minute
    const int TIME_WINDOW_SECONDS = 60;
};
