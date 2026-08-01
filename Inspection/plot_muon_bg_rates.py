#!/usr/bin/env python3
"""Plot muon background rate vs. energy threshold as a bar chart.

Parses a `*_readme.txt` produced alongside the muon background inspection
(e.g. 2026_readme.txt) and plots rate per threshold, color-coded by its
cavern / SBT / upstream contributions. Rates span ~3 orders of magnitude
across thresholds, so three plot modes are available (--mode):

  log     stacked bars, log-scaled y-axis. Keeps a single "total" bar per
          threshold readable across ~3 orders of magnitude. Note: on a log
          axis, equal segment heights do NOT mean equal MHz (a segment
          spanning 100->200 MHz looks the same size as one spanning
          1->2 MHz) — read segment values from the printed totals /
          underlying table, not from stacked heights.
  split   true stacked bars, split into two linear-scaled panels (low
          thresholds / high thresholds) so each panel's own range stays
          readable. Stacking remains meaningful within each panel.
  linear  single-panel stacked bars on one linear axis (original/simple
          view). Correct total height, but high-threshold bars can be
          visually tiny next to low-threshold ones.

Usage:
    python plot_muon_bg_rates.py [readme.txt] [--mode log|split|linear] [-o output.png]
"""

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# dataviz reference palette, categorical slots 1-3 (light mode)
COLORS = {
    "cavern": "#f5ddb9",    # 
    "SBT": "#b8c6de",       # 
    "upstream": "#f6c5db",  # 
}
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
BASELINE = "#c3c2b7"

HEADER_RE = re.compile(r"THRESHOLD.*TOTAL", re.IGNORECASE)
ROW_RE = re.compile(r"^\s*(\d+(?:\.\d+)?\s*\S+)\s*\t(.+)$")


def parse_readme(path):
    """Return (thresholds, {series_name: [values]}) parsed from the table."""
    lines = Path(path).read_text().splitlines()

    header_idx = next((i for i, l in enumerate(lines) if HEADER_RE.search(l)), None)
    if header_idx is None:
        raise ValueError(f"no THRESHOLD/TOTAL table header found in {path}")

    columns = [c.strip() for c in lines[header_idx].strip().split("\t")]
    # columns[0] is "THRESHOLD", the rest line up with each data row's fields
    series_names = columns[1:]

    thresholds = []
    values = {name: [] for name in series_names}
    for line in lines[header_idx + 1:]:
        m = ROW_RE.match(line)
        if not m:
            if thresholds:
                break  # table ended (hit the closing '---' line)
            continue  # still skipping the separator line before data starts
        threshold, rest = m.groups()
        fields = [f.strip() for f in rest.split("\t")]
        if len(fields) != len(series_names):
            continue
        thresholds.append(threshold.strip())
        for name, val in zip(series_names, fields):
            values[name].append(float(val))

    if not thresholds:
        raise ValueError(f"no data rows parsed from {path}")
    return thresholds, values


def pick_column(values, keyword):
    for name in values:
        if keyword.lower() in name.lower():
            return name
    raise KeyError(f"no column matching '{keyword}' among {list(values)}")


SERIES = ["cavern", "SBT", "upstream"]


def style_axes(ax, log=False):
    ax.set_facecolor(SURFACE)
    ax.tick_params(axis="y", colors=INK_MUTED, labelsize=9)
    ax.tick_params(axis="x", colors=INK_MUTED, length=0)
    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    if log:
        ax.set_yscale("log")


def stacked_bars(ax, x, thresholds, values, columns, label_total_col=None, log=False):
    bottom = [0.0] * len(thresholds)
    for s in SERIES:
        vals = values[columns[s]]
        ax.bar(
            x, vals, bottom=bottom, width=0.6,
            color=COLORS[s], edgecolor=SURFACE, linewidth=1.5,
            label=s, zorder=3,
        )
        bottom = [b + v for b, v in zip(bottom, vals)]
    if label_total_col is not None:
        for xi, total in zip(x, values[label_total_col]):
            # additive headroom reads as a fixed gap on a linear axis; on a
            # log axis the gap must be multiplicative or small bars get a
            # label floating far above them
            label_y = total * 1.08 if log else total + max(bottom) * 0.02
            ax.text(
                xi, label_y, f"{total:.1f}",
                ha="center", va="bottom", fontsize=8, color=INK_SECONDARY,
            )
    return bottom


