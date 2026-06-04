# -*- coding: utf-8 -*-
"""
enrich_catalogue.py
Future University — Integrated Laboratory LIMS
Enriches master catalogue with global standard data from PubChem API
Run: python enrich_catalogue.py
"""

import pandas as pd
import requests
import time
import json
from pathlib import Path

CATALOGUE_FILE = Path(__file__).parent / "lab_sys_master_catalogue.xlsx"
OUTPUT_FILE = Path(__file__).parent / "lab_sys_master_catalogue_enriched.xlsx"
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

CHEMICAL_CATEGORIES = {"Chemical", "Reagent", "Reagent/Chemical"}

def get_pubchem_data(name: str) -> dict:
    """Query PubChem for CAS, IUPAC name, formula, molecular weight, GHS hazards."""
    result = {
        "cas_number": "",
        "iupac_name": "",
        "molecular_formula": "",
        "molecular_weight": "",
        "ghs_hazard_codes": "",
        "ghs_pictograms": "",
        "pubchem_cid": "",
        "pubchem_verified": False
    }
    try:
        # Step 1: Get CID from name
        search_url = f"{PUBCHEM_URL}/compound/name/{requests.utils.quote(name)}/cids/JSON"
        r = requests.get(search_url, timeout=8)
        if r.status_code != 200:
            return result
        cids = r.json().get("IdentifierList", {}).get("CID", [])
        if not cids:
            return result
        cid = cids[0]
        result["pubchem_cid"] = str(cid)

        # Step 2: Get compound properties
        props = "IUPACName,MolecularFormula,MolecularWeight"
        prop_url = f"{PUBCHEM_URL}/compound/cid/{cid}/property/{props}/JSON"
        r2 = requests.get(prop_url, timeout=8)
        if r2.status_code == 200:
            p = r2.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            result["iupac_name"] = p.get("IUPACName", "")
            result["molecular_formula"] = p.get("MolecularFormula", "")
            result["molecular_weight"] = str(p.get("MolecularWeight", ""))

        # Step 3: Get CAS number from synonyms
        syn_url = f"{PUBCHEM_URL}/compound/cid/{cid}/synonyms/JSON"
        r3 = requests.get(syn_url, timeout=8)
        if r3.status_code == 200:
            synonyms = r3.json().get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
            for syn in synonyms:
                if syn.replace("-", "").replace(" ", "").isdigit() or (
                    len(syn.split("-")) == 3 and all(p.isdigit() for p in syn.split("-"))
                ):
                    result["cas_number"] = syn
                    break

        # Step 4: Get GHS hazard codes
        ghs_url = f"{PUBCHEM_URL}/compound/cid/{cid}/JSON"
        r4 = requests.get(ghs_url, timeout=10)
        if r4.status_code == 200:
            full_data = r4.json()
            sections = full_data.get("Record", {}).get("Section", [])
            hazard_codes = []
            pictograms = []
            for section in sections:
                if "Safety" in section.get("TOCHeading", ""):
                    for sub in section.get("Section", []):
                        if "GHS" in sub.get("TOCHeading", ""):
                            for subsub in sub.get("Section", []):
                                heading = subsub.get("TOCHeading", "")
                                info = subsub.get("Information", [])
                                if "Hazard" in heading and "Statement" in heading:
                                    for item in info:
                                        for val in item.get("Value", {}).get("StringWithMarkup", []):
                                            text = val.get("String", "")
                                            codes = [w for w in text.split() if w.startswith("H") and len(w) == 4 and w[1:].isdigit()]
                                            hazard_codes.extend(codes)
                                if "Pictogram" in heading:
                                    for item in info:
                                        for val in item.get("Value", {}).get("StringWithMarkup", []):
                                            pic = val.get("String", "")
                                            if pic:
                                                pictograms.append(pic)
            result["ghs_hazard_codes"] = ", ".join(sorted(set(hazard_codes)))
            result["ghs_pictograms"] = ", ".join(sorted(set(pictograms)))

        result["pubchem_verified"] = True
        return result

    except Exception as e:
        return result


def enrich_sheet(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    """Add PubChem columns to a dataframe."""
    new_cols = ["cas_number","iupac_name","molecular_formula",
                "molecular_weight","ghs_hazard_codes","ghs_pictograms","pubchem_cid","pubchem_verified"]
    for col in new_cols:
        if col == "pubchem_verified":
            df[col] = False
        else:
            df[col] = ""

    chemical_mask = df["category"].isin(CHEMICAL_CATEGORIES) if "category" in df.columns else pd.Series([True]*len(df))
    chemicals = df[chemical_mask]
    total = len(chemicals)
    print(f"  Found {total} chemical items to enrich...")

    for idx, (row_idx, row) in enumerate(chemicals.iterrows()):
        name = str(row[name_col]).strip()
        print(f"  [{idx+1}/{total}] {name[:50]}", end=" ... ", flush=True)
        data = get_pubchem_data(name)
        for col in new_cols:
            df.at[row_idx, col] = data[col]
        status = "[found]" if data["pubchem_verified"] else "[not found]"
        cas = f"CAS: {data['cas_number']}" if data["cas_number"] else ""
        print(f"{status} {cas}")
        time.sleep(0.3)  # Respect PubChem rate limit

    return df


def main():
    print("=" * 60)
    print("Future University LIMS — PubChem Catalogue Enrichment")
    print("=" * 60)

    if not CATALOGUE_FILE.exists():
        print(f"ERROR: File not found: {CATALOGUE_FILE}")
        print("Make sure lab_sys_master_catalogue.xlsx is in the same folder.")
        return

    print(f"\nReading: {CATALOGUE_FILE.name}")
    enriched_sheets = {}

    # Sheet 1: Master Catalogue (headers on row 2)
    print("\n[Sheet 1] Master Catalogue")
    df1 = pd.read_excel(CATALOGUE_FILE, sheet_name="Master Catalogue", header=2)
    if not df1.empty:
        enriched_sheets["Master Catalogue"] = enrich_sheet(df1.copy(), "Item Name")
    
    # Sheet 2: Reagent Master (headers on row 2)
    print("\n[Sheet 2] Reagent Master")
    df2 = pd.read_excel(CATALOGUE_FILE, sheet_name="Reagent Master", header=2)
    if not df2.empty:
        df2["category"] = "Reagent/Chemical"
        enriched_sheets["Reagent Master"] = enrich_sheet(df2.copy(), "Reagent/Chemical Name")

    # Sheet 3: pass through unchanged (no header offset)
    if "Summary & Gaps" in pd.ExcelFile(CATALOGUE_FILE).sheet_names:
        df3 = pd.read_excel(CATALOGUE_FILE, sheet_name="Summary & Gaps", header=None)
        enriched_sheets["Summary & Gaps"] = df3

    # Save
    print(f"\nSaving enriched catalogue to: {OUTPUT_FILE.name}")
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, df in enriched_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print("\nDone! Open lab_sys_master_catalogue_enriched.xlsx to see results.")
    print(f"  Saved to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()