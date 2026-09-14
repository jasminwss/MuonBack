#!/usr/bin/env python3
"""Plot the digi-hit-rate-vs-threshold TGraphs (total / hottest cell / 2nd cell)
produced by inspect_Back.py as *_rate_vs_threshold.root.

Markers only, no connecting line - the thresholds are not evenly spaced and the
points are measurements, not a curve. y-axis is log (the total spans ~2 orders
of magnitude across thresholds). All input files are drawn as side-by-side
pads on one canvas, sharing a common y-axis range (only the leftmost pad
shows y-axis labels/title) so the rates are directly comparable. The pad
boundary is chosen so the actual plot areas (not just the raw pads) come out
equal width regardless of which pad carries the y-axis label margin.

Usage:
    python plot_rate_vs_threshold.py [file1_rate_vs_threshold.root ...]
"""
import sys, os, ROOT

ROOT.gROOT.SetBatch(True)

# ---- modern, minimal style: clean sans-serif, recessive gray grid, borderless
# title, ticks on all sides. Text uses ink tokens (not series colour); colour
# is reserved for the three data series. Palette = validated categorical
# slots 1-3 (blue/orange/aqua) from the dataviz skill's reference palette -
# the trio that clears the CVD/contrast checks for scatter ("all-pairs") use.
INK_PRIMARY = ROOT.TColor.GetColor("#0b0b0b")
INK_SECONDARY = ROOT.TColor.GetColor("#52514e")
INK_AXIS = ROOT.TColor.GetColor("#8a8a86")
GRID_COLOR = ROOT.TColor.GetColor("#dcdad2")

ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetCanvasColor(ROOT.kWhite)
ROOT.gStyle.SetPadColor(ROOT.kWhite)
ROOT.gStyle.SetFrameBorderMode(0)
ROOT.gStyle.SetCanvasBorderMode(0)
ROOT.gStyle.SetPadBorderMode(0)
ROOT.gStyle.SetFrameLineColor(INK_AXIS)
ROOT.gStyle.SetAxisColor(INK_AXIS, "xyz")
ROOT.gStyle.SetGridColor(GRID_COLOR)
ROOT.gStyle.SetGridStyle(1)
ROOT.gStyle.SetGridWidth(1)
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)
ROOT.gStyle.SetTitleFont(42, "")
ROOT.gStyle.SetTitleFontSize(0.052)
ROOT.gStyle.SetTitleBorderSize(0)
ROOT.gStyle.SetTitleFillColor(0)
ROOT.gStyle.SetTitleTextColor(INK_PRIMARY)
ROOT.gStyle.SetLabelFont(42, "xyz")
ROOT.gStyle.SetTitleFont(42, "xyz")
ROOT.gStyle.SetLabelSize(0.038, "xyz")
ROOT.gStyle.SetTitleSize(0.046, "xyz")
ROOT.gStyle.SetLabelColor(INK_SECONDARY, "xyz")

FILES = sys.argv[1:] or [
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY5PlSc_full_onlySIM_rate_vs_threshold.root",
    "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY6LiSc_full_onlySIM_rate_vs_threshold.root",
]

# graph name -> (legend label, colour, marker style)
GRAPHS = {
    "digihitrate_vs_threshold_total":        ("total",        ROOT.TColor.GetColor("#2a78d6"), 20),  # filled circle
    "digihitrate_vs_threshold_hottest_cell": ("hottest cell", ROOT.TColor.GetColor("#eb6834"), 21),  # filled square
    "digihitrate_vs_threshold_second_cell":  ("2nd cell",     ROOT.TColor.GetColor("#1baf7a"), 22),  # filled triangle
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
        g.SetMarkerSize(1.5)
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

# pad margins: only the leftmost pad reserves room for y-axis labels, only the
# rightmost pad reserves a bit of outer padding; pads otherwise touch, giving
# the shared-axis look.
LEFT_MARGIN, RIGHT_MARGIN = 0.16, 0.03
GAP_MARGIN = 0.006
margins = []
for i in range(n):
    left = LEFT_MARGIN if i == 0 else GAP_MARGIN
    right = RIGHT_MARGIN if i == n - 1 else GAP_MARGIN
    margins.append((left, right))

# choose pad widths so the *plot area* (pad width minus its margins) comes
# out equal for every pad, not just the raw pad width
plot_frac = [1 - l - r for l, r in margins]
raw_widths = [1.0 / pf for pf in plot_frac]
norm = sum(raw_widths)
pad_widths = [w / norm for w in raw_widths]
bounds = [0.0]
for w in pad_widths:
    bounds.append(bounds[-1] + w)

keep = []  # keep refs alive (pads, TMultiGraphs, legends)
for i, (path, graphs) in enumerate(pads_content):
    left, right = margins[i]
    pad = ROOT.TPad(f"pad{i}", "", bounds[i], 0, bounds[i + 1], 1)
    pad.SetLeftMargin(left)
    pad.SetRightMargin(right)
    pad.SetTopMargin(0.11)
    pad.SetBottomMargin(0.14)
    pad.SetLogy()
    pad.SetGridx()
    pad.SetGridy()
    pad.Draw()
    pad.cd()
    keep.append(pad)

    leg = ROOT.TLegend(0.60, 0.76, 0.95, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(42)
    leg.SetTextSize(0.036)
    leg.SetTextColor(INK_PRIMARY)

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
        mg.GetYaxis().SetTickLength(0.015)
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
