# to review: z=0 is at the Target?
# to improve: UNNECESSARY matching of reco and sim events, since we only need the sim tree for the vetoPoints

import ROOT, os, sys
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
parser.add_argument('--raw', dest='raw', action='store_true', default=False, help='If set, will fill digi hit histograms with 1 instead of weight')
parser.add_argument('--test', dest='test', action='store_true', default=False, help='If set, will only process the first some events for testing purposes')
options = parser.parse_args()
raw = options.raw
test = options.test

directory = '/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/additional_infos/'
tag = options.tag + ('_test' if test else '')
tag = tag + '_SIM'

class Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
    def flush(self):
        for s in self.streams:
            s.flush()

log_file = open(f'{directory}{tag}_log.txt', 'w')
sys.stdout = Tee(sys.stdout, log_file)


# setup histograms 
h = {}
ut.bookHist(h, 'vetopoint_pdg'							,'SBT (vetoPoint info)					; pdg  		; 	'				,20,-0.5,20.5)
ut.bookHist(h, 'vetopoint_pdg_vs_energydeposition'		,'SBT (vetoPoint info)					; pdg 		; Energy deposition (GeV) '		,20,-0.5,20.5,1000,0,1)
ut.bookHist(h, 'vetopoint_min_energydeposition_muons'			,'SBT (vetoPoint info) min(energy deposition) of muons 	; z(cm) ; #phi ;energy deposition(MeV)'	,100,3000.,8500.,36,0,360) #-3000.,3000.,36,0,360)
ut.bookHist(h, 'vetopoint_energydeposition'				,'SBT (vetoPoint info)					; Energy deposition per particle hit(GeV); 		'		,1000,0.,1)
ut.bookHist(h, 'vetopoint_energydeposition_shapewise'	,'SBT (vetoPoint info)					; Shape ID; Energy deposition per particle hit(GeV)	;'	,6,0.5,6.5,1000,0,1)#2D plot
ut.bookHist(h, 'vetopoint_topology_phi'					,'SBT (vetoPoint info) hitrate ; z(cm) ; #phi 	'			,100,3000.,8500.,36,0,360)
ut.bookHist(h, 'vetopoint_spatial_dist'					,'SBT (vetoPoint info) position of particle hit within the SBT cell ; x(cm) ; z(cm)	; y(cm) ',100,-200.,200.,100,-50,50,100,-300.,300.)

threshold_list=[0,10,20,30,45,50,60,90]
for threshold in threshold_list:
	
	ut.bookHist(h, f'{threshold}_digihit_topology'				,f'SBT (Digitised hits @ {threshold}MeV threshold ) hitrate	; x(cm)	; z(cm)	; y(cm) 	',100,-500.,500.,100 ,3000.,8500.,100,-500.,500.) #,-3000.,3000.,100,-500.,500.)
	ut.bookHist(h, f'{threshold}_digihit_topology_phi'			,f'SBT (Digitised hits @ {threshold}MeV threshold ) hitrate 	; z(cm) ; #phi ;			',100,3000.,8500.,36,0,360)#-3000.,3000.,36,0,360)
	
	ut.bookHist(h, f'{threshold}_vetopoint_multiplicity'		,f'SBT (Digitised hits @ {threshold}MeV threshold )	vetoPoint multiplicity		;Number of vetoPoints hitting the SBT cell	; 	',100,0,100)
	ut.bookHist(h, f'{threshold}_z_vs_vetopoint_multiplicity'	,f'SBT (Digitised hits @ {threshold}MeV threshold )			; z(cm)				;Number of vetoPoints hitting the SBT cell 	',100,0.,9000.,100,0,100)
    #ut.bookHist(h, f'{threshold}_z_vs_vetopoint_multiplicity'	,f'SBT (Digitised hits @ {threshold}MeV threshold )			; z(cm)				;Number of vetoPoints hitting the SBT cell 	',100,-30000.,30000.,100,0,100)

	ut.bookHist(h, f'{threshold}_maxenergydeposition'			,f'SBT (Digitised hits @ {threshold}MeV threshold )			; max(Energy deposition) (GeV)'				,1000,0,1)
	ut.bookHist(h, f'{threshold}_n_maxenergydeposition'			,f'SBT (Digitised hits @ {threshold}MeV threshold )			; Number of cells with max(Energy deposition) '	,100,0,100)
	ut.bookHist(h, f'{threshold}_cell_maxenergydeposition'		,f'SBT (Digitised hits @ {threshold}MeV threshold )			; Max(E_deposition) in a cell (GeV) 	;Number of cells with max(E_deposition) '	,1000,0.,1,50,0,50)
	
	ut.bookHist(h, f'{threshold}_digihit_max_edepval_topology_phi'		,f'SBT (Digitised hits @ {threshold}MeV threshold ) min( max(energy deposition) per event ) 	; z(cm) ; #phi ;energy deposition(MeV)',100,3000.,8500.,36,0,360) #-3000.,3000.,36,0,360)
	
	h[f'{threshold}_digihit_max_edepval_topology_phi'].GetZaxis().SetTitleOffset(-0.5);  
	h[f'{threshold}_digihit_max_edepval_topology_phi'].GetZaxis().SetTitleSize(0.03);   

	ut.bookHist(h, f'{threshold}_digihit_energydeposition'			,f'SBT (Digitised hits @ {threshold}MeV threshold ) ; E_deposition per digihit (GeV) 				;										',1000,0.,1)
	ut.bookHist(h, f'{threshold}_digihit_multiplicity'				,f'SBT (Digitised hits @ {threshold}MeV threshold ) ; Number of triggered SBT cells in an event 	;										',2000,-0.5,2000.5)
	ut.bookHist(h, f'{threshold}_digihit_rate_shapewise'			,f'SBT (Digitised hits @ {threshold}MeV threshold ) ; Shape ID 										; Digitised hit rate					',6,0.5,6.5)
	ut.bookHist(h, f'{threshold}_digihit_rate_cellwise'				,f'SBT (Digitised hits @ {threshold}MeV threshold ) ; Cellwise digihit rate  						; 										',2000,100e3,700e3)
	ut.bookHist(h, f'{threshold}_digihit_energydeposition_shapewise',f'SBT (Digitised hits @ {threshold}MeV threshold ) ; Shape ID 										; Energy deposition per Digihit(GeV)	',6,0.5,6.5,1000,0,1)
	ut.bookHist(h, f'{threshold}_digihit_z'							,f'SBT (Digitised hits @ {threshold}MeV threshold ) ; z(cm) 										; 										',100,3000.,8500)#-3000.,3000)

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

