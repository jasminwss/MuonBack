import ROOT
from argparse import ArgumentParser
from array import array
import numpy as np

ROOT.gROOT.SetBatch(True)

parser = ArgumentParser()
parser.add_argument('--geo', dest='geo', default='/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root')
parser.add_argument('--gap-deg', dest='gap_deg', type=float, default=5.0, help='report gaps in phi coverage larger than this many degrees')
options = parser.parse_args()

def Phicalc(x, y):
	"""Same convention as z_phi_origin.py: 90deg offset, start reading from bottom center."""
	r = ROOT.TMath.Sqrt(x*x + y*y)
	if r == 0:
	    return np.inf
	if y >= 0: phi = ROOT.TMath.ACos(x/r)
	else:      phi = -1*ROOT.TMath.ACos(x/r) + 2*ROOT.TMath.Pi()
	phi = phi*180/ROOT.TMath.Pi()
	phi = (phi + 90) % 360
	return phi

fgeo = ROOT.TFile.Open(options.geo)
geo = fgeo.Get("FAIRGeom")
ROOT.gGeoManager = geo
nav = geo.GetCurrentNavigator()
if not nav:
    nav = geo.AddNavigator()

parent_path = "cave/DecayVolume_1/T2_1/VetoLiSc_0"
if not nav.cd(parent_path):
    raise RuntimeError(f"could not cd to {parent_path}")
parent_vol = nav.GetCurrentNode().GetVolume()

# dedupe on phi rounded to 0.1 deg: the same (x,y) repeats across many z-layers of a bar
cells = {}  # rounded_phi_key -> (phi, x, y, count, example_name)
for i in range(parent_vol.GetNdaughters()):
    name = parent_vol.GetNode(i).GetName()
    nav.cd(f"{parent_path}/{name}")
    node = nav.GetCurrentNode()
    shape = node.GetVolume().GetShape()
    origin = array('d', [shape.GetOrigin()[0], shape.GetOrigin()[1], shape.GetOrigin()[2]])
    master = array('d', [0.0, 0.0, 0.0])
    nav.LocalToMaster(origin, master)
    phi = Phicalc(master[0], master[1])
    key = round(phi, 1)
    if key not in cells:
        cells[key] = [phi, master[0], master[1], 0, name]
    cells[key][3] += 1

print(f"{parent_vol.GetNdaughters()} daughter cells -> {len(cells)} distinct phi values (rounded to 0.1 deg)")
print(f"{'phi(deg)':>8} {'x(cm)':>10} {'y(cm)':>10} {'count':>6}   example_name")
for key in sorted(cells):
    phi, x, y, count, name = cells[key]
    print(f"{phi:8.1f} {x:10.3f} {y:10.3f} {count:6d}   {name}")

# report gaps in azimuthal coverage
sorted_phis = sorted(cells[k][0] for k in cells)
print(f"\nGaps in phi coverage larger than {options.gap_deg} deg:")
for a, b in zip(sorted_phis, sorted_phis[1:] + [sorted_phis[0] + 360]):
    if b - a > options.gap_deg:
        print(f"  [{a:.1f}, {b:.1f})  (width {b-a:.1f} deg)")
