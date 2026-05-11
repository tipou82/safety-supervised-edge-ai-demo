# ISO 26262 Gap Analysis

**Document**: GAP-001
**Project**: Safety-Supervised Edge AI Demonstrator
**Standard**: ISO 26262:2018 (Road vehicles — Functional safety), all parts
**Date**: 2026-05-11
**Author**: Yunpeng Yang
**Status**: COMPLETE — educational demonstrator scope

> **Purpose**: This document systematically identifies what this demonstrator achieves
> versus what full ISO 26262 ASIL-B certification requires. It is intended to show
> understanding of the standard and a clear path from demonstrator to production —
> NOT to claim compliance.

---

## 1. Executive Summary

The demonstrator implements the **technical architectural patterns** of an ASIL-B
safety-supervised system. It does not follow the **process requirements** of ISO 26262,
which mandate qualified tools, independent assessment, and a documented safety lifecycle.

| Category | Status |
|---|---|
| Safety architecture patterns | ✅ Implemented and verified |
| Hazard analysis (HARA) | ✅ Performed (demonstrator quality) |
| FMEA | ✅ Performed (qualitative, no FIT rates) |
| Requirements traceability | ✅ Full (62 PASS entries) |
| Unit testing | ✅ 33 gtest cases |
| Fault injection | ✅ 5 scenarios PASS |
| FFI verification | ✅ 3 interference tests PASS |
| Qualified development process | ❌ Not established |
| Tool qualification | ❌ Not performed |
| Independent safety assessment | ❌ Not performed |
| Quantitative safety metrics (FMEDA) | ❌ Not performed |
| MISRA C compliance | ❌ Not checked |
| Functional safety management plan | ❌ Not documented |

---

## 2. Gap Analysis by ISO 26262 Part

### Part 1 — Vocabulary

| Requirement | Demonstrator | Gap | Severity |
|---|---|---|---|
| Item definition (item, system, element) | Defined in HARA.md | Not formally structured per Part 1 terminology | Minor |
| Safety lifecycle terms used correctly | ASIL-B-inspired language throughout | Not all terms from standard used precisely | Minor |

---

### Part 2 — Management of Functional Safety

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Functional safety management plan | 5 | Not created | No documented safety plan | **Major** |
| Safety culture evidence | 6 | AGENTS.md defines AI/safety boundaries | No formal safety culture programme | Moderate |
| Competency of persons | 7 | Single engineer (no formal certification) | No evidence of qualified safety engineers | **Major** |
| Quality management system | 8 | Git version control + CI-like commit discipline | No ISO 9001 or ASPICE process | **Major** |
| Configuration management | 9 | Git + semantic commits + traceability.csv | No formal CM plan or baseline control | Moderate |
| Change management | 10 | Logbook entries per session | No formal change request process | Moderate |
| Documentation requirements | 11 | CLAUDE.md docs map; comprehensive logbook | No document management system | Minor |

---

### Part 3 — Concept Phase

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Item definition | 5 | HARA.md Section 1 | Not formally reviewed and released | Minor |
| Initiation of safety lifecycle | 6 | Implicit in HARA and planning | No formal safety lifecycle initiation record | Moderate |
| Hazard analysis and risk assessment | 6 | HARA.md — S/E/C → ASIL B | Not performed by a qualified assessor; single author | **Major** |
| Functional safety concept | 7 | docs/safety_concept.md + safety_mechanisms.md | Not structured per Part 3 template | Moderate |
| Safety goals with ASIL | 7 | SG-001/002/003 in HARA.md | Not formally allocated to item/element level | Moderate |

---

### Part 4 — Product Development at System Level

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Technical safety concept | 6 | docs/safety_mechanisms.md (SM-1 to SM-7) | Not structured per Part 4 template | Moderate |
| System design | 7 | architecture.md + SysML-style diagrams | No formal system design review record | Moderate |
| Hardware-software interface specification | 7.4 | requirements/interfaces.yaml | Not a formal HSI specification document | Minor |
| System integration and testing | 8 | M2–M7 integration tests | No formal system integration test plan | Moderate |
| Safety validation | 9 | Fault injection (M6) + FFI tests (M7) | No formal validation plan; no independent validator | **Major** |
| Functional safety assessment | 10 | Self-assessed only | No independent assessment | **Major** |
| Release for production | 11 | N/A (demonstrator) | No production release process | N/A |
| FMEA at system level | 8.4 | FMEA.md — 63 failure modes | Qualitative only; no FIT rates or DC percentages | Moderate |

---

