#include "CloudVerifier.h"
#include <thread>
#include <chrono>
#include <array>
#include <memory>
#include <stdexcept>
#include <sstream>

CloudVerifier::CloudVerifier() {
    // SECURITY WARNING: In a real production app, never hardcode API keys.
    // Load from secure storage or environment variable.
    apiKey = "e49e768367dafb79fc8a9edced43946288c6018de9927d2ccad5d4249c69f59a";
}

bool CloudVerifier::checkHash(const std::string& fileHash, std::string& outThreatName) {
    // Respect API rate limits (Public API is limited to 4 requests/minute)
    std::cout << "[Cloud] Checking hash: " << fileHash << std::endl;
    // std::this_thread::sleep_for(std::chrono::seconds(15)); 

    return queryVirusTotal(fileHash, outThreatName);
}

// Helper to run shell command and get output
std::string exec(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd, "r"), _pclose);
    if (!pipe) {
        throw std::runtime_error("popen() failed!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

bool CloudVerifier::queryVirusTotal(const std::string& hash, std::string& outThreatName) {
    if (hash.empty()) return false;
    
    // Construct curl command
    // Note: Windows requires escaping inner quotes for JSON, but here we just need headers
    std::string cmd = "curl --silent --request GET --url https://www.virustotal.com/api/v3/files/" + hash + 
                      " --header \"x-apikey: " + apiKey + "\"";

    try {
        std::string jsonResponse = exec(cmd.c_str());
        
        // Simple string parsing for MVP (Avoid adding JSON library dependency for now)
        // We look for "malicious": N
        size_t malIdx = jsonResponse.find("\"malicious\":");
        if (malIdx != std::string::npos) {
            // Extract the count
            // Format is "malicious": 5,
            size_t start = malIdx + 12; // Length of "malicious":
            size_t end = jsonResponse.find(",", start);
            if (end != std::string::npos) {
                std::string countStr = jsonResponse.substr(start, end - start);
                int maliciousCount = std::stoi(countStr);
                
                if (maliciousCount > 0) {
                    outThreatName = "VirusTotal.Detection." + std::to_string(maliciousCount) + "Engines";
                    return true;
                }
            }
        }
        
        // Also check if file is not found (error code)
        if (jsonResponse.find("\"code\": \"NotFoundError\"") != std::string::npos) {
             std::cout << "[Cloud] File unknown to VirusTotal." << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << "[Cloud] Error querying API: " << e.what() << std::endl;
    }

    return false;
}