def plot_linear(thresholds, values, columns, total_col, output):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)

    x = list(range(len(thresholds)))
    stacked_bars(ax, x, thresholds, values, columns, label_total_col=total_col)

    ax.set_xticks(x)
    ax.set_xticklabels(thresholds, color=INK_PRIMARY, fontsize=9)
    ax.set_ylabel("Rate (MHz)", color=INK_PRIMARY, fontsize=10)
    ax.set_xlabel("Energy threshold", color=INK_PRIMARY, fontsize=10)
    ax.set_title("Muon background rate vs. threshold", color=INK_PRIMARY, fontsize=12, pad=14)
    style_axes(ax)
    ax.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    fig.tight_layout()
    fig.savefig(output, facecolor=SURFACE)
    plt.close(fig)


def plot_log(thresholds, values, columns, total_col, output):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)

    x = list(range(len(thresholds)))
    stacked_bars(ax, x, thresholds, values, columns, label_total_col=total_col, log=True)

    ax.set_xticks(x)
    ax.set_xticklabels(thresholds, color=INK_PRIMARY, fontsize=9)
    ax.set_ylabel("Rate (MHz, log scale)", color=INK_PRIMARY, fontsize=10)
    ax.set_xlabel("Energy threshold", color=INK_PRIMARY, fontsize=10)
    ax.set_title("Muon background rate vs. threshold", color=INK_PRIMARY, fontsize=12, pad=14)
    style_axes(ax, log=True)
    ax.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    fig.tight_layout()
    fig.savefig(output, facecolor=SURFACE)
    plt.close(fig)


def plot_split(thresholds, values, columns, total_col, output, split_at=None):
    n = len(thresholds)
    split_at = split_at if split_at is not None else n // 2
    split_at = max(1, min(n - 1, split_at))

    slices = [slice(0, split_at), slice(split_at, n)]
    fig, axes = plt.subplots(
        1, 2, figsize=(9, 5), dpi=150,
        gridspec_kw={"width_ratios": [split_at, n - split_at]},
    )
    fig.patch.set_facecolor(SURFACE)

    for ax, sl in zip(axes, slices):
        sub_thresholds = thresholds[sl]
        sub_values = {name: vals[sl] for name, vals in values.items()}
        x = list(range(len(sub_thresholds)))
        stacked_bars(ax, x, sub_thresholds, sub_values, columns, label_total_col=total_col)
        ax.set_xticks(x)
        ax.set_xticklabels(sub_thresholds, color=INK_PRIMARY, fontsize=9)
        style_axes(ax)

    axes[0].set_ylabel("Rate (MHz)", color=INK_PRIMARY, fontsize=10)
    fig.supxlabel("Energy threshold", color=INK_PRIMARY, fontsize=10)
    fig.suptitle("Muon background rate vs. threshold", color=INK_PRIMARY, fontsize=12)
    axes[1].legend(loc="upper right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    fig.tight_layout()
    fig.savefig(output, facecolor=SURFACE)
    plt.close(fig)


PLOTTERS = {"linear": plot_linear, "log": plot_log, "split": plot_split}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input", nargs="?", default="2026_readme.txt",
        help="readme txt file to parse (default: %(default)s)",
    )
    parser.add_argument(
        "--mode", choices=sorted(PLOTTERS), default="log",
        help="plot mode: log-scale grouped bars, split-panel stacked bars, "
             "or single-panel linear stacked bars (default: %(default)s)",
    )
    parser.add_argument(
        "--split-at", type=int, default=None,
        help="number of leading thresholds in the first panel, --mode split only "
             "(default: half)",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="output PNG path (default: <input stem>_rates_<mode>.png)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_rates_{args.mode}.png")

    thresholds, values = parse_readme(input_path)
    columns = {s: pick_column(values, s) for s in SERIES}
    total_col = pick_column(values, "total")

    if args.mode == "split":
        plot_split(thresholds, values, columns, total_col, output_path, split_at=args.split_at)
    else:
        PLOTTERS[args.mode](thresholds, values, columns, total_col, output_path)
    print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
