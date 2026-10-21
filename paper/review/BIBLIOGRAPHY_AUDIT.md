# Bibliography audit (final manuscript review, 2026-10-21)

## Summary
- `references.bib` now has 36 entries, all cited. The two uncited entries (`berthet2025`, `coron2024rej`) were removed, and no duplicates were found.
- All citations and cross-references compile: 0 undefined citations or references in the final log.
- No missing field was invented. Fields that could not be confirmed are left out and listed below.
- The header comment of `references.bib` previously claimed that "every field" had been checked against a primary source or publisher metadata. That overstated the verification and was replaced by an accurate description pointing to this file.

## Changes in this review

| entry | change | source of the added field |
|---|---|---|
| `camacho2026hope` | added pages 272–295 and DOI 10.46586/tches.v2026.i2.272-295 | Tampere University research portal and repository records (two consistent records; also matches `validation/NOVELTY_REVIEW.md`) |
| `danvers2023` | added DOI 10.1109/TC.2022.3197074 | imec publication repository record (volume, issue and pages agree) |
| `hermelink2024` | added pages 2430–2444 | DBLP record for CCS 2024 (the ePrint version lists three authors; the CCS version lists four, as in the bib) |
| `berthet2025`, `coron2024rej` | removed (not cited) | — |
| header comment | rewritten (no "every field verified" claim) | — |

## Verification level per entry

| level | entries |
|---|---|
| **A: locally held full text** | Checked in the Phase XIV novelty statement (`final/FINAL_NOVELTY_STATEMENT.md`): `coron2023dil`, `coron2023poly`, `bos2021masking`, `azouaoui2023`, `fritzmann2022`, `danvers2023` (running page numbers).<br>Checked in this review: `danvers2022` (title page: TCHES 2022(2) 115–139 and DOI), `cassiers2021trans` (text and running heads).<br>Local copies, also checked: `cassiers2024rng`, `norga2024x2x` (Phase XI extract; the 2025 final version was not checked). |
| **B: external metadata found in this review** | `camacho2026hope`, `danvers2023` DOI, `hermelink2024` pages, `buschkowski2026` (ePrint page: title, authors), `ajayi2019openroad` (title, DAC 2019, pp. 1–4 per the proceedings listing; DOI not confirmed at ACM) |
| **C: frozen research documents and earlier-phase lookups, not re-verified in this review** | `fips203`, `bos2018kyber`, `shor1997`, `fujisaki1999`, `hofheinz2017`, `ravi2020`, `ishai2003`, `faust2018`, `cassiers2020pini`, `cassiers2021hpc`, `gross2016dom`, `knichel2020silver`, `mueller2022prolead`, `bronchain2022`, `shahmirzadi2024`, `ranney2026`, `kamucheka2022`, `brayton2010abc` |
| **Software / library (`misc`)** | `yosys`, `opensta`, `nangate45`, `icarus`: URL and the version actually used |

## Fields still unverified or missing (complete before submission)
- `knichel2020silver`: page range and DOI. The IACR archive path confirms LNCS 12491; Springer pages not confirmed.
- `ajayi2019openroad`: DOI. 10.1145/3316781.3326334 appears only on a mirror of the OpenROAD README, so it is not used. The full author list is abbreviated as "and others".
- `gross2016dom`, `brayton2010abc`: page ranges.
- `cassiers2024rng`, `shahmirzadi2024`: article numbers / pages (CiC uses DOIs; present).
- `ranney2026`: arXiv identifier from the frozen documents; listing seen in a search result, abstract not re-read.
- `kamucheka2022`, `norga2024x2x`: ePrint identifiers only; no published-version check.
- Entries at level C should be spot-checked against publisher pages by the authors.

## Claim attribution (in-text placement)
These attributions were checked against the frozen novelty statement and, where available, the local full texts. No misattribution was found:
- the lemma and offset → `coron2023dil`;
- the precision rule → `coron2023poly`;
- the anchoring → `bos2021masking`;
- the public-threshold comparison → `azouaoui2023`;
- Simple → `fritzmann2022`, `danvers2023`;
- the robust probing model → `faust2018`, `cassiers2021hpc`;
- PINI → `cassiers2020pini`;
- transitions and "HPC2 is not O-PINI" → `cassiers2021trans` (p. 149 of the local text);
- Trivium → `cassiers2024rng`;
- FO-comparison attacks → `hermelink2024`, `ranney2026`.

The D'Anvers 2022 description was corrected for accuracy (see NOVELTY_AUDIT).

## Full texts not included
No copyrighted full text is distributed. `refs/*.txt` are gitignored in the research repository, and `phase2/ext/` is outside it.
