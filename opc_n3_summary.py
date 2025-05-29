# pip install pandas

"""
OPC-N3 particle counter – summarise counts per size bin and basic climate stats.
"""

import argparse
from pathlib import Path
from datetime import timedelta
import sys
import pandas as pd


BIN_PREFIX = "Bin"
TEMP_KEYS = ("temperature", "temp")
HUM_KEYS = ("humidity", "hum", "rh")


def detect_skip(file_path: Path, fallback: int = 14) -> int:
    """Return number of header lines to skip so that `Bin0` is the first field."""
    with file_path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if line.strip().lower() == "data:":
                return i + 1
    return fallback


def extract_boundaries(lines: list[str]) -> list[float]:
    """Extract Boundary_um values from header lines."""
    for line in lines:
        if line.startswith("Boundary_um"):
            return list(map(float, line.strip().split(",")[1:]))
    raise RuntimeError(
        "Boundary_um line not found – cannot determine size bins.")


def make_size_labels(boundaries: list[float]) -> list[str]:
    """Return one label per bin (closed intervals only)."""
    return [
        f"[{boundaries[i]:.3f} – {boundaries[i + 1]:.3f}) µm"
        for i in range(len(boundaries) - 1)
    ]


def find_column(df: pd.DataFrame, keys: tuple[str, ...]) -> str | None:
    """Return first column whose name contains any of `keys` (case-insensitive)."""
    lowered = {c.lower(): c for c in df.columns}
    for key in keys:
        for col_lc, original in lowered.items():
            if key in col_lc:
                return original
    return None


def aggregate(file_path: Path, skip: int | None) -> tuple[pd.DataFrame, dict]:
    """Return (size-bin summary, climate stats dict)."""
    if skip is None:
        skip = detect_skip(file_path)

    with file_path.open(encoding="utf-8") as fh:
        header_lines = [next(fh) for _ in range(skip)]

    boundaries = extract_boundaries(header_lines)
    size_labels = make_size_labels(boundaries)

    df = pd.read_csv(file_path, skiprows=skip, header=0)
    bin_cols = [c for c in df.columns if str(c).startswith(BIN_PREFIX)]
    if not bin_cols:
        raise RuntimeError("No Bin* columns found – wrong --skip value?")

    totals = df[bin_cols].sum().astype(int)
    bin_summary = pd.DataFrame(
        {"size_range": size_labels, "total_count": totals})

    stats: dict[str, float | int | str] = {}
    stats["entries"] = len(df)
    stats["runtime"] = str(timedelta(seconds=stats["entries"]))

    temp_col = find_column(df, TEMP_KEYS)
    if temp_col:
        stats["temp_min"] = df[temp_col].min()
        stats["temp_max"] = df[temp_col].max()
        stats["temp_mean"] = df[temp_col].mean()

    hum_col = find_column(df, HUM_KEYS)
    if hum_col:
        stats["hum_min"] = df[hum_col].min()
        stats["hum_max"] = df[hum_col].max()
        stats["hum_mean"] = df[hum_col].mean()

    return bin_summary, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise total particle counts per size bin from OPC-N3 CSV."
    )
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--out", "-o", type=Path)
    parser.add_argument(
        "--skip",
        "-s",
        type=int,
        default=None,
        help="Header lines to skip (default: auto).",
    )
    args = parser.parse_args()

    summary, stats = aggregate(args.input_csv, args.skip)

    print("\nGesamtsummen pro Größen-Bin:\n")
    print(summary.to_string(index=False))

    print("\nZusatzinformationen:")
    print(f"  Messpunkte gesamt  : {stats['entries']}")
    print(f"  Laufzeit (1000 ms) : {stats['runtime']}")
    if "temp_min" in stats:
        print(
            f"  Temperatur [°C]    : min {stats['temp_min']:.2f} │ "
            f"max {stats['temp_max']:.2f} │ Ø {stats['temp_mean']:.2f}"
        )
    if "hum_min" in stats:
        print(
            f"  Luftfeuchte [%]    : min {stats['hum_min']:.2f} │ "
            f"max {stats['hum_max']:.2f} │ Ø {stats['hum_mean']:.2f}"
        )

    if args.out:
        summary.to_csv(args.out, index=False)
        print(f"\nErgebnis gespeichert in: {args.out.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(1)
