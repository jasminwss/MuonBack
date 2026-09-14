#!/usr/bin/env python3
"""Compare vetopoint vs digihit counts per SBT shape type (1-6), to check
whether the phi=90/270deg gap comes from one shape type being entirely
absent in the digihit data (it doesn't - all 6 shapes are present in both)."""

import ROOT

INFILE = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY6LiSc_full_onlySIM.root"

if __name__ == "__main__":
    f = ROOT.TFile.Open(INFILE)
    h_vp = f.Get("vetopoint_energydeposition_shapewise")  # TH2D shape(1-6) vs Eloss
    h_dh = f.Get("0_digihit_rate_shapewise")               # TH1D shape(1-6)

    print("shape  vetopoint_count   digihit_count(0MeV thr)")
    for s in range(1, 7):
        vp = h_vp.ProjectionX("_px", 0, -1).GetBinContent(s)
        dh = h_dh.GetBinContent(s)
        print(f"{s:5d}  {vp:15.6g}  {dh:15.6g}")
