#pragma once
#include <string>
#include <iostream>

class CloudVerifier {
public:
    CloudVerifier();
    
    // Returns true if the hash is flagged as malicious
    bool checkHash(const std::string& fileHash, std::string& outThreatName);

private:
    std::string apiKey;
    
    // Perform actual HTTP request to VirusTotal using curl
    bool queryVirusTotal(const std::string& hash, std::string& outThreatName);
};
