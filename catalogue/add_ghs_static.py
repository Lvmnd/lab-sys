# -*- coding: utf-8 -*-
"""
add_ghs_static.py
Future University LIMS — Static GHS Hazard Data
Applies known GHS classifications directly — no API needed.
Run: python add_ghs_static.py
"""
from __future__ import print_function
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(HERE, "lab_sys_master_catalogue_enriched.xlsx")
OUTPUT_FILE = os.path.join(HERE, "lab_sys_master_catalogue_enriched.xlsx")

# Static GHS data for common lab chemicals
# Format: "Chemical Name": ("H-codes", "Pictograms", "Storage")
GHS_DATA = {
    # ── SOLVENTS & ACIDS ─────────────────────────────────────
    "Acetic Acid glacial":      ("H226, H314",          "Flammable, Corrosive",         "Flammable cabinet"),
    "Acetic Acid 96%":          ("H226, H314",          "Flammable, Corrosive",         "Flammable cabinet"),
    "Acetic Anhydride":         ("H226, H314, H332",    "Flammable, Corrosive, Harmful","Flammable cabinet"),
    "Acetone":                  ("H225, H319, H336",    "Flammable, Irritant",          "Flammable cabinet"),
    "Chloroform":               ("H302, H315, H351",    "Harmful, Health Hazard",       "Cold, dark storage"),
    "HCl":                      ("H290, H314, H335",    "Corrosive",                    "Acid cabinet"),
    "Hydrochloric Acid 32%":    ("H290, H314, H335",    "Corrosive",                    "Acid cabinet"),
    "Hydrochloric Acid 37%":    ("H290, H314, H335",    "Corrosive",                    "Acid cabinet"),
    "Ethanol 70%":              ("H225, H319",          "Flammable, Irritant",          "Flammable cabinet"),
    "Ethanol 96%":              ("H225, H319",          "Flammable, Irritant",          "Flammable cabinet"),
    "Ethanol Absolute":         ("H225, H319",          "Flammable, Irritant",          "Flammable cabinet"),
    "Ethanol/Isopropanol":      ("H225, H319, H336",    "Flammable, Irritant",          "Flammable cabinet"),
    "Isopropanol":              ("H225, H319, H336",    "Flammable, Irritant",          "Flammable cabinet"),
    "1-Propanol":               ("H225, H315, H319",    "Flammable, Irritant",          "Flammable cabinet"),
    "Methanol":                 ("H225, H301, H311, H331, H370", "Flammable, Toxic",    "Flammable cabinet"),
    "n-Hexane":                 ("H225, H304, H315, H361", "Flammable, Harmful",        "Flammable cabinet"),
    "Benzene":                  ("H225, H304, H315, H340, H350", "Flammable, Carcinogen","Flammable cabinet"),
    "Cyclohexane":              ("H225, H304, H315, H336", "Flammable, Harmful",        "Flammable cabinet"),
    "Dichloromethane":          ("H315, H319, H335, H351", "Irritant, Health Hazard",   "Cold, dark storage"),
    "Dichlormethane":           ("H315, H319, H335, H351", "Irritant, Health Hazard",   "Cold, dark storage"),
    "Formic Acid 98-100%":      ("H226, H302, H314, H331", "Flammable, Corrosive, Toxic","Acid cabinet"),
    "Iso-Octane":               ("H225, H304, H315, H336", "Flammable, Harmful",        "Flammable cabinet"),
    "cis-decahydronapthalene 99%": ("H226, H304, H315", "Flammable, Harmful",           "Flammable cabinet"),
    # ── BASES ────────────────────────────────────────────────
    "NaOH":                     ("H290, H314",          "Corrosive",                    "Base cabinet"),
    "Ammonia Solution 25%":     ("H221, H280, H314, H331, H400", "Toxic, Corrosive, Environmental","Ventilated cabinet"),
    "Ammonium Hydroxide Solution": ("H221, H314, H331", "Corrosive, Toxic",             "Ventilated cabinet"),
    "Barium Hydroxide octahydrate": ("H302, H332",      "Harmful",                      "Dry storage"),
    # ── OXIDIZERS ────────────────────────────────────────────
    "Hydrogen Peroxide 30%":    ("H271, H302, H314, H335", "Oxidizing, Corrosive",      "Cold, ventilated"),
    "Ammonium Nitrate":         ("H271, H302, H400",    "Oxidizing, Harmful",           "Oxidizer cabinet"),
    "Ammonium PeroxodiSulfate": ("H272, H302, H315, H317, H319, H334", "Oxidizing, Sensitizer","Dry, cool storage"),
    "APS (Ammonium Persulfate)":("H272, H302, H315, H317, H334", "Oxidizing, Sensitizer","Dry, cool storage"),
    # ── TOXIC / HIGH HAZARD ──────────────────────────────────
    "Mercury (II) Chloride":    ("H290, H300, H310, H330, H373, H400, H410", "Toxic, Environmental","Locked toxic cabinet"),
    "Mercury (II) Iodide":      ("H300, H310, H330, H373, H410", "Toxic, Environmental","Locked toxic cabinet"),
    "Hydrofluoric Acid 40%":    ("H280, H300, H310, H314, H330, H372", "Toxic, Corrosive","Locked acid cabinet"),
    "Benzene":                  ("H225, H304, H315, H340, H350", "Flammable, Carcinogen","Locked flammable cabinet"),
    "Ethidium bromide alternatif": ("H302, H341, H361","Harmful, Mutagen",              "Locked toxic cabinet"),
    "TRIzol reagent":           ("H225, H315, H319, H331", "Flammable, Irritant, Toxic","Flammable cabinet"),
    "beta-Mercaptoethanol":     ("H225, H301, H310, H330, H400", "Toxic, Flammable, Environmental","Flammable cabinet"),
    "BORON TRIFLUORIDE-METHANOL COMPLEX ( 20": ("H225, H290, H301, H314, H330", "Toxic, Corrosive", "Flammable cabinet"),
    # ── IRRITANTS / LOW HAZARD ───────────────────────────────
    "NaCl":                     ("H319",                "Irritant",                     "Room temperature"),
    "Glucose":                  ("",                    "Non-hazardous",                "Room temperature"),
    "Sucrose":                  ("",                    "Non-hazardous",                "Room temperature"),
    "Lactose":                  ("",                    "Non-hazardous",                "Room temperature"),
    "Glycerol":                 ("H315, H319",          "Irritant",                     "Room temperature"),
    "Glycine":                  ("H315, H319, H335",    "Irritant",                     "Room temperature"),
    "Agarose":                  ("H315, H319, H335",    "Irritant",                     "Room temperature"),
    "Agar powder":              ("",                    "Non-hazardous",                "Room temperature"),
    "Agarose (Low electroendoosmosis)": ("H315, H319", "Irritant",                      "Room temperature"),
    "Agarose (medium electroendoosmosis)": ("H315, H319", "Irritant",                   "Room temperature"),
    "Agarose Elektroforesis":   ("H315, H319",          "Irritant",                     "Room temperature"),
    "Peptone":                  ("H315, H319, H335",    "Irritant",                     "Room temperature"),
    "Yeast extract":            ("",                    "Non-hazardous",                "Room temperature"),
    "Beef extract":             ("",                    "Non-hazardous",                "Room temperature"),
    "LB agar":                  ("",                    "Non-hazardous",                "Room temperature"),
    "LB broth":                 ("",                    "Non-hazardous",                "Room temperature"),
    "Nutrient agar":            ("",                    "Non-hazardous",                "Room temperature"),
    "Nutrient broth":           ("",                    "Non-hazardous",                "Room temperature"),
    "Tris-HCl buffer":          ("H315, H319",          "Irritant",                     "Room temperature"),
    "PBS buffer":               ("",                    "Non-hazardous",                "Room temperature"),
    "TAE/TBE buffer":           ("H315, H319",          "Irritant",                     "Room temperature"),
    "MgCl2":                    ("H302, H318",          "Harmful, Irritant",            "Dry storage"),
    "SDS":                      ("H228, H302, H311, H319, H335", "Flammable, Harmful",  "Dry, cool storage"),
    "dodecyl-Sulfate Sodium Salt": ("H228, H302, H311, H319, H335", "Flammable, Harmful","Dry, cool storage"),
    "Acrylamide/Bis":           ("H301, H311, H331, H340, H350, H372", "Toxic, Carcinogen","Locked toxic cabinet"),
    "TEMED (Tetramethylethylenediamine": ("H225, H302, H312, H314, H332", "Flammable, Corrosive","Flammable cabinet"),
    "Coomassie stain":          ("H226, H319",          "Flammable, Irritant",          "Flammable cabinet"),
    "Crystal violet":           ("H302, H318, H373, H411", "Harmful, Environmental",    "Dry storage"),
    "Methylene blue":           ("H302, H319, H373",    "Harmful",                      "Dry storage"),
    "Safranin":                 ("H302, H319",          "Harmful, Irritant",            "Dry storage"),
    "Iodine solution":          ("H312, H332, H400",    "Harmful, Environmental",       "Dark storage"),
    "Iodine Resublimed":        ("H312, H332, H400",    "Harmful, Environmental",       "Dark storage"),
    "Gram iodine":              ("H312, H332, H400",    "Harmful, Environmental",       "Dark storage"),
    "Benedict reagent":         ("H302, H315, H319",    "Harmful, Irritant",            "Room temperature"),
    "Biuret reagent":           ("H290, H314",          "Corrosive",                    "Base cabinet"),
    "Crystal violet indicator": ("H302, H318, H373, H411", "Harmful, Environmental",    "Dry storage"),
    "Folin-Ciocalteu's Phenol Reagent": ("H302, H312, H314, H332", "Corrosive, Harmful","Acid cabinet"),
    "Follin-ciocalteu's phenol reagent": ("H302, H312, H314, H332", "Corrosive, Harmful","Acid cabinet"),
    # ── SALTS & BUFFERS ──────────────────────────────────────
    "Ammonium Acetate":         ("H302, H332",          "Harmful",                      "Dry storage"),
    "Ammonium Chloride":        ("H302, H318, H332",    "Harmful",                      "Dry storage"),
    "Ammonium Sulfate":         ("H302",                "Harmful",                      "Dry storage"),
    "Barium Chloride dihydrate":("H301, H332",          "Toxic",                        "Locked toxic cabinet"),
    "Calcium Carbonate":        ("H319",                "Irritant",                     "Dry storage"),
    "Calcium Chloride":         ("H302, H318",          "Harmful",                      "Dry storage"),
    "Citric Acid monohydrate":  ("H315, H319",          "Irritant",                     "Room temperature"),
    "Copper (II) Sulfate anhydrous": ("H302, H318, H400, H410", "Harmful, Environmental","Dry storage"),
    "Hydrochloric Acid 32%":    ("H290, H314, H335",    "Corrosive",                    "Acid cabinet"),
    "Iron (II) Sulfate Heptahydrate": ("H302, H318",   "Harmful",                      "Dry storage"),
    "Magnesium Sulfate heptahydrate": ("H319",          "Irritant",                     "Dry storage"),
    "Potassium Chloride":       ("H319",                "Irritant",                     "Dry storage"),
    "Sodium Carbonate":         ("H319, H335",          "Irritant",                     "Dry storage"),
    "Sulfuric Acid":            ("H290, H314",          "Corrosive",                    "Acid cabinet"),
    "Boric Acid":               ("H360FD",              "Reproductive Toxin",           "Locked toxic cabinet"),
    "Benzoic Acid":             ("H302, H312, H332",    "Harmful",                      "Dry storage"),
}

