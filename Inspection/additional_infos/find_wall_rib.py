import ROOT

ROOT.gROOT.SetBatch(True)
fgeo = ROOT.TFile.Open("/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root")
geo = fgeo.Get("FAIRGeom")
ROOT.gGeoManager = geo
nav = geo.GetCurrentNavigator()
if not nav:
    nav = geo.AddNavigator()

top = geo.GetTopNode()

found = []

def walk(node, path, depth):
    name = node.GetName()
    full = path + "/" + name
    if ("wall" in name.lower() or "rib" in name.lower()):
        found.append(full)
    if depth > 6:
        return
    vol = node.GetVolume()
    for i in range(vol.GetNdaughters()):
        walk(vol.GetNode(i), full, depth+1)

walk(top, "", 0)

print(f"found {len(found)} nodes matching 'wall' or 'rib'")
for f in found[:60]:
    print(f)
if len(found) > 60:
    print(f"... and {len(found)-60} more")

# print unique parent paths (strip last component) to see grouping level
parents = sorted(set("/".join(f.split("/")[:-1]) for f in found))
print(f"\n{len(parents)} distinct parent paths:")
for p in parents:
    print(p)
