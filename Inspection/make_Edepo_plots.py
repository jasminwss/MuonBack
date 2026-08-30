import ROOT, os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
# The histograms are booked with 1000 bins over 0..1 GeV  ->  1 MeV / bin.
# BIN_WIDTH_MEV sets how wide the plotted bins should be; pick a divisor of
# 1000 MeV (2, 4, 5, 10, 20, 25, 50, ...) so the rebinning is exact.
BIN_WIDTH_MEV = 50
# Zoom the x-axis onto low energy depositions (GeV). None = full 0..1 GeV.
XMAX_GEV = 1
# ---------------------------------------------------------------------------

pathTRY5 = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY5PlSc_onlymaxEdepo.root"
pathTRY6 = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/TRY6LiSc_onlymaxEdepo.root"

outdirs = sorted({os.path.dirname(pathTRY5), os.path.dirname(pathTRY6)})

fTRY5 = ROOT.TFile.Open(pathTRY5)
fTRY6 = ROOT.TFile.Open(pathTRY6)

# these are the plots that get compared, one per SBT digitisation threshold
plots_Edepo = [
    "0_maxenergydeposition",
    "10_maxenergydeposition",
    "45_maxenergydeposition",
    "90_maxenergydeposition",
    "100_maxenergydeposition",
    "115_maxenergydeposition",
    "130_maxenergydeposition",
]

for name in plots_Edepo:
    h5src = fTRY5.Get(name)
    h6src = fTRY6.Get(name)
    if not h5src or not h6src:
        print(f"Skipping '{name}': missing in TRY5 and/or TRY6 file")
        continue

    h5 = h5src.Clone(f"{name}_TRY5")
    h6 = h6src.Clone(f"{name}_TRY6")
    h5.SetDirectory(0)
    h6.SetDirectory(0)

    # rebin to the requested bin width
    native_mev = h5.GetXaxis().GetBinWidth(1) * 1000.0
    rebin = max(1, int(round(BIN_WIDTH_MEV / native_mev)))
    if rebin > 1:
        h5.Rebin(rebin)
        h6.Rebin(rebin)
    bw_mev = h5.GetXaxis().GetBinWidth(1) * 1000.0

    threshold = name.split("_")[0]

    integral5 = h5.Integral()      # weighted sum = Rate-Beitrag
    entries5  = h5.GetEntries()    # unweighted Fill-Count
    integral6 = h6.Integral()
    entries6  = h6.GetEntries()

    # common log-y range across both histograms
    ymin_candidates = [
        h.GetBinContent(b)
        for h in (h5, h6)
        for b in range(1, h.GetNbinsX() + 1)
        if h.GetBinContent(b) > 0
    ]
    if not ymin_candidates:
        print(f"Skipping '{name}': no positive-content bins")
        continue
    ymin = min(ymin_candidates)
    ymax = max(h5.GetMaximum(), h6.GetMaximum())

    title = (
        f"max energy deposition per SBT cell  -  "
        f"digitised hits @ {threshold} MeV threshold"
    )
    for h in (h5, h6):
        h.SetTitle(title)
        h.GetXaxis().SetTitle("max(Energy deposition) per cell  (GeV)")
        h.GetYaxis().SetTitle(f"weighted entries / {bw_mev:.3g} MeV")
        h.GetYaxis().SetRangeUser(ymin * 0.5, ymax * 2.0)
        if XMAX_GEV is not None:
            h.GetXaxis().SetRangeUser(0.0, XMAX_GEV)

    h5.SetLineColor(ROOT.kAzure + 1)
    h5.SetMarkerColor(ROOT.kAzure + 1)
    h5.SetLineWidth(2)
    h6.SetLineColor(ROOT.kRed + 1)
    h6.SetMarkerColor(ROOT.kRed + 1)
    h6.SetLineWidth(2)

    canvas = ROOT.TCanvas(f"c_{name}", name, 1000, 750)
    ROOT.gPad.SetLogy()
    ROOT.gPad.SetLeftMargin(0.12)
    ROOT.gPad.SetRightMargin(0.05)

    h5.Draw("HIST E1")
    h6.Draw("HIST E1 SAME")

    leg = ROOT.TLegend(0.5, 0.76, 0.95, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h5, f"TRY5 (PlSc):  Integral = {integral5:.3e}, Entries = {entries5:.0f}", "le")
    leg.AddEntry(h6, f"TRY6 (LiSc):  Integral = {integral6:.3e}, Entries = {entries6:.0f}", "le")
    leg.Draw()

    outname = f"compare_{name}_{XMAX_GEV}.png"
    for outdir in outdirs:
        canvas.SaveAs(os.path.join(outdir, outname))
