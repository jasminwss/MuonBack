#include <TFile.h>
#include <TGeoManager.h>
#include <TGeoNode.h>
#include <TGeoVolume.h>
#include <TGeoBBox.h>
#include <TGeoNavigator.h>
#include <TMath.h>
#include <map>
#include <set>
#include <cstdio>

double Phicalc(double x, double y) {
    double r = TMath::Sqrt(x*x+y*y);
    if (r == 0) return 1e9;
    double phi;
    if (y >= 0) phi = TMath::ACos(x/r);
    else phi = -1*TMath::ACos(x/r) + 2*TMath::Pi();
    phi = phi*180/TMath::Pi();
    phi = fmod(phi+90, 360.0);
    return phi;
}

void list_veto_cells() {
    TFile* f = TFile::Open("/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root");
    TGeoManager* geo = (TGeoManager*)f->Get("FAIRGeom");
    gGeoManager = geo;
    TGeoNavigator* nav = geo->GetCurrentNavigator();
    if (!nav) nav = geo->AddNavigator();

    if (!nav->cd("cave/DecayVolume_1/T2_1/VetoLiSc_0")) {
        printf("could not cd to VetoLiSc_0\n");
        return;
    }
    TGeoNode* parent = nav->GetCurrentNode();
    TGeoVolume* vol = parent->GetVolume();
    int nd = vol->GetNdaughters();
    printf("VetoLiSc_0 has %d daughters\n", nd);

    // round phi to nearest 0.1 deg to dedupe, map phi -> {count, example x,y, example name}
    std::map<int, std::pair<int,std::string>> phiMap; // roundedphi*10 -> (count, examplename)
    std::map<int, double> phiX, phiY;

    for (int i = 0; i < nd; i++) {
        TGeoNode* dnode = vol->GetNode(i);
        TString name = dnode->GetName();
        nav->cd(Form("cave/DecayVolume_1/T2_1/VetoLiSc_0/%s", name.Data()));
        TGeoNode* node = nav->GetCurrentNode();
        TGeoVolume* dvol = node->GetVolume();
        TGeoBBox* shape = dynamic_cast<TGeoBBox*>(dvol->GetShape());
        if (!shape) continue;
        double origin[3] = {shape->GetOrigin()[0], shape->GetOrigin()[1], shape->GetOrigin()[2]};
        double master[3];
        nav->LocalToMaster(origin, master);
        double phi = Phicalc(master[0], master[1]);
        int key = (int)TMath::Nint(phi*10);
        if (phiMap.find(key) == phiMap.end()) {
            phiMap[key] = {0, name.Data()};
            phiX[key] = master[0];
            phiY[key] = master[1];
        }
        phiMap[key].first++;
    }

    printf("\n%d distinct phi values (rounded to 0.1 deg) among %d daughters:\n", (int)phiMap.size(), nd);
    printf("%8s %10s %10s %8s   %s\n", "phi(deg)", "x(cm)", "y(cm)", "count", "example_name");
    for (auto& kv : phiMap) {
        double phi = kv.first/10.0;
        printf("%8.1f %10.3f %10.3f %8d   %s\n", phi, phiX[kv.first], phiY[kv.first], kv.second.first, kv.second.second.c_str());
    }
}
