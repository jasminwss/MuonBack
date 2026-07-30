#!/bin/bash
#######################################################################################

#ClusterId= $1
#ProcId=    $2
#Comment=   $3
#runnumber= $4

#######################################################################################

#source /cvmfs/ship.cern.ch/26.07/setUp.sh
#eval $(alienv --work-dir /cvmfs/ship.cern.ch/26.07/sw load FairShip/latest)
#echo "Using FAIRSHIP=$FAIRSHIP"


FAIRSHIP=/afs/cern.ch/work/j/jaweiss/FairShip
export QT_QPA_PLATFORM=offscreen   # headless node: Geant4's Qt UI otherwise aborts with qFatal
PIXI_BIN=/afs/cern.ch/work/j/jaweiss/.pixi/bin/pixi
PIXI_RUN=("$PIXI_BIN" run --frozen --manifest-path "$FAIRSHIP/pixi.toml")
echo "Using FAIRSHIP=$FAIRSHIP (pixi env)"

#######################################################################################

python /afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/inspect_Back.py --path /eos/user/j/jaweiss/MuonBack/TRY2LiSc/11917294
