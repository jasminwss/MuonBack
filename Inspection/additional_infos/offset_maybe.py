#!/usr/bin/env python
"""
does ShipEventHeader.GetMCEntryNumber() count from 0 or from 1? IS ROOT MY ENEMY OR MY FRIEND

what am i even doing at this time of night
forrgive what a tired brain will do

SO WHATS THE DEAL?

All scripts with reco (diag-reco, diag-proc-reco, reco-debug-...) match each event in the
reco tree (`ship_reco_sim` in sim_N_rec.root) back to its truth event in the sim tree
(`cbmsim` in sim_N.root) with

    n = event.ShipEventHeader.GetMCEntryNumber()
    sim.GetEntry(n)

nice and simple and yay 

BUT this assumes MCEntryNumber is a 0-based TTree entry index. But whos fact checking? me apparently.

If it counts starting at 1: GetEntry(n) reads the NEXT (!) event's truth and the last reco
event asks for an entry that does not exist-> the weird empty MC Entry at the end

LETS CHECK

(A) Bookkeeping:  reco should have as many entries as the cbsim

    reco entry i is sim entry i. If MCEntryNumber prints i+1, it is 1-based.

(B) Brain juice: Digi_SBTHits in reco are digitised from vetopoint? or rather without vetopoint value >0 
    there can be no digihit. so digihits of >0 must match vetopoints of >0.
    so print vetoPoint count at sim[n] and sim[n-1]; and see which column has matching 0s or non 0s

(C) Edge case: I call GetEntry(N) on an N-entry tree and 0 bytes are read (so no error is
    raised). check bytes explicity! could the entry just be 0 ? i dont think so 

USE LIKE SO:

    python demo_mcentry_offset.py [path/to/job_*]

Defaults to job_0 of my He 2018 sample if no argument is given.
"""
import glob, sys, ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning   # silence ROOT Info: lines

JOB = sys.argv[1] if len(sys.argv) > 1 else \
      '/eos/user/j/jaweiss/MuonBack/TRY5PlSc/job_2_400000_1200001'

N_HEAD = 12   # rows to print at the start
N_TAIL = 3    # rows to print at the end (to see the last MCEntryNumber)


def one(pattern):
    """Resolve a glob pattern inside the job dir to exactly one file."""
    m = glob.glob(JOB + '/' + pattern)
    if len(m) != 1:
        sys.exit('expected exactly one match for %s, got %s' % (pattern, m))
    return m[0]


# --- open the two trees ------------------------------------------------------
# sim_*[!c].root : sim_N.root but not sim_N_rec.root (name ends in a digit, not 'c')
f_sim = ROOT.TFile.Open(one('sim_*.root'))
f_rec = ROOT.TFile.Open(one('reco_*.root'))
sim = f_sim.Get('cbmsim')          # truth: MCTrack, vetoPoint, ...
rec = f_rec.Get('ship_reco_sim')   # reco:  ShipEventHeader, Particles, Digi_SBTHits, ...
N_sim, N_rec = sim.GetEntries(), rec.GetEntries()

print('sim entries: %d   reco entries: %d' % (N_sim, N_rec))
if N_sim != N_rec:
    print('WARNING: entry counts differ')
print()


def n_vetopoints(k):
    """Number of MC SBT hits (vetoPoint) in cbmsim entry k, or '-' if k is out of range."""
    if k < 0 or k >= N_sim:
        return '-'
    sim.GetEntry(k)
    return len(sim.vetoPoint)


# --- check the mismatches, take a walk along the reco tree -------------------------------------------

print('reco#   MCEntryNumber   SBT digi hits (reco)   vetoPoints sim[n]   vetoPoints sim[n-1]')
mismatch_n, mismatch_nm1 = 0, 0   # count zero/non-zero disagreements for each offset

for i, ev in enumerate(rec):
    n = ev.ShipEventHeader.GetMCEntryNumber()
    ndigi = len(ev.Digi_SBTHits)
    v_n, v_nm1 = n_vetopoints(n), n_vetopoints(n - 1)

    # tally zero/non-zero disagreement between digi (reco) and MC points at each offset
    if v_n   != '-' and (ndigi == 0) != (v_n   == 0): mismatch_n   += 1
    if v_nm1 != '-' and (ndigi == 0) != (v_nm1 == 0): mismatch_nm1 += 1

    if i < N_HEAD or i >= N_rec - N_TAIL:
        print('%5d   %13d   %20d   %17s   %19s' % (i, n, ndigi, v_n, v_nm1))
    elif i == N_HEAD:
        print('  ...')

print()
print('(A) if MCEntryNumber == reco# + 1 in every row, the number is 1-based.')
print('(B) zero/non-zero mismatches between SBT digi hits and vetoPoints over all %d events:' % N_rec)
print('      using sim[n]   : %d' % mismatch_n)
print('      using sim[n-1] : %d' % mismatch_nm1)
print('    the offset with (close to?) zero mismatches is correctly aligned!')

# --- (C): what GetEntry reads at the end ------------------------------------
print()
print('(C) sim.GetEntry(%d) returns %d bytes  (valid entries are 0..%d)'
      % (N_sim, sim.GetEntry(N_sim), N_sim - 1))
print('    the current scripts do exactly this for the last reco event if MCEntryNumber is 1-based. But not anymore because now I added the offset fix')



print()
print('Extra check because I want to be sure about GetEntry')

#dont want to integrate it right now i am sorry
f = ROOT.TFile.Open('/eos/user/j/jaweiss/MuonBack/TRY5PlSc/job_2_400000_1200001/sim_301a443d-ad58-4d73-b433-fe85cd9bd9fe.root')
f.ls() #welche bäume gibts wirklich
t = f.Get('cbmsim') # muonen, gst wäre neutrinos
N = t.GetEntries()
print('entries:', N)

#i want to see if getentry REALLY starts at 0
# 1) im assuming that: bytes read: >0 means the entry exists, 0 means there is no such entry
print('GetEntry(0)    ->', t.GetEntry(0),   'bytes')
print('GetEntry(%d) ->' % (N-1), t.GetEntry(N-1), 'bytes')
print('GetEntry(%d) ->' % N,     t.GetEntry(N),   'bytes')

# 2) compare with an iteration, so walking the tree from the beginning
#first_iter = next(iter(t)).Ev            # neutrino energy of the first event via 'for event in tree'
#t.GetEntry(0); e0 = t.Ev
#t.GetEntry(1); e1 = t.Ev
#print('first event via iterator: Ev =', first_iter)
#print('GetEntry(0):              Ev =', e0)
#print('GetEntry(1):              Ev =', e1)
#print()
#print('Aheu my eyes do not deceive me')
#print()

for i in range(50):
    rec.GetEntry(i); sim.GetEntry(i)
    print(i, rec.ShipEventHeader.GetMCEntryNumber(),
             sim.MCEventHeader.GetEventID())

# close explicitly so ROOT does not segfault in static destruction at exit
f_sim.Close(); f_rec.Close()