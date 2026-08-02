# to review: z=0 is at the Target?
# to improve: UNNECESSARY matching of reco and sim events, since we only need the sim tree for the vetoPoints

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
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack/TRY2PlSc')
parser.add_argument('--tag', dest='tag', default='')
options = parser.parse_args()


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

for jobDir in sorted(os.listdir(options.path)):
    jobPath = f'{options.path}/{jobDir}'
    if not os.path.isdir(jobPath):
        continue
    job_files  = os.listdir(jobPath)
    reco_files = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('reco_') and fn.endswith('.root')]
    geo_files  = [f'{jobPath}/{fn}' for fn in job_files
                  if fn.startswith('geo_')  and fn.endswith('.root')]
    sim_files  = [f'{jobPath}/{fn}' for fn in job_files
                    if fn.startswith('sim_')  and fn.endswith('.root')]
    if not reco_files or not geo_files:
        print(f"Skipping {jobDir}: missing reco or geo file")
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


    # access reco and sim trees (sim is not copied to reco anymore)
    f = ROOT.TFile.Open(reco_files[0])
    tree = f["ship_reco_sim"]
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
        
    for eventNr, event in enumerate(tree): # UNNECESSARY 
        # sync sim tree to this reco event
        sim_entry = event.ShipEventHeader.GetMCEntryNumber()
        tree_sim.GetEntry(sim_entry)

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

        event_origin = ORIGIN_MAP[classify_event_origin(tree_sim)]

        for key, veto_MCPoint in enumerate(tree_sim.vetoPoint): # for every particle hitting the SBT in the simulation

            SBT_Event_weight[global_event_id] = Event_weight[global_event_id]  
            total_particlehitrate  += Event_weight[global_event_id]  

            pdgCode  = tree_sim.MCTrack[veto_MCPoint.GetTrackID()].GetPdgCode()
            detID    = veto_MCPoint.GetDetectorID()
            shape_nr = detID // 100000

            vetopoint_z,vetopoint_x,vetopoint_y = veto_MCPoint.GetZ(),veto_MCPoint.GetX(),veto_MCPoint.GetY()
            Eloss = veto_MCPoint.GetEnergyLoss()

            if detID not in ElossPerDetId:
                ElossPerDetId[detID]=0
                listOfVetoPoints[detID]=[]
                originElossPerDetId[detID] = {o: 0.0 for o in ORIGIN_CATEGORIES}

            ElossPerDetId[detID] += Eloss
            listOfVetoPoints[detID].append(key)
            originElossPerDetId[detID][event_origin] += Eloss

            try:	particle_name=PDGData.GetParticle(pdgCode).GetName()
            except:	particle_name='others'
            
            if particle_name not in sbt_pdg_list.values():
                sbt_pdg_list[sbt_pdg_index]=particle_name
                sbt_pdg_index+=1
                #print(f"New particle: {particle_name} (PDG code: {pdgCode})")

            veto_pdg_key = [k for k, v in sbt_pdg_list.items() if v == particle_name][0]
            #print(f"Particle: {particle_name}, PDG code: {pdgCode}, assigned key: {veto_pdg_key}")
            #print(f"particle_name][0]{particle_name[0]}")
            #Particle: e-, PDG code: 11, assigned key: 1
            #particle_name][0]e

            h[ 'vetopoint_pdg'							].Fill(veto_pdg_key,weight)
            h[ 'vetopoint_pdg_vs_energydeposition'		].Fill(veto_pdg_key,Eloss,weight)
            h[ 'vetopoint_energydeposition'			 	].Fill(Eloss,weight)
            h[ 'vetopoint_energydeposition_shapewise'	].Fill(shape_nr,Eloss,weight)
            h[ 'vetopoint_topology_phi'				 	].Fill(vetopoint_z,Phicalc(vetopoint_x,vetopoint_y),weight) 

            if particle_name.startswith('mu'):

                z_bin 	= h['vetopoint_min_energydeposition_muons'].GetXaxis().FindBin(vetopoint_z)
                phi_bin = h['vetopoint_min_energydeposition_muons'].GetYaxis().FindBin(Phicalc(vetopoint_x,vetopoint_y))

                # Skip underflow (0) and overflow (nBins+1)
                if 1 <= z_bin <= 100 and 1 <= phi_bin <= 36:
                    if (Eloss/0.001) < muon_min_eloss_array[z_bin-1, phi_bin-1]:
                        muon_min_eloss_array[z_bin-1, phi_bin-1] = Eloss/0.001
                #if z_bin == 0 or z_bin == 101:
                    #print(f"Out of range z: {vetopoint_z:.1f}, shape_nr: {shape_nr}, detID: {detID}") OUT OF RANGE Z

            relative_x, relative_z, relative_y = print_SBTcell_relative_pos(veto_MCPoint)
            h['vetopoint_spatial_dist'].Fill(relative_x, relative_z, relative_y, weight)

        #Explicit  Digitisation 
        digiSBT = {}
        digihit_multiplicity = {threshold: 0 for threshold in threshold_list} #nSBT cells fired per event

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

                digihit_multiplicity[threshold] += 1
                digihitrate_by_origin[f'{threshold}MeV'][cell_origin][detID] += Event_weight[global_event_id]
                
                h[f'{threshold}_vetopoint_multiplicity'			].Fill(len(listOfVetoPoints[detID]),weight) 	#how many vetopoints per digitised hit	
                h[f'{threshold}_z_vs_vetopoint_multiplicity'	].Fill(aHit.GetZ(),len(listOfVetoPoints[detID]),weight)

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
            
                if eLoss<0.001*threshold: continue

                if eLoss>maxeLoss[threshold]:
                    nmaxcells[threshold]=0
                    maxeLoss[threshold]= eLoss
                    max_z[threshold]   = z
                    max_phi[threshold] = Phicalc(x,y)

                #print(ElossPerDetId[detID],maxeLoss)
						
                if eLoss==maxeLoss[threshold]:
                    nmaxcells[threshold]+=1
                
                h[ f'{threshold}_digihit_topology'					].Fill(x,z,y,weight)
                h[ f'{threshold}_digihit_topology_phi'				].Fill(z,Phicalc(x,y),weight)
                h[ f'{threshold}_digihit_z'							].Fill(z,weight)
                h[ f'{threshold}_digihit_rate_shapewise'			].Fill(shape_nr,weight)
                h[ f'{threshold}_digihit_rate_cellwise'				].Fill(detID,weight)
                h[ f'{threshold}_digihit_energydeposition'			].Fill(eLoss,weight)
                h[ f'{threshold}_digihit_energydeposition_shapewise'].Fill(shape_nr,eLoss,weight)

                # Update the min_maxEloss_array if the current eLoss is smaller than the stored value
                #h[ f'{threshold}_digihit_max_edepval_topology_phi'			  ].Fill(z,Phicalc(x,y),eLoss/0.001)
                #print('ElossPerDetId[detID]',maxeLoss,nmaxcells)

        for threshold in threshold_list:

            h[f'{threshold}_digihit_multiplicity'].Fill(digihit_multiplicity[threshold],weight) #how many digihits per event
            
            if maxeLoss[threshold]==-1: continue
        
            h[f'{threshold}_cell_maxenergydeposition'	].Fill(maxeLoss[threshold],nmaxcells[threshold],weight)#2Dplot
            h[f'{threshold}_n_maxenergydeposition'		].Fill(nmaxcells[threshold],weight)
            h[f'{threshold}_maxenergydeposition'		].Fill(maxeLoss[threshold],weight)

            z_bin 	= h[f'{threshold}_digihit_max_edepval_topology_phi'].GetXaxis().FindBin(max_z[threshold])
            phi_bin = h[f'{threshold}_digihit_max_edepval_topology_phi'].GetYaxis().FindBin(max_phi[threshold])
            
            if maxeLoss[threshold]/0.001 < min_maxEloss_array[threshold][z_bin-1, phi_bin-1]:  # -1 to adjust for array index
                min_maxEloss_array[threshold][z_bin-1, phi_bin-1] = maxeLoss[threshold]/0.001


                









