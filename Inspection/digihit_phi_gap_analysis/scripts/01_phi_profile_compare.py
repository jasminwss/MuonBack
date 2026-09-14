#!/usr/bin/env python3
"""Project vetopoint_topology_phi and 0_digihit_topology_phi onto the phi
axis (summed over z) and print bin-by-bin content, to show where the
digihit histogram has empty bins that the vetopoint histogram does not."""

import ROOT

INFILE = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY6LiSc_full_onlySIM.root"


def phi_profile(f, hname):
    h = f.Get(hname)
    nx = h.GetNbinsX()
    ny = h.GetNbinsY()
    proj = [0.0] * ny
    for iy in range(1, ny + 1):
        s = 0.0
        for ix in range(1, nx + 1):
            s += h.GetBinContent(ix, iy)
        proj[iy - 1] = s
    yaxis = h.GetYaxis()
    print(hname)
    for iy in range(1, ny + 1):
        lo = yaxis.GetBinLowEdge(iy)
        hi = lo + yaxis.GetBinWidth(iy)
        print(f"  bin {iy:2d} phi[{lo:6.1f},{hi:6.1f}) center={0.5*(lo+hi):6.1f}  sum={proj[iy-1]:.6g}")
    print()


if __name__ == "__main__":
    f = ROOT.TFile.Open(INFILE)
    phi_profile(f, "vetopoint_topology_phi")
    phi_profile(f, "0_digihit_topology_phi")
