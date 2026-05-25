import ROOT, os
from rootpyPickler import Unpickler
from argparse import ArgumentParser

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

parser = ArgumentParser()
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack')
options = parser.parse_args()

sGeo = None

for jobDir in sorted(os.listdir(options.path)):
    print(f"Checking {jobDir}...")
    jobPath = f'{options.path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    print(f"after continue")
    job_files  = os.listdir(jobPath)
    #print(f"Files in {jobDir}: {job_files}")
    reco_files = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('reco_') and fn.endswith('.root')]
    geo_files  = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('geo_')  and fn.endswith('.root')]
    print('all files checked')
    if not reco_files or not geo_files:
        print(f"Skipping {jobDir}: missing reco or geo file")
        continue

    # Geo einmal laden
    fgeo = None  # declare outside the loop
    if sGeo is None:
        try:
            fgeo = ROOT.TFile.Open(geo_files[0])
            print(f"Opened geo file: {geo_files[0]}")
            # Skip upkl entirely — ShipGeo is never used downstream
            #upkl    = Unpickler(fgeo) #load Shipgeo dictionary written by run_simSfcript.py
			#ShipGeo = upkl.load('ShipGeo')
            sGeo = fgeo.FAIRGeom
            print(f"sGeo loaded: {sGeo}")
        except Exception as e:
            print(f"Geo load failed: {e}")

    f = ROOT.TFile.Open(reco_files[0])
    tree = f.ship_reco_sim
    #print('tree is here')
    
    for eventNr, event in enumerate(tree):
        for track in event.goodTracks:
            print("good track")
