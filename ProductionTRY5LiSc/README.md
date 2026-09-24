# AFS overload fix (2026-09-12)

Submitting the 8256-job cluster in `sim_jobs.txt` in one go overloaded the
`work.jaweiss` AFS volume and got it marked offline by CERN IT. Cause: every
job reads the FairShip/pixi environment from AFS
(`/afs/cern.ch/work/j/jaweiss/FairShip` in `submitscript3.sh`), so thousands
of jobs starting at once meant thousands of concurrent AFS reads. AFS is not
built for that; EOS is.

## Done

In `muonback.sub`:
- `output` / `error` / `log` moved back to AFS (`logs/...`, relative to this
  dir). Briefly tried EOS (`/eos/user/j/jaweiss/MuonBack/TRY5LiSc/condorlogs/`)
  to get everything off AFS, but HTCondor's own file-transfer-back for these
  three (CEDAR write-to-temp-then-rename) doesn't work reliably on EOS —
  every job held with "Transfer output files failure ... errno 2 No such
  file or directory" even though the target dir existed and was writable.
  Not the AFS-overload problem (that was thousands of concurrent jobs each
  reading FairShip from AFS, fixed below) — these are a handful of small
  files at a `max_materialize`-throttled rate, AFS handles that fine.
- Added `max_materialize = 200` — caps how many jobs run at the same time,
  instead of all 8256 starting (and hitting AFS) simultaneously.
- Merged the two duplicate `requirements` lines (the second was silently
  overwriting the first, so the "don't reuse last host" condition was never
  applied).
- Copied the FairShip build (7.7GB, 132082 files) once to `/eos/user/j/jaweiss/FairShip`
  and pointed `FAIRSHIP=` in `submitscript3.sh` there, so jobs read from EOS
  instead of AFS. Copy finished and verified (file count matches AFS).

## Still open

`PIXI_BIN` in `submitscript3.sh` still points at
`/afs/cern.ch/work/j/jaweiss/.pixi/bin/pixi` (AFS, ~74MB). Small and fine
with `max_materialize = 200`, but worth moving to EOS too at some point.

Test with `sim_jobs_short.txt` before switching back to the full
`sim_jobs.txt` (8255 jobs).
