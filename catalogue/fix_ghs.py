"""
fix_ghs.py
Future University LIMS — GHS Hazard Code Patch
Reads enriched catalogue, re-fetches only GHS data using correct PubChem endpoint
Run: python fix_ghs.py
"""

import pandas as pd
import requests
import time
import json
from pathlib import Path

INPUT_FILE     = Path(__file__).parent / "lab_sys_master_catalogue_enriched.xlsx"
OUTPUT_FILE    = Path(__file__).parent / "lab_sys_master_catalogue_enriched.xlsx"
CHECKPOINT_FILE= Path(__file__).parent / "ghs_checkpoint.json"
PUBCHEM_URL    = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
DELAY = 0.4

GHS_PICTOGRAM_MAP = {
    "GHS01": "Explosive",
    "GHS02": "Flammable",
    "GHS03": "Oxidizing",
    "GHS04": "Compressed Gas",
    "GHS05": "Corrosive",
    "GHS06": "Toxic",
    "GHS07": "Irritant/Harmful",
    "GHS08": "Health Hazard",
    "GHS09": "Environmental Hazard",
}

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {}

def save_checkpoint(data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_ghs_by_cid(cid: str) -> tuple:
    """Fetch GHS hazard statements and pictograms using correct PubChem path."""
    hazard_codes, pictograms = [], []
    try:
        # Correct endpoint: safety and hazards section
        url = f"{PUBCHEM_URL}/compound/cid/{cid}/property/IUPACName/JSON"
        # Use the GHS classification via the compound heading
        ghs_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=GHS+Classification"
        r = requests.get(ghs_url, timeout=12)
        if r.status_code != 200:
            return "", ""
        
        data = r.json()
        record = data.get("Record", {})
        
        def walk(node):
            if isinstance(node, dict):
                heading = node.get("TOCHeading", "")
                info_list = node.get("Information", [])
                
                if "Hazard Statements" in heading:
                    for info in info_list:
                        for markup in info.get("Value", {}).get("StringWithMarkup", []):
                            text = markup.get("String", "")
                            # Extract H-codes like H301, H302 etc
                            for word in text.split():
                                w = word.strip(".,;:()")
                                if len(w) == 4 and w[0] == "H" and w[1:].isdigit():
                                    hazard_codes.append(w)
                
                if "Pictogram" in heading:
                    for info in info_list:
                        for markup in info.get("Value", {}).get("StringWithMarkup", []):
                            for extra in markup.get("Markup", []):
                                extra_val = extra.get("Extra", "")
                                if extra_val.startswith("GHS"):
                                    code = extra_val[:5]
                                    label = GHS_PICTOGRAM_MAP.get(code, code)
                                    pictograms.append(label)
                
                for val in node.values():
                    if isinstance(val, (dict, list)):
                        walk(val)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        
        walk(record)
        
    except Exception:
        pass
    
    h_codes = ", ".join(sorted(set(hazard_codes)))
    pics    = ", ".join(sorted(set(pictograms)))
    return h_codes, pics


def process_sheet(df: pd.DataFrame, name_col: str, sheet_key: str, checkpoint: dict) -> pd.DataFrame:
    if "ghs_hazard_codes" not in df.columns:
        df["ghs_hazard_codes"] = ""
    if "ghs_pictograms" not in df.columns:
        df["ghs_pictograms"] = ""

    # Ensure GHS columns are object type (they may be float64 from Excel NaN)
    for col in ["ghs_hazard_codes", "ghs_pictograms"]:
        if col in df.columns:
            df[col] = df[col].astype(object)
        else:
            df[col] = ""

    done = checkpoint.get(sheet_key, {})
    for idx in df.index:
        name = str(df.at[idx, name_col]).strip()
        if name in done:
            df.at[idx, "ghs_hazard_codes"] = done[name]["ghs_hazard_codes"]
            df.at[idx, "ghs_pictograms"]   = done[name]["ghs_pictograms"]

    # Find items with a CID but no GHS data yet
    todo = []
    for idx in df.index:
        name = str(df.at[idx, name_col]).strip()
        cid  = str(df.at[idx, "pubchem_cid"]).strip() if "pubchem_cid" in df.columns else ""
        already_done = name in done
        has_cid = cid and cid not in ("", "nan", "0")
        if has_cid and not already_done:
            todo.append((idx, name, cid))

    total_done = len(done)
    total = total_done + len(todo)
    print(f"  Already done: {total_done} | Remaining: {len(todo)}")

    for i, (idx, name, cid) in enumerate(todo):
        print(f"  [{total_done+i+1}/{total}] {name[:50]}", end=" ... ", flush=True)
        h_codes, pics = get_ghs_by_cid(cid)
        df.at[idx, "ghs_hazard_codes"] = h_codes
        df.at[idx, "ghs_pictograms"]   = pics

        if sheet_key not in checkpoint:
            checkpoint[sheet_key] = {}
        checkpoint[sheet_key][name] = {"ghs_hazard_codes": h_codes, "ghs_pictograms": pics}
        save_checkpoint(checkpoint)

        result = h_codes if h_codes else "no GHS data"
        print(result[:60])
        time.sleep(DELAY)

    return df


def main():
    print("=" * 62)
    print("  Future University LIMS — GHS Hazard Patch")
    print("=" * 62)

    checkpoint = load_checkpoint()
    if checkpoint:
        total_done = sum(len(v) for v in checkpoint.values())
        print(f"  Resuming — {total_done} items already patched")

    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
    result = {}

    print("\n[Sheet 1] Master Catalogue")
    df1 = sheets.get("Master Catalogue", pd.DataFrame()).copy()
    if not df1.empty:
        result["Master Catalogue"] = process_sheet(df1, "Item Name", "s1", checkpoint)

    print("\n[Sheet 2] Reagent Master")
    df2 = sheets.get("Reagent Master", pd.DataFrame()).copy()
    if not df2.empty:
        result["Reagent Master"] = process_sheet(df2, "Reagent/Chemical Name", "s2", checkpoint)

    if "Summary & Gaps" in sheets:
        result["Summary & Gaps"] = sheets["Summary & Gaps"]

    print(f"\nSaving -> {OUTPUT_FILE.name}")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sname, df in result.items():
            df.to_excel(writer, sheet_name=sname, index=False)

    # Quick stats
    df_check = result.get("Reagent Master", pd.DataFrame())
    if not df_check.empty and "ghs_hazard_codes" in df_check.columns:
        filled = (df_check["ghs_hazard_codes"].astype(str).str.strip() != "").sum()
        print(f"\n  GHS codes filled: {filled}/{len(df_check)} reagents")

    print("  Done! Delete ghs_checkpoint.json to start fresh next time.")
    print("=" * 62)

if __name__ == "__main__":
    main()