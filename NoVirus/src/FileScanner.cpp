#include "FileScanner.h"
#include <windows.h>
#include <iostream>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <array>
#include <memory>
#include <regex>

// Use standard filesystem for directory iteration
namespace fs = std::filesystem;

FileScanner::FileScanner() {}

// Execute command and get output
std::string exec_cmd(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd, "r"), _pclose);
    if (!pipe) {
        return "";
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

std::vector<FileThreat> FileScanner::scanDirectory(const std::string& directoryPath) {
    std::vector<FileThreat> threats;

    std::cout << "Scanning directory: " << directoryPath << "..." << std::endl;

    try {
        if (!fs::exists(directoryPath)) {
            std::cerr << "Directory does not exist: " << directoryPath << std::endl;
            return threats;
        }

        for (const auto& entry : fs::recursive_directory_iterator(directoryPath)) {
            if (entry.is_regular_file()) {
                std::string filePath = entry.path().string();
                
                // 1. Signature Check (Cloud/Hash)
                std::string hash = calculateFileHash(filePath);
                
                // Special Case: Local EICAR Detection
                if (hash == "EICAR_TEST_FILE") {
                     FileThreat threat;
                     threat.filePath = filePath;
                     threat.threatName = "EICAR-Test-Signature";
                     threats.push_back(threat);
                     std::cout << "[!] MALWARE FOUND (Signature): " << filePath << " (EICAR-Test-Signature)" << std::endl;
                     continue;
                }

                std::string threatName;
                if (!hash.empty() && cloudVerifier.checkHash(hash, threatName)) {
                    FileThreat threat;
                    threat.filePath = filePath;
                    threat.threatName = threatName;
                    threats.push_back(threat);
                    std::cout << "[!] MALWARE FOUND (Signature): " << filePath << " (" << threatName << ")" << std::endl;
                    continue; // Skip heuristics if already found
                }

                // 2. Heuristic Check (Content Analysis)
                if (checkHeuristics(filePath, threatName)) {
                    FileThreat threat;
                    threat.filePath = filePath;
                    threat.threatName = threatName;
                    threats.push_back(threat);
                    std::cout << "[!] MALWARE FOUND (Heuristic): " << filePath << " (" << threatName << ")" << std::endl;
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Scan error: " << e.what() << std::endl;
    }

    return threats;
}

bool FileScanner::checkHeuristics(const std::string& filePath, std::string& outThreatName) {
    // Basic Static Heuristics for Scripts (PS1, BAT, VBS)
    std::string ext = filePath.substr(filePath.find_last_of(".") + 1);
    if (ext == "ps1" || ext == "bat" || ext == "vbs") {
        std::ifstream file(filePath);
        if (!file.is_open()) return false;
        
        std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
        
        // Test #3: Obfuscation Detection (Base64)
        // Regex to find large base64 strings or specific patterns
        // Simple check for "FromBase64String" which is common in obfuscated downloaders
        if (content.find("FromBase64String") != std::string::npos) {
            outThreatName = "Heuristic.Obfuscated.Script";
            return true;
        }
        
        // Check for "IEX" or "Invoke-Expression" (common for executing downloaded code)
        if (content.find("IEX") != std::string::npos || content.find("Invoke-Expression") != std::string::npos) {
             outThreatName = "Heuristic.PowerShell.Execution";
             return true;
        }
    }
    return false;
}

std::string FileScanner::calculateFileHash(const std::string& filePath) {
    // EICAR Test Check (Manual Override for safety tests)
    std::ifstream file(filePath);
    if (file.is_open()) {
        std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
        if (content.find("EICAR-STANDARD-ANTIVIRUS-TEST-FILE") != std::string::npos) {
            return "EICAR_TEST_FILE";
        }
    }

    // Use certutil to calculate SHA256
    std::string cmd = "certutil -hashfile \"" + filePath + "\" SHA256";
    std::string output = exec_cmd(cmd.c_str());

    std::istringstream iss(output);
    std::string line;
    bool nextIsHash = false;
    while (std::getline(iss, line)) {
        if (nextIsHash) {
            std::string hash;
            for (char c : line) {
                if (c != ' ' && c != '\r' && c != '\n') hash += c;
            }
            return hash;
        }
        if (line.find("SHA256") != std::string::npos) {
            nextIsHash = true;
        }
    }
    
    // Debug output if hash not found
    // std::cout << "Failed to parse hash for " << filePath << ". Output:\n" << output << std::endl;

    return "";
}