### Part 5 — Product Development at Hardware Level

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Hardware safety requirements | 6 | gpio_mapping.md, wiring.md | Not structured per Part 5 template | Moderate |
| Hardware design | 7 | Breadboard prototype | Not a qualified hardware design | **Major** |
| Hardware architectural metrics | 8 | FMEA provides qualitative DC | No SPFM/LFM/PMHF metrics | **Major** |
| Hardware integration and testing | 9 | M1 hardware bring-up; e-stop verified | No formal hardware test plan | Moderate |
| Evaluation of hardware elements | 10 | RPi not automotive-qualified | RPi hardware not ASIL-rated | **Major** |
| Production and operation | 11 | N/A | N/A |  |

#### Hardware architectural metric gaps (Part 5, Clause 8)

| Metric | ASIL B requirement | Demonstrator | Gap |
|---|---|---|---|
| SPFM (Single-Point Fault Metric) | ≥ 90% | Not calculated | No FIT rate data for RPi hardware |
| LFM (Latent Fault Metric) | ≥ 60% | Not calculated | No FIT rate data |
| PMHF (Probabilistic Metric for HW Failures) | < 10⁻⁷/h | Not calculated | No FIT rate data |

---

### Part 6 — Product Development at Software Level

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Initiation of SW safety | 5 | Implicit — safety mechanisms in SW | No formal SW safety plan | Moderate |
| SW safety requirements | 6 | system_requirements.md (30+ SYS-SAFE-*) | Requirements partially structured for Part 6 | Minor |
| SW architectural design | 7 | C++20 StateEvaluator; Python nodes; ROS2 | No formal SW architectural design review | Moderate |
| SW unit design and implementation | 8 | decision_node C++20; 33 gtest | No formal unit design documents | Minor |
| SW unit verification | 9 | 33 gtest all pass | No formal unit verification plan; no MC/DC coverage | Moderate |
| SW integration and verification | 10 | M2–M7 integration; FI tests | No formal SW integration test plan | Moderate |
| Verification of SW safety requirements | 11 | Fault injection (M6) all pass | Not performed against formal plan | Moderate |
| SW tool confidence level (TCL) | 11.4 | GCC, colcon, pytest, gtest | Tools not qualified; TCL not assessed | **Major** |
| MISRA C:2012 compliance | 8.4 | Not checked | No static analysis with MISRA ruleset | **Major** |
| Absence of dynamic memory allocation | 8.4 | Python nodes use heap | Python ROS2 nodes use dynamic allocation | **Major** |
| No recursion | 8.4 | No recursion identified | Not formally verified | Minor |
| No undefined behaviour | 8.4 | C++ StateEvaluator uses noexcept | Python nodes not analysed | Moderate |

#### Software coding guidelines gap

| ASIL-B guideline (Part 6 Table 1) | Demonstrator | Gap |
|---|---|---|
| Enforce strong typing | ✅ C++20 strong types in StateEvaluator | Python nodes not strongly typed |
| No dynamic memory in safety path | ✅ StateEvaluator: pure function, stack only | Python health_node uses heap |
| Defensive implementation | ✅ isfinite() guards, FLT_MAX defaults | Partial — not systematic |
| No dead code | Not verified | No static analysis tool used |
| Code coverage ≥ MC/DC | Not measured | gtest covers transitions but no MC/DC metric |

---

### Part 7 — Production, Operation, Service, Decommissioning

| Requirement | Gap | Severity |
|---|---|---|
| Production plan | N/A for demonstrator | N/A |
| Field monitoring | No field monitoring implemented | N/A |
| Service and repair | No service documentation | N/A |

---

### Part 8 — Supporting Processes

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Configuration management | 6 | Git + semantic commits | No formal CM plan; no baseline freeze | Moderate |
| Documentation management | 7 | CLAUDE.md docs map; logbooks | No document management system | Minor |
| Qualification of SW tools | 11 | None | GCC, colcon, gtest not qualified | **Major** |
| Qualification of HW components | 12 | None | RPi not automotive-qualified | **Major** |
| Proven-in-use argument | 14 | N/A (custom system) | No field data | N/A |

---

### Part 9 — ASIL-Oriented and Safety-Oriented Analyses

| Requirement | Clause | Demonstrator | Gap | Severity |
|---|---|---|---|---|
| Requirements decomposition | 5 | traceability.csv (62 PASS) | Not formally ASIL-decomposed at element level | Moderate |
| Dependent failure analysis | 6 | FMEA.md SPOF register | No formal DFA per Part 9 | Moderate |
| Safety analyses (FMEA/FTA) | 7–8 | FMEA.md (qualitative) | No FTA; no quantitative FMEDA | **Major** |
| Evaluation of safety goal violations | 9 | HARA.md Section 5 | Not formally validated against safety goals | Moderate |

