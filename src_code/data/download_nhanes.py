"""
NHANES Multi-Cycle Downloader -- LMSIS Project
==============================================
Downloads NHANES 2017-2018 (J) and pre-pandemic 2019-March 2020 (P) data.

CRITICAL DISCOVERY (verified 2026-06-11):
  The 2019-2020 NHANES cycle was SUSPENDED mid-collection due to COVID-19.
  CDC released the partial 2019-March 2020 data as a pre-pandemic (P_) dataset.
  It is NOT hosted at a '2019' URL with '_K' suffixes -- those URLs return 404.

  Correct files: P_DEMO.xpt, P_LUX.xpt, P_INS.xpt etc.
  Correct base URL: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/
  (Same server as J cycle -- co-released as a 4-year combined dataset)

  Dissertation framing (use this exactly):
    "The model was trained on NHANES 2017-2018 (cycle J). Evaluation on the
     NHANES 2019-March 2020 pre-pandemic partial release constitutes a temporal
     out-of-distribution test. Data collection was suspended in March 2020
     due to COVID-19; CDC released the partial dataset as P_-prefixed files."

Weight pooling:
  For combined J+P analysis: adjusted_weight = WTMEC2YR / 2
  (CDC multi-cycle recommendation for 4-year pooled analysis)

XPT validation:
  CDC sometimes returns HTML error pages instead of XPT files.
  This downloader validates the first 8 bytes (XPT magic header)
  before accepting any file. Corrupted stubs are deleted and re-downloaded.
"""
import urllib.request
import urllib.error
import os
import time
import pandas as pd
import numpy as np

# -- XPT magic bytes (first 8 bytes of a valid SAS XPORT file) ---------------
XPT_MAGIC = b"HEADER R"

CYCLE_MAP = {
    "J": {
        "label": "2017-2018",
        "base_url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles",
        "files": {
            "DEMO":   "DEMO_J.xpt",
            "BMX":    "BMX_J.xpt",
            "BIOPRO": "BIOPRO_J.xpt",
            "GLU":    "GLU_J.xpt",
            "INS":    "INS_J.xpt",
            "TRIGLY": "TRIGLY_J.xpt",
            "HDL":    "HDL_J.xpt",
            "LUX":    "LUX_J.xpt",
            "CBC":    "CBC_J.xpt",
        },
        "weight_var": "WTMEC2YR",
        "stratum_offset": 0,
    },
    "P": {
        # Pre-pandemic partial cycle: 2019-March 2020
        # P_ prefix files, hosted on same 2017 DataFiles server as J cycle.
        # Verified 2026-06-11: all P_ URLs return valid XPT (magic bytes confirmed).
        "label": "2019-Mar2020 (pre-pandemic partial)",
        "base_url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles",
        "files": {
            "DEMO":   "P_DEMO.xpt",
            "BMX":    "P_BMX.xpt",
            "BIOPRO": "P_BIOPRO.xpt",
            "GLU":    "P_GLU.xpt",
            "INS":    "P_INS.xpt",
            "TRIGLY": "P_TRIGLY.xpt",
            "HDL":    "P_HDL.xpt",
            "LUX":    "P_LUX.xpt",
            "CBC":    "P_CBC.xpt",
        },
        "weight_var": "WTMECPRP",   # Confirmed: pre-pandemic MEC weight (WTMEC2YR absent in P_DEMO)
        # Offset SDMVSTRA by 100 to prevent PSU/stratum ID collision
        # when combining J and P cycles into a single survey design object.
        "stratum_offset": 100,
    },
}

# Number of cycles being pooled -- used for weight adjustment
N_CYCLES = len(CYCLE_MAP)


def _is_valid_xpt(path: str) -> bool:
    """Check the first 8 bytes for the XPT magic header."""
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        return header == XPT_MAGIC
    except Exception:
        return False


