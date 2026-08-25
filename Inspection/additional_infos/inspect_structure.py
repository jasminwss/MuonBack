import ROOT
ROOT.gROOT.SetBatch(True)
fgeo = ROOT.TFile.Open("/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/job_0/geo_11921562_0.root")
geo = fgeo.Get("FAIRGeom")
ROOT.gGeoManager = geo
nav = geo.GetCurrentNavigator()
if not nav:
    nav = geo.AddNavigator()

for parent in ["cave/DecayVolume_1/T2_1/VetoInnerWall_0",
               "cave/DecayVolume_1/T2_1/VetoOuterWall_0",
               "cave/DecayVolume_1/T2_1/VetoVerticalRib_0",
               "cave/DecayVolume_1/T2_1/VetoLongitRib_0"]:
    nav.cd(parent)
    vol = nav.GetCurrentNode().GetVolume()
    nd = vol.GetNdaughters()
    print(f"{parent}: {nd} daughters")
    for i in range(min(nd, 3)):
        child = vol.GetNode(i)
        cname = child.GetName()
        nav.cd(f"{parent}/{cname}")
        cnode = nav.GetCurrentNode()
        cvol = cnode.GetVolume()
        cnd = cvol.GetNdaughters()
        shape = cvol.GetShape()
        print(f"   {cname}  (grandchildren={cnd}, shape={shape.ClassName() if shape else None})")
