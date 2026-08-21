import ROOT, os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)


# Make plots comparing the histograms with regard to origin
pathTRY5zphi = "/eos/user/j/jaweiss/MuonBack/TRY5PlSc/z_phi_origin/phi-z-plots.root"
pathTRY6zphi = "/eos/user/j/jaweiss/MuonBack/TRY6LiSc/z_phi_origin/phi-z-plots.root"


outdirs = [os.path.dirname(pathTRY5zphi), os.path.dirname(pathTRY6zphi)]

fTRY5 = ROOT.TFile.Open(pathTRY5zphi)
fTRY6 = ROOT.TFile.Open(pathTRY6zphi)

for origin in ["cavern", "SBT", "upstream"]:
    plots_phi_z = [
        f"0_digihit_topology_phi {origin}",
        f"90_digihit_topology_phi {origin}",
        f"0_digihit_max_edepval_topology_phi {origin}",
        f"90_digihit_max_edepval_topology_phi {origin}",
    ]

    for name in plots_phi_z:
        h2 = fTRY5.Get(name)
        h5 = fTRY6.Get(name)
        if not h2 or not h5:
            print(f"Skipping '{name}': missing in TRY5 and/or TRY6 file")
            continue

        h2 = h2.Clone(f"{name.replace(' ', '_')}_TRY5")
        h5 = h5.Clone(f"{name.replace(' ', '_')}_TRY6")

        integral2 = h2.Integral()       # weighted sum = Rate-Beitrag
        entries2  = h2.GetEntries()     # unweighted Fill-Count
        integral5 = h5.Integral()       # weighted sum = Rate-Beitrag
        entries5  = h5.GetEntries()     # unweighted Fill-Count

        # common log-z range: smallest positive bin over largest bin, across both histograms
        zmin_candidates = [h.GetMinimum(0) for h in (h2, h5) if h.GetMinimum(0) > 0]
        if not zmin_candidates:
            print(f"Skipping '{name}': no positive-content bins")
            continue
        zmin = min(zmin_candidates)
        zmax = max(h2.GetMaximum(), h5.GetMaximum())

        h2.GetZaxis().SetRangeUser(zmin, zmax)
        h5.GetZaxis().SetRangeUser(zmin, zmax)

        canvas = ROOT.TCanvas(f"c_{name.replace(' ', '_')}", name, 1600, 700)
        canvas.Divide(2, 1)

        canvas.cd(1)
        ROOT.gPad.SetLogz()
        ROOT.gPad.SetRightMargin(0.15)
        h2.SetTitle(f"TRY5 (PlSc)  -  {name}")
        h2.Draw("COLZ")
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.2, 0.91, f"Integral = {integral2:.3e},Entries = {entries2:.0f} ")


        canvas.cd(2)
        ROOT.gPad.SetLogz()
        ROOT.gPad.SetRightMargin(0.15)
        h5.SetTitle(f"TRY6 (LiSc)  -  {name}")
        h5.Draw("COLZ")
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextSize(0.035)
        latex.DrawLatex(0.2, 0.91, f"Integral = {integral5:.3e},Entries = {entries5:.0f} ")

        outname = f"compare_{name.replace(' ', '_')}.png"
        for outdir in outdirs:
            canvas.SaveAs(os.path.join(outdir, outname))


#make histogram without distinguishing origin
pathTRY5 = "/eos/user/j/jaweiss/TRY5PlScTRY5LiScBranch.root"
pathTRY6 = "/eos/user/j/jaweiss/TRY6LiSc_TRY5LiScBranch.root"



outdirs = [os.path.dirname(pathTRY5), os.path.dirname(pathTRY6)]

fTRY5 = ROOT.TFile.Open(pathTRY5)
fTRY6 = ROOT.TFile.Open(pathTRY6)

plots_phi_z = [
    f"0_digihit_topology_phi",
    f"90_digihit_topology_phi",
    f"0_digihit_max_edepval_topology_phi",
    f"90_digihit_max_edepval_topology_phi",
]

for name in plots_phi_z:
    h2 = fTRY5.Get(name)
    h5 = fTRY6.Get(name)
    if not h2 or not h5:
        print(f"Skipping '{name}': missing in TRY5 and/or TRY6 file")
        continue

    h2 = h2.Clone(f"{name.replace(' ', '_')}_TRY5")
    h5 = h5.Clone(f"{name.replace(' ', '_')}_TRY6")

    integral5 = h5.Integral()       # weighted sum = Rate-Beitrag
    entries5  = h5.GetEntries()     # unweighted Fill-Count

    integral2 = h2.Integral()       # weighted sum = Rate-Beitrag
    entries2  = h2.GetEntries()     # unweighted Fill-Count

    # common log-z range: smallest positive bin over largest bin, across both histograms
    zmin_candidates = [h.GetMinimum(0) for h in (h2, h5) if h.GetMinimum(0) > 0]
    if not zmin_candidates:
        print(f"Skipping '{name}': no positive-content bins")
        continue
    zmin = min(zmin_candidates)
    zmax = max(h2.GetMaximum(), h5.GetMaximum())

    h2.GetZaxis().SetRangeUser(zmin, zmax)
    h5.GetZaxis().SetRangeUser(zmin, zmax)

    canvas = ROOT.TCanvas(f"c_{name.replace(' ', '_')}", name, 1600, 700)
    canvas.Divide(2, 1)

    canvas.cd(1)
    ROOT.gPad.SetLogz()
    ROOT.gPad.SetRightMargin(0.15)
    h2.SetTitle(f"TRY5 (PlSc)  -  {name}")
    h2.Draw("COLZ")
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.035)
    latex.DrawLatex(0.2, 0.91, f"Integral = {integral2:.3e},Entries = {entries2:.0f} ")
    canvas.cd(2)
    ROOT.gPad.SetLogz()
    ROOT.gPad.SetRightMargin(0.15)
    h5.SetTitle(f"TRY6 (LiSc)  -  {name}")
    h5.Draw("COLZ")
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.035)
    latex.DrawLatex(0.2, 0.91, f"Integral = {integral5:.3e},Entries = {entries5:.0f} ")

    outname = f"compare_{name.replace(' ', '_')}.png"
    for outdir in outdirs:
        canvas.SaveAs(os.path.join(outdir, outname))