def _download_file(url: str, local_path: str, max_retries: int = 3) -> bool:
    """
    Download a file with retry logic and XPT validation.
    Returns True on success, False if the file cannot be retrieved.
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Downloading (attempt {attempt}): {url}")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (NHANES Research Download)"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp, \
                 open(local_path, "wb") as out:
                out.write(resp.read())

            if _is_valid_xpt(local_path):
                size_kb = os.path.getsize(local_path) // 1024
                print(f"  [OK] Saved {os.path.basename(local_path)} ({size_kb} KB)")
                return True
            else:
                print(f"  [FAIL] Invalid XPT (probably HTML error page). Removing.")
                os.remove(local_path)

        except urllib.error.HTTPError as e:
            print(f"  [FAIL] HTTP {e.code}: {url}")
        except urllib.error.URLError as e:
            print(f"  [FAIL] URL error: {e.reason}")
        except Exception as e:
            print(f"  [FAIL] Unexpected error: {e}")

        if attempt < max_retries:
            time.sleep(2 ** attempt)  # exponential backoff

    return False


def download_cycle(cycle_key: str, raw_dir: str) -> dict:
    """
    Download all files for one NHANES cycle.
    Returns dict: {module_name: local_path_or_None}
    """
    cfg = CYCLE_MAP[cycle_key]
    print(f"\n{'='*60}")
    print(f"Cycle {cycle_key} ({cfg['label']})")
    print(f"{'='*60}")

    results = {}
    for module, filename in cfg["files"].items():
        local_path = os.path.join(raw_dir, filename)

        # If file exists and is valid, skip download
        if os.path.exists(local_path) and _is_valid_xpt(local_path):
            size_kb = os.path.getsize(local_path) // 1024
            print(f"  [cached] {filename} ({size_kb} KB)")
            results[module] = local_path
            continue

        # If file exists but is invalid (corrupted stub), remove it
        if os.path.exists(local_path) and not _is_valid_xpt(local_path):
            print(f"  [corrupt] {filename} -- removing stale stub and re-downloading")
            os.remove(local_path)

        url = f"{cfg['base_url']}/{filename}"
        ok = _download_file(url, local_path)
        results[module] = local_path if ok else None

    return results


def merge_cycle_files(cycle_key: str, file_map: dict) -> pd.DataFrame | None:
    """
    Merge all downloaded XPT files for one cycle on SEQN.
    Returns merged DataFrame with 'cycle' column and pooled weight column.
    """
    cfg = CYCLE_MAP[cycle_key]
    df_merged = None
    for module, path in file_map.items():
        if path is None or not os.path.exists(path):
            print(f"  [skip] {module} -- file unavailable")
            continue
        try:
            df_temp = pd.read_sas(path)
            print(f"  Merged {module}: {len(df_temp)} rows, {len(df_temp.columns)} cols")
            if df_merged is None:
                df_merged = df_temp
            else:
                # Outer join: preserve participants even if they lack some files
                df_merged = pd.merge(df_merged, df_temp, on="SEQN", how="outer",
                                     suffixes=("", f"_{module}"))
        except Exception as e:
            print(f"  [error] Could not read {module} ({path}): {e}")

    if df_merged is None:
        return None

    df_merged["cycle"] = cycle_key

    # -- Pooled survey weight (CDC multi-cycle recommendation) ----------------
    # For a combined 4-year (J + P) analysis:
    #   adjusted_weight = WTMEC2YR / n_cycles (= WTMEC2YR / 2)
    weight_var = cfg["weight_var"]
    if weight_var in df_merged.columns:
        df_merged["WTMEC_POOLED"] = df_merged[weight_var] / N_CYCLES
    else:
        print(f"  [warn] Weight variable '{weight_var}' not found in cycle {cycle_key}")
        df_merged["WTMEC_POOLED"] = np.nan

    # -- Fix SDMVSTRA collision across cycles ---------------------------------
    # PSU/stratum IDs can overlap between survey cycles.
    # Standard fix: offset the later cycle's strata by 100 to ensure uniqueness
    # in combined survey design objects (e.g. R survey package or statsmodels).
    offset = cfg.get("stratum_offset", 0)
    if offset > 0 and "SDMVSTRA" in df_merged.columns:
        df_merged["SDMVSTRA"] = df_merged["SDMVSTRA"] + offset

    return df_merged


def download_and_merge(output_dir: str | None = None) -> dict:
    """
    Main entry point. Downloads both cycles, merges within each cycle,
    saves per-cycle CSVs, and saves a combined CSV for OOD evaluation.

    Returns dict with keys: 'j', 'p', 'combined' -> DataFrames (or None).
    """
    base_dir = os.path.dirname(__file__)
    raw_dir = os.path.join(base_dir, "raw_data")
    os.makedirs(raw_dir, exist_ok=True)

    if output_dir is None:
        output_dir = base_dir

    results = {}
    cycle_dfs = {}

    for cycle_key in ["J", "P"]:
        file_map = download_cycle(cycle_key, raw_dir)
        df_cycle = merge_cycle_files(cycle_key, file_map)

        if df_cycle is not None:
            out_path = os.path.join(output_dir, f"raw_nhanes_{cycle_key.lower()}.csv")
            df_cycle.to_csv(out_path, index=False)
            print(f"\n  Saved cycle {cycle_key}: {len(df_cycle)} rows -> {out_path}")
            cycle_dfs[cycle_key] = df_cycle
            results[cycle_key.lower()] = df_cycle
        else:
            print(f"\n  [ERROR] Cycle {cycle_key} produced no data.")
            results[cycle_key.lower()] = None

    # -- Combined dataset (J + P) ---------------------------------------------
    dfs_to_combine = [df for df in cycle_dfs.values() if df is not None]
    if len(dfs_to_combine) == 2:
        df_combined = pd.concat(dfs_to_combine, ignore_index=True)
        out_combined = os.path.join(output_dir, "raw_nhanes_merged.csv")
        df_combined.to_csv(out_combined, index=False)
        print(f"\n  Combined dataset: {len(df_combined)} rows -> {out_combined}")
        j_n = len(cycle_dfs.get("J", []))
        p_n = len(cycle_dfs.get("P", []))
        print(f"  Cycle breakdown: J={j_n}, P={p_n}")
        results["combined"] = df_combined
    elif len(dfs_to_combine) == 1:
        key = list(cycle_dfs.keys())[0]
        df_combined = cycle_dfs[key]
        out_combined = os.path.join(output_dir, "raw_nhanes_merged.csv")
        df_combined.to_csv(out_combined, index=False)
        print(f"\n  Only cycle {key} available. Saved as merged.")
        results["combined"] = df_combined
    else:
        print("\n  [FATAL] No cycle data available.")
        results["combined"] = None

    return results


if __name__ == "__main__":
    print("NHANES 2017-2020 Multi-Cycle Downloader")
    print("=========================================")
    results = download_and_merge()

    # -- Post-download diagnostic ---------------------------------------------
    print("\n\n--- Post-Download Diagnostic ---")
    for key in ["j", "p", "combined"]:
        df = results.get(key)
        if df is not None:
            cap_col = "LUXCAPM"
            n_cap = df[cap_col].notna().sum() if cap_col in df.columns else 0
            n_bmi_normal = 0
            if "BMXBMI" in df.columns:
                n_bmi_normal = ((df["BMXBMI"] >= 18.5) & (df["BMXBMI"] <= 24.9)).sum()
            print(f"  Cycle {key.upper()}: n={len(df)}, normal-BMI={n_bmi_normal}, "
                  f"with CAP={n_cap}")
        else:
            print(f"  Cycle {key.upper()}: NO DATA")
