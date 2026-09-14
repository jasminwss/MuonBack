"""
Voraussetzung: XQuartz installiert & läuft (macOS).

1. Mac-Terminal: `ssh -Y jaweiss@lxplus.cern.ch`
2. Prüfen: `echo $DISPLAY` (muss einen Wert zeigen, z.B. `localhost:47.0`)
3. `source /cvmfs/ship.cern.ch/26.04/setUp.sh`
4. `alienv enter -w /afs/cern.ch/work/j/jaweiss/private/sw FairShip/latest`
5. Falls `echo $DISPLAY` jetzt leer ist: `export DISPLAY=<Wert aus Schritt 2>`

"""

import ROOT
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--long", type=float, default=20, help="longitude for view rotation")
parser.add_argument("--lat", type=float, default=20, help="latitude for view rotation")
parser.add_argument("--block", type=int, default=2, help="blockNr to select (1 = short block, 2 = long block)")
parser.add_argument("--zlayer", type=int, default=1, help="Zlayer to select (block1 only has Zlayer=1; block2 has 1..60)")
options = parser.parse_args()
print("1. ROOT imported", flush=True)

f = ROOT.TFile.Open("/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_1026/geo_11921562_1026.root")
print("2. file opened:", f, flush=True)

geo = f.Get("FAIRGeom")
print("3. geo manager loaded:", geo, flush=True)

ROOT.gGeoManager = geo
print("4. gGeoManager set", flush=True)

nav = geo.GetCurrentNavigator()
print("5. navigator obtained:", nav, flush=True)

ok = nav.cd("cave_1/DecayVolume_1/T2_1/VetoLiSc_0")
print("6. cd to VetoLiSc_0, ok =", ok, flush=True)

vol = nav.GetCurrentNode().GetVolume()
print("7. volume obtained:", vol.GetName(), "ndaughters =", vol.GetNdaughters(), flush=True)

only_liscy = ROOT.TGeoVolumeAssembly("OnlyLiScY")
print("8. empty assembly created", flush=True)

# detID = ShapeType*100000 + blockNr*10000 + Zlayer*100 + number*10 + position
n_added = 0
for i in range(vol.GetNdaughters()):
    dn = vol.GetNode(i)
    name = dn.GetName()
    if not name.startswith("LiSc"):
        continue
    detID = int(name.split("_")[2])
    blockNr = (detID % 100000) // 10000
    Zlayer = (detID % 10000) // 100
    if blockNr != options.block or Zlayer != options.zlayer:
        continue
    only_liscy.AddNode(dn.GetVolume(), i, dn.GetMatrix())
    n_added += 1
print(f"9. loop done, added {n_added} LiSc nodes (block={options.block}, Zlayer={options.zlayer})", flush=True)

c = ROOT.TCanvas("c", "LiSc", 1000, 800)
c.SetFillColor(ROOT.TColor.GetColor("#333333"))
print("10. canvas created", flush=True)

only_liscy.Draw()
print("11. Draw() returned - window should be open now", flush=True)

view = ROOT.gPad.GetView()
long = options.long
lat = options.lat
view.RotateView(long, lat)   # (longitude, latitude) in Grad
ROOT.gPad.Modified()
ROOT.gPad.Update()

out = (
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/digihit_phi_gap_analysis/results/"
    f"lisc{long}_{lat}_block{options.block}_z{options.zlayer}.png"
)
c.SaveAs(out)
print(f"12. saved {out} - done", flush=True)
