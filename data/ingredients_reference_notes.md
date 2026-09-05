# Ingredient reference — gaps for manual follow-up

25 rows in `ingredients_reference.csv`, covering all 13 requested active families. CAS numbers and
functions come from CosIng-sourced web results (CosmeticObs, CosIng Checker, SpecialChem citing CosIng)
and PubChem, cross-checked where a direct CosIng page render wasn't reachable via search. Not a live
CosIng database export — verify against https://ec.europa.eu/growth/tools-databases/cosing/ before citing
in anything graded on primary-source accuracy.

## Well covered (CAS + function reasonably solid)
Vitamin C family, Niacinamide, Salicylic Acid, AHAs (Glycolic/Lactic/Mandelic), Benzoyl Peroxide,
Azelaic Acid, Hyaluronic Acid/Sodium Hyaluronate, Alpha-Arbutin, Tranexamic Acid, Kojic Acid, Retinol,
Retinyl Palmitate.

## Weak / needs manual research
- **Ceramide EOP and Ceramide AP** — could not find verified CAS numbers this session. Only Ceramide NP
  has a solid CAS/PubChem hit. These two rows are left with blank CAS/source — team should pull them
  directly from CosIng or an INCI supplier spec sheet (e.g. Evonik/Croda ceramide complex datasheets).
- **Peptides (Copper Peptides / Copper Tripeptide-1)** — this family is intentionally broad per the task
  brief. Only Palmitoyl Pentapeptide-4 (Matrixyl) got a solid, individually-verified entry. Copper peptide
  row is a category-level placeholder with no CAS — if the catalogue actually stocks a copper-peptide
  product, look up the specific named ingredient (usually "Copper Tripeptide-1") on CosIng directly.
- **Retinaldehyde** — CAS/PubChem identity is solid, but I could not confirm its CosIng functional
  category label directly (marked "reported, not separately confirmed").
- **Adapalene** — included only as a labeling note per the brief. It is a prescription/OTC drug active,
  not a CosIng cosmetic ingredient, so it has no CosIng function or standard cosmetic CAS classification.
  Do not treat it as equivalent to the other rows in a RAG index — flag it differently if it shows up on
  a product label (it implies drug-monograph status, not cosmetic-only).
- **Benzoyl Peroxide** — CosIng lists it, but its primary regulatory function is acne-drug-adjacent
  (antimicrobial/keratolytic) rather than a typical cosmetic function; noted in the function field rather
  than left blank.

## Suggested next step if time allows
Spot-check the "reported, not separately confirmed" and blank-CAS rows directly against the CosIng portal
search UI (search box takes INCI name) since search-engine summaries of CosIng pages can lag the live
database.
