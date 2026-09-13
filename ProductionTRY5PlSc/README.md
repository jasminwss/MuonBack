# AFS overload fix (2026-09-12)

Submitting the 8256-job cluster in `sim_jobs.txt` in one go overloaded the
`work.jaweiss` AFS volume and got it marked offline by CERN IT. Cause: every
job reads the FairShip/pixi environment from AFS
(`/afs/cern.ch/work/j/jaweiss/FairShip` in `submitscript3.sh`), so thousands
of jobs starting at once meant thousands of concurrent AFS reads. AFS is not
built for that; EOS is.

## Done

In `muonback.sub`:
- `output` / `error` / `log` moved from a relative (AFS) path to
  `/eos/user/j/jaweiss/MuonBack/TRY5LiSc/condorlogs/` — was 8256 jobs writing
  their own `.out`/`.err` files plus one shared `.log` file all to AFS at once.
- Added `max_materialize = 200` — caps how many jobs run at the same time,
  instead of all 8256 starting (and hitting AFS) simultaneously.
- Merged the two duplicate `requirements` lines (the second was silently
  overwriting the first, so the "don't reuse last host" condition was never
  applied).

## Still open

`submitscript3.sh` still reads FairShip from AFS. Plan: copy the build once
to `/eos/user/j/jaweiss/FairShip` and point `FAIRSHIP=` in the script there,
so jobs read from EOS instead of AFS. Not done yet — pending go-ahead, since
the build is 7.7 GB and copying still means reading it once from AFS.
