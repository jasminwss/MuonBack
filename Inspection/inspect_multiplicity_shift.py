# Why is there no ~61-cell peak in the digihit multiplicity at 0 MeV threshold?
# Hypothesis: the peak events also have extra cells with tiny Eloss, which push their
# 0 MeV multiplicity above 61 and smear the peak out.
# Check per event: multiplicity at 0 MeV vs multiplicity at threshold t (2D), and the
# 0 MeV multiplicity of the events that sit in the peak at threshold t (1D).
#
# usage:
#   python inspect_multiplicity_shift.py --path /eos/user/j/jaweiss/MuonBack/TRY6LiSc_88d2794/12996649/ --tag TRY6LiSc_88d2794
#   python inspect_multiplicity_shift.py --tag TRY6LiSc_88d2794 --plot-only   (redraw from the existing ROOT file)

import ROOT, os
from argparse import ArgumentParser

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

parser = ArgumentParser()
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack/TRY6LiSc_88d2794/12996649/')
parser.add_argument('--tag', dest='tag', default='TRY6LiSc_88d2794')
parser.add_argument('--raw', dest='raw', action='store_true', default=False, help='fill with 1 instead of the event weight')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='only process the first 50 jobs')
parser.add_argument('--plot-only', dest='plot_only', action='store_true', default=False, help='skip the event loop, redraw from the ROOT file')
parser.add_argument('--peak-lo', dest='peak_lo', type=int, default=60, help='lower edge of the peak window (cells, inclusive)')
parser.add_argument('--peak-hi', dest='peak_hi', type=int, default=62, help='upper edge of the peak window (cells, inclusive)')
options = parser.parse_args()

threshold_list = [0, 10, 20, 30, 45, 50, 60, 90]
compare_list   = [t for t in threshold_list if t > 0]
plot_list      = [10, 45, 90]  # thresholds shown in the PNGs

tag = options.tag
if options.raw:  tag += '_raw'
if options.test: tag += '_test'

outdir   = os.path.dirname(os.path.abspath(__file__))
rootname = os.path.join(outdir, f'{tag}_multiplicity_shift.root')
peak_str = f'{options.peak_lo}-{options.peak_hi}'

def book():
    h = {}
    for t in compare_list:
        h[f'mult_0MeV_vs_{t}MeV'] = ROOT.TH2D(
            f'mult_0MeV_vs_{t}MeV',
            f'per event;triggered SBT cells @ {t} MeV;triggered SBT cells @ 0 MeV',
            151, -0.5, 150.5, 401, -0.5, 400.5)
        h[f'mult_0MeV_peakevents_{t}MeV'] = ROOT.TH1D(
            f'mult_0MeV_peakevents_{t}MeV',
            f'events with {peak_str} cells @ {t} MeV;triggered SBT cells @ 0 MeV;Events per spill',
            401, -0.5, 400.5)
        h[f'shift_peakevents_{t}MeV'] = ROOT.TH1D(
            f'shift_peakevents_{t}MeV',
            f'events with {peak_str} cells @ {t} MeV;extra cells at 0 MeV (N_{{0 MeV}} - N_{{{t} MeV}});Events per spill',
            301, -0.5, 300.5)
    for hist in h.values():
        hist.Sumw2()
        hist.SetDirectory(0)
    return h

