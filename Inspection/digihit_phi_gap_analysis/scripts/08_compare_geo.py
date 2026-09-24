import ROOT

files = [
    "/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_1026/geo_11921562_1026.root",
    "/eos/experiment/ship/simulation/cuda_muons/try_2025/processed_muons/geo_cuda_test.root",
]

def walk(node, prefix, out):
    vol = node.GetVolume()
    matrix = node.GetMatrix()
    trans = matrix.GetTranslation()
    entry = f"{prefix}/{node.GetName()} vol={vol.GetName()} pos=({trans[0]:.3f},{trans[1]:.3f},{trans[2]:.3f})"
    out.append(entry)
    for i in range(node.GetNdaughters()):
        walk(node.GetDaughter(i), prefix + "/" + node.GetName(), out)

results = {}
for fn in files:
    f = ROOT.TFile.Open(fn)
    geo = f.Get("FAIRGeom")
    top = geo.GetTopVolume()
    per_branch = {}
    for i in range(top.GetNdaughters()):
        n = top.GetNode(i)
        out = []
        walk(n, "", out)
        per_branch[n.GetName()] = out
    results[fn] = per_branch
    f.Close()

a, b = files
names = sorted(set(results[a].keys()) | set(results[b].keys()))
for name in names:
    #print(name)
    oa = results[a].get(name)
    #print(oa)
    ob = results[b].get(name)
    if oa is None:
        print(f"{name}: MISSING in A")
    elif ob is None:
        print(f"{name}: MISSING in B")
    elif set(oa) == set(ob):
        print(f"{name}: identical ({len(oa)} nodes)")
    else:
        print(f"{name}: DIFFERS A={len(oa)} B={len(ob)}")
