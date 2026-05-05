# M6: Portfolio-Ready Demo

## Goal

Prepare the project for external presentation so that an interviewer or reviewer can understand the goal, architecture, engineering evidence, and limitations within approximately ten minutes of reviewing the repository.

## Scope

- README finalization with clear project summary, architecture diagram reference, and limitations section
- Demo script or walkthrough guide (`docs/demo_script.md`)
- Architecture diagram (block diagram or SysML diagram rendered as image)
- Test report summarizing unit tests, fault-injection results, and timing measurements
- Lessons learned document (`docs/lessons_learned.md`)
- Known limitations section in README or dedicated `docs/limitations.md`
- Optional: demo video link in README (external hosting, e.g. YouTube or similar)
- Final pass for safety wording consistency across all documentation

## Out of Scope

- Overstated safety claims or implied certification
- Presenting unfinished or untested features as completed
- Adding new features not covered by M1–M5
- Refactoring implementation code for aesthetics

## Engineering Tasks

- [ ] Review and finalize README: project summary, architecture, build instructions, limitations, portfolio context
- [ ] Write `docs/demo_script.md`: step-by-step walkthrough of the running system for an interviewer
- [ ] Render or export architecture block diagram as an image (PNG or SVG) for README embedding
- [ ] Compile test report (`docs/test_report.md`) summarizing:
  - Unit test results (M3)
  - Fault-injection results (M4)
  - Timing measurements (M2, M5)
- [ ] Write `docs/lessons_learned.md` covering engineering decisions, challenges, and open items
- [ ] Audit all documentation for safety wording compliance (ASIL-B-inspired, demonstrator, FFI-inspired)
- [ ] Confirm all links in README and docs resolve to existing files
- [ ] Add optional demo video link to README if video is available
- [ ] Final review of `requirements/traceability.csv` for completeness
- [ ] Tag repository with milestone version (e.g. `v0.6.0-m6`)

## Acceptance Criteria

- [ ] README can be read cold in under five minutes and clearly explains: goal, architecture, evidence, and limitations
- [ ] `docs/demo_script.md` allows an interviewer to follow the system demonstration step by step
- [ ] Architecture diagram is rendered and visible in README without requiring external tools
- [ ] `docs/test_report.md` summarizes all test evidence from M3 and M4
- [ ] `docs/lessons_learned.md` is present and covers at least three substantive engineering observations
- [ ] No documentation contains certification claims or overstated safety language
- [ ] All internal document links resolve correctly
- [ ] `requirements/traceability.csv` is complete for all implemented requirements
- [ ] Repository is tagged and the tag is documented in the logbook

## Related Requirements

- All implemented requirements from M1–M5
- SYS-001 (System scope and limitations documented)
- To be linked: portfolio documentation requirement

## Related Documents

- `README.md`
- `docs/demo_script.md`
- `docs/test_report.md`
- `docs/lessons_learned.md`
- `docs/architecture.md`
- `docs/safety_concept.md`
- `docs/ffi_argument.md`
- `docs/fault_injection_report.md`
- `requirements/traceability.csv`
- `docs/logbook.md`

## Test Evidence

- Final wording audit report (documented in logbook or as a checklist in this issue)
- Confirmation that README renders correctly on GitHub
- Confirmation that all links resolve
- Repository tag `v0.6.0-m6` or equivalent created and logged

## Safety / AI Boundary

- AI agents may assist with README editing, demo script drafting, diagram description, and lessons-learned formatting.
- AI agents shall not generate test results, timing measurements, or engineering conclusions that were not produced by actual test execution.
- AI agents shall not introduce certification claims or soften limitation statements.
- The limitations section must be written by the engineer and must be honest about what was not achieved.
- All AI-assisted content must pass the safety wording audit before the milestone is closed.

## Suggested Labels

`documentation` `portfolio` `safety` `testing`

## Suggested Branch Name

`docs/m6-portfolio-ready-demo`

## Suggested Commit Message

```
docs: finalize portfolio documentation and add demo script
```
