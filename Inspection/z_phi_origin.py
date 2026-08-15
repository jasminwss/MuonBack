# formerly inspect_root.py

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
parser.add_argument('--version', dest='version', default= 'TRY5LiSc')
parser.add_argument('--tag', dest='tag', default='')
options = parser.parse_args()
tag = options.tag if options.tag else "phi-z-plots"
path = '/eos/user/j/jaweiss/MuonBack/TRY5LiSc/11921562/' if options.version == 'TRY5LiSc' else '/eos/user/j/jaweiss/MuonBack/TRY2PlSc/'
print(f"Using path: {path}")


threshold_list=[0,10,45,90]
origin_list=['cavern','SBT','upstream']

# setup histograms 
h = {}
for origin in origin_list:
    ut.bookHist(h, f'vetopoint_min_energydeposition_muons {origin}'			,'SBT (vetoPoint info) min(energy deposition) of muons 	; z(cm) ; #phi ;energy deposition(MeV)'	,100,3000.,8500.,36,0,360) #-3000.,3000.,36,0,360)
    ut.bookHist(h, f'vetopoint_topology_phi {origin}'					,'SBT (vetoPoint info) hitrate ; z(cm) ; #phi 	'			,100,3000.,8500.,36,0,360)

for threshold in threshold_list:
    for origin in origin_list:
        ut.bookHist(h, f'{threshold}_digihit_topology_phi {origin}'			,f'SBT (Digitised hits @ {threshold}MeV threshold ) hitrate 	; z(cm) ; #phi ;			',100,3000.,8500.,36,0,360)#-3000.,3000.,36,0,360)
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
sbt_pdg_index = 0
Event_weight = {}
global_event_id = -1 #s.t. it starts at 0
muon_min_eloss_array = np.full((100, 36), np.inf)  # Initialize with infinity
total_particlehitrate = 0
SBT_Event_weight = {}
min_maxEloss_array = {} 
for threshold in threshold_list:
    min_maxEloss_array[threshold]={o: np.full((100,36), np.inf) for o in origin_list} # Create a 3D array or dictionary to store minimum eLoss values per (z, phi) bin and origin, initialized with inf
ORIGIN_CATEGORIES = ('cavern', 'SBT', 'upstream')
digihitrate_by_origin = {}   # [threshold][origin][detID] =  hitrate

