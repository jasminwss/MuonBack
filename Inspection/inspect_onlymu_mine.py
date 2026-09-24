# to review: z=0 is at the Target?

import ROOT, os
from argparse import ArgumentParser
from ShipGeoConfig import load_from_root_file
import rootUtils as ut
from array import array
import numpy as np

ROOT.gROOT.SetBatch(True)
#ROOT.gErrorIgnoreLevel = ROOT.kFatal
PDGData = ROOT.TDatabasePDG.Instance()

parser = ArgumentParser()
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack/TRY5PlSc')
parser.add_argument('--tag', dest='tag', default='')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='If set, will only process the first some events for testing purposes')
options = parser.parse_args()
test = options.test

print("using path:", options.path)

h={}
#histogram for E_loss


def print_result(tag):
	
	global h,Event_weight,SBT_Event_weight,digihitrate_by_origin,sst_hitrate
	ut.writeHists(h, directory +tag+'.root')

	with open(directory +tag+'_readme.txt', 'w') as readme: 
				
		print("\n\n\n")
		
		
		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics',float(len(Event_weight)),float(sum(Event_weight.values()))))
		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics with SBT activity',float(len(SBT_Event_weight)),float(sum(SBT_Event_weight.values()))))

		total_weight = sum(Event_weight.values())
		frac_SBT           = 100*muons_in_SBT/total_weight if total_weight else 0.0
		frac_SBT_withEloss = 100*muons_in_SBT_withEloss/total_weight if total_weight else 0.0

		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}\t ({:.3f}% of all muons)".format(
			'Muons with a muon-hit in SBT', float(muons_in_SBT_raw), float(muons_in_SBT), frac_SBT))
		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}\t ({:.3f}% of all muons)".format(
			'...of those with Eloss>0', float(muons_in_SBT_withEloss_raw), float(muons_in_SBT_withEloss), frac_SBT_withEloss))

		print("\n\n  ================================================================================")
		print("\n  SBT")
		print("  --------------------------------------------------------------------------------\n\n")
		


# global variables
sGeo = None
sbt_pdg_list={}
sbt_pdg_index = 0
Event_weight = {}
global_event_id = -1 #s.t. it starts at 0
muon_min_eloss_array = np.full((100, 36), np.inf)  # Initialize with infinity
total_particlehitrate = 0
SBT_Event_weight = {}
min_maxEloss_array = {} 
ORIGIN_CATEGORIES = ('cavern', 'SBT', 'upstream')
digihitrate_by_origin = {}   # [threshold][origin][detID] =  hitrate
exception_issues = {}
job_nmbr = 0

muons_in_SBT_raw = 0
muons_in_SBT = 0
muons_in_SBT_withEloss_raw = 0 
muons_in_SBT_withEloss = 0

for jobDir in sorted(os.listdir(options.path)):
    if test and job_nmbr >= 10:  # Limit to first job for testing
        break
    job_nmbr += 1
    jobPath = f'{options.path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    job_files  = os.listdir(jobPath)
    #reco_files = [f'{jobPath}/{fn}' for fn in job_files
     #             if fn.startswith('reco_') and fn.endswith('.root')]
    geo_files  = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('geo_')  and fn.endswith('.root')]
    sim_files  = [f'{jobPath}/{fn}' for fn in job_files
                    if fn.startswith('sim_')  and fn.endswith('.root')]
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

        f_sim  = ROOT.TFile.Open(sim_files[0])
        tree_sim  = f_sim.Get("cbmsim")
        
        for eventNr, event in enumerate(tree_sim): 

            #setup empty dicts
            ElossPerDetId       = {}
            listOfVetoPoints    = {}
            originElossPerDetId = {}  # [detID][origin] = total Eloss from that origin

            global_event_id += 1

            # MCTrack lives in tree_sim, not event
            for track in tree_sim.MCTrack:
                if track.GetPdgCode() in [13, -13]:  # muon
                    Event_weight[global_event_id] = track.GetWeight()
                    break
            weight = Event_weight[global_event_id]



            muon_hit_SBT = False
            max_Eloss = 0
            for key, veto_MCPoint in enumerate(tree_sim.vetoPoint):
                pdgCode = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
                if abs(pdgCode) == 13:
                    muon_hit_SBT = True
                    Eloss = veto_MCPoint.GetEnergyLoss()
                    if Eloss > max_Eloss:
                        max_Eloss = Eloss

            if muon_hit_SBT:
                muons_in_SBT_raw += 1
                muons_in_SBT += weight
            
            if muon_hit_SBT and max_Eloss>0:
                muons_in_SBT_withEloss_raw += 1
                muons_in_SBT_withEloss += weight


                
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


tag = options.tag if options.tag else "inspection_onlyMU_mine"
if test:
    tag = tag + "_test"

out_file = ROOT.TFile(
    f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/{tag}.root",
    "RECREATE"
)
out_file.cd()

for key in h:
    h[key].SetOption('HIST')
    h[key].Write()

out_file.Close()
print(f"Histograms written to /afs/cern.ch/work/j/jaweiss/private/MuonBack/{tag}.root")

directory = './'
print_result(tag)
print('Exceptions:\n', exception_issues)
        