def fill(h):
    n_events, n_no_muon, exception_issues = 0, 0, {}
    job_nmbr = 0
    for jobDir in sorted(os.listdir(options.path)):
        if options.test and job_nmbr >= 50:
            break
        job_nmbr += 1
        jobPath = f'{options.path}/{jobDir}'
        if not os.path.isdir(jobPath):
            continue
        sim_files = [f'{jobPath}/{fn}' for fn in os.listdir(jobPath) if fn.startswith('sim_') and fn.endswith('.root')]
        if not sim_files:
            print(f'Skipping {jobDir}: missing sim file')
            continue

        f_sim = None
        try:
            f_sim    = ROOT.TFile.Open(sim_files[0])
            tree_sim = f_sim.Get('cbmsim')

            for event in tree_sim:
                n_events += 1

                # same event weight as inspect_Back.py: weight of the first muon in MCTrack
                weight = None
                for track in event.MCTrack:
                    if track.GetPdgCode() in [13, -13]:
                        weight = track.GetWeight()
                        break
                if weight is None:
                    n_no_muon += 1
                    continue
                if options.raw:
                    weight = 1.0

                # sum Eloss per cell, as in inspect_Back.py
                ElossPerDetId = {}
                for veto_MCPoint in event.vetoPoint:
                    detID = veto_MCPoint.GetDetectorID()
                    ElossPerDetId[detID] = ElossPerDetId.get(detID, 0.) + veto_MCPoint.GetEnergyLoss()

                mult = {t: sum(1 for eloss in ElossPerDetId.values() if eloss >= 0.001 * t) for t in threshold_list}

                for t in compare_list:
                    h[f'mult_0MeV_vs_{t}MeV'].Fill(mult[t], mult[0], weight)
                    if options.peak_lo <= mult[t] <= options.peak_hi:
                        h[f'mult_0MeV_peakevents_{t}MeV'].Fill(mult[0], weight)
                        h[f'shift_peakevents_{t}MeV'].Fill(mult[0] - mult[t], weight)

            f_sim.Close()
        except Exception as e:
            if f_sim:
                f_sim.Close()
            exception_issues[jobDir] = e
            continue

    print(f'processed {n_events} events, skipped {n_no_muon} without a muon in MCTrack')
    print('Exceptions:\n', exception_issues)

def summary(h):
    print(f'\n  peak window: {peak_str} cells at threshold t')
    print('  {:>8} {:>12} {:>14} {:>16} {:>18}'.format('t (MeV)', 'n events', 'events/spill', 'mean N(0 MeV)', 'mean extra cells'))
    for t in compare_list:
        hp = h[f'mult_0MeV_peakevents_{t}MeV']
        hs = h[f'shift_peakevents_{t}MeV']
        print('  {:>8} {:>12.0f} {:>14.3e} {:>16.1f} {:>18.1f}'.format(
            t, hp.GetEntries(), hp.Integral(0, hp.GetNbinsX() + 1), hp.GetMean(), hs.GetMean()))

