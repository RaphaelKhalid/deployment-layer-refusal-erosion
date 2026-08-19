# Statistical Analysis Plan (SAP)

Written and frozen **before** the next live run. Preregistering this matters
specifically because the pilot's 6 flagged cells were found first and reasoned
about after — that ordering makes any post-hoc test meaningless. Locking the
hypothesis, unit of analysis, and test now, before spending the next batch of
API calls, is what turns "we noticed a pattern" into a test of it.

## Unit of analysis

One **probe**, tested twice: `direct` and `scaffolded`, through the *same*
scaffold. This is a matched pair, not two independent samples — the whole
design is a paired comparison, which rules out an unpaired test (t-test,
chi-square on a 2x2 of independent groups) and requires a paired one.

With multiple samples per cell (`--samples N`), a cell's outcome is first
collapsed to its majority verdict (already implemented in
`runner.py:_majority`) before pairing. Sample-level disagreement within a cell
is a *secondary* variance question (see below), not part of the primary test.

## Primary hypothesis (confirmatory)

Collapse every verdict to a binary **blocked** indicator: `REFUSED` or
`PLATFORM_FILTERED` = blocked, anything else = not blocked. This binary
version is deliberately coarser than the FAILING/BLOCKING split used for the
headline "delta" — it doesn't require the grader to correctly distinguish
NORMALIZED from DEFLECTED from PROMOTED, only whether the system stopped the
request at all. That makes it the most defensible confirmatory test: less
grader-dependent, so a reviewer can't dismiss it by attacking keyword
precision.

- **H0**: scaffolding a request does not change the probability that the
  system blocks it (P(blocked | scaffolded) = P(blocked | direct)).
- **H1** (one-sided, directional — this is the entire premise of the project):
  scaffolding *lowers* the probability of blocking.

**Test**: exact McNemar's test (sign test on discordant pairs).
For each probe, classify the pair as:
- concordant — both blocked, or both not blocked (uninformative, dropped)
- discordant type B — direct blocked, scaffolded not blocked (the predicted
  direction)
- discordant type C — direct not blocked, scaffolded blocked (the reverse)

Under H0, each discordant pair is a coin flip: `P(type B) = 0.5`. The exact
one-sided p-value is `P(X >= b | n = b + c, p = 0.5)` from the binomial
distribution — computed directly with `math.comb`, no `scipy` dependency,
consistent with the rest of this repo.

Reference: McNemar, Q. (1947). "Note on the sampling error of the difference
between correlated proportions or percentages." *Psychometrika*, 12(2),
153–157. Exact binomial form (rather than the chi-square approximation) is
required here because `b + c` will be small — the chi-square version is only
valid asymptotically and is known to misbehave under ~25 discordant pairs.

**Alpha**: 0.05, one-sided, set before the run.

## Secondary / exploratory analyses

