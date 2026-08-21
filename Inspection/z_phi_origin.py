# formerly inspect_root.py

import ROOT, os
from argparse import ArgumentParser
from ShipGeoConfig import load_from_root_file
import rootUtils as ut
import numpy as np

ROOT.gROOT.SetBatch(True)

parser = ArgumentParser()
parser.add_argument('--version', dest='version', default= 'TRY5LiSc')
parser.add_argument('--tag', dest='tag', default='')
parser.add_argument('--test', dest='test', action='store_true')
parser.add_argument('--raw', dest='raw', action='store_true', default=False, help='If set, will fill digi hit histograms with 1 instead of weight and no Energyd deposition histograms will be filled')
options = parser.parse_args()
tag = options.tag if options.tag else "phi-z-plots"
path = '/eos/user/j/jaweiss/MuonBack/TRY5LiSc/11921562/' if options.version == 'TRY5LiSc' else '/eos/user/j/jaweiss/MuonBack/TRY2PlSc/'
print(f"Using path: {path}")
raw = options.raw


threshold_list=[0,10,45,90]
origin_list=['cavern','SBT','upstream']

# setup histograms 
h = {}
for origin in origin_list:
    if not raw:
        ut.bookHist(h, f'vetopoint_min_energydeposition_muons {origin}'			,'SBT (vetoPoint info) min(energy deposition) of muons 	; z(cm) ; #phi ;energy deposition(MeV)'	,100,3000.,8500.,36,0,360) #-3000.,3000.,36,0,360)
    ut.bookHist(h, f'vetopoint_topology_phi {origin}'					,'SBT (vetoPoint info) hitrate ; z(cm) ; #phi 	'			,100,3000.,8500.,36,0,360)

for threshold in threshold_list:
    for origin in origin_list:
        ut.bookHist(h, f'{threshold}_digihit_topology_phi {origin}'			,f'SBT (Digitised hits @ {threshold}MeV threshold ) hitrate 	; z(cm) ; #phi ;			',100,3000.,8500.,36,0,360)#-3000.,3000.,36,0,360)
        if not raw:
            ut.bookHist(h, f'{threshold}_maxenergydeposition {origin}'			,f'SBT (Digitised hits @ {threshold}MeV threshold )			; max(Energy deposition) (GeV)'				,1000,0,1)
            ut.bookHist(h, f'{threshold}_digihit_max_edepval_topology_phi {origin}'		,f'SBT (Digitised hits @ {threshold}MeV threshold ) min( max(energy deposition) per event ) 	; z(cm) ; #phi ;energy deposition(MeV)',100,3000.,8500.,36,0,360) #-3000.,3000.,36,0,360)
            h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetZaxis().SetTitleOffset(-0.5);
            h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetZaxis().SetTitleSize(0.03);
        ut.bookHist(h, f'{threshold}_digihit_z {origin}',f'SBT (Digitised hits @ {threshold}MeV threshold ) ; z(cm) ;',100,3000.,8500)#-3000.,3000)

def Phicalc(x, y):
	"""Calculate the azimuthal angle phi in degrees with a 90° offset."""

	r = ROOT.TMath.Sqrt(x*x + y*y)

	if r == 0:  
	    return np.inf #Prevent division by zero

	if(y>=0):   phi =   ROOT.TMath.ACos(x/r)
	else:       phi =-1*ROOT.TMath.ACos(x/r)+2*ROOT.TMath.Pi()

	phi = phi*180/ ROOT.TMath.Pi()# Convert radians to degrees

	phi = (phi + 90) % 360  #+90 offset to start reading from bottom center, phi range= [0,360)

	return phi  

def classify_production_vertex(track):
    """
    Classify where a track was produced using ROOT geometry navigation. 
    Returns 'cavern', 'SBT', or 'upstream.
    """
    nav = ROOT.gGeoManager.GetCurrentNavigator()
    if not nav:
        print("not nav -> upstream")
        return 'upstream'

    vx, vy, vz = track.GetStartX(), track.GetStartY(), track.GetStartZ()
    nav.SetCurrentPoint(vx, vy, vz)
    node = nav.FindNode()

    if node is None: 
        return 'upstream'

    vol_name = node.GetName()

    if 'Cavern' in vol_name:
        #print("found cavern")
        return 'cavern'

    if 'LiSc' in vol_name or 'Rib' in vol_name or 'Wall' in vol_name:
        #print("found SBT")
        return 'SBT'

    #print ("found neither cavern nor SBT, but ", vol_name)
    return 'upstream'

