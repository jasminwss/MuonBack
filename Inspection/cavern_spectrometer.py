# OPEN QUESTION (22.10.2026), revisit once the full run is done:
#   Which SBT cell multiplicity do we want for cavern events -
#   (a) all particles hitting the SBT in an event where a muon interacted in the cavern (what this script fills), or
#   (b) only the cells coming from the cavern muon itself (+ its descendants)?
#   Quick check (4 jobs, 6569 cavern events with SBT hits): 96-98% of the fired cells come from the cavern muon, so (a) ~ (b).
#   Related: is cavern background only an SBT rate issue (cavern muons never reached the straws in the test),
#   or also a background for the signal?
#
# SBT multiplicity and Edep per cell for cavern events only, split by whether the
# cavern muon also makes it into the spectrometer:
#   all   - every event classified as cavern (same condition as classify_event_origin in inspect_Back.py)
#   truth - the cavern muon has >= 1 strawtubesPoint
#   digi  - the cavern muon has >= 1 valid Digi_strawtubesHit
#   reco  - a converged FitTrack has fitTrack2MC == cavern muon
# The categories are nested: all > truth > digi > reco.
# SBT digitisation is the same as in inspect_Back.py (sum Eloss per cell, threshold cut).
# Wall heatmaps: where the cavern muon interacts in the concrete = start vertex of its most
# energetic daughter inside the Cavern volume, one entry per cavern muon, z-y (wall face) and x-y (beam view).
# p_station1 / station1_xy: momentum and x-y of the cavern muon at its most upstream strawtubesPoint in station 1 (truth/digi/reco only).
#
# usage:
#   python cavern_spectrometer.py --path /eos/user/j/jaweiss/MuonBack/TRY6LiSc_88d2794/12996649/ --tag TRY6LiSc_88d2794
#   python cavern_spectrometer.py --tag TRY6LiSc_88d2794 --plot-only   (redraw from the existing ROOT file)

import ROOT, os, math
from argparse import ArgumentParser
from array import array

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

parser = ArgumentParser()
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack/TRY6LiSc_88d2794/12996649/')
parser.add_argument('--tag', dest='tag', default='TRY6LiSc_88d2794')
parser.add_argument('--raw', dest='raw', action='store_true', default=False, help='fill with 1 instead of the event weight')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='only process the first 50 jobs')
parser.add_argument('--plot-only', dest='plot_only', action='store_true', default=False, help='skip the event loop, redraw from the ROOT file')
options = parser.parse_args()

threshold_list = [0, 10, 20, 30, 45, 50, 60, 90]
categories = ['all', 'truth', 'digi', 'reco']
cat_label = {
    'all':   'all cavern events',
    'truth': '#mu has straw MC points',
    'digi':  '#mu has straw digi hits',
    'reco':  '#mu reconstructed (converged fit)',
}
p_categories = categories[1:]  # 'all' would be identical to 'truth' for the station-1 momentum
cat_style = {  # (colour, line style)
    'all':   ('#071b3c', 1),
    'truth': ('#c64384', 2),
    'digi':  ('#e3a0c0', 7),
    'reco':  ('#f1debc', 1),
}
EDEP_REBIN = 10  # Edep is booked with 1 MeV bins, plotted in 10 MeV bins
# inner ECN3 hall in cm (passive/ShipCave.cxx: experiment_cavern box at ECN3_shift, z_transition = 20.52 m)
HALL_X = (-456., 1143.)
HALL_Y = (-336., 864.)
HALL_Z = (2134., 12052.)
# straw aperture in cm (geometry/strawtubes_config.yaml: SST width/height = half lengths)
ST_X = (-200., 200.)
ST_Y = (-300., 300.)

tag = options.tag
if options.raw:  tag += '_raw'
if options.test: tag += '_test'

outdir   = os.path.dirname(os.path.abspath(__file__))
rootname = os.path.join(outdir, f'{tag}_cavern_spectrometer.root')

