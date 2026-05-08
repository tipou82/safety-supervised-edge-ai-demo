# SysML v2 Pilot Implementation — Setup Notes

**Host**: Ubuntu 22.04.5 LTS (x86_64)
**Status**: Investigation complete — Mermaid chosen as diagram approach (see decision below).

This is an **educational demonstrator** only. No ISO 26262 certification is claimed.

---

## Decision: Mermaid diagrams over SysML v2 Pilot Implementation

After investigating the SysML v2 Pilot Implementation toolchain, the project uses
**Mermaid diagrams in `docs/sysml/architecture_diagrams.md`** as the single source of truth
for all architecture diagrams. Reasons:

| Path | Outcome |
|---|---|
| Eclipse Pilot Implementation (from source) | Blocked — `sysand.so` proprietary native library missing from public Maven |
| Eclipse via Oomph installer | Complex — requires Sensmetry-controlled package |
| SysIDE (VS Code) diagram rendering | Commercial — 126€/month for graphical views |
| Jupyter SysML v2 kernel | Text validation only, no diagrams |
| **Mermaid in `.md` (chosen)** | **Free, renders on GitHub, single source of truth** |

All diagram rules are documented in `AGENTS.md` (Mermaid diagram rules section).

---

## Prerequisites (for future reference if Eclipse path is revisited)

```bash
sudo apt update
sudo apt install -y git openjdk-17-jdk plantuml graphviz
```

| Tool | Required version | Status on this machine |
|---|---|---|
| Java (JDK) | 17+ | Installed (openjdk-17) |
| git | Any recent | ✅ 2.34.1 |
| plantuml | Any | Installed |
| graphviz (dot) | Any | Installed |

---

## SysML v2 Pilot Implementation Clone

Cloned 2026-05-08 to `~/tools/SysML-v2-Pilot-Implementation/` (not committed to repo).

```bash
# To update:
cd ~/tools/SysML-v2-Pilot-Implementation && git pull
```

---

## Known Blockers (Eclipse path)

| Blocker | Detail |
|---|---|
| `sysand.so` missing | `com.sensmetry:sysand-maven-plugin` requires a proprietary native library not in public Maven — Maven build fails with `UnsatisfiedLinkError` |
| Java 17 required | Tycho 4.x (used in the build) requires Java 17; `default-jdk` on Ubuntu 22.04 installs Java 11 |
| No pre-built update site | GitHub releases (2026-03) contain only Jupyter kernel and KPAR library files — no Eclipse update site ZIP |
| SysIDE graphical rendering | Free tier: syntax highlighting and validation only; diagrams require commercial licence |

---

## Troubleshooting (if revisiting Eclipse path)

| Problem | Fix |
|---|---|
| `java: command not found` | `sudo apt install openjdk-17-jdk` |
| `sysand.so` build failure | Use Oomph installer instead of Maven from source |
| Plugin update site not found | Check current URL in `README.adoc` of cloned repo |
| Maven memory error | `export MAVEN_OPTS="-Xmx2g"` |

---

*Last updated: 2026-05-08*
*Author: Yunpeng*