---

### Part 10 — SGBM Guideline (Guidebook)

Not applicable as a normative requirement.

---

### Part 11 — Semiconductors

| Requirement | Gap |
|---|---|
| Semiconductor qualification | RPi silicon not ASIL-qualified; no AEC-Q100 rating |
| Safety element out of context (SEooC) | RPi used as SEooC without safety manual |

---

## 3. Gap Severity Classification

| Severity | Count | Examples |
|---|---|---|
| **Major** (blocks certification) | 18 | Tool qualification, independent assessment, SPFM/LFM/PMHF, MISRA, dynamic memory in SW |
| **Moderate** (requires process work) | 16 | Formal plans, structured documents, formal reviews, ASIL decomposition |
| **Minor** (documentation polish) | 8 | Template adherence, terminology precision |
| **N/A** | 5 | Production/decommissioning phases |

---

## 4. Path from Demonstrator to ASIL-B Production

The following would be required to take this architecture to a certified production system:

### Phase 1 — Process establishment (~6 months)
- [ ] Establish functional safety management plan (Part 2)
- [ ] Appoint qualified functional safety manager
- [ ] Define and document safety lifecycle
- [ ] Select and qualify development tools (GCC, static analyser, test framework)
- [ ] Adopt ASPICE Level 2 development process

### Phase 2 — Hardware redesign (~3 months)
- [ ] Replace Raspberry Pi with ASIL-rated microcontroller (e.g., Infineon TC3xx, NXP S32K)
- [ ] Perform hardware FMEDA with FIT rates (IEC 62380 or SN 29500)
- [ ] Calculate SPFM, LFM, PMHF per Part 5
- [ ] Resolve SPOF-001 (GPIO 25 redundancy) and SPOF-002 (GPIO self-test)
- [ ] Replace prototype wiring with qualified PCB design

### Phase 3 — Software re-implementation (~6 months)
- [ ] Port StateEvaluator to MISRA C:2012-compliant C
- [ ] Eliminate dynamic memory allocation in safety path
- [ ] Achieve MC/DC code coverage ≥ 100% for safety-relevant code
- [ ] Replace Python nodes with C POSIX implementation for safety path
- [ ] Perform formal SW architectural design review

### Phase 4 — Verification and validation (~3 months)
- [ ] Perform independent safety assessment (ISA)
- [ ] Execute formal validation plan against safety goals
- [ ] Perform quantitative FMEDA
- [ ] Perform dependent failure analysis (Part 9)
- [ ] Document functional safety case (Part 2 Clause 6.4)

### Phase 5 — Release
- [ ] Functional safety audit by notified body (if required)
- [ ] Issue safety certificate or functional safety assessment report

**Estimated total effort**: 18–24 months with a team of 3–5 engineers including
a qualified functional safety manager, hardware safety engineer, and SW safety engineer.

---

## 5. What the Demonstrator Successfully Shows

Despite the gaps above, this demonstrator provides strong evidence of:

| Competency demonstrated | Evidence |
|---|---|
| Understanding of FFI and ASIL decomposition | Dual-processor architecture, verified interference tests |
| Safety-driven requirements engineering | 60+ requirements with full traceability |
| HARA methodology | HARA.md with S/E/C → ASIL B determination |
| FMEA discipline | 63 failure modes, SPOF register, DC assessment |
| Deterministic safety logic design | C++20 StateEvaluator, pure function, 33 gtest |
| AI safety boundary enforcement | Liveness-only camera input; FI-02 proves boundary |
| E2E communication protection | CRC-16 + sequence counter on watchdog channel |
| Fault injection test practice | 5 scenarios executed and documented |
| FFI verification practice | 3 interference tests under real load |
| Honest safety documentation | Limitations explicitly documented throughout |

---

## 6. References

- ISO 26262:2018 Parts 1–12 (Road vehicles — Functional safety)
- ISO 21448:2022 (SOTIF)
- IEC 62380:2004 (Reliability data handbook)
- ASPICE v3.1 (Automotive SPICE)
- MISRA C:2012 (Guidelines for the use of the C language in critical systems)
- `docs/safety_analysis/HARA.md`
- `docs/safety_analysis/FMEA.md`
- `docs/safety_mechanisms.md`

---

*This gap analysis is the author's own assessment and has not been independently reviewed.*
*It is provided for educational and portfolio purposes to demonstrate understanding of*
*ISO 26262 requirements and the effort required for full certification.*