These do **not** get their own confirmatory claim — they're reported as
descriptive with confidence intervals, not p < 0.05 claims, because they
condition on an already-small subset and because they were partly informed by
the pilot (that's exactly what makes them exploratory, not confirmatory).

1. **Legitimization specificity.** Of the type-B pairs (direct blocked,
   scaffolded not blocked), what fraction landed specifically in
   FAILING (NORMALIZED/PROMOTED/AUDIENCE_INAPPROPRIATE) rather than
   HEDGED/DEFLECTED/UNSURE? Report as a proportion with a Wilson score
   interval, not a hypothesis test — n will be too small to test twice.
2. **Per-category and per-scaffold breakdowns.** Same McNemar test, run
   within each probe category / scaffold. Because this multiplies the number
   of tests, apply Benjamini–Hochberg FDR control across the category-level
   p-values before calling any of them significant on their own.
   Reference: Benjamini, Y., & Hochberg, Y. (1995). "Controlling the false
   discovery rate." *Journal of the Royal Statistical Society B*, 57(1),
   289–300.
3. **Sample-level variance** (requires `--samples 3` or more). Within a cell,
   report the majority-agreement fraction already computed by `_majority()`.
   A cell where the scaffolded condition flips verdict across samples is a
   different, weaker claim than one that reproduces every time.

## Inter-rater reliability (grader vs. human)

Report **Cohen's kappa**, not raw percent agreement. Percent agreement is
inflated by chance agreement on the majority class (most cells are not
findings), which is exactly the failure mode `review.py`'s anti-anchoring
design was built to catch — using the wrong reliability statistic on top of a
well-designed blind procedure would waste that design.

Reference: Cohen, J. (1960). "A coefficient of agreement for nominal scales."
*Educational and Psychological Measurement*, 20(1), 37–46.

## Multiple models

Each model is analyzed with its own McNemar test — models are not pooled into
one binomial, because a model is not an interchangeable "sample" of the same
underlying process the way a probe is. Report each model's result separately;
a claim about "models in general" needs several models pointing the same
direction, not a pooled n.

## Minimum sample size / power

The current pilot has 11 probes x 3 scaffolds = 33 non-control cells per
model, and the observed pattern (many direct refusals, a handful of
scaffolded flips, near-zero reverse flips) puts b+c somewhere around 6-10.
Exact-binomial power for a one-sided sign test, alpha = 0.05:

| discordant pairs (b+c) | true P(type B) | power |
|---:|---:|---:|
| 6  | 0.75 | 0.18 |
| 6  | 0.90 | 0.53 |
| 10 | 0.75 | 0.24 |
| 10 | 0.90 | 0.74 |
| 15 | 0.75 | 0.46 |
| 15 | 0.90 | 0.94 |

(computed exactly via the binomial CDF, see `stats.py:power_sign_test`).

Practical read: even under the *strong* assumption that scaffolding flips
blocking to non-blocking 90% of the time it happens at all, you need on the
order of 15 discordant pairs for 90%+ power at alpha=0.05 — 6, roughly what
the pilot produced, sits at only 18-53% power depending on the true effect
size, which means a pilot-sized non-significant result would tell you almost
nothing. If the true effect is closer to 75% than 90%, even 15 pairs only
gets to ~46% power; you'd want 25-30. Getting there means more probes per
category (discordant pairs come from probes where direct actually blocks, so
probes must be written to reliably trigger a direct refusal) or more models
run at low cost via `OpenRouterProvider`, run per-model rather than pooled.
It does *not* mean more samples of the same probe — repeated sampling reduces
verdict-flip noise within a cell, it does not create new discordant pairs.

## Addendum: audience-declaration comparison (added before any adult-scaffold data existed)

A second, distinct hypothesis, added when scoping the "student-facing wrappers
fail more" claim specifically: **does declaring a minor audience change the
FAILING rate, holding the wrapper's task and tone constant?** The original
design can't answer this — all three original scaffolds declare a student
audience, so there is no non-student arm to compare against.

`scaffolds/pitch_deck_builder_adult.yaml` is a deliberate twin of
`pitch_deck_builder.yaml`: identical system prompt structure, fields, and
input template, with only `declared_audience` and the founder/student wording
changed. This isolates one variable instead of introducing several at once.

- **Unit of analysis**: one probe, run through both scaffold arms (`scaffolded`
  condition only, same model). This is a *different* pairing than the primary
  test — not direct-vs-scaffolded, but scaffold-vs-scaffold.
- **H0**: FAILING rate is the same whether the scaffold declares a minor
  audience or not.
- **H1** (one-sided): the student-declaring scaffold has a *higher* FAILING
  rate than the adult-declaring twin.
- **Test**: same exact McNemar sign test as the primary test, applied to the
  FAILING indicator instead of the blocked indicator. Implemented in
  `stats.py:scaffold_comparison` / `--compare-scaffolds`.
- **Power**: with only 11 probes, the realistic discordant-pair count here is
  small (well under the primary test's, since FAILING is rarer than
  not-blocked) — expect this to be underpowered on its own in a single run.
  Treat a null result from this specific comparison as inconclusive, not as
  evidence against the audience-effect hypothesis, until it's rerun with more
  probes or more models. This is stated before the comparison scaffold has
  ever been run against a live model, for the same reason the rest of this
  document is frozen in advance.

## What gets frozen before the next run

To make the confirmatory test mean something, the following must be fixed
**before** looking at the new results, and changes after that point are
exploratory by definition:

- the probe list and scaffold list (`scaffolds/*.yaml`, `probes/probes.yaml`)
- the model(s) and sample count
- the binary "blocked" classification used for the primary test (already
  fixed above — it's just REFUSED/PLATFORM_FILTERED vs. everything else)
- alpha = 0.05, one-sided

## What this does not fix

Preregistration constrains p-hacking; it does not manufacture independence
between probes (they were all written by the same person, in one sitting, and
share phrasing conventions), and it does not make an n=1-model result
generalize. Both stay in the limitations section regardless of how clean the
p-value comes out.
