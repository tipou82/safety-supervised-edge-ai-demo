# SysML v2 Pilot Implementation — Setup Notes

**Host**: Ubuntu 22.04.5 LTS (x86_64)
**Purpose**: Validate and visualise `docs/sysml/architecture.sysml` for the
Safety-Supervised Edge AI Demonstrator project.

This is an **educational demonstrator** only. No ISO 26262 certification is claimed.

---

## 1. Prerequisites

### 1.1 Check installed tools

```bash
java -version
git --version
plantuml -version
dot -V
```

**Status on this machine (checked 2026-05-08):**

| Tool | Required version | Status |
|---|---|---|
| Java (JDK) | 11 or 17 recommended | ❌ Not installed |
| git | Any recent | ✅ 2.34.1 |
| plantuml | Any | ❌ Not installed |
| graphviz (dot) | Any | ❌ Not installed |

### 1.2 Install missing packages

Run the following (enter your sudo password when prompted):

```bash
sudo apt update
sudo apt install -y git default-jdk plantuml graphviz
```

**Note**: `default-jdk` on Ubuntu 22.04 installs OpenJDK 11. The Pilot Implementation
requires Java 11+. Do not automate sudo password entry.

Verify after install:

```bash
java -version
plantuml -version
dot -V
```

---

## 2. Clone SysML v2 Pilot Implementation

```bash
mkdir -p ~/tools
cd ~/tools
git clone https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation.git
```

If already cloned, update instead:

```bash
cd ~/tools/SysML-v2-Pilot-Implementation
git pull
```

**Status**: Cloned successfully 2026-05-08 to `~/tools/SysML-v2-Pilot-Implementation/`.

### Repository structure

```
SysML-v2-Pilot-Implementation/
  kerml/                  ← KerML grammar and Xtext sources
  sysml/                  ← SysML v2 grammar and Xtext sources
  sysml.library/          ← Standard SysML v2 library
  tool-support/           ← Jupyter/API server support
  org.omg.*/              ← 32 Eclipse plugin projects
  pom.xml                 ← Maven build file
  mvnw / mvnw.cmd         ← Maven wrapper
  README.adoc
```

---

## 3. Eclipse Modeling Tools — Installation (Manual Step)

The Pilot Implementation is distributed as an Eclipse plugin. You need
**Eclipse Modeling Tools** as the base IDE.

### 3.1 Download Eclipse Modeling Tools

1. Go to: https://www.eclipse.org/downloads/packages/
2. Download **Eclipse Modeling Tools** (not Eclipse IDE for Java — the Modeling variant)
3. Extract to `~/tools/eclipse/` (or similar)
4. Launch: `~/tools/eclipse/eclipse`

### 3.2 Install SysML v2 Plugin via Eclipse Update Site

Two options:

**Option A — Nightly update site (recommended for latest)**:
1. Eclipse → Help → Install New Software
2. Add site: `https://sysml.org/sysml-api-20240901/`
   *(Check https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation for current URL)*
3. Select all SysML v2 features
4. Accept licence → Finish → Restart Eclipse

**Option B — Build from source with Maven**:
```bash
cd ~/tools/SysML-v2-Pilot-Implementation
./mvnw package -DskipTests
```
Then install the generated update site from `org.omg.sysml.updatesite/target/repository/`.

### 3.3 Import the SysML v2 project

1. Eclipse → File → Import → Existing Projects into Workspace
2. Navigate to `~/tools/SysML-v2-Pilot-Implementation/`
3. Import all projects
4. Wait for Xtext build to complete

---

## 4. PlantUML and Graphviz

PlantUML is used for rendering UML/SysML diagrams as images from text.
Graphviz (`dot`) is a PlantUML dependency for layout.

After installing:

```bash
# Test PlantUML with a simple diagram
echo '@startuml\nA -> B : hello\n@enduml' | plantuml -pipe > /tmp/test.png
xdg-open /tmp/test.png
```

**Note**: PlantUML does **not** natively support SysML v2 textual syntax. It supports
a subset of SysML block diagrams via its own notation. For full SysML v2 validation
and rendering, use the Eclipse plugin.

---

## 5. Using the Pilot Implementation

### 5.1 Open a SysML v2 file

After Eclipse + plugin are installed:

1. Create a new SysML v2 project (File → New → SysML v2 Project)
2. Copy or link `docs/sysml/architecture.sysml` into the project
3. Eclipse will validate syntax automatically (red markers = errors)
4. Use the SysML v2 diagram views for rendering

### 5.2 Jupyter Notebook API server (alternative)

The `tool-support/` directory contains a Jupyter-based API server for
programmatic model access. Requires Python 3.8+ and additional setup:

```bash
cd ~/tools/SysML-v2-Pilot-Implementation/tool-support
pip install -r requirements.txt
jupyter notebook
```

See `tool-support/README.md` for details.

---

## 6. Known Limitations

| Limitation | Detail |
|---|---|
| Java required | Pilot Implementation will not run without JDK 11+ |
| Eclipse only | No standalone CLI validator in the free distribution |
| PlantUML gap | PlantUML cannot parse SysML v2 textual syntax directly |
| Build time | Maven source build can take 20–30 min on first run |
| Plugin URL | Update site URL changes with releases — always check the README.adoc |
| `architecture.sysml` compatibility | File uses SysML v2 syntax but has not been validated by the Pilot Implementation yet — see Section 7 |

---

## 7. Current architecture.sysml — Compatibility Notes

See `docs/tooling/sysml_compatibility_review.md` for a full review.

**Summary**: `docs/sysml/architecture.sysml` uses SysML v2 inspired syntax and is
likely structurally close to valid SysML v2, but has not been validated by the Pilot
Implementation. Some constructs (interaction defs, occurrence defs, inline doc strings)
may need adjustment. Review before importing.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `java: command not found` | `sudo apt install default-jdk` |
| `plantuml: command not found` | `sudo apt install plantuml` |
| `dot: command not found` | `sudo apt install graphviz` |
| Eclipse build errors after import | Ensure Java 11 is the workspace JDK (Window → Preferences → Java → Installed JREs) |
| SysML v2 files not recognised | Confirm plugin installed; try File → Open With → SysML v2 Editor |
| Maven build fails — memory | Add `-Xmx2g` to `MAVEN_OPTS`: `export MAVEN_OPTS="-Xmx2g"` |
| Plugin update site not found | Check current URL in `README.adoc` of cloned repo |

---

*Last updated: 2026-05-08*
*Author: Yunpeng*
