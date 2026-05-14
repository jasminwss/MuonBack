# run withing fairshp 26.04

import rootUtils as ut
from rootpyPickler import Unpickler
import ROOT, os,sys
from argparse import ArgumentParser
import numpy as np 
from array import array
from tabulate import tabulate
import shipunit as u


PDGData = ROOT.TDatabasePDG.Instance()
parser = ArgumentParser()
parser.add_argument('--test', dest='testing_code', help='Run Test'   , required=False, action='store_true',default=False)
parser.add_argument('--path', dest='path' , help='path to the MuonBack files', required=False, action='store', default='/eos/user/j/jaweiss/MuonBack')

options = parser.parse_args()


if options.testing_code:    directory = './test_hitrates'    
else: 						directory = './'


tag=''
path=options.path

def Main_function():

    # global h,Event_weight,SBT_Event_weight,digihitrate,sst_hitrate

    Event_weight,SBT_Event_weight = {}, {}
    digihitrate = {}
    total_particlehitrate = 0
    files = 0
    global_event_id = -1
    sbt_pdg_list = {}
    sst_pdg_list = {}
    sbt_pdg_index = 0
    sst_pdg_index = 0
    sst_hitrate = {}

    # min_maxEloss_array = {}
    # for threshold in threshold_list:
    #     min_maxEloss_array[threshold] = np.full((100, 36), np.inf)  # Create a 2D array or dictionary to store minimum eLoss values per (z, phi) bin, initialized with inf
    
    # muon_min_eloss_array = np.full((100, 36), np.inf)  # Initialize with infinity

    sGeo = None

    exception_issues = {}


    # Get only ROOT files
    root_files = [f for f in os.listdir(path) if f.endswith('.root')]

    for entry in root_files:
        try:
            inputFile = os.path.join(path, entry)
            
            f = ROOT.TFile.Open(inputFile)
            if not f or f.IsZombie():
                print(f"Cannot open file: {entry}")
                continue
            
            tree = f.Get("ship_reco_sim")
            if not tree:
                print(f"No tree in {entry}")
                f.Close()
                continue
            
            print(f"\n[File] {entry} ({tree.GetEntries()} events)")
            
            for eventNr, event in enumerate(tree):
                global_event_id += 1
                
                # Only access these - they work without crashes
                good_tracks = event.Digi_strawtubesHits
                track_mc_map = event.fitTrack2MC
                
                print(f"Event {eventNr}: {len(good_tracks)} good tracks, {len(track_mc_map)} MC mappings")
                
                if eventNr >= 10:  # limit to 10 events per file
                    break
            
            f.Close()  # Always close the file
            
        except Exception as error:
            print(f"Error processing {entry}: {error}")

Main_function()
