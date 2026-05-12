#!/bin/bash
set -e

# --- Argument ---
SIM_FILE=$1
SUBDIR=$(dirname "$SIM_FILE")
SUBFOLDER=$(basename "$SUBDIR")                  # e.g. 14_400000_1
BASENAME=$(basename "$SIM_FILE" .root)           # e.g. sim_3a057161-...
UUID=${BASENAME#sim_}                            # e.g. 3a057161-...

GEO_FILE=${SUBDIR}/geo_${UUID}.root
OUTPUT_DIR=/eos/user/j/jaweiss/MuonBack
OUTPUT_FILE=${OUTPUT_DIR}/reco_${SUBFOLDER}_${UUID}.root

# --- Sanity checks ---
[ -f "$SIM_FILE" ] || { echo "ERROR: sim file missing: $SIM_FILE"; exit 1; }
[ -f "$GEO_FILE" ] || { echo "ERROR: geo file missing: $GEO_FILE"; exit 1; }

# --- Environment ---
source /cvmfs/ship.cern.ch/26.03/setUp.sh 
source /afs/cern.ch/work/j/jaweiss/private/MuonBack/config_fairship.sh

# --- Run reconstruction in a tmp scratch dir ---
# (ShipReco.py writes output to current directory)
TMPDIR=$(mktemp -d)
cd "$TMPDIR"

python $FAIRSHIP/macro/ShipReco.py \
  -f "$SIM_FILE"                   \
  -g "$GEO_FILE"                   \
  --heartbeat 10000

# --- Copy output to EOS ---
REC_FILE=$(ls ship.*rec*.root 2>/dev/null | head -1)
if [ -z "$REC_FILE" ]; then
  echo "ERROR: no rec file produced by ShipReco.py"
  ls -lh "$TMPDIR"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
cp "$REC_FILE" "$OUTPUT_FILE"
echo "SUCCESS: $OUTPUT_FILE"

# --- Cleanup ---
rm -rf "$TMPDIR"