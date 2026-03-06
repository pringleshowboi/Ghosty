#pragma once
#include <string>
#include <vector>
#include "CloudVerifier.h"

struct FileThreat {
    std::string filePath;
    std::string threatName;
};

class FileScanner {
public:
    FileScanner();
    std::vector<FileThreat> scanDirectory(const std::string& directoryPath);

private:
    CloudVerifier cloudVerifier;
    std::string calculateFileHash(const std::string& filePath);
    bool checkHeuristics(const std::string& filePath, std::string& outThreatName);
};
