# diagnose.py
import ROOT

# KEINE genfit-Libs laden — das ist wichtig für den Test

#f = ROOT.TFile.Open("/eos/user/j/jaweiss/MuonBack/job_0_400000_10400001/reco_7b661362-0713-4154-a5ca-44948fadc46c.root")  # <-- meine (neu)
f = ROOT.TFile.Open("/eos/experiment/ship/simulation/bkg/MuonBack_2024helium/8070735/job_0/ship.conical.MuonBack-TGeant4_rec.root")  # <-- anupama (alt)
t = f.Get("ship_reco_sim")

# C++ Macro kompilieren und laden
ROOT.gROOT.ProcessLine('.L CheckFitTracks.C+')

# Funktion aufrufen
ROOT.CheckFitTracks(t)