def plot(h):
    keep = []

    # 2D: N(0 MeV) vs N(t), one panel per threshold
    c2 = ROOT.TCanvas('c_mult_shift_2D', 'multiplicity 0 MeV vs t', 2700, 820)
    title_pad = ROOT.TPad('title_pad_2D', '', 0, 0.91, 1, 1)
    main_pad  = ROOT.TPad('main_pad_2D',  '', 0, 0, 1, 0.91)
    title_pad.Draw(); main_pad.Draw()
    title_pad.cd()
    title = ROOT.TLatex(); title.SetNDC(); title.SetTextFont(62); title.SetTextSize(0.55); title.SetTextAlign(22)
    title.DrawLatex(0.5, 0.5, f'{options.tag}: SBT digihit multiplicity per event, 0 MeV vs threshold')
    main_pad.Divide(len(plot_list), 1)
    for i, t in enumerate(plot_list, start=1):
        pad = main_pad.cd(i)
        pad.SetLogz(); pad.SetLeftMargin(0.13); pad.SetRightMargin(0.19)
        h2 = h[f'mult_0MeV_vs_{t}MeV']
        h2.SetTitle('')
        h2.GetXaxis().SetRangeUser(0, 100)
        h2.GetYaxis().SetRangeUser(0, 250)
        h2.GetZaxis().SetTitle('Events per spill')
        h2.GetZaxis().SetTitleOffset(1.5)
        h2.Draw('COLZ')
        diag = ROOT.TLine(0, 0, 100, 100)  # N(0 MeV) >= N(t) always, so everything sits on or above this line
        diag.SetLineStyle(2); diag.SetLineColor(ROOT.kGray + 2); diag.Draw()
        band = ROOT.TBox(options.peak_lo - 0.5, 0, options.peak_hi + 0.5, 250)
        band.SetFillStyle(0); band.SetLineColor(ROOT.kRed + 1); band.SetLineWidth(2); band.Draw()
        lab = ROOT.TLatex(); lab.SetNDC(); lab.SetTextFont(62); lab.SetTextSize(0.045)
        lab.DrawLatex(0.17, 0.83, f'{t} MeV threshold')
        keep += [diag, band, lab]
    keep += [title_pad, main_pad, title]
    c2.SaveAs(os.path.join(outdir, f'{tag}_multiplicity_shift_2D.png'))

    # 1D: where do the peak events end up at 0 MeV?
    c1 = ROOT.TCanvas('c_mult_shift_1D', 'peak events at 0 MeV', 2700, 820)
    title_pad1 = ROOT.TPad('title_pad_1D', '', 0, 0.91, 1, 1)
    main_pad1  = ROOT.TPad('main_pad_1D',  '', 0, 0, 1, 0.91)
    title_pad1.Draw(); main_pad1.Draw()
    title_pad1.cd()
    title1 = ROOT.TLatex(); title1.SetNDC(); title1.SetTextFont(62); title1.SetTextSize(0.55); title1.SetTextAlign(22)
    title1.DrawLatex(0.5, 0.5, f'{options.tag}: 0 MeV multiplicity of the events with {peak_str} cells at threshold')
    main_pad1.Divide(len(plot_list), 1)
    for i, t in enumerate(plot_list, start=1):
        pad = main_pad1.cd(i)
        pad.SetLeftMargin(0.14); pad.SetRightMargin(0.04)
        h1 = h[f'mult_0MeV_peakevents_{t}MeV']
        h1.SetTitle(f';triggered SBT cells @ 0 MeV;Events per spill')
        h1.SetFillColor(ROOT.TColor.GetColor(0xB0, 0x60, 0x60)); h1.SetLineColor(ROOT.TColor.GetColor(0x6A, 0x3A, 0x3A))
        h1.SetFillStyle(1001); h1.SetLineWidth(2)
        h1.GetXaxis().SetRangeUser(0, 250)
        h1.SetMaximum(1.15 * h1.GetMaximum())
        h1.Draw('HIST')
        pad.Update()
        band = ROOT.TBox(options.peak_lo - 0.5, pad.GetUymin(), options.peak_hi + 0.5, pad.GetUymax())
        band.SetFillColorAlpha(ROOT.kAzure + 1, 0.35); band.SetLineWidth(0); band.Draw()
        lab = ROOT.TLatex(); lab.SetNDC(); lab.SetTextFont(62); lab.SetTextSize(0.045)
        lab.DrawLatex(0.45, 0.83, f'peak at {t} MeV: {peak_str} cells')
        lab2 = ROOT.TLatex(); lab2.SetNDC(); lab2.SetTextSize(0.04)
        lab2.DrawLatex(0.45, 0.77, f'{h1.GetEntries():.0f} events, mean @ 0 MeV = {h1.GetMean():.1f}')
        keep += [band, lab, lab2]
    keep += [title_pad1, main_pad1, title1]
    c1.SaveAs(os.path.join(outdir, f'{tag}_multiplicity_shift_peakevents.png'))

if options.plot_only:
    f_in = ROOT.TFile.Open(rootname)
    h = {}
    for k in f_in.GetListOfKeys():
        h[k.GetName()] = f_in.Get(k.GetName())
        h[k.GetName()].SetDirectory(0)
    f_in.Close()
else:
    h = book()
    fill(h)
    f_out = ROOT.TFile(rootname, 'RECREATE')
    for hist in h.values():
        hist.Write()
    f_out.Close()
    print(f'Histograms written to {rootname}')

summary(h)
plot(h)