def book():
    h = {}
    h['n_events']     = ROOT.TH1D('n_events',     'cavern events;;Events per spill', len(categories), 0, len(categories))
    h['n_events_raw'] = ROOT.TH1D('n_events_raw', 'cavern events;;MC events',       len(categories), 0, len(categories))
    for c in categories:
        for t in threshold_list:
            h[f'{c}_{t}_digihit_multiplicity'] = ROOT.TH1D(
                f'{c}_{t}_digihit_multiplicity',
                f'{cat_label[c]} @ {t} MeV;Number of triggered SBT cells in an event;Events per spill',
                2001, -0.5, 2000.5)
            h[f'{c}_{t}_digihit_energydeposition'] = ROOT.TH1D(
                f'{c}_{t}_digihit_energydeposition',
                f'{cat_label[c]} @ {t} MeV;E_deposition per digihit (GeV);Digihits per spill',
                1000, 0., 1.)
        h[f'{c}_wall_zy'] = ROOT.TH2D(f'{c}_wall_zy', f'{cat_label[c]};z (cm);y (cm);Muons per spill',
                                      202, 2000., 12100., 65, -400., 900.)
        h[f'{c}_wall_xy'] = ROOT.TH2D(f'{c}_wall_xy', f'{cat_label[c]};x (cm);y (cm);Muons per spill',
                                      200, -700., 1300., 150, -500., 1000.)
    for c in p_categories:
        h[f'{c}_p_station1'] = ROOT.TH1D(f'{c}_p_station1', f'{cat_label[c]};p at straw station 1 (GeV);Muons per spill',
                                         80, 0., 400.)
        h[f'{c}_station1_xy'] = ROOT.TH2D(f'{c}_station1_xy', f'{cat_label[c]};x (cm);y (cm);Muons per spill',
                                          70, -350., 350., 80, -400., 400.)
    for hist in h.values():
        hist.Sumw2()
        hist.SetDirectory(0)
    return h

def get_cavern_muons(event):
    """{TrackID: (x, y, z)} for all muons with a daughter starting inside the Cavern volume,
    (x, y, z) = start vertex of the most energetic such daughter (interaction point in the wall).
    Same condition as is_event_with_muonhit_in_CAVERN in inspect_Back.py, but
    collects every such muon instead of returning at the first."""
    vtx = {}  # TrackID -> (E, x, y, z)
    for track in event.MCTrack:
        motherId = track.GetMotherId()
        if motherId == -1: continue
        if abs(event.MCTrack[motherId].GetPdgCode()) == 13:
            node = ROOT.gGeoManager.FindNode(track.GetStartX(), track.GetStartY(), track.GetStartZ())
            if node and node.GetVolume().GetName().startswith('Cavern'):
                if motherId not in vtx or track.GetEnergy() > vtx[motherId][0]:
                    vtx[motherId] = (track.GetEnergy(), track.GetStartX(), track.GetStartY(), track.GetStartZ())
    return {k: v[1:] for k, v in vtx.items()}

def spectrometer_flags(tree, tree_sim, eventNr, muon_ids):
    """truth / digi / reco flags for the cavern muons. tree = reco, tree_sim = sim (already at eventNr).
    digi and reco need straw MC points of the muon, so reco is only read if truth is set."""
    truth = any(p.GetTrackID() in muon_ids for p in tree_sim.strawtubesPoint)
    if not truth:
        return {'all': True, 'truth': False, 'digi': False, 'reco': False}

    tree.GetEntry(eventNr)
    assert tree.ShipEventHeader.GetMCEntryNumber() == tree_sim.MCEventHeader.GetEventID(), \
        f'sim/reco mismatch at entry {eventNr}'
    # Digi_strawtubesHits[i] is made from strawtubesPoint[i] (strawtubesDetector.digitize)
    assert tree.Digi_strawtubesHits.size() == tree_sim.strawtubesPoint.size(), 'straw digi/point mismatch'
    digi = any(hit.isValid() and tree_sim.strawtubesPoint[i].GetTrackID() in muon_ids
               for i, hit in enumerate(tree.Digi_strawtubesHits))
    reco = any(tree.fitTrack2MC[k] in muon_ids and track.getFitStatus().isFitConverged()
               for k, track in enumerate(tree.FitTracks))
    return {'all': True, 'truth': truth, 'digi': digi, 'reco': reco}

