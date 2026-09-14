#!/usr/bin/env python3
"""Load the real SBT geometry (geo_*.root) and compute the master-frame
phi of EVERY placed SBT cell (all 854 nodes, all 6 shape types, all
blocks/Z-layers), the same way vetoHit::GetXYZ() does. Sort all phi
values and report the largest angular gaps between consecutive cell
centers - this is the ground-truth confirmation of the empty phi=90/270deg
band seen in the digihit histograms."""

from array import array
import math
import ROOT

GEOFILE = "/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_1026/geo_11921562_1026.root"
BASE = "cave_1/DecayVolume_1/T2_1/VetoLiSc_0/"


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
    f = ROOT.TFile.Open(GEOFILE)
    geo = f.Get("FAIRGeom")
    ROOT.gGeoManager = geo
    nav = geo.GetCurrentNavigator()
    nav.cd(BASE[:-1])
    vol = nav.GetCurrentNode().GetVolume()

    allphis = []
    byshape = {}
    for i in range(vol.GetNdaughters()):
        dn = vol.GetNode(i)
        name = dn.GetName()
        detID = int(name.split("_")[-1])
        ShapeType = detID // 100000

        path = BASE + name
        if not nav.cd(path):
            continue
        node = nav.GetCurrentNode()
        shape = node.GetVolume().GetShape()
        origin = shape.GetOrigin()
        local = array("d", [origin[0], origin[1], origin[2]])
        master = array("d", [0, 0, 0])
        nav.LocalToMaster(local, master)
        x, y, z = master
        phi = phicalc(x, y)
        allphis.append(phi)
        byshape.setdefault(ShapeType, []).append(phi)

    for s in sorted(byshape):
        phis = byshape[s]
        print(f"ShapeType {s}: n={len(phis)}  phi range=[{min(phis):.1f},{max(phis):.1f}]")

    allphis.sort()
    diffs = sorted([(b - a, a, b) for a, b in zip(allphis, allphis[1:])], reverse=True)
    print("\nlargest gaps between consecutive cell-center phi values (all shapes, whole geometry):")
    for d, a, b in diffs[:5]:
        print(f"  gap width={d:.2f}deg  from {a:.2f} to {b:.2f}")
