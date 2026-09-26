# to review: z=0 is at the Target?

import ROOT, os, ctypes
from argparse import ArgumentParser
from ShipGeoConfig import load_from_root_file
import rootUtils as ut

ROOT.gROOT.SetBatch(True)
PDGData = ROOT.TDatabasePDG.Instance()

parser = ArgumentParser()
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack/TRY5PlSc')
parser.add_argument('--tag', dest='tag', default='')
parser.add_argument('--raw', dest='raw', action='store_true', default=False, help='If set, will fill histograms with weight=1 instead of the muon flux weight')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='If set, will only process the first 50 jobs for testing purposes')
options = parser.parse_args()
raw = options.raw
test = options.test

print("using path:", options.path)

# 0 = "any digihit" (for comparison with the geometric numbers below), 90 = Heiko's
# reference threshold from the slack thread
threshold_list = [0, 90]

MUON_PDGS = (13, -13)
STEP_LIMIT = 5000  # safety cap on navigator boundary crossings per muon, protects
                    # against an ill-formed geometry/direction causing an infinite loop
SBT_NODE = 'DecayVolume_1/T2_1'  # SBT envelope (walls, ribs, LiSc cells), used as ray-trace bounding box

# Straight-line ray trace in C++ (a PyROOT loop costs ~6 python->C++ calls per step).
# Only the part of the ray inside the SBT bounding box is stepped; rays that miss the
# box are skipped entirely, so the navigator no longer walks the whole world
# (SplitCal, muon shield, ...) for every muon.
ROOT.gInterpreter.Declare('''
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TGeoBBox.h"
#include "TGeoMatrix.h"
#include <cstring>
#include <algorithm>
namespace onlymu {
double bbLo[3], bbHi[3];

bool InitSBTBox(const char *path) {
    if (!gGeoManager->cd(path)) return false;
    const TGeoHMatrix *m = gGeoManager->GetCurrentMatrix();
    const TGeoBBox *box = (const TGeoBBox *)gGeoManager->GetCurrentVolume()->GetShape();
    const double *o = box->GetOrigin();
    const double d[3] = {box->GetDX(), box->GetDY(), box->GetDZ()};
    for (int k = 0; k < 3; ++k) { bbLo[k] = 1e30; bbHi[k] = -1e30; }
    for (int c = 0; c < 8; ++c) {
        double loc[3], mas[3];
        for (int k = 0; k < 3; ++k) loc[k] = o[k] + ((c >> k) & 1 ? d[k] : -d[k]);
        m->LocalToMaster(loc, mas);
        for (int k = 0; k < 3; ++k) { bbLo[k] = std::min(bbLo[k], mas[k]); bbHi[k] = std::max(bbHi[k], mas[k]); }
    }
    return true;
}

// returns false if the ray misses the SBT box (paths stay 0)
bool TraceSBT(double x0, double y0, double z0, double ux, double uy, double uz,
              const char *scintMat, int stepLimit, double &pathLiSc, double &pathAl) {
    pathLiSc = 0.; pathAl = 0.;
    const double o[3] = {x0, y0, z0}, u[3] = {ux, uy, uz};
    double tmin = 0., tmax = 1e30;
    for (int k = 0; k < 3; ++k) {
        if (std::abs(u[k]) < 1e-12) {
            if (o[k] < bbLo[k] || o[k] > bbHi[k]) return false;
            continue;
        }
        double t1 = (bbLo[k] - o[k]) / u[k], t2 = (bbHi[k] - o[k]) / u[k];
        if (t1 > t2) std::swap(t1, t2);
        tmin = std::max(tmin, t1); tmax = std::min(tmax, t2);
        if (tmin > tmax) return false;
    }
    TGeoNavigator *nav = gGeoManager->GetCurrentNavigator();
    nav->InitTrack(x0 + ux * tmin, y0 + uy * tmin, z0 + uz * tmin, ux, uy, uz);
    double travelled = tmin;
    for (int n = 0; n < stepLimit && !nav->IsOutside() && travelled < tmax; ++n) {
        TGeoVolume *vol = nav->GetCurrentVolume();
        const char *mat = vol ? vol->GetMaterial()->GetName() : "";
        nav->FindNextBoundaryAndStep();
        const double step = nav->GetStep();
        travelled += step;
        if (!std::strcmp(mat, scintMat))        pathLiSc += step;
        else if (!std::strcmp(mat, "Aluminum"))      pathAl   += step;
    }
    return true;
}
}
''')

# setup histograms
h = {}
ut.bookHist(h, 'vetopoint_pdg', 'SBT (vetoPoint info) ; pdg ; ', 20, -0.5, 20.5)
ut.bookHist(h, 'muon_scint_pathlength_cm',
            'Muon path length through SBT scintillator (straight-line geometry ray-trace) ; path length (cm) ; ',
            500, 0., 6000.)
