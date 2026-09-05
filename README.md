# SkincareMVP

Planning and data workspace for the BITSoM "AI in Business" midterm project: a
skincare-compatibility assistant built on [myAI6](https://github.com/dringel/myAI6).

**This is not the graded submission repo.** The assignment requires the
submission repo to be created by importing myAI6 directly (private, with
`dringel` added as collaborator). This repo holds the team's planning docs and
the sourced data pulled ahead of ingestion, so that work isn't lost before the
real submission repo is set up.

## Contents

- `Skincare_Compatibility_Assistant_Project_Plan.docx` — the team's original project plan
- `BUILD-GUIDE.md` — phased walkthrough of standing up a myAI6-based assistant
- `myAI6/` — unmodified reference copy of the template (git history stripped; see the [upstream repo](https://github.com/dringel/myAI6) for that)
- `scripts/` — data-pull scripts (Open Beauty Facts puller)
- `data/` — sourced datasets for the knowledge base, see table below

## Data pulled so far

| File | Rows | Source | Notes |
|---|---|---|---|
| `products_clean.csv` | 622 | Open Beauty Facts | 45 curated brands + full India-tagged sweep, real INCI lists |
| `ingredients_reference.csv` | 25 | CosIng + PubChem | Normalized actives, CAS numbers, all 13 target active families |
| `cir_evidence.csv` | 12 | Cosmetic Ingredient Review | Family-level safety findings, 3 correctly marked out of CIR's scope |
| `cir_evidence_variants.csv` | 11 | CIR | Variant/INCI-name-level safety findings |
| `compatibility_evidence.csv` | 23 | PubMed / PMC | Real studies per ingredient-pair, 3 honestly marked insufficient evidence |
| `regulatory_gapfill.csv` | 3 | FDA / EU | Binding regulatory data for actives CIR doesn't cover |
| `pubchem_safety.csv` | 25 | PubChem | GHS hazard data per ingredient, with bulk-vs-topical caveats |
| `obf_raw/` | — | Open Beauty Facts | Raw API responses per brand, kept for audit/re-runs |

Known issues to resolve before ingestion: India-native D2C brands (Mamaearth,
Plum, WOW, Dot & Key, Minimalist) are essentially absent from Open Beauty
Facts; several CIR entries are search-snippet-derived and need a manual
spot-check; PubChem hazard flags describe the bulk chemical, not diluted
cosmetic use, and must be framed that way in the assistant's prompts; Kojic
Acid carries an EU H351 hazard code worth a team decision.
