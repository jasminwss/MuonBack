#!/bin/bash
set -e

SIM_FILE=$1
NEVENTS=${2:-999999}
PROCESS=$3          # ← Condor $(Process) → job_0, job_1, ...

SUBDIR=$(dirname "$SIM_FILE")
BASENAME=$(basename "$SIM_FILE" .root)
UUID=${BASENAME#sim_}
GEO_FILE=${SUBDIR}/geo_${UUID}.root
PARAMS_FILE=${SUBDIR}/params_${UUID}.root

OUTPUT_BASE=/eos/user/j/jaweiss/MuonBack
SUBFOLDER=$(basename $(dirname "$SIM_FILE"))   # e.g. 16_400000_2000001
OUTPUT_DIR=${OUTPUT_BASE}/job_${SUBFOLDER}    # ← one folder per job
mkdir -p "$OUTPUT_DIR"

[ -f "$SIM_FILE" ]    || { echo "ERROR: sim file missing: $SIM_FILE"; exit 1; }
[ -f "$GEO_FILE" ]    || { echo "ERROR: geo file missing: $GEO_FILE"; exit 1; }
[ -f "$PARAMS_FILE" ] || { echo "ERROR: params file missing: $PARAMS_FILE"; exit 1; }

source /cvmfs/ship.cern.ch/26.04/setUp.sh
eval $(alienv --work-dir /cvmfs/ship.cern.ch/26.04/sw load FairShip/latest)
echo "Using FAIRSHIP=$FAIRSHIP"

TMPDIR=$(mktemp -d)
cd "$TMPDIR"

python "$FAIRSHIP/macro/ShipReco.py" \
    -f "$SIM_FILE" \
    -g "$GEO_FILE"

REC_FILE="${TMPDIR}/${BASENAME}_rec.root"
if [ ! -f "$REC_FILE" ]; then
    echo "ERROR: reco output not found:"
    ls -lh "$TMPDIR"
    rm -rf "$TMPDIR"
    exit 1
fi

cp "$SIM_FILE"    "${OUTPUT_DIR}/sim_${UUID}.root"
cp "$GEO_FILE"    "${OUTPUT_DIR}/geo_${UUID}.root"
cp "$PARAMS_FILE" "${OUTPUT_DIR}/params_${UUID}.root"
cp "$REC_FILE"    "${OUTPUT_DIR}/reco_${UUID}.root"

for logfile in "$SUBDIR"simRunOutput_*.txt "$SUBDIR"simRunCommand_*.txt; do
    [ -f "$logfile" ] && cp "$logfile" "$OUTPUT_DIR/"
done

rm -rf "$TMPDIR"
echo "SUCCESS: $OUTPUT_DIR"