ut.bookHist(h, 'muon_alu_pathlength_cm',
            'Muon path length through SBT Aluminum walls/ribs (straight-line geometry ray-trace) ; path length (cm) ; ',
            500, 0., 2000.)
for threshold in threshold_list:
    ut.bookHist(h, f'{threshold}_digihit_multiplicity',
                f'SBT digitised hits @ {threshold}MeV threshold ; Number of triggered SBT cells in an event ; ',
                2000, -0.5, 1999.5)

# global variables
sGeo = None
pathLiSc_ref = ctypes.c_double(0.)  # output args of onlymu::TraceSBT
pathAl_ref = ctypes.c_double(0.)
scint_mat = None
scint_density = None
alu_density = None
sbt_pdg_list = {}
sbt_pdg_index = 0
Event_weight = {}          # global_event_id -> muon flux weight
global_event_id = -1       # so it starts at 0
exception_issues = {}
job_nmbr = 0

# running sums for the printed summary (kept separate from the histograms so the
# reported means aren't affected by histogram bin width, see the plan's note on this)
total_muons_weight = 0.0
digihit_weight_sum = {threshold: 0.0 for threshold in threshold_list}
n_with_LiSc_path_weight = 0.0        # sum of weight, muons with a geometric path through LiSc
sum_LiSc_path_weighted_length = 0.0  # sum of weight * pathLiSc, same subset
sum_Al_path_weighted_length = 0.0    # sum of weight * pathAl, same subset (conditioned on LiSc path>0)

for jobDir in sorted(os.listdir(options.path)):
    if test and job_nmbr >= 10:  # Limit to first jobs for testing
        break
    job_nmbr += 1
    jobPath = f'{options.path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    job_files = os.listdir(jobPath)
    geo_files = [f'{jobPath}/{fn}' for fn in job_files
                 if fn.startswith('geo_') and fn.endswith('.root')]
    sim_files = [f'{jobPath}/{fn}' for fn in job_files
                 if fn.startswith('sim_') and fn.endswith('.root')]
    if not sim_files or not geo_files:
        print(f"Skipping {jobDir}: missing sim or geo file")
        continue

    f_sim, fgeo = None, None
    try:
        # Geo einmal laden
        if sGeo is None:
            fgeo = ROOT.TFile.Open(geo_files[0])
            ShipGeo = load_from_root_file(fgeo, "ShipGeo")
            print('ShipGeo loaded')
            sGeo = fgeo["FAIRGeom"]
            ROOT.gGeoManager = sGeo
            sbt_path = f'/{sGeo.GetTopNode().GetName()}/{SBT_NODE}'
            if not ROOT.onlymu.InitSBTBox(sbt_path):
                raise RuntimeError(f'SBT node {sbt_path} not found in geometry')
            print(f'SBT bounding box: x [{ROOT.onlymu.bbLo[0]:.1f}, {ROOT.onlymu.bbHi[0]:.1f}]  '
                  f'y [{ROOT.onlymu.bbLo[1]:.1f}, {ROOT.onlymu.bbHi[1]:.1f}]  '
                  f'z [{ROOT.onlymu.bbLo[2]:.1f}, {ROOT.onlymu.bbHi[2]:.1f}] cm')
            # SBT cell material, read from an actual cell: LiSc geometries use
            # "LiquidScintillator", PlSc ones "Scintillator"
            cells = sGeo.FindVolumeFast('VetoLiSc')
            if not cells or cells.GetNdaughters() == 0:
                raise RuntimeError('VetoLiSc volume (SBT cells) not found in geometry')
            scint_mat = cells.GetNode(0).GetVolume().GetMaterial().GetName()
            scint_density = sGeo.GetMaterial(scint_mat).GetDensity()
            alu_density = sGeo.GetMaterial("Aluminum").GetDensity()
            print(f"{scint_mat} density: {scint_density} g/cm3, Aluminum density: {alu_density} g/cm3")

        f_sim = ROOT.TFile.Open(sim_files[0])
        tree_sim = f_sim.Get("cbmsim")

        for eventNr, event in enumerate(tree_sim):

            global_event_id += 1

            # find the primary input muon: gives us both the flux weight and the
            # start position/momentum used as the straight-line ray for the
            # geometry path-length scan below
            muon_track = None
            for track in tree_sim.MCTrack:
                if track.GetPdgCode() in MUON_PDGS:
                    muon_track = track
                    break
            if muon_track is None:
                continue  # no muon in this event, nothing to measure

            Event_weight[global_event_id] = muon_track.GetWeight()
            weight = 1.0 if raw else Event_weight[global_event_id]
            total_muons_weight += weight

            # -- digihit multiplicity bookkeeping (any-particle deposit, for comparison
            #    with the geometric numbers -- see slack thread: >99.8% of these hits
            #    are EM debris, not the muon itself) --
            ElossPerDetId = {}
            for veto_MCPoint in tree_sim.vetoPoint:
                pdgCode = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
                detID = veto_MCPoint.GetDetectorID()
                Eloss = veto_MCPoint.GetEnergyLoss()
                ElossPerDetId[detID] = ElossPerDetId.get(detID, 0.0) + Eloss

                try:    particle_name = PDGData.GetParticle(pdgCode).GetName()
                except: particle_name = 'others'
                if particle_name not in sbt_pdg_list.values():
                    sbt_pdg_list[sbt_pdg_index] = particle_name
                    sbt_pdg_index += 1
                veto_pdg_key = [k for k, v in sbt_pdg_list.items() if v == particle_name][0]
                h['vetopoint_pdg'].Fill(veto_pdg_key, weight)

            for threshold in threshold_list:
                multiplicity = sum(1 for e in ElossPerDetId.values() if e >= 0.001 * threshold)
                h[f'{threshold}_digihit_multiplicity'].Fill(multiplicity, weight)
                if multiplicity >= 1:
                    digihit_weight_sum[threshold] += weight

            # -- geometric path length through SBT sensitive/frame material --
            # straight-line assumption, consistent with how the rest of the thread
            # treats the muon path ("the bouncing path was anyway also ignored")
            px, py, pz = muon_track.GetPx(), muon_track.GetPy(), muon_track.GetPz()
            p = (px * px + py * py + pz * pz) ** 0.5
            if p == 0:
                continue
            ROOT.onlymu.TraceSBT(muon_track.GetStartX(), muon_track.GetStartY(), muon_track.GetStartZ(),
                                 px / p, py / p, pz / p, scint_mat, STEP_LIMIT, pathLiSc_ref, pathAl_ref)
            pathLiSc, pathAl = pathLiSc_ref.value, pathAl_ref.value

            h['muon_scint_pathlength_cm'].Fill(pathLiSc, weight)
            h['muon_alu_pathlength_cm'].Fill(pathAl, weight)

            if pathLiSc > 0:
                n_with_LiSc_path_weight += weight
                sum_LiSc_path_weighted_length += weight * pathLiSc
                sum_Al_path_weighted_length += weight * pathAl

        f_sim.Close()
        if fgeo:
            fgeo.Close()
    except Exception as e:
        if f_sim:
            f_sim.Close()
        if fgeo:
            fgeo.Close()
        exception_issues[jobDir] = e
        continue

