# formerly inspect_root.py

import ROOT, os
from argparse import ArgumentParser
from ShipGeoConfig import load_from_root_file
import rootUtils as ut

ROOT.gROOT.SetBatch(True)

parser = ArgumentParser()
parser.add_argument('--version', dest='version', default= 'TRY6LiSc')
parser.add_argument('--tag', dest='tag', default='onlymaxEdepo')
options = parser.parse_args()
tag = options.tag if options.tag else "onlymaxEdepo"
path = '/eos/user/j/jaweiss/MuonBack/TRY6LiSc/11921562/' if options.version == 'TRY6LiSc' else '/eos/user/j/jaweiss/MuonBack/TRY5PlSc/'
print(f"Using path: {path}")


threshold_list=[0,10,45,90]

# setup histograms
h = {}

for threshold in threshold_list:
    ut.bookHist(h, f'{threshold}_maxenergydeposition'			,f'SBT (Digitised hits @ {threshold}MeV threshold )			; max(Energy deposition) (GeV)'				,1000,0,1)
    h[f'{threshold}_maxenergydeposition'].Sumw2()

# global variables
sGeo = None
Event_weight = {}
global_event_id = -1 #s.t. it starts at 0

for jobDir in sorted(os.listdir(path)):
    jobPath = f'{path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    job_files  = os.listdir(jobPath)
    geo_files  = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('geo_')  and fn.endswith('.root')]
    sim_files  = [f'{jobPath}/{fn}' for fn in job_files
                    if fn.startswith('sim_')  and fn.endswith('.root')]
    if not sim_files or not geo_files:
        print(f"Skipping {jobDir}: missing sim or geo file")
        continue

    # Geo einmal laden
    fgeo = None  # declare outside the loop
    if sGeo is None:
        try:
            fgeo = ROOT.TFile.Open(geo_files[0])
            ShipGeo = load_from_root_file(fgeo, "ShipGeo")
            print('ShipGeo loaded')
            sGeo = fgeo["FAIRGeom"]
        except Exception as e:
            print(f"Geo load failed: {e}")


    # access sim tree (MCTrack and vetoPoint both live here, no reco file needed)
    f_sim  = ROOT.TFile.Open(sim_files[0])
    tree_sim  = f_sim.Get("cbmsim")

    for eventNr in range(tree_sim.GetEntries()):
        tree_sim.GetEntry(eventNr)

        #setup empty dicts
        ElossPerDetId       = {}

        global_event_id += 1

        # MCTrack lives in tree_sim
        for track in tree_sim.MCTrack:
            if track.GetPdgCode() in [13, -13]:  # muon
                Event_weight[global_event_id] = track.GetWeight()
                break

        weight = Event_weight[global_event_id]

        for veto_MCPoint in tree_sim.vetoPoint: # for every particle hitting the SBT in the simulation
            detID = veto_MCPoint.GetDetectorID()
            Eloss = veto_MCPoint.GetEnergyLoss()

            if detID not in ElossPerDetId:
                ElossPerDetId[detID] = 0

            ElossPerDetId[detID] += Eloss

        #Explicit  Digitisation
        digiSBT = {}

        for index,detID in enumerate(ElossPerDetId):
            aHit = ROOT.vetoHit(detID,ElossPerDetId[detID]) # digitized hit object — combining the cell ID with the total Eloss into a single reconstructed hit
            digiSBT[index] = aHit # storing all digi hits for the event


        #Reading Digitised Data

        maxeLoss = {threshold: -1 for threshold in threshold_list} #maximum energy deposition percell
        for aHit in digiSBT.values():

            eLoss  	=aHit.GetEloss()

            for threshold in threshold_list:

                if eLoss<0.001*threshold: continue

                if eLoss>maxeLoss[threshold]:
                    maxeLoss[threshold]= eLoss

        for threshold in threshold_list:

            if maxeLoss[threshold]==-1: continue

            h[f'{threshold}_maxenergydeposition'		].Fill(maxeLoss[threshold],weight)



out_file = ROOT.TFile(
    f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/{options.version}_{tag}.root",
    "RECREATE"
)
out_file.cd()

for key in h:
    h[key].SetOption('E1')
    h[key].Write()

out_file.Close()
