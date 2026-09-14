#!/usr/bin/env python3
"""Plot the digi-hit-rate-vs-threshold TGraphs (total / hottest cell / 2nd cell)
produced by inspect_Back.py as *_rate_vs_threshold.root.

Markers only, no connecting line - the thresholds are not evenly spaced and the
points are measurements, not a curve. y-axis is log (the total spans ~2 orders
of magnitude across thresholds). All input files are drawn as side-by-side
pads on one canvas, sharing a common y-axis range (only the leftmost pad
shows y-axis labels/title) so the rates are directly comparable.

Usage:
    python plot_rate_vs_threshold.py [file1_rate_vs_threshold.root ...]
"""
import sys, os, ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

FILES = sys.argv[1:] or [
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY5PlSc_full_onlySIM_rate_vs_threshold.root",
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY6LiSc_full_onlySIM_rate_vs_threshold.root",
]

# graph name -> (legend label, colour, marker style)
GRAPHS = {
    "digihitrate_vs_threshold_total":        ("total",        ROOT.kBlack,   20),  # filled circle
    "digihitrate_vs_threshold_hottest_cell": ("hottest cell", ROOT.kRed + 1, 21),  # filled square
    "digihitrate_vs_threshold_second_cell":  ("2nd cell",     ROOT.kAzure + 1, 22),  # filled triangle
}

open_files = []
pads_content = []  # list of (path, {name: graph})
all_y = []

for path in FILES:
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        print(f"skip: cannot open {path}")
        continue
    open_files.append(f)

    graphs = {}
    for name, (label, colour, marker) in GRAPHS.items():
        g = f.Get(name)
        if not g:
            print(f"  {os.path.basename(path)}: '{name}' missing")
            continue
        g.SetMarkerStyle(marker)
        g.SetMarkerSize(1.3)
        g.SetMarkerColor(colour)
        g.SetLineColor(colour)          # legend swatch only, no line is drawn
        graphs[name] = g
        for y in g.GetY():
            if y > 0:
                all_y.append(y)
    pads_content.append((path, graphs))

if not pads_content:
    sys.exit("no valid input files")

# common log-y range across all pads, with a bit of headroom
ymin, ymax = min(all_y), max(all_y)
ymin, ymax = ymin / 1.5, ymax * 1.5

n = len(pads_content)
canvas = ROOT.TCanvas("c", "", 650 * n + 150, 650)
canvas.SetFillColor(0)

keep = []  # keep refs alive (pads, TMultiGraphs, legends)
for i, (path, graphs) in enumerate(pads_content):
    xlow, xup = i / n, (i + 1) / n
    pad = ROOT.TPad(f"pad{i}", "", xlow, 0, xup, 1)
    pad.SetLeftMargin(0.16 if i == 0 else 0.001)
    pad.SetRightMargin(0.02 if i == n - 1 else 0.001)
    pad.SetTopMargin(0.10)
    pad.SetBottomMargin(0.14)
    pad.SetLogy()
    pad.SetGridx()
    pad.SetGridy()
    pad.Draw()
    pad.cd()
    keep.append(pad)

    leg = ROOT.TLegend(0.40, 0.74, 0.95, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)

    mg = ROOT.TMultiGraph()
    mg.SetTitle(f"{os.path.basename(path)};SBT digi threshold (MeV);digi hit rate (MHz)")
    for name, (label, colour, marker) in GRAPHS.items():
        g = graphs.get(name)
        if not g:
            continue
        mg.Add(g, "P")                  # "P" = points only for this graph
        leg.AddEntry(g, label, "p")

    mg.SetMinimum(ymin)
    mg.SetMaximum(ymax)
    mg.Draw("AP")                       # "A" axes, "P" points only
    if i > 0:
        mg.GetYaxis().SetLabelSize(0)
        mg.GetYaxis().SetTitleSize(0)
        mg.GetYaxis().SetTickLength(0.02)
    leg.Draw()
    keep += [mg, leg]

    canvas.cd()

stem = lambda p: os.path.basename(p).replace("_rate_vs_threshold.root", "")
out_dir = os.path.dirname(pads_content[0][0]) or "."
out = os.path.join(out_dir, "_vs_".join(stem(p) for p, _ in pads_content) + "_rate_vs_threshold.png")
canvas.SaveAs(out)
print(f"wrote {out}")

for f in open_files:
    f.Close()
