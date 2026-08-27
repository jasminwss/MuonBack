# vetoPoint vs digi hit (vetoHit) — what we've established

Reference notes from investigating the SBT/veto hit-rate scripts (`z_phi_origin.py`,
`inspect_Back.py`, `MuonBack_hitrates.py`) against the real FairShip digitization
(`shipDigiReco.py` / `SBTDetector.py`) and geometry (`veto.cxx`, `vetoHit.cxx`).

## 1. Two different objects

- **`vetoPoint`** — raw MC truth. One entry per particle crossing a *sensitive*
  scintillator volume. Lives in `sim_*.root`, tree `cbmsim`, branch `vetoPoint`.
  Has a true continuous impact position, `GetEnergyLoss()`, `GetTime()`,
  `GetDetectorID()`, `GetTrackID()`.
- **`vetoHit`** (a.k.a. "digi hit") — one per (`detID`, event), built by *summing*
  all `vetoPoint`s that land in the same cell in the same event
  (`ElossPerDetId[detID] += Eloss`, not max-of). Constructed as
  `ROOT.vetoHit(detID, summedEloss)`.

## 2. Where digitization actually happens

- `run_simScript.py` only runs the simulation and writes `vetoPoint` — **no
  digitization here**.
- `ShipReco.py` → `shipDigiReco.py`'s `SHiP.digitize()` → instantiates
  `SBTDetector("veto", ...)` → `SBTDetector.digitize()`
  ([SBTDetector.py:27-58](../../sw/slc9_x86-64/FairShip/master-local2/python/detectors/SBTDetector.py#L27)).
  This is the *real* digitization step. Output would land in the reco tree
  (`ship_reco_sim`, branch `digiSBT`), in `reco_*.root`.
- **None of our analysis scripts read that branch.** `z_phi_origin.py`,
  `inspect_Back.py`, `MuonBack_hitrates.py` all open only the sim file (`cbmsim`)
  and re-implement the digitization themselves in Python, building their own
  `vetoHit` objects from `vetoPoint`s. `inspect_Back.py` even has the reco-file
  open commented out (lines 220-221, 241-242).

## 3. Own digitization vs real `SBTDetector.digitize()`

| | own scripts | real `SBTDetector.digitize()` |
|---|---|---|
| Eloss sum per cell/event | ✅ identical (`+=`) | ✅ identical |
| `vetoHit(detID, Eloss)` constructor | ✅ identical | ✅ identical |
| **Position** (`GetXYZ()`/`GetNode()`) | ✅ identical — same method, same object | ✅ identical |
| TDC (`SetTDC(min(times)+t0)`) | ❌ never set | ✅ set |
| **45 MeV validity cut** (`if Eloss<0.045: setInvalid()`) | ❌ never applied | ✅ applied — "threshold for liquid scintillator, source Berlin group" |
| Track matching (`findVetoHitOnTrack`/`linkVetoOnTracks`) | ❌ not done | ✅ done, downstream of digitize() |
| Persisted to file | ❌ transient dict only | ✅ written as `digiSBT` branch |

`MuonBack_hitrates.py` at one point *did* replicate the TDC/validity logic
almost verbatim — it's still there, commented out
([MuonBack_hitrates.py:434-435, 474](../../FairShip_MuonAnalysis/MuonBack_hitratestudy/MuonBack_hitrates.py#L434)).

**Consequence:** the `0 MeV` and `10 MeV` rows in our rate tables include hits
that real reco would mark `isValid()==False` (below the 45 MeV SBT threshold)
and would normally be discarded downstream. Only the `45 MeV`/`90 MeV` rows are
consistent with what real reco calls a valid hit.

## 4. Position = cell center, not true hit position

`vetoHit::GetXYZ()` ([vetoHit.cxx:32-43](../../sw/slc9_x86-64/FairShip/latest/veto/vetoHit.cxx#L32)):
decodes `detID` → `ShapeType`, `blockNr`, `Zlayer`, `number` → builds a fixed
node path under `.../VetoLiSc_0/...` → reads the `TGeoBBox` local origin of
that node → `LocalToMaster()`. So every particle that lands in the same cell
in the same event (regardless of exact impact point) gets mapped to the exact
same (x,y,z) — the cell's geometric center. `vetopoint_topology_phi` (true,
continuous positions) and `{threshold}_digihit_topology_phi` (quantized cell
centers) are **not** directly comparable maps of the same thing.

## 5. Geometry: only LiSc is sensitive, Wall/Rib are not

Checked in `veto.cxx`:
- `GeoCornerLiSc1`/`GeoCornerLiSc2` (LiSc_S3-S6, LiScX/Y) are called with
  explicit `sens=true` → `AddSensitiveVolume()` fires.
- `GeoCornerRib()` (builds `VetoLongitRib_0`'s corner pieces) has
  `sens=kFALSE` by default and the call site never overrides it → **not
  sensitive**.
- `GeoTrapezoidHollow()` (builds `InnerWall`/`OuterWall`/`VerticalRib`) is
  never passed to `AddSensitiveVolume` at all.

→ A `vetoPoint` (and therefore a digi hit) can **only** ever come from a LiSc
cell. Walls/ribs never produce hits — they're passive structure. (They *do*
matter for `classify_production_vertex`, which checks where a *track* was
*produced*, e.g. a secondary from an interaction in the wall material — a
completely separate geometry query from where a hit is registered.)

## 6. Real azimuthal gaps in LiSc coverage

Built `list_veto_cells.py` to enumerate all `VetoLiSc_0` daughter cell centers
directly from `geo_*.root` (854 cells → 690 distinct phi values after
dedup — z-layers of the same bar share x,y). Confirmed **actual gaps**, not
histogram binning artifacts:

```
[0.0, 18.2)    [41.1, 57.3)   [69.0, 111.0)  [122.7, 138.9)  [161.8, 198.2)
[221.1, 237.3) [249.0, 291.0) [302.7, 318.9) [341.8, 360.0)
```

The two big ones ([69°,111°) and [249°,291°), ~42° each) are where
`digihit_topology_phi` is completely empty across all thresholds/origins in
`phi-z-plots.root`. `VetoLongitRib_0` (not sensitive, but still real
geometry) places a rib segment right at 90.0° and 270.0°, splitting each 42°
gap into two 21° halves — consistent with a support rib occupying that
azimuth where scintillator isn't placed, though the rib doesn't fill the
whole gap.

## 7. Where to look

- `MuonBack/Inspection/z_phi_origin.py`, `inspect_Back.py` — own digitization + phi/z topology histograms, split by origin (cavern/SBT/upstream).
- `FairShip_MuonAnalysis/MuonBack_hitratestudy/MuonBack_hitrates.py` — same pattern, has commented-out TDC/validity code.
- `sw/.../FairShip/master-local2/python/detectors/SBTDetector.py` — real digitization.
- `sw/.../FairShip/latest/veto/vetoHit.cxx` / `veto.h` — hit class, position lookup, validity flag.
- `sw/.../FairShip/master-local2/veto/veto.cxx` — geometry construction, sensitive-volume registration.
- `MuonBack/Inspection/additional_infos/list_veto_cells.py` — geometry-level cell center / phi coverage scan (LiSc only).

## 8. Open questions / not yet checked

- Where (if anywhere) downstream reco code actually checks `isValid()` before
  using a hit — i.e. what real consequence the 45 MeV flag has further down
  the chain.
- Whether the ~16-18° gaps (besides the two big ones) also line up with rib/
  wall placement, or have a different cause.