def print_SBTcell_relative_pos(vetoPoint):
    # Initialize the navigator
    nav = ROOT.gGeoManager.GetCurrentNavigator()
    if not nav:
        print("Navigator could not be initialized.")
        return

    # Define master (global) coordinates for the vetoPoint = where are we in the SHiP geometry? 
    master_point = array('d', [vetoPoint.GetX(), vetoPoint.GetY(), vetoPoint.GetZ()])

    # Set the current point to the master coordinates in the navigator
    nav.SetCurrentPoint(master_point[0], master_point[1], master_point[2])

    # Find the node at this point, which moves the navigator to the correct volume
    current_node = nav.FindNode()
    if not current_node:
        print("No node found at the given coordinates.")
        return

    # Print the name of the node where the point is located
    #print(f"Found node: {current_node.GetName()}")

    # Prepare an array to hold the local coordinates
    local_coords = array('d', [0, 0, 0])

    # Perform the transformation from master (global) to local coordinates = Where in the Volume (e.q. SBT cell) are we?, close to the edge? How much LiSc was traversed? …
    nav.MasterToLocal(master_point, local_coords)

    # Print the result
    #print(f"Master coordinates: {master_point}")
    #print(f"Local coordinates in '{nav.GetCurrentNode().GetName()}': {local_coords}")

    return local_coords[0],local_coords[2],local_coords[1]