for jobDir in sorted(os.listdir(options.path)):
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


    # access sim trees (sim is not copied to reco anymore)
    f_sim  = ROOT.TFile.Open(sim_files[0])
    tree_sim  = f_sim.Get("cbmsim")
        
    for eventNr, event in enumerate(tree_sim): # UNNECESSARY 
        #setup empty dicts
        ElossPerDetId       = {}
        listOfVetoPoints    = {}
        originElossPerDetId = {}  # [detID][origin] = total Eloss from that origin

        for key, veto_MCPoint in enumerate(tree_sim.vetoPoint): # for every particle hitting the SBT in the simulation

            SBT_Event_weight[global_event_id] = Event_weight[global_event_id]  
            total_particlehitrate  += Event_weight[global_event_id]  

            pdgCode  = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
            detID    = veto_MCPoint.GetDetectorID()
            shape_nr = detID // 100000

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

            if pdgCode in (13,-13):

                z_bin 	= h[f'vetopoint_min_energydeposition_muons {origin}'].GetXaxis().FindBin(vetopoint_z)
                phi_bin = h[f'vetopoint_min_energydeposition_muons {origin}'].GetYaxis().FindBin(Phicalc(vetopoint_x,vetopoint_y))

                # Skip underflow (0) and overflow (nBins+1)
                if 1 <= z_bin <= 100 and 1 <= phi_bin <= 36:
                    if (Eloss/0.001) < muon_min_eloss_array[z_bin-1, phi_bin-1]:
                        muon_min_eloss_array[z_bin-1, phi_bin-1] = Eloss/0.001

        #Explicit  Digitisation 
        digiSBT = {}

        for index,detID in enumerate(ElossPerDetId):
            aHit = ROOT.vetoHit(detID,ElossPerDetId[detID]) # digitized hit object — combining the cell ID with the total Eloss into a single reconstructed hit
            digiSBT[index] = aHit # storing all digi hits for the event

            # dominant origin for this cell = whichever origin deposited the most Eloss
            cell_origin = max(originElossPerDetId[detID], key=lambda o: originElossPerDetId[detID][o])

            for threshold in threshold_list:
                if ElossPerDetId[detID]<0.001*threshold:
                    continue

                if f'{threshold}MeV' not in digihitrate_by_origin:
                    digihitrate_by_origin[f'{threshold}MeV'] = {o: {} for o in ORIGIN_CATEGORIES}

                if detID not in digihitrate_by_origin[f'{threshold}MeV'][cell_origin]:
                    digihitrate_by_origin[f'{threshold}MeV'][cell_origin][detID] = 0

                digihitrate_by_origin[f'{threshold}MeV'][cell_origin][detID] += Event_weight[global_event_id]
            

        #Reading Digitised Data

        maxeLoss = {threshold: -1 for threshold in threshold_list} #maximum energy deposition percell
        
        nmaxcells={}
        max_z={}
        max_phi={}

        for aHit in digiSBT.values():

            x 		=aHit.GetX()
            y 		=aHit.GetY()
            z 	 	=aHit.GetZ()
            eLoss  	=aHit.GetEloss()
            detID 	=aHit.GetDetectorID()
            shape_nr=int(ROOT.TMath.Floor(detID/100000))
					
            for threshold in threshold_list:
                for origin in origin_list:
                    if eLoss<0.001*threshold: continue

                    if eLoss>maxeLoss[threshold]:
                        nmaxcells[threshold]=0
                        maxeLoss[threshold]= eLoss
                        max_z[threshold]   = z
                        max_phi[threshold] = Phicalc(x,y)

                    #print(ElossPerDetId[detID],maxeLoss)
                            
                    if eLoss==maxeLoss[threshold]:
                        nmaxcells[threshold]+=1
                    
                    h[ f'{threshold}_digihit_topology_phi {origin}'].Fill(z,Phicalc(x,y),weight)
                    h[ f'{threshold}_digihit_z {origin}'].Fill(z,weight)

            

        for threshold in threshold_list:
            for origin in origin_list:
            
                if maxeLoss[threshold]==-1: continue
                h[f'{threshold}_maxenergydeposition {origin}'].Fill(maxeLoss[threshold],weight)

                z_bin 	= h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetXaxis().FindBin(max_z[threshold])
                phi_bin = h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].GetYaxis().FindBin(max_phi[threshold])
                
                if maxeLoss[threshold]/0.001 < min_maxEloss_array[threshold][z_bin-1, phi_bin-1][origin]:  # -1 to adjust for array index
                    min_maxEloss_array[threshold][z_bin-1, phi_bin-1][origin] = maxeLoss[threshold]/0.001




# Fill the histogram with the minimum eLoss values
for z_bin in range(1,101):
    for phi_bin in range(1,37):
        for threshold in threshold_list:
            for origin in origin_list:
                min_eloss = min_maxEloss_array[threshold][z_bin-1, phi_bin-1][origin]
                if min_eloss != np.inf:  # Only fill if there's a valid min eLoss
                    h[f'{threshold}_digihit_max_edepval_topology_phi {origin}'].SetBinContent(z_bin, phi_bin, min_eloss)
            
        min_eloss_veto = muon_min_eloss_array[z_bin-1, phi_bin-1]
        if min_eloss_veto != np.inf:  # Only fill if there's a valid min eLoss
            h[f'vetopoint_min_energydeposition_muons {origin}'].SetBinContent(z_bin, phi_bin, min_eloss_veto)	

out_file = ROOT.TFile(f"{path}/z_phi_origin/{tag}.root","RECREATE")
out_file.cd()

for key in h:
    h[key].SetOption('HIST')
    h[key].Write()

out_file.Close()
        
