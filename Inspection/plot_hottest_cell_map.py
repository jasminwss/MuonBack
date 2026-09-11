#!/usr/bin/env python3
"""Where in the detector do the hottest / 2nd-hottest SBT cells (per threshold,
from inspect_Back.py's *_readme.txt) actually sit?

Doesn't re-run the event loop: just loads the geometry once (cheap) and asks
ROOT.vetoHit(detID, 0.) for its X/Y/Z, the same call inspect_Back.py already
uses to digitise a hit's position. Parses the "hottest detID / 2nd detID"
table straight out of the readme, so no numbers need to be copied by hand.

Top/side/back-view layout and geometry outline borrowed from
MuonBackground/dis_surviving_xyzplots.py (aka Anupama).

Usage:
    python plot_hottest_cell_map.py --readme TRY6LiSc_full_matchedRecoSim_readme.txt \
                                     --geo /eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root

or 

    python plot_hottest_cell_map.py --readme TRY5PlSc_full_matchedRecoSim_readme.txt \
                                     --geo /eos/user/j/jaweiss/MuonBack/TRY5PlSc/job_0_250389_13200001/geo_83621811-e605-4dec-acb1-2154419ea7e4.root
"""
import os, re, sys
from argparse import ArgumentParser
from itertools import zip_longest

import ROOT
from ShipGeoConfig import load_from_root_file
ROOT.gROOT.SetBatch(True)

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.transforms import Affine2D

sys.path.insert(0, '/afs/cern.ch/work/j/jaweiss/private/MuonBackground')
from dis_surviving_xyzplots import load_style, add_geometry

parser = ArgumentParser()
parser.add_argument('--readme', default='TRY6LiSc_full_matchedRecoSim_readme.txt')
parser.add_argument('--geo',    default='/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root',
                     help='any single geo_*.root file from the production (geometry is the same for every job)')
parser.add_argument('--out',    default=None, help='output basename (default: derived from --readme)')
options = parser.parse_args()

# --- parse "hottest detID / 2nd detID" table out of the readme ------------
row_re = re.compile(r'^\s*(\d+)\s*MeV\s+(-?\d+)\s+[\d.]+\s+(-?\d+)\s+[\d.]+\s*$')
hottest_cells = {}  # threshold -> (hottest_detID, second_detID)
with open(options.readme) as f:
    in_table = False
    for line in f:
        if 'hottest detID' in line:
            in_table = True
            continue
        if not in_table:
            continue
        m = row_re.match(line)
        if m:
            threshold, h_id, s_id = int(m.group(1)), int(m.group(2)), int(m.group(3))
            hottest_cells[threshold] = (h_id, s_id)
        elif hottest_cells:
            break  # hit the closing '---' line after the table

if not hottest_cells:
    raise RuntimeError(f"couldn't find a 'hottest detID' table in {options.readme}")
print('parsed:', hottest_cells)

# --- load geometry once (no event loop) ------------------------------------
fgeo = ROOT.TFile.Open(options.geo)
ShipGeo = load_from_root_file(fgeo, "ShipGeo")
sGeo = fgeo["FAIRGeom"]
print('geometry loaded from', options.geo)

# dis_surviving_xyzplots.add_geometry() draws the decay vessel in a
# target-centred local frame (z in [-2500, 2500], length 5000 cm) but
# vetoHit/vetoPoint z is in the raw ShipGeo frame, where the vessel is
# ShipGeo.decayVolume.z0 .. z0+length (here ~3312..8312). Shifting the
# drawn geometry by the vessel's real centre z lines the two frames up.
Z_SHIFT = ShipGeo.decayVolume.z
print(f'decayVolume: z0={ShipGeo.decayVolume.z0:.0f}  length={ShipGeo.decayVolume.length:.0f}  '
      f'-> shifting drawn geometry by Z_SHIFT={Z_SHIFT:.0f} cm')

# --- coordinates per unique detID ------------------------------------------
detIDs = {detID for h_id, s_id in hottest_cells.values() for detID in (h_id, s_id) if detID >= 0}
coords = {}
for detID in detIDs:
    hit = ROOT.vetoHit(detID, 0.0)
    coords[detID] = (hit.GetX(), hit.GetY(), hit.GetZ())
    x, y, z = coords[detID]
    print(f'  detID {detID}: x={x:.1f} y={y:.1f} z={z:.1f}')
fgeo.Close()

