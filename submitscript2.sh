#!/bin/bash
set -e

# --- Arguments ---
SIM_FILE=$1
NEVENTS=${2:-999999}
SUBDIR=$(dirname "$SIM_FILE")
SUBFOLDER=$(basename "$SUBDIR")
BASENAME=$(basename "$SIM_FILE" .root)
UUID=${BASENAME#sim_}
GEO_FILE=${SUBDIR}/geo_${UUID}.root
OUTPUT_DIR=/eos/user/j/jaweiss/MuonBack
OUTPUT_FILE=${OUTPUT_DIR}/reco_${SUBFOLDER}_${UUID}.root

# --- Sanity checks ---
[ -f "$SIM_FILE" ] || { echo "ERROR: sim file missing: $SIM_FILE"; exit 1; }
[ -f "$GEO_FILE" ] || { echo "ERROR: geo file missing: $GEO_FILE"; exit 1; }

# --- Load environment FIRST ---
source /cvmfs/ship.cern.ch/26.04/setUp.sh
echo 'FairShip 26.04 set up'

# Load CVMFS env directly — bypasses your local build entirely
eval $(alienv --work-dir /cvmfs/ship.cern.ch/26.04/sw load FairShip/latest)
echo 'config sourced'
echo "Using FAIRSHIP=$FAIRSHIP"

# --- Run in tmp dir ---
TMPDIR=$(mktemp -d)
cd "$TMPDIR"

# --- Write reco script (use \$ so vars expand at run time, not now) ---
RECO_SCRIPT="$TMPDIR/run_reco.sh"
cat > "$RECO_SCRIPT" << 'EOF'
#!/bin/bash
echo $LD_LIBRARY_PATH | tr ':' '\n' | grep -i genfit
python $FAIRSHIP/macro/ShipReco.py \
  -f SIM_FILE_PLACEHOLDER \
  -g GEO_FILE_PLACEHOLDER \
  -n NEVENTS_PLACEHOLDER
EOF

# Substitute actual values in
sed -i "s|SIM_FILE_PLACEHOLDER|$SIM_FILE|g" "$RECO_SCRIPT"
sed -i "s|GEO_FILE_PLACEHOLDER|$GEO_FILE|g" "$RECO_SCRIPT"
sed -i "s|NEVENTS_PLACEHOLDER|$NEVENTS|g"   "$RECO_SCRIPT"

chmod +x "$RECO_SCRIPT"

# --- Actually run the reco script ---
bash "$RECO_SCRIPT"

# --- Copy output to EOS ---
REC_FILE="${TMPDIR}/${BASENAME}_rec.root"
if [ ! -f "$REC_FILE" ]; then
    echo "ERROR: expected output file not found: $REC_FILE"
    ls -lh "$TMPDIR"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
cp "$REC_FILE" "$OUTPUT_FILE"
cp "$REC_FILE" "$OUTPUT_FILE" #also paste to reconstruction directory from guglielmo run_Sim.py
cp "$SIM_FILE" "${OUTPUT_DIR}/sim_${SUBFOLDER}_${UUID}.root"
cp "$GEO_FILE" "${OUTPUT_DIR}/geo_${SUBFOLDER}_${UUID}.root"
echo "SUCCESS: $OUTPUT_FILE"
rm -rf "$TMPDIR"