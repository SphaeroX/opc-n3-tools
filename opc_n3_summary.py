# pip install pandas

"""
OPC-N3 particle counter – summarise counts per size bin and basic climate stats.
"""

import argparse
from pathlib import Path
from datetime import timedelta
import sys
import os # Added for clear_console
import pandas as pd
from time import sleep
try:
    from usbiss.spi import SPI
    import opcng as opc
    USBISS_AVAILABLE = True
except ImportError:
    USBISS_AVAILABLE = False
    # Define placeholder classes for SPI and opc to allow CSV mode if libraries are missing
    class SPI: # type: ignore
        def __init__(self, com_port: str): pass
        mode = 1; max_speed_hz = 500000; lsbfirst = False # type: ignore

    class OPCN3Placeholder: # type: ignore
        def info(self): return "N/A (libs missing)"
        def serial(self): return "N/A (libs missing)"
        def firmware(self): return "N/A (libs missing)"
        def on(self): print("Placeholder: Sensor ON (libs missing)")
        def off(self): print("Placeholder: Sensor OFF (libs missing)")
        def histogram(self): print("Placeholder: Reading histogram (libs missing)"); return {}

    class opc: # type: ignore
        @staticmethod
        def detect(spi_bus_ignored): # type: ignore
            raise RuntimeError("Sensor libraries (pyusbiss, py-opc-ng) not installed. Cannot use live data mode.")


BIN_PREFIX = "Bin"
DEFAULT_LIVE_DATA_BIN_LABELS = [f"Bin {i}" for i in range(24)] # OPC-N3 has 24 bins
TEMP_KEYS = ("temperature", "temp")
HUM_KEYS = ("humidity", "hum", "rh")
ANSI_RED = "41"
ANSI_YELLOW = "43"
ANSI_GREEN = "42"
RESET = "\033[0m"


