#!/usr/bin/env python3
"""Plot the digi-hit-rate-vs-threshold TGraphs (total / hottest cell / 2nd cell)
produced by inspect_Back.py as *_rate_vs_threshold.root.

Markers only, no connecting line - the thresholds are not evenly spaced and the
points are measurements, not a curve. y-axis is log (the total spans ~2 orders
of magnitude across thresholds).

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

for path in FILES:
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        print(f"skip: cannot open {path}")
        continue

    canvas = ROOT.TCanvas("c", "", 800, 600)
    ROOT.gPad.SetLogy()
    ROOT.gPad.SetGridx()
    ROOT.gPad.SetGridy()

    leg = ROOT.TLegend(0.62, 0.72, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)

    # TMultiGraph so the axis auto-scales across all three graphs
    mg = ROOT.TMultiGraph()
    mg.SetTitle(f"{os.path.basename(path)};SBT digi threshold (MeV);digi hit rate (MHz)")
    keep = []
    for name, (label, colour, marker) in GRAPHS.items():
        g = f.Get(name)
        if not g:
            print(f"  {os.path.basename(path)}: '{name}' missing")
            continue
        g.SetMarkerStyle(marker)
        g.SetMarkerSize(1.3)
        g.SetMarkerColor(colour)
        g.SetLineColor(colour)          # legend swatch only, no line is drawn
        mg.Add(g, "P")                  # "P" = points only for this graph
        leg.AddEntry(g, label, "p")
        keep.append(g)

    # "A" axes, "P" points only.  use "APL" if you ever want the line too
    mg.Draw("AP")
    leg.Draw()
    out = path.replace("_rate_vs_threshold.root", "_rate_vs_threshold.png")
    canvas.SaveAs(out)
    print(f"wrote {out}")
    f.Close()
