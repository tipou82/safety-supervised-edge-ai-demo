# M0: Repository Baseline

## Goal

Establish a clean, consistent documentation and repository baseline that defines the project scope, architecture, safety concept, requirements, hardware design, and AI-agent rules before any implementation begins.

## Scope

- README with project overview, architecture summary, and limitations
- Architecture documentation (`docs/architecture.md`)
- Safety concept documentation (`docs/safety_concept.md`)
- QNX supervisor design documentation (`docs/qnx_supervisor.md`)
- FFI argument documentation (`docs/ffi_argument.md`)
- System and safety requirements (`requirements/system_requirements.md`, `requirements/safety_requirements.md`)
- Interface specification (`requirements/interfaces.yaml`)
- Traceability matrix (`requirements/traceability.csv`)
- Hardware wiring and GPIO documentation (`hardware/wiring.md`, `hardware/gpio_mapping.md`)
- SysML architecture model (`docs/sysml/architecture.sysml`)
- Milestone plan (`docs/milestones.md`)
- AI-agent engineering rules (`AGENTS.md`)
- Engineering logbook (`docs/logbook.md`)
- Prepared GitHub Issue descriptions (`docs/project_management/issues/`)

## Out of Scope

- Implementation code of any kind
- ROS2 runtime nodes or hardware scripts
- Hardware procurement or physical assembly
- CI pipeline configuration

## Engineering Tasks

- [x] Create repository structure
- [x] Write README with project overview and limitations
- [x] Write architecture documentation
- [x] Write safety concept documentation
- [x] Write QNX supervisor design documentation
- [x] Write FFI argument documentation
- [x] Define system and safety requirements
- [x] Define interface specification (YAML)
- [x] Create traceability matrix (CSV)
- [x] Document hardware wiring and GPIO mapping
- [x] Create SysML architecture model
- [x] Write milestone plan
- [x] Write AGENTS.md with AI-agent engineering rules
- [x] Prepare GitHub Issue descriptions for all milestones

## Acceptance Criteria

- [ ] Repository folder structure is complete and consistent with `docs/architecture.md`
- [ ] All documentation uses correct safety wording (ASIL-B-inspired, demonstrator, FFI-inspired)
- [ ] No implementation code is present in the repository
- [ ] `AGENTS.md` is present and defines AI-agent boundaries
- [ ] `requirements/traceability.csv` links requirements to design documents
- [ ] `requirements/interfaces.yaml` contains authoritative timing constraints
- [ ] All Markdown files render correctly without broken links to existing files
- [ ] README clearly states that this project is not ISO 26262 certified

## Related Requirements

- SYS-001 (System overview and scope)
- SYS-FSR-001 (Safety concept documentation)
- To be linked: documentation completeness requirement

## Related Documents

- `README.md`
- `AGENTS.md`
- `docs/architecture.md`
- `docs/safety_concept.md`
- `docs/ffi_argument.md`
- `docs/qnx_supervisor.md`
- `docs/milestones.md`
- `requirements/system_requirements.md`
- `requirements/safety_requirements.md`
- `requirements/interfaces.yaml`
- `requirements/traceability.csv`
- `hardware/wiring.md`
- `hardware/gpio_mapping.md`

## Test Evidence

- Repository review confirming structure completeness
- Wording audit confirming no certification claims
- Traceability matrix review confirming requirement coverage

## Safety / AI Boundary

- AI agents may draft and review documentation in this milestone.
- AI agents shall not introduce certification claims or overstate the project scope.
- All safety wording must comply with the rules defined in `AGENTS.md`.
- No runtime code is present in this milestone; the safety boundary is enforced by scope.

## Suggested Labels

`documentation` `safety` `portfolio`

## Suggested Branch Name

`docs/m0-repository-baseline`

## Suggested Commit Message

```
docs: add AI-assisted engineering rules
```