# --- plot, same look as dis_surviving_xyzplots.py --------------------------
load_style()

fig = plt.figure(figsize=(15, 7), constrained_layout=True)
fig.suptitle('SBT hottest / 2nd-hottest cell per threshold', fontsize=15, fontweight='bold')
gs = gridspec.GridSpec(2, 8, figure=fig)

ax_zx = fig.add_subplot(gs[0, 0:5]); ax_zx.set_title('top view')
ax_zx.set_ylabel('x (cm)'); ax_zx.set_xlim(2500, 9500); ax_zx.set_ylim(-600, 600)

ax_zy = fig.add_subplot(gs[1, 0:5]); ax_zy.set_title('side view')
ax_zy.set_xlabel('z (cm)'); ax_zy.set_ylabel('y (cm)')
ax_zy.set_xlim(2500, 9500); ax_zy.set_ylim(-600, 600)

ax_xy = fig.add_subplot(gs[0:2, 5:7]); ax_xy.set_title('back view')
ax_xy.set_xlabel('x (cm)'); ax_xy.set_ylabel('y (cm)')
ax_xy.set_xlim(-250, 250); ax_xy.set_ylim(-400, 400)

add_geometry(ax_zx, ax_zy, ax_xy, show_detectors=True)
# add_geometry draws in the local (unshifted) z frame -> shift those patches
# into the raw frame. ax_xy (back view, x-y only) is untouched.
shift = Affine2D().translate(Z_SHIFT, 0)
for ax in (ax_zx, ax_zy):
    for patch in ax.patches:
        patch.set_transform(shift + patch.get_transform())

# one marker per (cell, rank): group the thresholds where a given cell was
# hottest / 2nd-hottest, so "hottest, 0,10,20 MeV" is a single star, and a
# different cell that was hottest at other thresholds is a second, darker
# star ("hottest, 30,45,50 MeV"). marker shape = rank, colour shade = group
# order (darker for the group with the higher thresholds).
cmap_hottest = plt.get_cmap('Reds')
cmap_second  = plt.get_cmap('Blues')

legend_entries = {'hottest': [], 'second': []}  # kind -> [(label, handle), ...]
for kind, cmap, marker, rank_label, size in (('hottest', cmap_hottest, '*', 'hottest', 260),
                                              ('second',  cmap_second,  '^', '2nd hottest', 170)):
    idx = 0 if kind == 'hottest' else 1
    cell_thresholds = {}  # detID -> [thresholds where it ranked this way]
    for threshold, ids in hottest_cells.items():
        detID = ids[idx]
        if detID >= 0:
            cell_thresholds.setdefault(detID, []).append(threshold)

    groups = sorted(cell_thresholds.items(), key=lambda kv: min(kv[1]))  # lowest thresholds first
    n = len(groups)
    for i, (detID, thrs) in enumerate(groups):
        x, y, z = coords[detID]
        frac = 0.5 if n == 1 else 0.3 + 0.6 * i / (n - 1)
        thrs_str = ','.join(str(t) for t in sorted(thrs))
        label = f'{detID} – {rank_label}, {thrs_str} MeV'
        kw = dict(marker=marker, s=size, color=cmap(frac),
                   edgecolor='black', linewidth=0.4, zorder=5 + i, label=label)
        h = ax_xy.scatter([x], [y], **kw)
        ax_zx.scatter([z], [x], **kw)
        ax_zy.scatter([z], [y], **kw)
        legend_entries[kind].append((label, h))

# interleave hottest/2nd column-major so the legend grid shows all "hottest"
# entries in row 1 and all "2nd hottest" entries directly below them
hot, sec = legend_entries['hottest'], legend_entries['second']
ordered = []
for h_entry, s_entry in zip_longest(hot, sec):
    if h_entry: ordered.append(h_entry)
    if s_entry: ordered.append(s_entry)
labels, handles = [l for l, h in ordered], [h for l, h in ordered]
ncol = max(len(hot), len(sec), 1)
fig.legend(handles, labels,
           loc='lower center', ncol=ncol, bbox_to_anchor=(0.45, -0.1),
           columnspacing=1.2, fontsize=12, frameon=True)

out_base = options.out or os.path.basename(options.readme).replace('_readme.txt', '')
out_png = f'{out_base}_hottest_cells_map.png'
fig.savefig(out_png, dpi=300, bbox_inches='tight', pad_inches=0.4)
plt.close(fig)
print(f'wrote {out_png}')
