#!/usr/bin/env python
"""
Independent check that reco entry i really is sim entry i.

The header check (MCEntryNumber == GetEventID) is almost circular: reco copies the
header from sim, so the IDs agree whenever the two files belong together - regardless
of whether the entries line up.

This test uses physics instead. A digitised SBT hit cannot exist without an underlying
vetoPoint, so for correct alignment:

    ndigi(reco, i) > 0   =>   nvetoPoint(sim, i) > 0        must ALWAYS hold

The reverse is NOT required (a vetoPoint below threshold produces no digi hit), which
is why a symmetric zero/non-zero comparison is useless here.

Shifting sim by k and counting violations gives the answer: only the correct offset
has zero. Everything else breaks immediately.

Usage:
    python check_alignment_physics.py [path/to/job_dir]
"""
import glob, sys, ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kError

JOB = sys.argv[1] if len(sys.argv) > 1 else \
    '/eos/user/j/jaweiss/MuonBack/TRY5PlSc/job_2_400000_1200001'

SHIFTS = [-2, -1, 0, 1, 2]
MAX_EVENTS = 5000          # plenty; the wrong offsets fail within a handful of events


def one(pattern):
    m = glob.glob(JOB + '/' + pattern)
    if len(m) != 1:
        sys.exit('expected exactly one match for %s, got %s' % (pattern, m))
    return m[0]


f_sim = ROOT.TFile.Open(one('sim_*.root'))
f_rec = ROOT.TFile.Open(one('reco_*.root'))
sim = f_sim.Get('cbmsim')
rec = f_rec.Get('ship_reco_sim')

sim.SetBranchStatus('*', 0); sim.SetBranchStatus('vetoPoint*', 1)
rec.SetBranchStatus('*', 0); rec.SetBranchStatus('Digi_SBTHits*', 1)

n = min(rec.GetEntries(), MAX_EVENTS)
print('checking %d events from %s\n' % (n, JOB))

violations = {k: 0 for k in SHIFTS}   # digi > 0 but no vetoPoint -> impossible
tested     = {k: 0 for k in SHIFTS}
n_with_digi = 0

for i in range(n):
    rec.GetEntry(i)
    ndigi = len(rec.Digi_SBTHits)
    if ndigi == 0:
        continue                      # carries no information for this test
    n_with_digi += 1
    for k in SHIFTS:
        j = i + k
        if j < 0 or j >= sim.GetEntries():
            continue
        sim.GetEntry(j)
        tested[k] += 1
        if len(sim.vetoPoint) == 0:
            violations[k] += 1

print('%d of %d events have at least one SBT digi hit\n' % (n_with_digi, n))
print('shift   events tested   impossible (digi>0, vetoPoint==0)   rate')
for k in SHIFTS:
    rate = violations[k] / tested[k] if tested[k] else 0
    print('%+5d   %13d   %32d   %5.1f%%' % (k, tested[k], violations[k], 100 * rate))

print('\nthe shift with 0 violations is the true alignment.')
print('if shift 0 is clean and all others are not, positional matching is confirmed.')

f_sim.Close(); f_rec.Close()