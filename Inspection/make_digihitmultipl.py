import ROOT, os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

pathTRY5 = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY5PlSc_full_onlySIM.root"
pathTRY6 = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/TRY6LiSc_full_onlySIM.root"

outdirs = sorted({os.path.dirname(pathTRY5), os.path.dirname(pathTRY6)})

# left panel = TRY5, right panel = TRY6
panels = [
    ("TRY5 (PlSc)", ROOT.TFile.Open(pathTRY5)),
    ("TRY6 (LiSc)", ROOT.TFile.Open(pathTRY6)),
]

# one overlay per file, all thresholds together, light->dark red like the reference slide
threshold_list = [0, 10, 20, 30, 45, 50, 60, 90]
light_rgb = (0xFB, 0xEA, 0xEA)
dark_rgb  = (0x7A, 0x00, 0x00)
n = len(threshold_list)

keep_alive = []  # PyROOT needs these kept around or the pad ends up empty

def draw_overlay(pad, f, label):
    pad.cd()
    pad.SetLogy()
    pad.SetLeftMargin(0.14)
    pad.SetRightMargin(0.04)

    clones = []
    for i, threshold in enumerate(threshold_list):
        hsrc = f.Get(f"{threshold}_digihit_multiplicity")
        if not hsrc:
            print(f"Skipping {label} {threshold} MeV: histogram missing")
            continue

        hist = hsrc.Clone(f"{label}_{threshold}_digihit_multiplicity")
        hist.SetDirectory(0)

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

    clones[0][1].SetTitle(';Number of triggered SBT cells per event;Events per spill')
    clones[0][1].Draw('HIST')
    for _, hist in clones[1:]:
        hist.Draw('HIST SAME')

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(62)
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.16, 0.83, label)

    leg = ROOT.TLegend(0.68, 0.45, 0.95, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    for threshold, hist in clones:
        leg.AddEntry(hist, f'{threshold} MeV threshold', 'f')
    leg.Draw()

    keep_alive.append((clones, leg, latex))

canvas = ROOT.TCanvas("c_digihit_multiplicity_compare", "digihit multiplicity: TRY5 vs TRY6", 1800, 750)
canvas.Divide(2, 1)

for i, (label, f) in enumerate(panels, start=1):
    draw_overlay(canvas.cd(i), f, label)

outname = "compare_digihit_multiplicity_overlay.png"
for outdir in outdirs:
    canvas.SaveAs(os.path.join(outdir, outname))

print("written " + ", ".join(os.path.join(outdir, outname) for outdir in outdirs))
