# surfaceproteins: Localization prediction logic

## Introduction

SignalP, TMHMM, Phobius and PSortB each answer a narrower question ("is there a
signal peptide?", "how many transmembrane helices?", "what does PSortB's
classifier say?") and they don't always agree. The `PREDICT_LOCALIZATION`
process (`modules/local/predict_localization/`) resolves these into one
consensus call per protein, with a confidence level and a plain-English
rationale, so you don't have to eyeball five columns per protein yourself.

This document describes exactly how that call is made. The logic itself lives
in `modules/local/predict_localization/templates/predict_localization.py`
(function `classify()`) - this page is a readable version of that code, kept
in sync with it.

## Inputs to the classifier

| Column                                | Source  | Meaning                                                                 |
| -------------------------------------- | ------- | ------------------------------------------------------------------------ |
| `sign_prediction`                      | SignalP | `SP` (Sec signal peptide), `LIPO` (lipoprotein signal), or `OTHER`       |
| `sign_cspos`                           | SignalP | Cleavage site position and probability, e.g. `CS pos: 25-26. Pr: 0.97`   |
| `PredHel`                               | TMHMM   | Number of predicted transmembrane helices                               |
| `phob_TM`                               | Phobius | Number of predicted transmembrane helices                               |
| `phob_SP`                               | Phobius | Whether Phobius also calls a signal peptide (`Y` / `0`)                 |
| `psort_prediction` / `psort_score`      | PSortB  | Predicted compartment and PSortB's own confidence score (0-10)          |
| `gram_stain`                            | Samplesheet | `positive` / `negative` / `unknown`, taken from the `gram` column of `--input` (not re-derived from species name) |

Gram stain matters because it changes what "has a signal peptide, no
transmembrane helix" *means*: in a Gram-negative cell that protein most likely
sits in the periplasm; in a Gram-positive cell (no periplasm) it's more likely
fully secreted.

## Decision order

The classifier checks conditions in this order and returns on the first match:

### 1. Multi-pass transmembrane protein

**If** `PredHel >= 2` **or** `phob_TM >= 2` **→** `Integral membrane protein
(multi-pass, ~N TM helices)`

- **Confidence `High`** if both TMHMM and Phobius agree on ≥2 helices, otherwise `Moderate`.
- If PSortB disagrees (predicts anything other than `CytoplasmicMembrane`), that conflict is recorded in `rationale_notes`.

### 2. Single-pass signal-anchor

**If** `PredHel == 1` **and** `phob_TM == 1` **→**
`Membrane-anchored (signal-anchor / single-pass TM)`, **confidence `High`**.

Both tools agreeing on exactly one genuine transmembrane helix is treated as a
real (uncleaved) signal-anchor - the protein most likely stays membrane-bound
rather than being released.

### 3. TMHMM-only single helix (ambiguous)

**If** `PredHel == 1` **and** `phob_TM == 0`, this is *not* treated as a real
transmembrane helix. TMHMM jointly-models nothing else, so it can mistake the
hydrophobic core of a signal peptide for a TM helix; Phobius models both
signal peptides and TM helices together and didn't call one, so it's trusted
here. A note is added and the classifier falls through to the next checks
(the protein's fate is then decided by its signal peptide, below) - but any
resulting confidence is capped at `Moderate`.

### 4. Has a signal peptide (`SP` or `LIPO`), no confirmed TM helix

This is where Gram stain comes in:

**Gram-negative:**

| PSortB says...           | Call                                                          | Confidence                          |
| ------------------------- | -------------------------------------------------------------- | ------------------------------------ |
| (no PSortB hit)           | `Periplasmic (Sec-dependent...)` or `Periplasmic (lipoprotein...)` if `LIPO` | `Moderate`             |
| `Extracellular`           | `Extracellular (Sec-secreted, exported beyond periplasm)`      | `High` if PSortB score ≥ 9, else `Moderate` |
| `Periplasmic`              | same periplasmic call as default, PSortB agreement noted       | `High` if PSortB score ≥ 9, else `Moderate` |
| `CytoplasmicMembrane`      | `Membrane-associated (PSORTb: cytoplasmic membrane)`           | `Moderate`                           |
| anything else              | default periplasmic call, conflict noted                       | `Moderate`                           |

**Gram-positive** (no periplasm, so a cleaved signal peptide with no TM
usually means full secretion; cell-wall-anchoring motifs like LPXTG are *not*
evaluated by any of these tools, so they aren't part of this call):

| PSortB says...           | Call                                                     | Confidence                          |
| ------------------------- | ----------------------------------------------------------- | ------------------------------------ |
| (no PSortB hit)           | `Cell-surface anchored lipoprotein` if `LIPO`, else `Extracellular (Sec-secreted)` | `Moderate`     |
| `Extracellular`           | same call, PSortB agreement noted                            | `High` if PSortB score ≥ 9, else `Moderate` |
| `CytoplasmicMembrane`      | `Membrane-associated (PSORTb: cytoplasmic membrane)`         | `Moderate`                           |
| `Periplasmic`              | default call kept, flagged as unusual for Gram-positive       | `Moderate`                           |

**Unknown Gram stain:** `Putative secreted/exported (Gram stain unknown)`,
**confidence `Low`** - there isn't enough information to say more.

In every branch here, confidence is capped at `Moderate` if step 3's
"TMHMM-only helix" ambiguity applies, or if SignalP and Phobius disagreed on
whether there's a signal peptide at all (SignalP says yes, Phobius says no).
The dominant SignalP signal-peptide subtype (Sec/SPI, Lipoprotein/SPII,
Tat/SPI, Tat-lipoprotein/SPII, or Pilin-like/SPIII) is always recorded in
`rationale_notes`.

### 5. No signal peptide, no transmembrane helix

| PSortB says...        | Call                                                                | Confidence |
| ----------------------- | ---------------------------------------------------------------------- | ----------- |
| `Extracellular`         | `Possible non-classical secretion` (no SP/TM detected by SignalP/Phobius, but PSortB disagrees - could be real non-classical secretion, a moonlighting protein, or a PSortB false positive) | `Low` |
| `CytoplasmicMembrane`   | `Ambiguous (no SP/TM detected, but PSORTb: cytoplasmic membrane)`      | `Low`       |
| `Cytoplasmic`           | `Cytoplasmic`                                                           | `High` if PSortB score ≥ 9, else `Moderate` |
| anything else / no hit  | `Cytoplasmic`                                                           | `Moderate` (or `Low` if PSortB disagrees) |

## Confidence levels, summarized

- **High** - Multiple tools independently agree (e.g. TMHMM and Phobius both call the same number of TM helices, or PSortB corroborates with a high score).
- **Moderate** - One tool gives a clear signal but there's no independent corroboration (most commonly: SignalP calls a signal peptide but PSortB has no hit for that protein at all).
- **Low** - Tools actively disagree, or there isn't enough information (unknown Gram stain, or PSortB contradicts an otherwise-negative SignalP/Phobius/TMHMM result).

`Moderate` calls are the largest group in most runs, and the most common
reason is simply that **PSortB didn't return a prediction for that protein at
all** (rather than that the tools disagree) - check `psortb_localization` in
`localization.csv`/`localization_full.csv` if you want to know whether a
`Moderate` call reflects a genuine disagreement or just missing
corroboration.

## Limitations

- Cell-wall anchoring signals (e.g. the LPXTG motif recognized by sortase in
  Gram-positive bacteria) are not evaluated by any of these four tools, so a
  `Cell-surface anchored lipoprotein` or `Extracellular` call in a
  Gram-positive genome may still, in reality, be covalently wall-anchored.
- The classifier trusts the `gram` column of your samplesheet as-is; it does
  not attempt to infer or double-check Gram stain from the `taxonomy` column.
- This is a rule-based heuristic, not a trained classifier - it is meant to
  triage and explain, not to replace manual curation of proteins you plan to
  act on experimentally.
