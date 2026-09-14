import ROOT
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--long", type=float, default=20, help="longitude for view rotation")
parser.add_argument("--lat", type=float, default=20, help="latitude for view rotation")
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

n_added = 0
for i in range(vol.GetNdaughters()):
    dn = vol.GetNode(i)
    if dn.GetName().startswith("LiSc"):
        only_liscy.AddNode(dn.GetVolume(), i, dn.GetMatrix())
        n_added += 1
print(f"9. loop done, added {n_added} LiSc nodes out of {vol.GetNdaughters()}", flush=True)

c = ROOT.TCanvas("c", "LiSc", 1000, 800)
print("10. canvas created", flush=True)

only_liscy.Draw()
print("11. Draw() returned - window should be open now", flush=True)

view = ROOT.gPad.GetView()
long=options.long
lat=options.lat
view.RotateView(long, lat)   # (longitude, latitude) in Grad
ROOT.gPad.Modified()
ROOT.gPad.Update()

c.SaveAs(f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/digihit_phi_gap_analysis/results/lisc{long}_{lat}.png")
print(f"12. saved lisc{long}_{lat}.png - done", flush=True)
