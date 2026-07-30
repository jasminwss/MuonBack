#!/bin/bash
set -eo pipefail

# Condor arguments (see muonback.sub):
#   $1 = inputFile   muon background flux file to sample from
#   $2 = startEvent  first event to read from inputFile
#   $3 = nEvents     number of events to generate
#   $4 = ProcId      $(Process)
#   $5 = ClusterId   $(Cluster)

inputFile=$1
startEvent=$2
nEvents=$3
ProcId=$4
ClusterId=$5

RUN_ID="${ClusterId}_${ProcId}"

OUTPUT_BASE=/eos/user/j/jaweiss/MuonBack/TRY2LiSc
OUTPUT_DIR=${OUTPUT_BASE}/${ClusterId}/job_${ProcId}   # ← one folder per job
mkdir -p "$OUTPUT_DIR"

[ -f "$inputFile" ] || { echo "ERROR: input file missing: $inputFile"; exit 1; }

FAIRSHIP=/afs/cern.ch/work/j/jaweiss/FairShip
export QT_QPA_PLATFORM=offscreen   # headless node: Geant4's Qt UI otherwise aborts with qFatal
PIXI_BIN=/afs/cern.ch/work/j/jaweiss/.pixi/bin/pixi
PIXI_RUN=("$PIXI_BIN" run --frozen --manifest-path "$FAIRSHIP/pixi.toml")
echo "Using FAIRSHIP=$FAIRSHIP (pixi env)"

TMPDIR=$(mktemp -d)
cd "$TMPDIR"

echo
echo " Step 1: MuonBack simulation using run_simScript.py"
echo "=============================================================="
"${PIXI_RUN[@]}" python "$FAIRSHIP/macro/run_simScript.py" \
    --MuonBack \
    -f "$inputFile" \
    -i "$startEvent" \
    -n "$nEvents" \
    --shieldName TRY_2025 \
    --tag "$RUN_ID" \
    -o "$TMPDIR" | tee simRunOutput_1.txt

SIM_FILE="${TMPDIR}/sim_${RUN_ID}.root"
GEO_FILE="${TMPDIR}/geo_${RUN_ID}.root"
PARAMS_FILE="${TMPDIR}/params_${RUN_ID}.root"

[ -f "$SIM_FILE" ]    || { echo "ERROR: sim file not produced: $SIM_FILE";    ls -lh "$TMPDIR"; exit 1; }
[ -f "$GEO_FILE" ]    || { echo "ERROR: geo file not produced: $GEO_FILE";    ls -lh "$TMPDIR"; exit 1; }
[ -f "$PARAMS_FILE" ] || { echo "ERROR: params file not produced: $PARAMS_FILE"; ls -lh "$TMPDIR"; exit 1; }

echo
echo " Step 2: Reconstruction using ShipReco.py"
echo "=============================================================="
"${PIXI_RUN[@]}" python "$FAIRSHIP/macro/ShipReco.py" \
    -f "$SIM_FILE" \
    -g "$GEO_FILE" | tee simRunOutput_2.txt

REC_FILE="${TMPDIR}/sim_${RUN_ID}_rec.root"
if [ ! -f "$REC_FILE" ]; then
    echo "ERROR: reco output not found:"
    ls -lh "$TMPDIR"
    rm -rf "$TMPDIR"
    exit 1
fi

cp "$SIM_FILE"        "${OUTPUT_DIR}/sim_${RUN_ID}.root"
cp "$GEO_FILE"        "${OUTPUT_DIR}/geo_${RUN_ID}.root"
cp "$PARAMS_FILE"     "${OUTPUT_DIR}/params_${RUN_ID}.root"
cp "$REC_FILE"        "${OUTPUT_DIR}/reco_${RUN_ID}.root"
cp simRunOutput_1.txt "${OUTPUT_DIR}/"
cp simRunOutput_2.txt "${OUTPUT_DIR}/"

rm -rf "$TMPDIR"
echo "SUCCESS: $OUTPUT_DIR"