def fill(h):
    n_events, n_cavern, exception_issues = 0, 0, {}
    fgeo = None
    job_nmbr = 0
    for jobDir in sorted(os.listdir(options.path)):
        if options.test and job_nmbr >= 50:
            break
        job_nmbr += 1
        jobPath = f'{options.path}/{jobDir}'
        if not os.path.isdir(jobPath):
            continue
        job_files  = os.listdir(jobPath)
        reco_files = [f'{jobPath}/{fn}' for fn in job_files if fn.startswith('reco_') and fn.endswith('.root')]
        geo_files  = [f'{jobPath}/{fn}' for fn in job_files if fn.startswith('geo_')  and fn.endswith('.root')]
        sim_files  = [f'{jobPath}/{fn}' for fn in job_files if fn.startswith('sim_')  and fn.endswith('.root')]
        if not reco_files or not sim_files or not geo_files:
            print(f'Skipping {jobDir}: missing reco, sim or geo file')
            continue

        f, f_sim = None, None
        try:
            # geometry once, needed for gGeoManager.FindNode in the cavern check
            if fgeo is None:
                fgeo = ROOT.TFile.Open(geo_files[0])
                fgeo.Get('FAIRGeom')

            f_sim    = ROOT.TFile.Open(sim_files[0])
            tree_sim = f_sim.Get('cbmsim')
            f        = ROOT.TFile.Open(reco_files[0])
            tree     = f['ship_reco_sim']
            tree_sim.SetBranchStatus('*', 0)
            for b in ['MCEventHeader*', 'MCTrack*', 'vetoPoint*', 'strawtubesPoint*']:
                tree_sim.SetBranchStatus(b, 1)
            tree.SetBranchStatus('*', 0)
            for b in ['ShipEventHeader*', 'Digi_strawtubesHits*', 'FitTracks*', 'fitTrack2MC*']:
                tree.SetBranchStatus(b, 1)

            # loop over sim, pull reco to the same row with GetEntry (only where needed, see spectrometer_flags)
            for eventNr, event_sim in enumerate(tree_sim):
                n_events += 1

                # same event weight as inspect_Back.py: weight of the first muon in MCTrack
                weight = None
                for track in event_sim.MCTrack:
                    if track.GetPdgCode() in [13, -13]:
                        weight = track.GetWeight()
                        break
                if weight is None:
                    continue
                if options.raw:
                    weight = 1.0

                cavern_vtx = get_cavern_muons(event_sim)
                if not cavern_vtx:
                    continue
                muon_ids = set(cavern_vtx)
                n_cavern += 1

                flags = spectrometer_flags(tree, event_sim, eventNr, muon_ids)

                # cavern muon TrackID -> (z, p, x, y) of its most upstream strawtubesPoint in station 1 (detID = station * 1e6 + ...)
                st1 = {}
                if flags['truth']:
                    for point in event_sim.strawtubesPoint:
                        tid = point.GetTrackID()
                        if tid not in muon_ids or point.GetDetectorID() // 1000000 != 1: continue
                        if tid not in st1 or point.GetZ() < st1[tid][0]:
                            st1[tid] = (point.GetZ(), math.sqrt(point.GetPx()**2 + point.GetPy()**2 + point.GetPz()**2),
                                        point.GetX(), point.GetY())

                # sum Eloss per cell, as in inspect_Back.py
                ElossPerDetId = {}
                for veto_MCPoint in event_sim.vetoPoint:
                    detID = veto_MCPoint.GetDetectorID()
                    ElossPerDetId[detID] = ElossPerDetId.get(detID, 0.) + veto_MCPoint.GetEnergyLoss()

                for c in categories:
                    if not flags[c]:
                        continue
                    h['n_events'].Fill(categories.index(c), weight)
                    h['n_events_raw'].Fill(categories.index(c))
                    for x, y, z in cavern_vtx.values():
                        h[f'{c}_wall_zy'].Fill(z, y, weight)
                        h[f'{c}_wall_xy'].Fill(x, y, weight)
                    if c in p_categories:
                        for _, p, x, y in st1.values():
                            h[f'{c}_p_station1'].Fill(p, weight)
                            h[f'{c}_station1_xy'].Fill(x, y, weight)
                    for t in threshold_list:
                        mult = 0
                        for eloss in ElossPerDetId.values():
                            if eloss < 0.001 * t: continue
                            mult += 1
                            h[f'{c}_{t}_digihit_energydeposition'].Fill(eloss, weight)
                        h[f'{c}_{t}_digihit_multiplicity'].Fill(mult, weight)

            f_sim.Close()
            f.Close()
        except Exception as e:
            if f_sim:
                f_sim.Close()
            if f:
                f.Close()
            exception_issues[jobDir] = e
            continue

    print(f'processed {n_events} events, {n_cavern} classified as cavern')
    print('Exceptions:\n', exception_issues)

