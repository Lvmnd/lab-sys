"""
seed_catalogue.py — Future University LIMS
Management command to import master catalogue from Excel into PostgreSQL
Run: py -3 manage.py seed_catalogue
"""

import os
import uuid
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.needs.models import CatalogueItem

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


CATALOGUE_FILE = Path(__file__).resolve().parents[5] / \
    "catalogue" / "lab_sys_master_catalogue_enriched.xlsx"

UNIT_NORMALIZE = {
    "nan": "pcs", "": "pcs", "NaN": "pcs",
    "Pcs": "pcs", "PCS": "pcs",
    "Btl": "bottle", "BTL": "bottle",
    "Box": "box", "BOX": "box",
    "Set": "set", "SET": "set",
    "Unit": "unit", "UNIT": "unit",
    "Lembar": "sheet",
    "Buah": "pcs",
    "Pasang": "pair",
}

CATEGORY_NORMALIZE = {
    "chemical":        "Chemical",
    "chemicals":       "Chemical",
    "reagent":         "Reagent",
    "reagent/chemical":"Reagent",
    "glassware":       "Glassware",
    "instrument":      "Instrument",
    "consumable":      "Consumable",
    "consumables":     "Consumable",
    "equipment":       "Equipment",
    "equipment/tools": "Equipment",
    "furniture":       "Furniture",
    "ppe":             "PPE",
    "other":           "Other",
}


def clean_str(val, default=""):
    if val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "") else s


def normalize_unit(val):
    s = clean_str(val, "pcs")
    return UNIT_NORMALIZE.get(s, s.lower())


def normalize_category(val):
    s = clean_str(val, "Other").lower()
    return CATEGORY_NORMALIZE.get(s, "Other")


def make_item_code(category, index):
    prefix_map = {
        "Chemical":   "CHEM",
        "Reagent":    "REAG",
        "Glassware":  "GLAS",
        "Instrument": "INST",
        "Consumable": "CONS",
        "Equipment":  "EQUP",
        "Furniture":  "FURN",
        "PPE":        "PPE",
        "Other":      "OTHR",
    }
    prefix = prefix_map.get(category, "ITEM")
    return f"{prefix}-{str(index).zfill(4)}"


class Command(BaseCommand):
    help = "Seed CatalogueItem table from lab_sys_master_catalogue_enriched.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, default=str(CATALOGUE_FILE),
            help='Path to the enriched catalogue Excel file'
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing catalogue items before seeding'
        )

    def handle(self, *args, **options):
        if not HAS_PANDAS:
            self.stderr.write("pandas not installed. Run: pip install pandas openpyxl")
            return

        file_path = Path(options['file'])
        if not file_path.exists():
            self.stderr.write(f"File not found: {file_path}")
            self.stderr.write(f"Expected at: {CATALOGUE_FILE}")
            return

        if options['clear']:
            count = CatalogueItem.objects.count()
            CatalogueItem.objects.all().delete()
            self.stdout.write(f"  Cleared {count} existing items.")

        self.stdout.write("=" * 60)
        self.stdout.write("  Future University LIMS — Catalogue Seeder")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Reading: {file_path.name}")

        created = 0
        skipped = 0
        errors  = 0
        index   = CatalogueItem.objects.count() + 1

        # ── SHEET 1: Master Catalogue ──────────────────────
        self.stdout.write("\n[Sheet 1] Master Catalogue")
        try:
            df1 = pd.read_excel(file_path, sheet_name="Master Catalogue", header=0)
            for _, row in df1.iterrows():
                name = clean_str(row.get("Item Name"))
                if not name:
                    continue
                category = normalize_category(row.get("category", "Other"))
                unit     = normalize_unit(row.get("unit", "pcs"))
                code     = make_item_code(category, index)

                # Skip duplicates by name
                if CatalogueItem.objects.filter(common_name__iexact=name).exists():
                    skipped += 1
                    continue

                try:
                    CatalogueItem.objects.create(
                        item_code         = code,
                        common_name       = name,
                        iupac_name        = clean_str(row.get("iupac_name")),
                        cas_number        = clean_str(row.get("cas_number")),
                        molecular_formula = clean_str(row.get("molecular_formula")),
                        molecular_weight  = clean_str(row.get("molecular_weight")),
                        category          = category,
                        unit              = unit,
                        ghs_hazard_codes  = clean_str(row.get("ghs_hazard_codes")),
                        ghs_pictograms    = clean_str(row.get("ghs_pictograms")),
                        storage_condition = clean_str(row.get("storage_condition"), "Room temperature"),
                        study_programs    = "",
                        is_active         = True,
                    )
                    created += 1
                    index   += 1
                    self.stdout.write(f"  + {code}  {name[:50]}")
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  ERROR: {name[:40]} — {e}")

        except Exception as e:
            self.stderr.write(f"  Could not read Sheet 1: {e}")

        # ── SHEET 2: Reagent Master ────────────────────────
        self.stdout.write("\n[Sheet 2] Reagent Master")
        try:
            df2 = pd.read_excel(file_path, sheet_name="Reagent Master", header=0)
            for _, row in df2.iterrows():
                name = clean_str(row.get("Reagent/Chemical Name"))
                if not name:
                    continue
                category = "Reagent"
                unit     = normalize_unit(row.get("unit", "pcs"))
                code     = make_item_code(category, index)

                if CatalogueItem.objects.filter(common_name__iexact=name).exists():
                    skipped += 1
                    continue

                try:
                    CatalogueItem.objects.create(
                        item_code         = code,
                        common_name       = name,
                        iupac_name        = clean_str(row.get("iupac_name")),
                        cas_number        = clean_str(row.get("cas_number")),
                        molecular_formula = clean_str(row.get("molecular_formula")),
                        molecular_weight  = clean_str(row.get("molecular_weight")),
                        category          = category,
                        unit              = unit,
                        ghs_hazard_codes  = clean_str(row.get("ghs_hazard_codes")),
                        ghs_pictograms    = clean_str(row.get("ghs_pictograms")),
                        storage_condition = clean_str(row.get("storage_condition"), "Room temperature"),
                        study_programs    = "",
                        is_active         = True,
                    )
                    created += 1
                    index   += 1
                    self.stdout.write(f"  + {code}  {name[:50]}")
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  ERROR: {name[:40]} — {e}")

        except Exception as e:
            self.stderr.write(f"  Could not read Sheet 2: {e}")

        # ── SUMMARY ───────────────────────────────────────
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"  Created : {created}")
        self.stdout.write(f"  Skipped : {skipped} (duplicates)")
        self.stdout.write(f"  Errors  : {errors}")
        self.stdout.write(f"  Total in DB: {CatalogueItem.objects.count()}")
        self.stdout.write("=" * 60)
        self.stdout.write("  Done! Open /admin/ to verify catalogue items.")
