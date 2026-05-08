# architecture.sysml — SysML v2 Pilot Implementation Compatibility Review

**File**: `docs/sysml/architecture.sysml`
**Size**: 597 lines
**Reviewed**: 2026-05-08
**Status**: NOT yet validated by Pilot Implementation (Java not installed)

---

## Overall Assessment

`architecture.sysml` uses **SysML v2 inspired syntax** and is structurally close to
valid SysML v2, but it has **not been validated** by the Pilot Implementation tool.
Several constructs are likely correct; others carry syntax risk and would need
adjustment before the Pilot Implementation will accept the file without errors.

The file is best described as: **SysML v2-style architectural documentation** with
the intent of being importable once tooling is available.

---

## What Looks Correct (Low Risk)

| Construct | Example | Assessment |
|---|---|---|
| `package` block | `package SafetySupervisedEdgeAI {` | ✅ Standard SysML v2 |
| `part def` | `part def RaspberryPi5 {` | ✅ Standard |
| `part` declaration | `part pi5 : RaspberryPi5;` | ✅ Standard |
| `attribute` | `attribute ram_gb : Integer = 8;` | ✅ Standard |
| `port def` | `port def I2CMasterPort {` | ✅ Standard |
| `port` declaration | `port i2c_master_port : I2CMasterPort;` | ✅ Standard |
| `connect` | `connect linux_domain.i2c_master_port to qnx_domain.i2c_slave_port;` | ✅ Standard |
| `doc /* ... */` | `doc /* Educational demonstrator */` | ✅ Standard |
| `state def` | `state def SystemStateMachine {` | ✅ Standard |
| `state` | `state NORMAL { ... }` | ✅ Standard |
| `entry; then INIT;` | Initial transition | ✅ Standard |
| `requirement def` | `requirement def <'SYS-001'> { ... }` | ✅ Standard |

---

## Syntax Risks (Medium Risk)

| Construct | Location | Risk | Notes |
|---|---|---|---|
| `Real[2]` array attribute | Line 100: `attribute range_cm : Real[2] = (2.0, 350.0);` | ⚠️ Medium | Array-valued attributes with tuple initialiser — may need `[2]` syntax adjustment |
| Hex integer literals | Lines 133–136, 152–155, 212: `Integer = 0x40` | ⚠️ Medium | SysML v2 may not support hex literals; may need decimal equivalents (e.g. `64`) |
| `[[fallthrough]]` in doc strings | None in SysML — only in C++ source | ✅ Not present | Confirmed not in the SysML file |
| `action def` with only `doc` | Lines 216–237: `action def StateEntry_INIT { doc /* ... */ }` | ⚠️ Medium | `action def` requires at least one action body in strict SysML v2; doc-only may be accepted as abstract |
| `occurrence def` | Lines 560–570: `occurrence def SystemBoot;` | ⚠️ Medium | `occurrence def` is valid SysML v2 KerML-level; Pilot Implementation support may be partial |

---

## High-Risk Constructs (Likely Need Revision)

| Construct | Location | Risk | Notes |
|---|---|---|---|
| `interaction def` | Lines 441–555: `interaction def Scenario_Startup_M3 {` | 🔴 High | `interaction def` is not a standard SysML v2 keyword; closest valid forms are `action def` with message flows or separate sequence diagram notation |
| `occurrence` instances inside `interaction def` | `occurrence nodes_boot : SystemBoot;` | 🔴 High | `occurrence` member inside `interaction def` — may require `perform` or `action` instead |
| `then` sequencing inside `interaction def` | `then state_safe;` | 🔴 High | `then` is valid inside `state def` transitions, but sequencing `then` inside `interaction def` is non-standard |
| `require` inside `requirement def` | `require system.qnx_domain.watchdog_server;` | ⚠️ Medium | Valid syntax exists; path expressions like `system.qnx_domain.watchdog_server` need the parts to be instantiated |
| `assume watchdog_timeout;` | Line 341: `assume wdg_failure_counter_gte_3;` | ⚠️ Medium | `assume` in requirements is valid KerML but usage as a bare signal name may not parse |

---

## Summary Table

| Category | Count | Action needed |
|---|---|---|
| Low-risk (likely valid) | ~80% of constructs | None — keep as-is |
| Medium-risk | `Real[2]`, hex literals, `action def` doc-only | Minor adjustments |
| High-risk | `interaction def`, `occurrence` in interaction, `then` sequencing | Rewrite as `action def` flows or comment out for first import |

---

## Recommended Migration Strategy

**Do not rewrite architecture.sysml yet.** Instead:

1. **Install Java + Eclipse + Pilot Implementation** (see `sysmlv2_pilot_setup.md`)
2. **Import `minimal_test.sysml` first** — confirms tooling works with safe baseline
3. **Import `architecture.sysml`** — note which lines produce red markers in Eclipse
4. **Fix in priority order**:
   - Replace hex literals with decimal (`0x40` → `64`)
   - Change `Real[2]` to `Real[0..1]` or split into two attributes
   - Replace `interaction def` blocks with `action def` or comment them out
5. **Re-validate after each fix** to isolate errors

**The dynamic interaction scenarios can be preserved as block comments** if the
SysML v2 syntax proves too restrictive for the desired level of narrative detail.
Block comments keep the documentation value without causing parse errors.

---

## What the architecture.sysml IS Good For Right Now

Even without Pilot Implementation validation, the file serves as:
- A structured, readable **MBSE-style architecture document**
- A clear description of **part/port/connection structure** and **state machine**
- **Traceability evidence** for the portfolio demonstrator
- A **starting point** for formal SysML v2 once tooling is set up

---

*Reviewed: 2026-05-08*
*Author: Yunpeng*
*Next action: Install Java (`sudo apt install default-jdk`) and re-validate*