def summary(h):
    n_all, n_all_raw = h['n_events'].GetBinContent(1), h['n_events_raw'].GetBinContent(1)
    print(f'\n  {"category":<36} {"MC events":>10} {"events/spill":>14} {"fraction":>10}')
    for i, c in enumerate(categories, start=1):
        n, n_raw = h['n_events'].GetBinContent(i), h['n_events_raw'].GetBinContent(i)
        print(f'  {cat_label[c].replace("#mu", "mu"):<36} {n_raw:>10.0f} {n:>14.3e} {n / n_all if n_all else 0:>10.3f}')

def draw_overlay(h, quantity, xtitle, ytitle, xmax, rebin, name):
    # clone + rebin everything first, so all panels can share one y range
    hists = {}
    for t in threshold_list:
        for cat in categories:
            hc = h[f'{cat}_{t}_{quantity}'].Clone(f'{cat}_{t}_{quantity}_draw')
            hc.SetDirectory(0)
            if rebin > 1: hc.Rebin(rebin)
            col, ls = cat_style[cat]
            hc.SetLineColor(ROOT.TColor.GetColor(col)); hc.SetLineStyle(ls); hc.SetLineWidth(4)
            hc.SetTitle(f';{xtitle};{ytitle}')
            hc.GetXaxis().SetRangeUser(0, xmax)
            hists[(t, cat)] = hc
    ymax = max(hc.GetMaximum() for hc in hists.values())
    ymin = min((hc.GetMinimum(0) for hc in hists.values() if hc.GetMinimum(0) > 0), default=1e-3)

    c = ROOT.TCanvas(f'c_{name}', name, 2800, 1500)
    title_pad = ROOT.TPad(f'title_pad_{name}', '', 0, 0.88, 1, 1)
    main_pad  = ROOT.TPad(f'main_pad_{name}',  '', 0, 0, 1, 0.88)
    title_pad.Draw(); main_pad.Draw()
    title_pad.cd()
    title = ROOT.TLatex(); title.SetNDC(); title.SetTextFont(62); title.SetTextSize(0.32); title.SetTextAlign(22)
    title.DrawLatex(0.5, 0.75, f'{options.tag}: cavern events, {name}')
    # legend across the top instead of inside a panel
    leg = ROOT.TLegend(0.03, 0.02, 0.97, 0.45)
    leg.SetNColumns(len(categories)); leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.26)
    for cat in categories:
        leg.AddEntry(hists[(threshold_list[0], cat)], cat_label[cat], 'l')
    leg.Draw()
    main_pad.Divide(4, 2)
    keep = [title_pad, main_pad, title, leg]
    for i, t in enumerate(threshold_list, start=1):
        pad = main_pad.cd(i)
        pad.SetLogy(); pad.SetLeftMargin(0.19); pad.SetRightMargin(0.04); pad.SetBottomMargin(0.17); pad.SetTopMargin(0.05)
        for j, cat in enumerate(categories):
            hc = hists[(t, cat)]
            hc.SetMaximum(5 * ymax); hc.SetMinimum(0.5 * ymin)
            for axis in (hc.GetXaxis(), hc.GetYaxis()):
                axis.SetLabelSize(0.06); axis.SetTitleSize(0.065)
            hc.GetXaxis().SetTitleOffset(1.1); hc.GetYaxis().SetTitleOffset(1.45)
            hc.GetXaxis().SetNdivisions(505)
            if j > 0 and hc.Integral() == 0: continue  # empty category would show up as a flat line at the bottom
            hc.Draw('HIST' if j == 0 else 'HIST SAME')
        lab = ROOT.TLatex(); lab.SetNDC(); lab.SetTextFont(62); lab.SetTextSize(0.075); lab.SetTextAlign(33)
        lab.DrawLatex(0.93, 0.92, f'{t} MeV')
        keep.append(lab)
    keep += list(hists.values())
    c.SaveAs(os.path.join(outdir, f'{tag}_cavern_spectrometer_{quantity}.png'))

