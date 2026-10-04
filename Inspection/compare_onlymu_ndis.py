#!/usr/bin/env python3
"""Compare N_mu (Eloss in SBT), mean cells hit and N_DIS for 0 / 90 MeV threshold
across several inspect_onlymu log files."""
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LOGDIR = "/afs/cern.ch/work/j/jaweiss/private/MuonBack/Inspection/logs"
LOGS = [
    "inspect_onlymu.12682103.0.out",  # TRY5PlSc
    "inspect_onlymu.12682118.0.out",  # TRY5LiSc
    "inspect_onlymu.12684389.0.out",  # TRY6LiSc
]
THRESHOLDS = [0, 90]

RHO = {"LiSc": 0.86, "PlSc": 1.032}  # g/cm^3, picked from the tag suffix


def compute_NDIS(data):
    """N_DIS per spill = M * x * sigma * rho * N_A/A * N_mu, with M = mean cells hit:
    {tag: [N_DIS(thr) for thr in THRESHOLDS]}"""
    x = 80  # cm, SBT cell length in z
    XS = 6e-30  # cm^2 (6e-3 mbarn)
    NA_A = 6e23  # 1/g
    out = {}
    for tag, vals in data:
        rho = RHO[tag[-4:]]
        out[tag] = [vals[thr][1] * x * XS * rho * NA_A * vals[thr][0] for thr in THRESHOLDS]
    return out


re_tag = re.compile(r"Histograms written to .*onlymu_(TRY\w+)\.root")
re_val = re.compile(r"cell Eloss >=\s*(\d+)MeV\):\s*([\d.eE+-]+).*mean cells hit:\s*([\d.]+)")


def parse(path):
    tag, vals = None, {}
    with open(path) as f:
        for line in f:
            m = re_tag.search(line)
            if m:
                tag = m.group(1)
            m = re_val.search(line)
            if m:
                vals[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    return tag, vals


data = [parse(os.path.join(LOGDIR, l)) for l in LOGS]
NDIS = compute_NDIS(data)
tags = [t for t, _ in data]
for t, v in data:
    print(t, {thr: v.get(thr) for thr in THRESHOLDS}, "N_DIS:", NDIS.get(t))

x = np.arange(len(tags))
w = 0.38
colors = {0: "#1f77b4", 90: "#d62728"}
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

for i, thr in enumerate(THRESHOLDS):
    off = (i - 0.5) * w
    nmu = [v[thr][0] for _, v in data]
    mean = [v[thr][1] for _, v in data]
    ndis = [NDIS.get(t, [None, None])[i] for t in tags]
    lab = f"cell Eloss >= {thr} MeV"

    b = axes[0].bar(x + off, nmu, w, color=colors[thr], label=lab)
    axes[0].bar_label(b, fmt="%.2e", fontsize=8)
    b = axes[1].bar(x + off, mean, w, color=colors[thr], label=lab)
    axes[1].bar_label(b, fmt="%.2f", fontsize=8)
    ok = [j for j, n in enumerate(ndis) if n is not None]
    if ok:
        b = axes[2].bar(x[ok] + off, [ndis[j] for j in ok], w, color=colors[thr], label=lab)
        axes[2].bar_label(b, fmt="%.0f", fontsize=8)

axes[0].set_ylabel(r"$N_{\mu}$ depositing energy in SBT / spill")
axes[1].set_ylabel("mean cells hit")
axes[2].set_ylabel(r"estimated $N_{DIS}$ / spill")
for ax in axes:
    ax.set_xticks(x)
    ax.set_xticklabels(tags)
    ax.set_xlim(-0.6, len(tags) - 0.4)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.margins(y=0.15)

fig.tight_layout()
out = os.path.join(os.path.dirname(LOGDIR), "compare_onlymu_NDIS_" + "_".join(tags) + ".png")
fig.savefig(out, dpi=200)
print("saved", out)
