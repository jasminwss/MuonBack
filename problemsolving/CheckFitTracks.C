// CheckFitTracks.C
#include <TTree.h>
#include <iostream>

void CheckFitTracks(TTree* t) {
    t->SetBranchStatus("*", 0);
    t->SetBranchStatus("FitTracks", 1);
    std::cout << "Versuche GetEntry(0)..." << std::endl;
    t->GetEntry(0);
    std::cout << "Kein Crash!" << std::endl;
}