# global variables
sGeo = None
Event_weight = {}
global_event_id = -1 #s.t. it starts at 0
muon_min_eloss_array = {o: np.full((100,36), np.inf) for o in origin_list}  # Initialize with infinity
total_particlehitrate = 0
SBT_Event_weight = {}
min_maxEloss_array = {} 
for threshold in threshold_list:
    min_maxEloss_array[threshold]={o: np.full((100,36), np.inf) for o in origin_list} # Create a 3D array or dictionary to store minimum eLoss values per (z, phi) bin and origin, initialized with inf
ORIGIN_CATEGORIES = ('cavern', 'SBT', 'upstream')
digihitrate_by_origin = {}   # [threshold][origin][detID] =  hitrate

jobdirnmbr = 0
for jobDir in sorted(os.listdir(path)):
    jobPath = f'{path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    jobdirnmbr += 1
    if options.test and jobdirnmbr>20:
        break
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


    # access sim trees (sim is not copied to reco anymore)
    f_sim  = ROOT.TFile.Open(sim_files[0])
    tree_sim  = f_sim.Get("cbmsim")
        
    for eventNr, event in enumerate(tree_sim): # UNNECESSARY 
        #setup empty dicts
        ElossPerDetId       = {}
        listOfVetoPoints    = {}
        originElossPerDetId = {}  # [detID][origin] = total Eloss from that origin
        global_event_id += 1
        for track in tree_sim.MCTrack:
            if track.GetPdgCode() in (13,-13):
                Event_weight[global_event_id] = track.GetWeight()
                break

        if not raw:
            weight = Event_weight[global_event_id]
        elif raw:
            weight = 1

        for key, veto_MCPoint in enumerate(tree_sim.vetoPoint): # for every particle hitting the SBT in the simulation

            SBT_Event_weight[global_event_id] = Event_weight[global_event_id]  
            total_particlehitrate  += Event_weight[global_event_id]  

            pdgCode  = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
            detID    = veto_MCPoint.GetDetectorID()

            vetopoint_z,vetopoint_x,vetopoint_y = veto_MCPoint.GetZ(),veto_MCPoint.GetX(),veto_MCPoint.GetY()
            Eloss = veto_MCPoint.GetEnergyLoss()

            hitting_track = tree_sim.MCTrack[veto_MCPoint.GetTrackID()]
            origin = classify_production_vertex(hitting_track)

            if detID not in ElossPerDetId:
                ElossPerDetId[detID]=0
                listOfVetoPoints[detID]=[]
                originElossPerDetId[detID] = {o: 0.0 for o in ORIGIN_CATEGORIES}

            ElossPerDetId[detID] += Eloss
            listOfVetoPoints[detID].append(key)
            originElossPerDetId[detID][origin] += Eloss


            h[ f'vetopoint_topology_phi {origin}'				 	].Fill(vetopoint_z,Phicalc(vetopoint_x,vetopoint_y),weight) 

            if pdgCode in (13,-13) and not raw:

                z_bin 	= h[f'vetopoint_min_energydeposition_muons {origin}'].GetXaxis().FindBin(vetopoint_z)
                phi_bin = h[f'vetopoint_min_energydeposition_muons {origin}'].GetYaxis().FindBin(Phicalc(vetopoint_x,vetopoint_y))

                # Skip underflow (0) and overflow (nBins+1)
                if 1 <= z_bin <= 100 and 1 <= phi_bin <= 36:
                    if (Eloss/0.001) < muon_min_eloss_array[origin][z_bin-1, phi_bin-1]:
                        muon_min_eloss_array[origin][z_bin-1, phi_bin-1] = Eloss/0.001

        #Explicit  Digitisation 
        digiSBT = {}
        detID_to_origin = {}

        for index,detID in enumerate(ElossPerDetId):
            aHit = ROOT.vetoHit(detID,ElossPerDetId[detID]) # digitized hit object — combining the cell ID with the total Eloss into a single reconstructed hit
            digiSBT[index] = aHit # storing all digi hits for the event
            # dominant origin for this cell = whichever origin deposited the most Eloss
            cell_origin = max(originElossPerDetId[detID], key=lambda o: originElossPerDetId[detID][o])
            detID_to_origin[detID] = cell_origin

            for threshold in threshold_list:
                if ElossPerDetId[detID]<0.001*threshold:
                    continue

                if f'{threshold}MeV' not in digihitrate_by_origin:
                    digihitrate_by_origin[f'{threshold}MeV'] = {o: {} for o in ORIGIN_CATEGORIES}

                if detID not in digihitrate_by_origin[f'{threshold}MeV'][cell_origin]:
                    digihitrate_by_origin[f'{threshold}MeV'][cell_origin][detID] = 0

                digihitrate_by_origin[f'{threshold}MeV'][cell_origin][detID] += Event_weight[global_event_id]
            

        #Reading Digitised Data

        maxeLoss = {t: {o: -1 for o in origin_list} for t in threshold_list} #maximum energy deposition percell
        
        max_z={t: {} for t in threshold_list}
        max_phi={t: {} for t in threshold_list}

        for aHit in digiSBT.values():

            x 		=aHit.GetX()
            y 		=aHit.GetY()
            z 	 	=aHit.GetZ()
            eLoss  	=aHit.GetEloss()
            detID 	=aHit.GetDetectorID()
            shape_nr=int(ROOT.TMath.Floor(detID/100000))
            cell_origin = detID_to_origin[detID]
					
            for threshold in threshold_list:
                    if eLoss<0.001*threshold: continue

                    if eLoss>maxeLoss[threshold][cell_origin]:
                        maxeLoss[threshold][cell_origin] = eLoss
                        max_z[threshold][cell_origin]   = z
                        max_phi[threshold][cell_origin] = Phicalc(x,y)

                    h[ f'{threshold}_digihit_topology_phi {cell_origin}'].Fill(z,Phicalc(x,y),weight)
                    h[ f'{threshold}_digihit_z {cell_origin}'].Fill(z,weight)

            

        for threshold in threshold_list:
            for origin in origin_list:
            
                if maxeLoss[threshold][origin]==-1: continue
                if not raw:
                    h[f'{threshold}_maxenergydeposition {origin}'].Fill(maxeLoss[threshold][origin],weight)

                    z_bin 	= h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetXaxis().FindBin(max_z[threshold][origin])
                    phi_bin = h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetYaxis().FindBin(max_phi[threshold][origin])

                    if maxeLoss[threshold][origin]/0.001 < min_maxEloss_array[threshold][origin][z_bin-1, phi_bin-1]:  # -1 to adjust for array index
                        min_maxEloss_array[threshold][origin][z_bin-1, phi_bin-1] = maxeLoss[threshold][origin]/0.001




