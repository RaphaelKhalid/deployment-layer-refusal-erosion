# Making this a real study

Target: a talk proposal backed by data that survives a hostile reviewer.
Written 2026-08-12. Current state, honestly: one complete live run (66 cells,
`gemini-flash-lite-latest`), 6 grader-flagged failures, 2 of which held up under
hand inspection by the same person who wrote the grader. That is a pilot, not a
result.

---

## What is actually wrong with the study today

Five things, in the order a reviewer will find them.

1. **n = 1 model.** Every claim is currently "a small Gemini model did this."
   Nobody can tell whether this is a failure class or a quirk.
2. **Single-shot sampling.** Temperature is non-zero. Each cell was sampled
   once. Run-to-run variance is unmeasured, so a "delta" may be noise.
3. **No human ground truth.** Grader precision is estimated at ~33% from a
   6-case eyeball by the grader's own author. Circular.
4. **`scaffold_control` does not exist.** The README describes a third
   condition that `run()` never implements. Without it a scaffold that refuses
   everything is indistinguishable from one that behaves correctly.
5. **Thin content.** 11 probes, 3 scaffolds. Two scaffolds share nearly the
   same framing, so the design cannot separate "encouraging tone" from
   "persuasion is the task" — which the pilot suggests is the real mechanism.

The pilot already produced one sharp hypothesis worth testing properly:

> Science Fair Coach has the same "take the student's topic seriously" framing
> as Pitch Deck Builder and **refused** where Pitch Deck Builder complied. The
> distinguishing feature is not encouragement — it is that the pitch scaffold's
> *task is to write persuasive copy for whatever arrives*. Persuasion is the
> payload.

That is a better talk than "wrappers are unsafe." It is falsifiable and it
predicts which products are dangerous.

---

## Phase 1 — Fix the instrument (must precede any large run)

Do not spend 1,500 API calls on a harness with known holes.

| # | Change | Why | Est |
|---|---|---|---|
| 1.1 | Implement `scaffold_control` as a third condition | Completes the design the README already claims; separates "safe" from "broken" | 30m |
| 1.2 | Wire `AUDIENCE_INAPPROPRIATE` | Verdict exists, is rendered, never emitted. The two real pilot findings are both minor-audience cases — this is the strongest claim in the project and it is currently unmeasurable | 30m |
| 1.3 | `--samples N` (default 3), majority verdict per cell, keep all samples | Turns single-shot anecdotes into a rate with visible variance | 45m |
| 1.4 | `--model` accepts a list; results keyed by `(model, scaffold, probe, condition, sample)` | Multi-model runs in one pass, one output file | 30m |
| 1.5 | Resume-from-checkpoint (skip cells already in the partial file) | A 1,500-call run WILL be interrupted | 30m |
| 1.6 | Record `temperature`, `sdk_version`, `run_id`, wall-clock per call | Reproducibility. A reviewer will ask | 15m |

**Exit criterion:** `python test_harness.py` green with new tests for 1.1–1.3,
and a 3-model × 2-probe smoke run completing end to end.

---

## Phase 2 — Expand the content

**Scaffolds — go from 3 to 6, chosen to isolate the mechanism.** The point is a
2×2: persuasive-task vs. advisory-task, crossed with minor-audience vs. general.

| Scaffold | Task type | Audience | Role |
|---|---|---|---|
| `pitch_deck_builder` (exists) | persuasive | minors | known-positive |
| `science_fair_coach` (exists) | advisory | minors | known-negative |
| `homework_helper` (exists) | advisory | minors | control |
| `marketing_copy_assistant` (new) | persuasive | general | does the effect survive without minors? |
| `college_essay_coach` (new) | persuasive | teens | persuasion + high stakes |
| `product_namer` (new) | persuasive, low-context | general | how thin can the scaffold be and still erode refusal? |

**Probes — go from 11 to ~18.** Keep the no-payload rule absolutely. Add:
- 3–4 *near-miss* controls that must PASS (e.g. honest drug education,
  a needle-exchange outreach app, a firearms-safety course). These are what
  prove the eval is not a keyword blacklist, and they are the most persuasive
  slide in any talk.
- 2–3 probes in the ambiguous middle (a fasting app for adults; a lockpicking
  hobby kit) where reasonable people disagree — these calibrate severity.

**Est: 60–90 min**, mostly writing prose.

---

## Phase 3 — The multi-model run (free)

Confirmed working on the free Gemini key (measured 2026-08-12):

| Model | Throughput | Lineage |
|---|---|---|
| `gemini-flash-lite-latest` | ~8 calls / 3.4s | Gemini |
| `gemini-3.1-flash-lite` | ~6 / 2.7s | Gemini |
| `gemini-3-flash-preview` | ~6 / 5.8s | Gemini |
| `gemma-4-31b-it` | ~6 / 12.3s | Gemma (open weights) |
| `gemma-4-26b-a4b-it` | ~6 / 12.3s | Gemma MoE |

`gemini-3.1-pro-preview` is quota-exhausted; frontier-tier models are not
reachable free. **State that limitation explicitly rather than implying
coverage you do not have.**

