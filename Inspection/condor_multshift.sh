#!/bin/bash
#######################################################################################

#ClusterId= $1
#ProcId=    $2

#######################################################################################

FAIRSHIP=/eos/user/j/jaweiss/FairShip_88d2794
export QT_QPA_PLATFORM=offscreen
export RATTLER_CACHE_DIR=/afs/cern.ch/work/j/jaweiss/.cache/rattler
PIXI_BIN=/afs/cern.ch/work/j/jaweiss/.pixi/bin/pixi
PIXI_RUN=("$PIXI_BIN" run --frozen --manifest-path "$FAIRSHIP/pixi.toml")
echo "Using FAIRSHIP=$FAIRSHIP (pixi env)"

#######################################################################################

"${PIXI_RUN[@]}" python /afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/inspect_multiplicity_shift.py --path /eos/user/j/jaweiss/MuonBack/TRY6LiSc_88d2794/12996649/ --tag TRY6LiSc_88d2794