# Set bin labels on the pdg histograms using your completed dictionary
for idx, particle_name in sbt_pdg_list.items():
    bin_number = idx + 1  # ROOT bins are 1-indexed!
    h['vetopoint_pdg'].GetXaxis().SetBinLabel(bin_number, particle_name)
    h['vetopoint_pdg_vs_energydeposition'].GetXaxis().SetBinLabel(bin_number, particle_name)

# Fill the histogram with the minimum eLoss values
for z_bin in range(1,101):
    for phi_bin in range(1,37):
        for threshold in threshold_list:
            min_eloss = min_maxEloss_array[threshold][z_bin-1, phi_bin-1]
            if min_eloss != np.inf:  # Only fill if there's a valid min eLoss
                h[f'{threshold}_digihit_max_edepval_topology_phi'].SetBinContent(z_bin, phi_bin, min_eloss)
            
        min_eloss_veto = muon_min_eloss_array[z_bin-1, phi_bin-1]
        if min_eloss_veto != np.inf:  # Only fill if there's a valid min eLoss
            h['vetopoint_min_energydeposition_muons'].SetBinContent(z_bin, phi_bin, min_eloss_veto)	

out_file = ROOT.TFile(
    f"/afs/cern.ch/work/j/jaweiss/private/MuonBack/{tag}.root",
    "RECREATE"
)
out_file.cd()

for key in h:
    h[key].SetOption('HIST')
    h[key].Write()

out_file.Close()

tag = options.tag if options.tag else "inspection"
directory = './'
print_result(tag)
        
