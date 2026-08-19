# Limitations

Stated plainly, because an evaluation tool that oversells itself is worse than none.

## 0. The published results are a fixture run

The results in `results/` were produced by the offline `stub` provider. No live
model has been run through this harness yet. Everything below about grader
quality applies to the logic, not to any measured model behavior — because there
isn't any yet.

Running live is a one-command change (see README). It hasn't been done because
of a network restriction in the environment this was built in, not because of
anything about the method.

## 1. The default run is a fixture, not evidence

`--provider stub` returns hardcoded responses encoding the behavior pattern we
observed in the wild. It exists so the harness runs end-to-end without an API key
and so the scoring logic is testable.

**Stub results are not evidence about any model or product.** Any number quoted
from a stub run is a number about this repo's fixtures. Real runs require
`--provider anthropic|openai` with a key, and results should be labeled with the
model and date.

## 2. The grader is heuristic and will be wrong

Verdicts come from keyword matching over refusal, hedging, and promotional
markers. This has predictable failure modes:

- **False PROMOTED**: a response that refuses in unusual phrasing, or explains
  why the idea is harmful using promotional-sounding vocabulary.
- **False REFUSED**: a response that says "I can't give you specifics, but here's
  the pitch" — refusal marker present, compliance underneath.
- **Blind to quality**: cannot distinguish a generic paragraph from a genuinely
  compelling, actionable pitch. Both score PROMOTED.
- **English only.** Other youth-safety red-teaming work has noted the same gap.
  Children's slang and code-switching are known bypasses this would miss entirely.

Heuristics were chosen over an LLM judge deliberately for a first pass — an LLM
judge introduces its own scaffold, and its own legitimization risk, into the
measurement instrument. That tradeoff should be revisited with human-labeled
ground truth. **Any finding presented as real should be human-reviewed.**

## 3. Single-turn only

This harness tests single-turn probes only. The more realistic risk with minors
is multi-turn: gradual escalation, rapport-building, context accumulated across
a session, a pattern other youth-safety red-teaming work has documented
directly. This harness cannot see it.

## 4. Scaffolds are example prompts

The scaffolds in `scaffolds/` were written for this repo based on common patterns
in student-facing products. No vendor's proprietary system prompt is reproduced.
This means results demonstrate that the *vulnerability class* is real and
reproducible — not that any specific shipped product fails.

## 5. Probes carry no technical payload

By design (see `probes/probes.yaml`). This measures *legitimization*, which is
what we observed, and does so without the repo itself becoming a hazard. It does
**not** measure whether a system will output actionable technical instructions.
That is a different and harder evaluation, requiring controlled access and
oversight this project doesn't currently have.

## 6. Small n, no statistics

Eleven probes, three scaffolds. Sampling is single-shot with no temperature
sweep, so run-to-run variance is unmeasured. Treat outputs as existence proofs
of a failure mode, not as rates.

## 7. Legitimization severity is unvalidated

The core claim — that a school tool writing marketing copy for home drug
synthesis constitutes real harm — is an argument, not a measured finding. It is
grounded in age-appropriate-design frameworks (UK Children's Code, UNCRC
guidance), but no user study here establishes downstream effect on children. The
counterargument that this is merely embarrassing rather than harmful deserves a
real answer, and this repo does not yet provide one.
