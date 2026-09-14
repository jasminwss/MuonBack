#!/usr/bin/env python3
"""Project the 0_digihit_topology TH3D (x,z,y) onto the x-y plane (summed
over z) to list the actual distinct digihit cell-center positions that
were ever filled, with their phi. Shows the hard jump from phi~70deg
straight to phi~110deg (and mirrored at 250/290deg) with no cell centers
in between."""

import math
import ROOT

INFILE = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY6LiSc_full_onlySIM.root"


def phicalc(x, y):
    r = math.hypot(x, y)
    if r == 0:
        return None
    if y >= 0:
        phi = math.acos(x / r)
    else:
        phi = -math.acos(x / r) + 2 * math.pi
    phi = math.degrees(phi)
    return (phi + 90) % 360


if __name__ == "__main__":
    f = ROOT.TFile.Open(INFILE)
    h = f.Get("0_digihit_topology")  # TH3D filled as Fill(x,z,y): X=x, Y=z, Z=y
    xax = h.GetXaxis()
    zax = h.GetZaxis()
    nx, nz, ny = h.GetNbinsX(), h.GetNbinsY(), h.GetNbinsZ()

    xy = {}
    for ix in range(1, nx + 1):
        for iz in range(1, nz + 1):
            for iy in range(1, ny + 1):
                c = h.GetBinContent(ix, iz, iy)
                if c > 0:
                    key = (ix, iy)
                    xy[key] = xy.get(key, 0) + c

    print("n distinct (x,y) cell-columns with content:", len(xy))

    rows = []
    for (ix, iy), c in xy.items():
        xc = xax.GetBinCenter(ix)
        yc = zax.GetBinCenter(iy)
        phi = phicalc(xc, yc)
        rows.append((phi, xc, yc, c))
    rows.sort()
    for phi, xc, yc, c in rows:
        print(f"phi={phi:6.1f}  x={xc:7.1f}  y={yc:7.1f}  content={c:.4g}")
