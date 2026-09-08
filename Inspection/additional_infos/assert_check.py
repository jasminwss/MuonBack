#!/usr/bin/env python
"""
Check that reco and sim trees are aligned entry-by-entry, for every job in a directory.

For each job:
    reco entry i  <->  sim entry i        (positional matching)
    rec.ShipEventHeader.GetMCEntryNumber() must equal sim.MCEventHeader.GetEventID()

MCEntryNumber is NOT a TTree index - it is the event ID of the muon in the flux input.
So it is useless for GetEntry(), but perfect as a consistency check: if sim and reco
files do not belong together, the IDs drift apart immediately.

Usage:
    python check_event_alignment.py [BASEDIR]
"""
import glob, os, sys, ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kError

BASEDIR = sys.argv[1] if len(sys.argv) > 1 else \
    '/eos/user/j/jaweiss/MuonBack/TRY5PlSc'


def one(job, pattern):
    """Exactly one file matching pattern inside job dir, else None + reason."""
    m = glob.glob(os.path.join(job, pattern))
    if len(m) != 1:
        return None, 'expected 1 match for %s, got %d' % (pattern, len(m))
    return m[0], None


def check_job(job):
    """Return (status, message). status is 'ok', 'fail' or 'skip'."""
    f_sim_path, err = one(job, 'sim_*.root')
    if err:
        return 'skip', err
    f_rec_path, err = one(job, 'reco_*.root')
    if err:
        return 'skip', err

    f_sim = ROOT.TFile.Open(f_sim_path)
    f_rec = ROOT.TFile.Open(f_rec_path)
    if not f_sim or f_sim.IsZombie() or not f_rec or f_rec.IsZombie():
        return 'skip', 'could not open root file(s)'

    sim = f_sim.Get('cbmsim')
    rec = f_rec.Get('ship_reco_sim')
    if not isinstance(sim, ROOT.TTree) or not isinstance(rec, ROOT.TTree):
        f_sim.Close(); f_rec.Close()
        return 'skip', 'cbmsim or ship_reco_sim missing'

    n_sim, n_rec = sim.GetEntries(), rec.GetEntries()
    if n_sim != n_rec:
        f_sim.Close(); f_rec.Close()
        return 'fail', 'entry counts differ: sim=%d reco=%d' % (n_sim, n_rec)

    # only read the header branches - makes this ~100x faster than full events
    sim.SetBranchStatus('*', 0); sim.SetBranchStatus('MCEventHeader*', 1)
    rec.SetBranchStatus('*', 0); rec.SetBranchStatus('ShipEventHeader*', 1)

    bad = []
    for i in range(n_sim):
        sim.GetEntry(i); rec.GetEntry(i)
        id_sim = sim.MCEventHeader.GetEventID()
        id_rec = rec.ShipEventHeader.GetMCEntryNumber()
        if id_sim != id_rec:
            bad.append((i, id_rec, id_sim))
            if len(bad) >= 5:
                break

    f_sim.Close(); f_rec.Close()

    if bad:
        detail = ', '.join('entry %d: reco=%d sim=%d' % b for b in bad)
        return 'fail', 'first mismatches: %s' % detail
    return 'ok', '%d entries aligned' % n_sim


def main():
    jobs = sorted(glob.glob(os.path.join(BASEDIR, 'job_*')))
    if not jobs:
        sys.exit('no job_* directories in %s' % BASEDIR)

    print('checking %d jobs in %s\n' % (len(jobs), BASEDIR))
    counts = {'ok': 0, 'fail': 0, 'skip': 0}

    for job in jobs:
        status, msg = check_job(job)
        counts[status] += 1
        mark = {'ok': 'OK  ', 'fail': 'FAIL', 'skip': 'SKIP'}[status]
        print('%s  %-45s  %s' % (mark, os.path.basename(job), msg))

    print('\n%d ok, %d failed, %d skipped' % (counts['ok'], counts['fail'], counts['skip']))
    sys.exit(1 if counts['fail'] else 0)


if __name__ == '__main__':
    main()