# MuonBack

Analysis of the Muon Background for the SHiP experiment, focused on hit rates in the **Surrounding Background Tagger (SBT)**.

The goal is to reconstruct simulation files from Guglielmo Frisell's TRY 2025 production and compute SBT hit rates as a function of energy threshold — for comparison with results from the 2018 production (Anupama Karmakar).

---

## Repository Structure

```
MuonBack/
├── Production/    # HTCondor job submission and reconstruction
└── Inspection/    # SBT hit rate analysis and output
```

---

## Production

Runs `ShipReco.py` (FairShip) on simulation files via HTCondor on lxplus. Each job takes one simulation file, reconstructs it, and copies the output to EOS.

### Input

Simulation files from Guglielmo Frisell's TRY 2025 production on EOS:
```
/eos/experiment/ship/user/gfrisell/Simulation_Results/TRY_2025_EM/<job_dir>/sim_<uuid>.root
```

Each job directory also contains:
- `geo_<uuid>.root` — geometry file
- `params_<uuid>.root` — parameter file
- `simRunOutput_2.txt` — simulation run log

The full list of input simulation files is in `Production/input_files.txt` (~1000 files).  
A short test list (5 files) is in `Production/input_files_short.txt`.

### Output

Reconstructed files are written to EOS at:
```
/eos/user/j/jaweiss/MuonBack/job_<job_dir>/
```

Each output folder contains:
- `sim_<uuid>.root` — original simulation file (copy)
- `geo_<uuid>.root` — geometry file (copy)
- `params_<uuid>.root` — parameter file (copy)
- `reco_<uuid>.root` — reconstruction output (`ship_reco_sim` tree)
- `simRunOutput_2.txt` — simulation run log

### Files

| File | Description |
|------|-------------|
| `muonback.sub` | HTCondor submission file |
| `submitscript3.sh` | Worker node script: loads FairShip, runs ShipReco.py, copies output to EOS |
| `config_fairship.sh` | FairShip environment configuration |
| `input_files.txt` | Full list of ~1000 simulation files |
| `input_files_short.txt` | Short list of 5 files for testing |
| `logs/` | HTCondor job logs (gitignored) |

### How to Submit Jobs

**Test run (5 files):**
```bash
cd Production/
# make sure input_files_short.txt is set in muonback.sub:
# queue SIM_FILE from input_files_short.txt
condor_submit muonback.sub
```

**Full production (~1000 files):**
```bash
cd Production/
# make sure input_files.txt is set in muonback.sub:
# queue SIM_FILE from input_files.txt
condor_submit muonback.sub
```

Monitor jobs:
```bash
condor_q -submitter jaweiss
condor_history -submitter jaweiss | head -20   # check completed/removed jobs
```

### HTCondor Configuration

| Setting | Value |
|---------|-------|
| CPUs | 1 |
| Memory | 4 GB |
| Disk | 5 GB |
| Job flavour | `espresso` (~20 min, sufficient per job) |
| Max retries | 3 |
| OS | AlmaLinux9 |
| FairShip version | `26.04/latest` via CVMFS |

Jobs are removed after 3 failed attempts (`on_exit_remove`). Failed jobs can be inspected via `condor_history`.

### ShipReco.py Arguments

`ShipReco.py` accepts the following optional arguments. **None of them were used in this production** — all defaults apply.

| Argument | Default | Description |
|----------|---------|-------------|
| `--noVertexing` | off | Skips the vertexing step (2-track vertex reconstruction). Not needed for SBT hit rate analysis, which uses only `MCTrack` and `vetoPoint` from the simulation tree. |
| `--noStrawSmearing` | off | Disables distance-to-wire smearing in the straw tracker. Relevant for tracking performance studies, not for SBT analysis. |
| `--withT0` | off | Simulates an arbitrary T0 offset and corrects for it. Relevant for timing studies. |
| `--patRec` | `AR` | Pattern recognition algorithm: `AR` (Artificial Retina, default), `FH` (Hough transform), or `TemplateMatching`. Not passing this argument does **not** skip pattern recognition — Artificial Retina runs by default. |
| `-dy` | from filename | Maximum tank height in cm. Extracted automatically from the input file name if not given. |
| `--firstEvent` | `0` | Index of the first event to process. |

---

## Inspection

Computes SBT hit rates from the reconstructed and simulation files stored on EOS.

### What it does

`inspect_Back.py` loops over all job output folders in `/eos/user/j/jaweiss/MuonBack/`, loads the `cbmsim` tree from each simulation file and the `ship_reco_sim` tree from each reco file (used only for event ID synchronisation), and fills histograms of:

- **vetoPoint** energy deposition per particle, PDG composition, spatial topology (z, φ)
- **Digitised SBT hits** at thresholds of 0, 10, 20, 30, 45, 50, 60, 90 MeV:
  - Total hit rate (MHz) and maximum per-cell rate (Hz)
  - Hit multiplicity per event
  - Energy deposition distributions
  - z–φ topology maps

Event weights from `MCTrack` are applied throughout to scale generated events to one SHiP spill.

### Input

```
/eos/user/j/jaweiss/MuonBack/job_<job_dir>/
    sim_<uuid>.root   →  cbmsim tree  (MCTrack, vetoPoint)
    reco_<uuid>.root  →  ship_reco_sim tree  (ShipEventHeader only)
    geo_<uuid>.root   →  FAIRGeom + ShipGeo
```

### Output

| File | Description |
|------|-------------|
| `inspection.root` | ROOT file with all histograms |
| `file_inspection_summary.txt` | Plain-text summary of hit rates per threshold |

### How to Run

```bash
cd Inspection/
python inspect_Back.py --path /eos/user/j/jaweiss/MuonBack
```

Requires FairShip environment (run on lxplus after sourcing CVMFS setup).

### Results (2026 production, ~314k generated events)

| Threshold | Total SBT hit rate | Max cell rate | Hottest cell |
|-----------|-------------------|---------------|--------------|
| 0 MeV | 2.02 MHz | 410 kHz | ID 226022 |
| 10 MeV | 73.7 kHz | 1.9 kHz | ID 220112 |
| 20 MeV | 35.0 kHz | 0.95 kHz | ID 220112 |
| 30 MeV | 18.7 kHz | 810 Hz | ID 624332 |
| 45 MeV | 11.3 kHz | 790 Hz | ID 624332 |
| 50 MeV | 9.9 kHz | 780 Hz | ID 624332 |
| 60 MeV | 9.0 kHz | 780 Hz | ID 624332 |
| 90 MeV | 6.2 kHz | 770 Hz | ID 524322 |

Scaled to one spill: ~3.2×10⁶ muon background events, of which ~1.2×10⁶ have SBT activity.

---

## Dependencies

- **FairShip** (via CVMFS: `/cvmfs/ship.cern.ch/26.04/`)
- **ROOT** (included in FairShip environment)
- **HTCondor** (lxplus)
- **EOS** access (CERN account with valid Kerberos ticket)