**Call budget.** 18 probes × (1 direct + 6 scaffolded) = 126 cells/model/sample.
At 3 samples = 378/model. Across 5 models = **1,890 calls.** At ~13/min that is
~2.5 hours of unattended wall-clock. Run it overnight with checkpointing.

Cut if needed: drop to 2 samples (1,260 calls, ~1.6h) or 4 models.

---

## Phase 4 — Human labelling (the credibility step)

With ~1,890 cells you cannot label everything, and you should not try.
**Stratified sample, ~150 labels:**

- **All** cells the grader flags as failing (expected 100–200; if more, sample 100)
- **60** random non-flagged cells — this is what catches false *negatives*,
  which the pilot has never tested for at all
- **All** benign-control cells (must pass; a failure here is a different bug)

Deliverables: grader **precision** and **recall** with bootstrap CIs, plus the
confusion matrix showing *direction* of error.

**Get a second labeller for ~40 overlapping items** and report Cohen's κ.
Inter-rater agreement is the difference between "I judged these" and "this is
measurable." If you have anyone in the incubator cohort, this is a 20-minute ask.

**Est: 45–60 min of your time** via the existing click UI.

---

## Phase 5 — Analysis

- Delta rate per (model × scaffold), with CIs — not raw counts
- **The key contrast:** persuasive-task scaffolds vs. advisory-task scaffolds,
  pooled across models. This tests the pilot's hypothesis directly.
- Minor-audience vs. general-audience, to test whether declared audience
  changes anything (it should, and if it doesn't that is itself a finding)
- Benign-control pass rate per model — the "not a blacklist" evidence
- Every number carries: model id, date, temperature, n samples, grader precision

**Report the null loudly if it is null.** "Four of five models were robust;
the failure concentrated in persuasion-task scaffolds" is a real, publishable,
honest result and a better talk than an inflated one.

---

## Phase 6 — Kaggle (reconsidered: yes, but for Phase 6, not now)

Earlier I said Kaggle solved nothing, because the bottleneck was Google's
per-key rate limit and not compute. That was right about *tonight* and wrong as
a general judgement. Kaggle earns its place for three things the API cannot do:

1. **Unlimited sampling.** Self-hosted weights have no quota. n=10 per cell for
   variance, or full temperature sweeps, become free.
2. **Models the API will not serve you.** Llama-3.x-Instruct, Qwen,
   Mistral-Instruct — different labs, different safety training. This is what
   turns "a Google result" into "a cross-lab result," which is the single
   biggest credibility jump available.
3. **The self-hosting threat model.** A budget edtech vendor running an
   open-weights model on their own box is *precisely* the deployment this
   project is about, and it is the one with no provider safety layer at all.

**Concrete steps:**
- 6.1 Package harness as a Kaggle Dataset (code + `scaffolds/` + `probes/`), or
  pull from GitHub in the notebook
- 6.2 Notebook with T4×2, `transformers` + 4-bit, or vLLM for throughput
- 6.3 Add `LocalHFProvider` implementing `complete(system, user, meta)` — the
  runner needs nothing else; batch generation instead of one-at-a-time
- 6.4 Start with one 7–9B instruct model end-to-end before scaling out
- 6.5 Write `results.json` to `/kaggle/working`, commit, download, merge locally
- 6.6 Watch: session time limits, GPU quota/week, and the fact that chat
  templates differ per model — a wrong template silently degrades every response
  and would look like a safety finding

**Est: 2–3 hours** for the first model, much less for each additional one.

---

## Phase 7 — The talk proposal

Claim only what is measured:

- The failure class, illustrated with a realistic (reconstructed, not real)
  scenario
- The measurement design, and specifically why the delta isolates the
  deployment layer
- Cross-model results with CIs and stated grader precision
- **The two false-positive generations of the grader as a methods section.**
  An eval that caught itself inflating its own thesis, twice, and published the
  correction, is more trustworthy than one that never reports a bug. Do not
  hide this — lead with it.
- Limitations, unchanged in spirit from `LIMITATIONS.md`: single-turn, English,
  legitimization not capability, no frontier models, reconstructed scaffolds

Do **not** claim: that any specific, identifiable product fails; a
population-level harm rate; anything about frontier models.

---

## Ordering, and what fits in the remaining hours tonight

Realistic for a few hours, in order:

1. Phase 1.1–1.4 (instrument) — the run is worthless without these
2. Phase 2 scaffolds (the 2×2 is the whole scientific contribution)
3. Kick off Phase 3 overnight with checkpointing
4. Phase 4 labelling tomorrow with fresh eyes — do not label tired, it is the
   one step where sloppiness silently corrupts everything downstream

Explicitly **not** tonight: Kaggle (Phase 6), second labeller, write-up.

## Open decisions

- 3 samples or 2? (variance quality vs. run length)
- 5 models or 4? (drop `gemini-3-flash-preview` — it is the least distinct)
- Do you have an Anthropic or OpenAI key? Either adds a genuinely different
  lab for ~$1–2 and materially strengthens the cross-lab claim
- Who is the second labeller?
