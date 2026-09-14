#!/usr/bin/env python3
"""Load the real SBT geometry (geo_*.root) and, for the ShapeType==2
("LiScY", side-wall) cells only, compute each cell's true master-frame
position the same way vetoHit::GetXYZ() does (BBox local origin ->
LocalToMaster), decode the detID, and list x,y,z,phi vs (blockNr, Zlayer,
number, position). Shows there are only 2 side cells per z-layer (upper
"number=1" and lower "number=2" half of the wall), and traces how their
phi drifts along z."""

import math
from array import array
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

    rows = []
    for i in range(vol.GetNdaughters()):
        dn = vol.GetNode(i)
        name = dn.GetName()
        if not name.startswith("LiScY_"):
            continue
        detID = int(name.split("_")[2])
        ShapeType = detID // 100000
        blockNr = (detID % 100000) // 10000
        Zlayer = (detID % 10000) // 100
        number = (detID % 100) // 10
        position = detID % 10

        path = BASE + name
        if not nav.cd(path):
            print("FAILED cd", path)
            continue
        node = nav.GetCurrentNode()
        shape = node.GetVolume().GetShape()
        origin = shape.GetOrigin()
        local = array("d", [origin[0], origin[1], origin[2]])
        master = array("d", [0, 0, 0])
        nav.LocalToMaster(local, master)
        x, y, z = master
        phi = phicalc(x, y)
        rows.append((blockNr, Zlayer, number, position, x, y, z, phi, detID))

    rows.sort()
    print(f"total LiScY cells: {len(rows)}")
    print("number values seen:", sorted(set(r[2] for r in rows)))
    print("blockNr values seen:", sorted(set(r[0] for r in rows)))

    for which_number, which_position in [(2, 1), (1, 1)]:
        print(f"\nLiScY shape2, number={which_number}, position={which_position} across Zlayer (block2):")
        sub = [r for r in rows if r[2] == which_number and r[3] == which_position and r[0] == 2]
        sub.sort(key=lambda r: r[2])
        for r in sub:
            blockNr, Zlayer, number, position, x, y, z, phi, detID = r
            print(f"  Zlayer={Zlayer:3d} z={z:7.1f} x={x:7.1f} y={y:7.1f} phi={phi:6.2f}")
