import ROOT

files = [
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY6LiSc_full_matchedRecoSim.root",
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY5PlSc_full_matchedRecoSim.root",
]
hist_name = "0_digihit_topology_phi"
N = 10

for path in files:
    f = ROOT.TFile.Open(path)
    h = f.Get(hist_name)
    print(f"\n=== {path.split('/')[-1]}  ({hist_name}) ===")
    entries = []
    nx, ny = h.GetNbinsX(), h.GetNbinsY()
    for ix in range(1, nx+1):
        for iy in range(1, ny+1):
            c = h.GetBinContent(ix, iy)
            if c > 0:
                z = h.GetXaxis().GetBinCenter(ix)
                phi = h.GetYaxis().GetBinCenter(iy)
                entries.append((c, z, phi, ix, iy))
    entries.sort(reverse=True)
    for c, z, phi, ix, iy in entries[:N]:
        print(f"  z={z:7.1f} cm  phi={phi:6.1f} deg  rate={c:.3e}  (bin ix={ix},iy={iy})")
    f.Close()