def print_result(tag):
	
	global h,Event_weight,SBT_Event_weight,digihitrate_by_origin,sst_hitrate
	ut.writeHists(h, directory +tag+'.root')

	with open(directory +tag+'_readme.txt', 'w') as readme: 
				
		print("\n\n\n")
		
		
		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics',float(len(Event_weight)),float(sum(Event_weight.values()))))
		print(" {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics with SBT activity',float(len(SBT_Event_weight)),float(sum(SBT_Event_weight.values()))))
		
		print("\n\n  ================================================================================")
		print("\n  SBT")
		print("  --------------------------------------------------------------------------------\n\n")
		

		
		readme.write("\n {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics',float(len(Event_weight)),float(sum(Event_weight.values()))))
		readme.write("\n {:46} Generated: {:10.5}\t Scaled to one spill: {:10.5}".format('Muon BG Statistics with SBT activity',float(len(SBT_Event_weight)),float(sum(SBT_Event_weight.values()))))
		
		readme.write("\n\n  ================================================================================")
		readme.write("\n  SBT")
		readme.write("\n  --------------------------------------------------------------------------------\n\n")
		
		
		header = "  {:10}\t {:>12}\t {:>12}\t {:>12}\t {:>12}".format(
				'THRESHOLD', 'TOTAL (MHz)', 'cavern (MHz)', 'SBT (MHz)', 'upstream (MHz)')
		print(header)
		print("  " + "-"*80)
		readme.write("\n\n" + header + "\n  " + "-"*80)

		for threshold in threshold_list:
			tkey = f'{threshold}MeV'
			origin_totals = {o: sum(digihitrate_by_origin.get(tkey, {}).get(o, {}).values()) for o in ORIGIN_CATEGORIES}
			total = sum(origin_totals.values())

			line = " {:5} MeV\t {:>12.4f}\t {:>12.4f}\t {:>12.4f}\t {:>12.4f}".format(
				threshold,
				total * 1e-6,
				origin_totals['cavern']   * 1e-6,
				origin_totals['SBT']      * 1e-6,
				origin_totals['upstream'] * 1e-6,
			)
			print(line)
			readme.write("\n" + line)

		print(       "\n  " + "-"*80 + "\n")
		readme.write("\n  " + "-"*80 + "\n")

ORIGIN_MAP = {'muon_cavern': 'cavern', 'muon_SBT': 'SBT', 'EM_debris_upstream': 'upstream'}

def get_muon_tracks_hitting_SBT(event):
    muon_tracks = set()
    for hit in event.vetoPoint:
        detID = hit.GetDetectorID()
        if 1000 < detID < 999999 and abs(hit.PdgCode()) == 13:
            muon_tracks.add(hit.GetTrackID())
    return muon_tracks

def is_event_with_muonhit_in_CAVERN(event):
    """Any muon track in the event (not just those that hit the SBT) that
    produces a daughter starting inside the Cavern volume."""
    for track in event.MCTrack:
        if track.GetMotherId() == -1: continue
        if abs(event.MCTrack[track.GetMotherId()].GetPdgCode()) == 13:
            X, Y, Z = track.GetStartX(), track.GetStartY(), track.GetStartZ()
            node = ROOT.gGeoManager.FindNode(X, Y, Z)
            if node and node.GetVolume().GetName().startswith('Cavern'):
                return True
    return False

def classify_event_origin(event):
    # Cavern check first and unrestricted, so muons that never leave an SBT
    # hit but do interact in the Cavern aren't mis-bucketed as EM_debris_upstream.
    if is_event_with_muonhit_in_CAVERN(event):
        return 'muon_cavern'
    if get_muon_tracks_hitting_SBT(event):
        return 'muon_SBT'
    return 'EM_debris_upstream'


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
for threshold in threshold_list:
	min_maxEloss_array[threshold]=np.full((100, 36), np.inf)  # Create a 2D array or dictionary to store minimum eLoss values per (z, phi) bin, initialized with inf
ORIGIN_CATEGORIES = ('cavern', 'SBT', 'upstream')
digihitrate_by_origin = {}   # [threshold][origin][detID] =  hitrate
exception_issues = {}
job_nmbr = 0

for jobDir in sorted(os.listdir(options.path)):
    if test and job_nmbr >= 1:  # Limit to first job for testing
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


        # access reco and sim trees (sim is not copied to reco anymore)
        #f = ROOT.TFile.Open(reco_files[0])
        #tree = f["ship_reco_sim"]
        f_sim  = ROOT.TFile.Open(sim_files[0])
        tree_sim  = f_sim.Get("cbmsim")

        #print("reco entries:", tree.GetEntries())
        #print("sim  entries:", tree_sim.GetEntries())

        # Check event IDs match at a few entries
        #for i, event in enumerate(tree):
          #  tree.GetEntry(i)
         #   tree_sim.GetEntry(i)
           # if tree.ShipEventHeader.GetMCEntryNumber() != tree_sim.MCEventHeader.GetEventID():
            #    print(f"Mismatch at entry {i}: reco eventID={tree.ShipEventHeader.GetMCEntryNumber()}, "
             #         f"sim eventID={tree_sim.MCEventHeader.GetEventID()}")
        
        for eventNr, event in enumerate(tree_sim): # UNNECESSARY 
            # sync sim tree to this reco event
            #sim_entry = event.ShipEventHeader.GetMCEntryNumber()
            #tree_sim.GetEntry(sim_entry)

            print(f"Event number: {eventNr}")
            #print(f"event number = sim entry? ", eventNr == tree_sim.MCEventHeader.GetEventID())

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
            if not raw:
                weight = Event_weight[global_event_id]
                print('weight',weight)
            else:
                weight = 1.0  # If raw option is set, use weight=1 for all events

            event_origin = ORIGIN_MAP[classify_event_origin(tree_sim)]
            print(f"Event origin: {event_origin}")

            for key, veto_MCPoint in enumerate(tree_sim.vetoPoint): # for every particle hitting the SBT in the simulation

                SBT_Event_weight[global_event_id] = Event_weight[global_event_id]  
                total_particlehitrate  += Event_weight[global_event_id]  

                pdgCode  = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
                detID    = veto_MCPoint.GetDetectorID()
                shape_nr = detID // 100000
                print(f"vetoPoint {key}: pdg={pdgCode}, detID={detID}, shape_nr={shape_nr}")

                vetopoint_z,vetopoint_x,vetopoint_y = veto_MCPoint.GetZ(),veto_MCPoint.GetX(),veto_MCPoint.GetY()
                Eloss = veto_MCPoint.GetEnergyLoss()


            #Explicit  Digitisation 
            digiSBT = {}
            digihit_multiplicity = {threshold: 0 for threshold in threshold_list} #nSBT cells fired per event

            for index,detID in enumerate(ElossPerDetId):
                aHit = ROOT.vetoHit(detID,ElossPerDetId[detID]) # digitized hit object — combining the cell ID with the total Eloss into a single reconstructed hit
                digiSBT[index] = aHit # storing all digi hits for the event

                # dominant origin for this cell = whichever origin deposited the most Eloss
                cell_origin = max(originElossPerDetId[detID], key=lambda o: originElossPerDetId[detID][o])

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

print(f"Histograms written to {directory}{tag}.root")
print_result(tag)
print('Exceptions:\n', exception_issues)