def apply_ghs(df, name_col):
    matched, unmatched = 0, 0
    for col in ["ghs_hazard_codes", "ghs_pictograms", "storage_condition"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].astype(object)

    for idx in df.index:
        name = str(df.at[idx, name_col]).strip()
        if name in GHS_DATA:
            h, pic, storage = GHS_DATA[name]
            df.at[idx, "ghs_hazard_codes"]  = h
            df.at[idx, "ghs_pictograms"]    = pic
            df.at[idx, "storage_condition"] = storage
            matched += 1
        else:
            # Default storage for items we know are safe
            sto = df.at[idx, "storage_condition"]
            if pd.isna(sto) or sto == "":
                df.at[idx, "storage_condition"] = "Room temperature"
            unmatched += 1
    return df, matched, unmatched

def main():
    print("=" * 60)
    print("  Future University LIMS — Static GHS Patch")
    print("=" * 60)
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
    result = {}

    print("\n[Sheet 1] Master Catalogue")
    df1 = sheets.get("Master Catalogue", pd.DataFrame()).copy()
    if not df1.empty:
        df1, m, u = apply_ghs(df1, "Item Name")
        result["Master Catalogue"] = df1
        print("  Matched: {} | Unmatched: {}".format(m, u))

    print("\n[Sheet 2] Reagent Master")
    df2 = sheets.get("Reagent Master", pd.DataFrame()).copy()
    if not df2.empty:
        df2, m, u = apply_ghs(df2, "Reagent/Chemical Name")
        result["Reagent Master"] = df2
        print("  Matched: {} | Unmatched: {}".format(m, u))

    if "Summary & Gaps" in sheets:
        result["Summary & Gaps"] = sheets["Summary & Gaps"]

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sname, df in result.items():
            df.to_excel(writer, sheet_name=sname, index=False)

    print("\n  Saved: {}".format(os.path.basename(OUTPUT_FILE)))
    print("  Done! storage_condition column also added.")
    print("=" * 60)

if __name__ == "__main__":
    main()