# Set bin labels on the pdg histogram using the completed dictionary
for idx, particle_name in sbt_pdg_list.items():
    h['vetopoint_pdg'].GetXaxis().SetBinLabel(idx + 1, particle_name)

if raw:
    for hist in h.values():
        hist.SetName(hist.GetName() + '_raw')

tag = options.tag if options.tag else "inspection_onlymu"
if raw:
    tag = tag + "_raw"
if test:
    tag = tag + "_test"

out_path = f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/{tag}.root"
out_file = ROOT.TFile(out_path, "RECREATE")
out_file.cd()
for key in h:
    h[key].SetOption('HIST')
    h[key].Write()
out_file.Close()
print(f"Histograms written to {out_path}")

mean_LiSc = sum_LiSc_path_weighted_length / n_with_LiSc_path_weight if n_with_LiSc_path_weight else 0.0
mean_Al = sum_Al_path_weighted_length / n_with_LiSc_path_weight if n_with_LiSc_path_weight else 0.0

lines = []
lines.append(f"Muons total (weighted, scaled to one spill):             {total_muons_weight:.5e}")
for threshold in threshold_list:
    frac = 100 * digihit_weight_sum[threshold] / total_muons_weight if total_muons_weight else 0.0
    lines.append(f"Muons with >=1 digihit in SBT (any particle, {threshold:3}MeV): "
                 f"{digihit_weight_sum[threshold]:.5e}  ({frac:.3f} %)")
lines.append("")
frac_geo = 100 * n_with_LiSc_path_weight / total_muons_weight if total_muons_weight else 0.0
lines.append(f"Muons with a geometric path through {scint_mat}:  {n_with_LiSc_path_weight:.5e}  ({frac_geo:.3f} %)")
lines.append(f"  mean scintillator path length (muons with path>0):  {mean_LiSc:.2f} cm  "
             f"({mean_LiSc * scint_density:.2f} g/cm2, rho={scint_density:.3f} g/cm3)")
lines.append(f"  mean aluminum path length     (same muons):         {mean_Al:.2f} cm  "
             f"({mean_Al * alu_density:.2f} g/cm2, rho={alu_density:.3f} g/cm3)")

summary = "\n".join(lines)
print("\n" + summary + "\n")

readme_path = f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/{tag}_readme.txt"
with open(readme_path, 'w') as readme:
    readme.write(summary + "\n")
print(f"Summary written to {readme_path}")

print('Exceptions:\n', exception_issues)