def decile_counts(df: pd.DataFrame, bin_col: str) -> list[int]:
    """Return list with 10 sums of `bin_col`, one per 10-% segment of df."""
    n = len(df)
    step = max(1, n // 10)
    return [
        df[bin_col].iloc[i: i + step].sum()
        for i in range(0, n, step)
    ][:10]                               # exactly 10 elements


def colour_block(ratio: float) -> str:
    """Green <0.33, Yellow 0.33-0.66, Red >0.66."""
    if ratio > 0.66:
        code = ANSI_RED
    elif ratio > 0.33:
        code = ANSI_YELLOW
    else:
        code = ANSI_GREEN
    return f"\033[{code}m  {RESET}"      # two-space block


def timeline_bar(counts: list[int]) -> str:
    """Return coloured 10-block bar for one size bin."""
    if not counts or max(counts) == 0:
        return " " * 20                  # blank if no data
    maxc = max(counts)
    return "".join(colour_block(c / maxc) for c in counts)


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
    """Return one label per bin (closed intervals only), max 24 labels."""
    # Max 24 bins for OPC-N3 typically.
    num_labels = min(len(boundaries) - 1, 24)
    return [
        f"[{boundaries[i]:.3f} – {boundaries[i + 1]:.3f}) µm"
        for i in range(num_labels)
    ]


def find_column(df: pd.DataFrame, keys: tuple[str, ...]) -> str | None:
    """Return first column whose name contains any of `keys` (case-insensitive)."""
    lowered = {c.lower(): c for c in df.columns}
    for key in keys:
        for col_lc, original in lowered.items():
            if key in col_lc:
                return original
    return None


def aggregate(file_path: Path, skip: int | None) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Return (size-bin summary, climate stats dict)."""
    if skip is None:
        skip = detect_skip(file_path)

    # Initialize output_size_labels with default "Bin 0" to "Bin 23"
    output_size_labels = [f"{BIN_PREFIX}{i}" for i in range(24)] # Uses "Bin0", "Bin1" (no space)

    try:
        with file_path.open(encoding="utf-8") as fh:
            header_lines = [next(fh) for _ in range(skip)]
        boundaries = extract_boundaries(header_lines)
        csv_size_labels = make_size_labels(boundaries) # Capped at 24 by make_size_labels

        # Override default labels with what we found from CSV header
        for i in range(len(csv_size_labels)):
            if i < 24:
                output_size_labels[i] = csv_size_labels[i]
        # If csv_size_labels has fewer than 24, remaining output_size_labels stay as "BinX"
    except RuntimeError as e: # Specifically for extract_boundaries or make_size_labels issues
        print(f"Warning: Could not determine size bin labels from CSV header ({e}). Using default '{BIN_PREFIX}N' labels.", file=sys.stderr)
    except FileNotFoundError: # Reraise if file not found, so main can handle it.
        raise
    except Exception as e: # Catch other potential errors during header processing
        print(f"Warning: Error processing CSV header for size labels ({e}). Using default '{BIN_PREFIX}N' labels.", file=sys.stderr)

    df = pd.read_csv(file_path, skiprows=skip, header=0)

    # Determine bin_cols_to_process from df: "Bin 0" through "Bin 23" that actually exist
    bin_cols_to_process = []
    # Standardized keys for totals_series (used for lookup later)
    standardized_keys_for_totals = []

    for i in range(24):
        # Prefer "BinN" (no space, matching DEFAULT_LIVE_DATA_BIN_LABELS)
        col_name_no_space = f"{BIN_PREFIX}{i}"
        col_name_with_space = f"{BIN_PREFIX} {i}" # Common in some CSVs or OPC outputs

        actual_col_in_df = None
        standard_key = col_name_no_space # Key for totals_series should be standardized

        if col_name_no_space in df.columns and pd.api.types.is_numeric_dtype(df[col_name_no_space]):
            actual_col_in_df = col_name_no_space
        elif col_name_with_space in df.columns and pd.api.types.is_numeric_dtype(df[col_name_with_space]):
            actual_col_in_df = col_name_with_space

        if actual_col_in_df:
            bin_cols_to_process.append(actual_col_in_df)
            standardized_keys_for_totals.append(standard_key) # Store the key we'll use for this column's total

    totals_series = pd.Series(dtype='int')
    if bin_cols_to_process:
        # Sum using actual column names found, then re-index with standardized keys
        raw_totals = df[bin_cols_to_process].sum().astype(int)
        # Ensure raw_totals.index matches bin_cols_to_process before creating dictionary for reindexing
        totals_dict_for_reindex = {}
        for idx, actual_col_name in enumerate(bin_cols_to_process):
            if idx < len(standardized_keys_for_totals): # Should always be true
                 totals_dict_for_reindex[standardized_keys_for_totals[idx]] = raw_totals.get(actual_col_name, 0)
        totals_series = pd.Series(totals_dict_for_reindex)


    # Construct bin_summary DataFrame (must have 24 rows)
    total_counts_for_summary = []
    for i in range(24):
        lookup_key = f"{BIN_PREFIX}{i}" # Standard key "Bin0", "Bin1"
        total_counts_for_summary.append(totals_series.get(lookup_key, 0))

    bin_summary = pd.DataFrame({
        "size_range": output_size_labels, # Should be 24 display labels
        "total_count": total_counts_for_summary
    })
    if len(bin_summary) != 24: # Should not happen with current logic
        print(f"Warning: aggregate produced bin_summary with {len(bin_summary)} rows, expected 24.", file=sys.stderr)


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

    return bin_summary, stats, df


def clear_console():
    """Clears the terminal screen."""
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')
    # A more universal ANSI escape sequence method (might not work on all terminals e.g. basic Windows cmd)
    # print('[H[J', end='')


# Modify existing read_live_data function
def read_live_data(com_port_value: str, num_readings: int = 60, update_interval_secs: int = 1) -> pd.DataFrame:
    # Ensure imports for SPI, opc, pd, process_live_data, print_summary_and_timeline, clear_console, DEFAULT_LIVE_DATA_BIN_LABELS, BIN_PREFIX are available in scope.
    # For simplicity, assume they are globally accessible or imported.

    if not USBISS_AVAILABLE:
        # This check is technically redundant if main() already checks USBISS_AVAILABLE before calling,
        # but kept for safety if the function is ever called directly.
        raise RuntimeError("Critical: USBISS_AVAILABLE is False but execution reached read_live_data.")

    print(f"Attempting to connect to sensor on {com_port_value}...")
    spi_bus = SPI(com_port_value)
    spi_bus.mode = 1
    spi_bus.max_speed_hz = 500000
    spi_bus.lsbfirst = False

    dev = opc.detect(spi_bus)

    print(f'Device information: {dev.info()}')
    print(f'Serial: {dev.serial()}')

    firmware_version_str = "N/A"
    try:
        firmware_version_str = dev.firmware()
    except AttributeError:
        print("Note: dev.firmware() not found. Attempting dev.serial() for firmware version as fallback.")
        try:
            firmware_version_str = dev.serial()
        except AttributeError:
            print("Note: dev.serial() also not found for firmware version.")
    except Exception as e:
        print(f"Error accessing firmware version: {e}")
    print(f'Firmware version: {firmware_version_str}')

    live_data_list = []
    print(f"Powering on sensor. Preparing for {num_readings} total readings.")
    print(f"Display will update every {update_interval_secs} second(s). Press Ctrl+C to stop early.")
    dev.on()

    try:
        for i in range(num_readings):
            sleep(1) # Sleep for 1 second for each reading attempt
            data = dev.histogram()

            if data:
                live_data_list.append(data)
            else:
                print(f"\nWarning: Received empty data on reading {i+1}/{num_readings}", flush=True)
                sleep(0.5)

            if (i + 1) % update_interval_secs == 0 or (i + 1) == num_readings:
                if not live_data_list:
                    print("No data collected yet to display...", end='\r', flush=True)
                    continue

                clear_console()
                print(f"--- LIVE DATA VIEW (Reading {i+1}/{num_readings}) --- Press Ctrl+C to stop ---")

                current_df = pd.DataFrame(live_data_list)
                summary_df, stats, processed_df = process_live_data(current_df)

                bin_cols_for_timeline = [col for col in processed_df.columns if col.startswith(BIN_PREFIX)]

                print_summary_and_timeline(summary_df, stats, processed_df, bin_cols_for_timeline, is_live_data=True)
                print(f"\nLast reading: {i+1}/{num_readings}. Total data points: {len(live_data_list)}.")
                if (i + 1) == num_readings:
                    print("All live readings complete. Preparing final summary...")
                    sleep(2) # Pause to see the last live update

        print(" " * 80, end='\r', flush=True) # Clear any leftover progress line

    except KeyboardInterrupt:
        print("\nLive reading interrupted by user. Processing collected data for final summary...")
    finally:
        print("\nPowering off sensor...")
        dev.off()
        print("Sensor powered off.")

    if not live_data_list:
        print("No valid data collected from the sensor during live mode.")
        return pd.DataFrame()

    return pd.DataFrame(live_data_list)


def process_live_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Processes a DataFrame from live sensor readings to generate summary and stats."""
    if df.empty:
        # Return empty structures if no data, ensuring bin_summary matches expected 24 rows for consistency
        # if DEFAULT_LIVE_DATA_BIN_LABELS is used downstream without checking for emptiness.
        # However, print_summary_and_timeline handles empty summary_df.
        # For strictness, let's create a 24-row summary with 0 counts if df is empty.
        actual_bin_labels_for_empty = DEFAULT_LIVE_DATA_BIN_LABELS[:24]
        empty_bin_summary = pd.DataFrame({
            "size_range": actual_bin_labels_for_empty,
            "total_count": [0] * len(actual_bin_labels_for_empty)
        })
        return empty_bin_summary, {"entries": 0, "runtime": "0s"}, df

    # 1. Identify all potential bin columns from df and sort them
    potential_bin_cols = []
    for col in df.columns:
        if col.startswith(BIN_PREFIX):
            try:
                # Extract number for sorting, assuming format "Bin X"
                bin_num_str = col[len(BIN_PREFIX):].strip()
                if bin_num_str.isdigit():
                    potential_bin_cols.append((int(bin_num_str), col))
            except ValueError:
                # Column starts with BIN_PREFIX but isn't like "Bin X"
                pass # Ignore if not a parsable bin number
    potential_bin_cols.sort() # Sort by bin number

    # 2. Filter for Bins 0-23 that actually exist in df
    processed_bin_cols = []
    for bin_num, col_name in potential_bin_cols:
        if 0 <= bin_num <= 23:
            if col_name in df.columns: # Ensure column actually exists
                 processed_bin_cols.append(col_name)
        # Bins > 23 are ignored for bin_summary

    # 3. Define Output Bin Labels (always Bin 0-23)
    # Ensure DEFAULT_LIVE_DATA_BIN_LABELS provides at least 24 labels, or adjust.
    # Assuming DEFAULT_LIVE_DATA_BIN_LABELS is ["Bin 0", "Bin 1", ..., "Bin 23", ...]
    actual_bin_labels = DEFAULT_LIVE_DATA_BIN_LABELS[:24]

    # 4. Calculate Totals Series for processed_bin_cols
    totals_series = pd.Series(dtype='int') # Default to empty series
    if processed_bin_cols: # Only sum if there are relevant columns
        # Ensure we only try to sum columns that are actually in the DataFrame and numeric
        numeric_cols_to_sum = [col for col in processed_bin_cols if pd.api.types.is_numeric_dtype(df[col])]
        if numeric_cols_to_sum:
            totals_series = df[numeric_cols_to_sum].sum().astype(int)
        # totals_series will have an index like ["Bin 0", "Bin 1", ...] for columns that were summed

    # 5. Construct bin_summary DataFrame (must have 24 rows)
    total_counts_for_summary = []
    for label in actual_bin_labels: # e.g., "Bin 0", "Bin 1", ... "Bin 23"
        if label in totals_series.index:
            total_counts_for_summary.append(totals_series[label])
        else:
            total_counts_for_summary.append(0)

    bin_summary = pd.DataFrame({
        "size_range": actual_bin_labels,
        "total_count": total_counts_for_summary
    })

    # 6. Stats Calculation (remains unchanged, uses original full df)
    stats: dict[str, float | int | str] = {}
    stats["entries"] = len(df)
    # Estimate runtime: assume 1 reading per second, from num_readings in read_live_data
    # This is an approximation; 'Sampling Period' in histogram could be more accurate if summed.
    # For now, let's use the number of entries (which corresponds to num_readings).
    stats["runtime"] = str(timedelta(seconds=stats["entries"])) # type: ignore

    temp_col = find_column(df, TEMP_KEYS) # TEMP_KEYS = ("temperature", "temp")
    if temp_col and temp_col in df.columns and not df[temp_col].empty:
        stats["temp_min"] = df[temp_col].min()
        stats["temp_max"] = df[temp_col].max()
        stats["temp_mean"] = df[temp_col].mean()

    hum_col = find_column(df, HUM_KEYS) # HUM_KEYS = ("humidity", "hum", "rh")
    if hum_col and hum_col in df.columns and not df[hum_col].empty:
        stats["hum_min"] = df[hum_col].min()
        stats["hum_max"] = df[hum_col].max()
        stats["hum_mean"] = df[hum_col].mean()

    # The third element returned by aggregate is the original df, used by decile_counts
    return bin_summary, stats, df


def print_summary_and_timeline(summary_df: pd.DataFrame,
                               stats: dict,
                               data_df: pd.DataFrame, # This is the raw data (processed_df from main)
                               is_live_data: bool = False):
    """Prints the summary, statistics, and timeline bar for particle data (Bins 0-23)."""
    print("\nGesamtsummen pro Größen-Bin:\n")

    # summary_df is guaranteed to have 24 rows by process_live_data and aggregate
    for i in range(len(summary_df)): # Should be 24 iterations
        display_label = summary_df.iloc[i]["size_range"]
        total = summary_df.iloc[i]["total_count"]

        # Data for timeline bar is fetched from data_df.
        # `opc.histogram()` keys are 'Bin 0', 'Bin 1', ... (with a space).
        # `process_live_data` uses these directly, so data_df from live data has "Bin X" columns.
        # `aggregate` needs to ensure its `df` (which becomes data_df) also provides these.
        # The `bin_cols_to_process` in `aggregate` finds actual column names,
        # but `data_df` needs to be queryable by a standard "Bin X" name for this loop.
        # The `data_df` passed here IS the raw df from CSV or live_df.
        # So we need to check for "Bin X" (with space) and "BinX" (no space) in it.

        data_col_name_with_space = f"{BIN_PREFIX} {i}" # e.g. "Bin 0"
        data_col_name_no_space = f"{BIN_PREFIX}{i}"   # e.g. "Bin0"

        bar = " " * 20 # Default empty bar
        actual_data_col_for_timeline = None

        if data_col_name_with_space in data_df.columns:
            actual_data_col_for_timeline = data_col_name_with_space
        elif data_col_name_no_space in data_df.columns:
            actual_data_col_for_timeline = data_col_name_no_space

        if actual_data_col_for_timeline and not data_df[actual_data_col_for_timeline].empty:
            counts10 = decile_counts(data_df, actual_data_col_for_timeline)
            bar = timeline_bar(counts10)
        elif actual_data_col_for_timeline: # Column exists but is empty/all-NaN
             bar = " (no data in col) "
        # else: bar remains the default empty bar if column not found.

        print(f"{str(display_label):<22} {total:8d} {bar}")

    print("\nZusatzinformationen:")
    if stats.get("entries", 0) == 0:
        print("  Keine Datenpunkte vorhanden.") # No data points
        if is_live_data:
            print("  Sensor hat möglicherweise keine Daten geliefert oder es gab ein Verbindungsproblem.")
        else: # CSV
            print("  Die CSV-Datei enthält möglicherweise keine Datenzeilen oder hat ein unerwartetes Format.")
        return # Don't print other stats if no entries

    print(f"  Messpunkte gesamt  : {stats.get('entries', 'N/A')}")
    print(f"  Laufzeit           : {stats.get('runtime', 'N/A')}") # Changed from "Laufzeit (1000 ms)"

    if "temp_min" in stats: # Check if temp stats are available
        print(
            f"  Temperatur [°C]    : min {stats['temp_min']:.2f} │ "
            f"max {stats['temp_max']:.2f} │ Ø {stats['temp_mean']:.2f}"
        )
    else:
        print("  Temperatur [°C]    : N/A")

    if "hum_min" in stats: # Check if humidity stats are available
        print(
            f"  Luftfeuchte [%]    : min {stats['hum_min']:.2f} │ "
            f"max {stats['hum_max']:.2f} │ Ø {stats['hum_mean']:.2f}"
        )
    else:
        print("  Luftfeuchte [%]    : N/A")

    # Output file saving is specific to CSV mode in the original script.
    # We can pass args to this function if we want to keep that, or handle it in main.
    # For now, this function only prints.


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarise total particle counts per size bin from OPC-N3 CSV."
    )
    # Modify input_csv argument
    parser.add_argument("input_csv", type=Path, nargs='?', default=None,
                        help="Input CSV file path (optional if COM port is specified).")
    # Add com_port argument
    parser.add_argument("--com_port", "-c", type=str, default=None,
                        help="COM port for live data acquisition (optional if input CSV is specified).")
    parser.add_argument("--out", "-o", type=Path)
    parser.add_argument(
        "--skip",
        "-s",
        type=int,
        default=None,
        help="Header lines to skip (default: auto).",
    )
    args = parser.parse_args()

    # Add validation logic
    if args.input_csv is None and args.com_port is None:
        parser.error("Error: Either an input CSV file or a COM port must be specified.")

    if args.input_csv is not None and args.com_port is not None:
        parser.error("Error: Please specify either an input CSV file or a COM port, not both.")

    if args.com_port and not USBISS_AVAILABLE:
        parser.error("Sensor libraries (pyusbiss, py-opc-ng) must be installed to use the --com_port option.")

    # Conditional processing based on input type
    if args.com_port:
        try:
            # Removed the first, seemingly redundant call to read_live_data.
            # The main call is below for full_live_df.
            print("Starting live data acquisition mode with iterative display...")
            # num_readings can be made an argument to the script later if desired
            # For now, use a fixed number, e.g., 30 for 30 seconds.
            # update_interval_secs=1 means update every second.
            # The `read_live_data` itself now handles the KeyboardInterrupt for stopping.
            full_live_df = read_live_data(args.com_port, num_readings=30, update_interval_secs=1)

            clear_console() # Clear the last live update screen
            print("--- FINAL SUMMARY OF LIVE DATA ---")
            if full_live_df.empty:
                print("No data was collected during the live session.")
                # process_live_data now returns a 24-row empty summary
                summary_df, stats, processed_df = process_live_data(pd.DataFrame())
                print_summary_and_timeline(summary_df, stats, processed_df, is_live_data=True)
            else:
                print(f"Total data points collected: {len(full_live_df)}")
                # Process the full dataset for the final summary
                summary_df, stats, processed_df = process_live_data(full_live_df)
                print_summary_and_timeline(summary_df, stats, processed_df, is_live_data=True)

        except RuntimeError as e:
            # This will catch errors from sensor connection primarily
            # clear_console() # Optional: clear before error message
            print(f"Error during live data session: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # clear_console() # Optional
            print(f"An unexpected error occurred during live data session: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.input_csv:
        # Current CSV processing logic
        print(f"Starting CSV processing for: {args.input_csv}")
        summary_df, stats, processed_df = aggregate(args.input_csv, args.skip) # processed_df is the raw df from csv

        print_summary_and_timeline(summary_df, stats, processed_df, is_live_data=False)

        if args.out:
            summary_df.to_csv(args.out, index=False) # Use summary_df
            print(f"\nErgebnis gespeichert in: {args.out.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Use parser.error for argument validation errors to show usage
        if isinstance(exc, SystemExit) and exc.code == 2: # argparse errors exit with code 2
            pass # Already handled by argparse
        else:
            print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(1)
