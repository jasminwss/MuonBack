# run within fairship 26.04
import ROOT, os, sys
from rootpyPickler import Unpickler
from argparse import ArgumentParser

PDGData = ROOT.TDatabasePDG.Instance()
parser = ArgumentParser()
parser.add_argument('--test', dest='testing_code', action='store_true', default=False)
parser.add_argument('--path', dest='path', default='/eos/user/j/jaweiss/MuonBack')
options = parser.parse_args()

path = options.path

def Main_function():
    sGeo = None
    global_event_id = -1

    for jobDir in os.listdir(path):
        # FIX 1: skip anything that isn't a directory (loose files in path would crash os.listdir)
        if not os.path.isdir(f'{path}/{jobDir}'):
            continue

        f, fgeo = None, None
        try:
            job_files  = os.listdir(f'{path}/{jobDir}')
            reco_files = [f'{path}/{jobDir}/{fn}' for fn in job_files if fn.startswith('reco_') and fn.endswith('.root')]
            geo_files  = [f'{path}/{jobDir}/{fn}' for fn in job_files if fn.startswith('geo_')  and fn.endswith('.root')]

            if not reco_files:
                print(f"No reco file in {jobDir}, skipping.")
                continue
            if not geo_files:
                print(f"No geo file in {jobDir}, skipping.")
                continue

            inputFile = reco_files[0]
            geoFile   = geo_files[0]

            f = ROOT.TFile.Open(inputFile)
            # FIX 2: check file opened successfully before accessing anything
            if not f or f.IsZombie():
                print(f"Failed to open reco file: {inputFile}")
                continue

            # FIX 3: use Get() instead of attribute access — safer, won't segfault on missing tree
            tree = f.Get("ship_reco_sim")
            if not tree:
                print(f"No tree 'ship_reco_sim' in {inputFile}")
                f.Close()
                continue

            # FIX 4: use `is None` not `if not sGeo` — ROOT objects don't evaluate cleanly as bool
            if sGeo is None:
                fgeo = ROOT.TFile.Open(geoFile)   # FIX 5: use TFile.Open, not TFile()
                if not fgeo or fgeo.IsZombie():
                    print(f"Failed to open geo file: {geoFile}")
                    f.Close()
                    continue
                upkl    = Unpickler(fgeo)
                ShipGeo = upkl.load('ShipGeo')
                sGeo    = fgeo.FAIRGeom

            print(f"\n[File] {jobDir} ({tree.GetEntries()} events)")

            for eventNr, event in enumerate(tree):
                global_event_id += 1
                good_tracks  = event.goodTracks
                track_mc_map = event.fitTrack2MC
                print(f"  Event {eventNr}: {len(good_tracks)} good tracks, {len(track_mc_map)} MC mappings")
                if eventNr >= 10:
                    break

        except Exception as e:
            print(f"Error processing {jobDir}: {e}")
        finally:
            # FIX 6: always close files in finally block
            if f    and not f.IsZombie():    f.Close()
            if fgeo and not fgeo.IsZombie(): fgeo.Close()

Main_function()