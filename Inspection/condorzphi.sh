#!/bin/bash
#######################################################################################

#ClusterId= $1
#ProcId=    $2
#Comment=   $3
#runnumber= $4

#######################################################################################

FAIRSHIP=/afs/cern.ch/work/j/jaweiss/FairShip
export QT_QPA_PLATFORM=offscreen   # headless node: Geant4's Qt UI otherwise aborts with qFatal
PIXI_BIN=/afs/cern.ch/work/j/jaweiss/.pixi/bin/pixi
PIXI_RUN=("$PIXI_BIN" run --frozen --manifest-path "$FAIRSHIP/pixi.toml")
echo "Using FAIRSHIP=$FAIRSHIP (pixi env)"

#######################################################################################

"${PIXI_RUN[@]}" python /afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/z_phi_origin.py --version TRY2PlSc