def draw_heatmap(h, quantity, cats, outline, nx, ny):
    """2D heatmap {cat}_{quantity}, one panel per category in an nx x ny grid; outline = (x1, y1, x2, y2) drawn as a dashed box"""
    # single-hue sequential palette (light -> dark magenta), so low and high rates are not read as different categories
    cols = ['#fbeef4', '#c64384', '#3d0a24']
    rgb = [[int(col[i:i + 2], 16) / 255. for col in cols] for i in (1, 3, 5)]
    ROOT.TColor.CreateGradientColorTable(len(cols), array('d', [0., 0.5, 1.]), *[array('d', v) for v in rgb], 255)

    c = ROOT.TCanvas(f'c_{quantity}', quantity, 2800, 1500)
    c.Divide(nx, ny)
    keep = []
    for i, cat in enumerate(cats, start=1):
        pad = c.cd(i)
        pad.SetLogz(); pad.SetLeftMargin(0.05 * nx); pad.SetRightMargin(0.08 * nx); pad.SetBottomMargin(0.12)  # narrower pads -> larger margins
        hc = h[f'{cat}_{quantity}']
        hc.SetTitle(f'{options.tag}: {cat_label[cat]}')
        for axis in (hc.GetXaxis(), hc.GetYaxis(), hc.GetZaxis()):
            axis.SetLabelSize(0.045); axis.SetTitleSize(0.05)
        hc.GetYaxis().SetTitleOffset(0.95); hc.GetZaxis().SetTitleOffset(1.1)
        hc.Draw('COLZ')
        box = ROOT.TBox(*outline)
        box.SetFillStyle(0); box.SetLineColor(ROOT.kGray + 2); box.SetLineStyle(2); box.SetLineWidth(2)
        box.Draw()
        keep.append(box)
    c.SaveAs(os.path.join(outdir, f'{tag}_cavern_spectrometer_{quantity}.png'))

def draw_p_station1(h):
    hists = [h[f'{cat}_p_station1'] for cat in p_categories]
    ymax = max(hc.GetMaximum() for hc in hists)
    ymin = min((hc.GetMinimum(0) for hc in hists if hc.GetMinimum(0) > 0), default=1e-3)
    c = ROOT.TCanvas('c_p_station1', 'p station 1', 1800, 1200)
    c.SetLogy(); c.SetLeftMargin(0.12); c.SetRightMargin(0.04)
    leg = ROOT.TLegend(0.5, 0.74, 0.94, 0.88)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.035)
    for j, (cat, hc) in enumerate(zip(p_categories, hists)):
        col, ls = cat_style[cat]
        hc.SetLineColor(ROOT.TColor.GetColor(col)); hc.SetLineStyle(ls); hc.SetLineWidth(4)
        hc.SetTitle(f'{options.tag}: cavern #mu at straw station 1')
        hc.SetMaximum(5 * ymax); hc.SetMinimum(0.5 * ymin)
        hc.Draw('HIST' if j == 0 else 'HIST SAME')
        leg.AddEntry(hc, cat_label[cat], 'l')
    leg.Draw()
    c.SaveAs(os.path.join(outdir, f'{tag}_cavern_spectrometer_p_station1.png'))

def plot(h):
    draw_overlay(h, 'digihit_multiplicity', 'Triggered SBT cells per event', 'Events per spill',
                 100, 1, 'SBT digihit multiplicity')
    draw_overlay(h, 'digihit_energydeposition', 'E_deposition per digihit (GeV)', 'Digihits per spill',
                 1., EDEP_REBIN, 'SBT E_deposition per cell')
    if 'all_wall_zy' in h:  # older ROOT files have no wall histograms
        draw_heatmap(h, 'wall_zy', categories, (HALL_Z[0], HALL_Y[0], HALL_Z[1], HALL_Y[1]), 2, 2)
        draw_heatmap(h, 'wall_xy', categories, (HALL_X[0], HALL_Y[0], HALL_X[1], HALL_Y[1]), 2, 2)
    if 'truth_p_station1' in h:
        draw_p_station1(h)
        draw_heatmap(h, 'station1_xy', p_categories, (ST_X[0], ST_Y[0], ST_X[1], ST_Y[1]), 3, 1)

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
