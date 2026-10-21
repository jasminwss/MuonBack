import ROOT, os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

RESULTS = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/results"
pathTRY5 = f"{RESULTS}/TRY5PlSc/full/TRY5PlSc_full_onlySIM.root"
pathTRY5LiSc = f"{RESULTS}/TRY5LiSc/full/TRY5LiSc.root"
pathTRY6 = f"{RESULTS}/TRY6LiSc_88d2794/full/TRY6LiSc_88d2794_full.root"

outdirs = [f"{RESULTS}/comparisons"]

# panel order: TRY5, TRY5LiSc, TRY6
panels = [
    ("TRY5 (PlSc)", ROOT.TFile.Open(pathTRY5)),
    ("TRY5 (LiSc)", ROOT.TFile.Open(pathTRY5LiSc)),
    ("TRY6 (LiSc)", ROOT.TFile.Open(pathTRY6)),
]

# one overlay per file, all thresholds together, light->dark red like the reference slide
threshold_list = [0, 10, 20, 30, 45, 50, 60, 90]
light_rgb = (0xFB, 0xEA, 0xEA)
dark_rgb  = (0x7A, 0x00, 0x00)
n = len(threshold_list)

keep_alive = []  # PyROOT needs these kept around or the pad ends up empty

def common_yrange(thresholds):
    # smallest non-zero / largest bin content in x = 0..100 over all panels, for a shared log y axis
    ymax = 0.
    for _, f in panels:
        for threshold in thresholds:
            h = f.Get(f"{threshold}_digihit_multiplicity")
            if not h:
                continue
            for b in range(h.GetXaxis().FindBin(0), h.GetXaxis().FindBin(100) + 1):
                c = h.GetBinContent(b)
                if c > 0:
                    ymax = max(ymax, c)
    return 1, 5 * ymax  # headroom on log scale

def draw_overlay(pad, f, label, thresholds=threshold_list):
    pad.cd()
    pad.SetLogy()
    pad.SetLeftMargin(0.14)
    pad.SetRightMargin(0.04)

    clones = []
    for threshold in thresholds:
        hsrc = f.Get(f"{threshold}_digihit_multiplicity")
        if not hsrc:
            print(f"Skipping {label} {threshold} MeV: histogram missing")
            continue

        hist = hsrc.Clone(f"{label}_{threshold}_digihit_multiplicity_{len(thresholds)}")
        hist.SetDirectory(0)

        # colour index from the full list so single-threshold plots match the overlay
        i = threshold_list.index(threshold)
        frac = i / (n - 1) if n > 1 else 0
        rgb = tuple(int(light_rgb[k] + frac * (dark_rgb[k] - light_rgb[k])) for k in range(3))
        color = ROOT.TColor.GetColor(*rgb)
        border_rgb = tuple(int(v * 0.6) for v in rgb)  # darker outline than the fill
        border_color = ROOT.TColor.GetColor(*border_rgb)
        hist.SetFillColor(color)
        hist.SetFillStyle(1001)
        hist.SetLineColor(border_color)
        hist.SetLineWidth(2)
        hist.GetXaxis().SetRangeUser(0, 100)
        clones.append((threshold, hist))

    if not clones:
        return

    ymin, ymax = common_yrange(thresholds)
    clones[0][1].SetMinimum(ymin)
    clones[0][1].SetMaximum(ymax)
    clones[0][1].SetTitle(';Number of triggered SBT cells per event;Events per spill')
    clones[0][1].Draw('HIST')
    for _, hist in clones[1:]:
        hist.Draw('HIST SAME')

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(62)
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.16, 0.83, label)

    leg = ROOT.TLegend(0.68, 0.88 - 0.054 * len(clones), 0.95, 0.88)  # height scales with number of entries
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    for threshold, hist in clones:
        leg.AddEntry(hist, f'{threshold} MeV threshold', 'f')
    leg.Draw()

    # single-threshold plots: weighted content of the 61-cell bin
    if len(clones) == 1:
        hist = clones[0][1]
        content = hist.GetBinContent(hist.GetXaxis().FindBin(61))
        latex.SetTextFont(42)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.55, 0.76, f'bin 61: {content:.2e} events/spill')

    keep_alive.append((clones, leg, latex))

canvas = ROOT.TCanvas("c_digihit_multiplicity_compare", "digihit multiplicity: TRY5 vs TRY5LiSc vs TRY6", 2700, 750)
canvas.Divide(3, 1)

for i, (label, f) in enumerate(panels, start=1):
    draw_overlay(canvas.cd(i), f, label)

outname = "compare_digihit_multiplicity_overlay.png"
for outdir in outdirs:
    canvas.SaveAs(os.path.join(outdir, outname))

print("written " + ", ".join(os.path.join(outdir, outname) for outdir in outdirs))

# one canvas per threshold, same 3 panels, common title on top
for threshold in threshold_list:
    c = ROOT.TCanvas(f"c_digihit_multiplicity_{threshold}MeV", f"digihit multiplicity {threshold} MeV", 2700, 820)
    title_pad = ROOT.TPad(f"title_pad_{threshold}", "", 0, 0.91, 1, 1)
    main_pad  = ROOT.TPad(f"main_pad_{threshold}",  "", 0, 0, 1, 0.91)
    title_pad.Draw()
    main_pad.Draw()

    title_pad.cd()
    title = ROOT.TLatex()
    title.SetNDC()
    title.SetTextFont(62)
    title.SetTextSize(0.55)
    title.SetTextAlign(22)
    title.DrawLatex(0.5, 0.5, f"SBT digihit multiplicity @ {threshold} MeV threshold")

    main_pad.Divide(3, 1)
    for i, (label, f) in enumerate(panels, start=1):
        draw_overlay(main_pad.cd(i), f, label, thresholds=[threshold])

    keep_alive.append((c, title_pad, main_pad, title))

    outname = f"compare_digihit_multiplicity_TRY5PlSc_TRY5LiSc_TRY6LiSc_{threshold}MeV.png"
    for outdir in outdirs:
        c.SaveAs(os.path.join(outdir, outname))
    print("written " + ", ".join(os.path.join(outdir, outname) for outdir in outdirs))