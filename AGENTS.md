# AGENTS.md – AI-Assisted Engineering Rules

This file defines how AI coding assistants (Claude Code, ChatGPT, GitHub Copilot, or similar) may support this repository. These rules are binding for all AI-assisted contributions.

---

## Permitted Uses

AI agents may assist with the following development activities:

- Documentation drafting and Markdown cleanup
- Repository structuring and file organization
- Code scaffolding and boilerplate generation
- Unit test generation for deterministic logic
- Review support and change summarization
- Traceability updates (requirements → design → test)
- Debugging support and root cause analysis
- CI configuration assistance

---

## Prohibited Uses

AI agents shall not be used for:

- Autonomous runtime safety decisions of any kind
- Replacing deterministic decision logic with model-generated logic
- Making ISO 26262 or ASIL certification claims
- Changing safety requirements without explicit human review and approval
- Weakening or softening safety wording
- Committing unreviewed code to the repository
- Introducing hidden external dependencies (packages, APIs, cloud services)
- Storing, logging, or transmitting secrets, credentials, or hardware keys

---

## Mandatory Safety Wording Rules

All AI-generated content in this repository must adhere to the following wording rules without exception:

- **Never** claim ISO 26262 certification. This project is not certified.
- **Never** claim real ASIL-B implementation. Use **"ASIL-B-inspired"** instead.
- Use **"ASIL-B-inspired monitoring path"**, not "ASIL-B path".
- Use **"FFI-inspired architectural measures"**, not "certified FFI".
- Use **"demonstrator"** or **"educational demonstrator"**, not "safety-certified system".
- Runtime safety decisions shall be **deterministic and rule-based**. No model inference.
- LLMs and AI agents shall not be part of the runtime safety decision path.
- The QNX supervisor shall be described as **planned or optional** until validated on hardware.
- The Linux PREEMPT_RT fallback for the supervisor is acceptable and shall be documented honestly.

---

## Engineering Workflow Rules

AI agents assisting with this repository shall follow these workflow rules:

- Prefer **small, reviewable changes** over large multi-concern commits.
- Do not implement multiple milestones in a single step.
- Update documentation **together with** code changes, not after.
- Add or update tests for any change to safety decision rules.
- Keep requirement IDs stable once introduced; do not renumber silently.
- Maintain traceability from requirement to design to test at all times.
- Keep code and documentation concise; avoid padding or filler prose.
- Prefer **explicit assumptions** over implicit behavior or hidden defaults.

---

## Implementation Boundaries

- **Python** may be used for fast prototyping, camera interfacing, and AI perception nodes.
- **C++20** shall be preferred for deterministic decision logic, heartbeat protocol, and supervisor logic.
- Runtime safety decisions shall be implemented as **testable, deterministic logic** with no probabilistic branching.
- Do not place LLM calls, cloud AI calls, or agent calls inside runtime safety code paths.
- Do not introduce ROS2 nodes, hardware drivers, or GPIO code unless the user explicitly requests that implementation step.

---

## Review Checklist

Before a change is accepted, verify all of the following:

- [ ] Does it preserve the project safety wording rules defined above?
- [ ] Is the change small and independently reviewable?
- [ ] Are assumptions explicitly documented in comments or docs?
- [ ] Are requirements, design, and tests mutually consistent?
- [ ] Are generated files free of secrets, credentials, and API keys?
- [ ] Does the change avoid exaggerated or misleading claims?
- [ ] Is the demonstrator scope and limitation clearly stated?

---

## Mermaid Diagram Rules

All Mermaid diagrams committed to this repository must comply with the following rules, validated against GitHub's Mermaid renderer before committing:

**`requirementDiagram` syntax:**
- `id:` fields must use only alphanumeric characters and underscores — no hyphens. Use `SYS_SAFE_007`, not `SYS-SAFE-007` (hyphens are parsed as subtraction and cause a parse error).
- `text:` fields must contain plain ASCII only — no em dash `—`, en dash `–`, or ampersand `&`.
- `verifymethod:` accepts exactly four values: `Test`, `Analysis`, `Inspection`, `Demonstration`. No other values (e.g. `Measurement`) are valid.

**General Mermaid rules:**
- Test all diagrams in VS Code Markdown Preview or GitHub before committing.
- Do not use Unicode punctuation (em dash, en dash, non-breaking space) inside any Mermaid block.
- `architecture_diagrams.md` is the single source of truth for all diagrams — do not maintain equivalent content in `.sysml` files separately.

---

## Commit Discipline

Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages.

**Format:** `<type>: <short description>`

**Examples:**

```
docs: add AI-assisted engineering rules
docs: update safety concept wording
test: add decision logic unit tests
feat: add deterministic state evaluator
chore: update repository structure
fix: correct heartbeat timeout threshold
refactor: extract state machine into dedicated module
```

Commit messages must accurately describe the change. Do not use vague messages such as "updates" or "fixes".

---

*This file applies to all contributors, human and AI-assisted alike.*