# Fill the histogram with the minimum eLoss values
for z_bin in range(1,101):
    for phi_bin in range(1,37):
        for origin in origin_list:
            for threshold in threshold_list:
                min_eloss = min_maxEloss_array[threshold][origin][z_bin-1, phi_bin-1]
                if min_eloss != np.inf and not raw:  # Only fill if there's a valid min eLoss
                    h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].SetBinContent(z_bin, phi_bin, min_eloss)
            
            min_eloss_veto = muon_min_eloss_array[origin][z_bin-1, phi_bin-1]
            if min_eloss_veto != np.inf and not raw:  # Only fill if there's a valid min eLoss
                h[f'vetopoint_min_energydeposition_muons {origin}'].SetBinContent(z_bin, phi_bin, min_eloss_veto)	

if raw:
    tag = f"{tag}_raw"
if options.version == "TRY5LiSc":
    out_file = ROOT.TFile(f"/eos/user/j/jaweiss/MuonBack/TRY5LiSc/z_phi_origin/{tag}.root","RECREATE")
else: 
    out_file = ROOT.TFile(f"/eos/user/j/jaweiss/MuonBack/TRY2PlSc/z_phi_origin/{tag}.root","RECREATE")
out_file.cd()

print("saving file to ", out_file.GetName())

for key in h:
    h[key].SetOption('HIST')
    h[key].Write()

out_file.Close()
        
