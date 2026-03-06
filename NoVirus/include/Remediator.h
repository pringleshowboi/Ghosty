#pragma once
#include "ContextAnalyzer.h"
#include <vector>

class Remediator {
public:
    Remediator();
    // Returns number of processes successfully terminated
    int remediate(const std::vector<SuspiciousActivity>& threats);

private:
    bool killProcess(unsigned long pid);
};
