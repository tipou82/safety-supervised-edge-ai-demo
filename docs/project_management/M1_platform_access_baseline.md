# M1.0 Platform Access Baseline

## Purpose

Verify that the host PC can reach both Raspberry Pi boards for development, that both boards have a documented OS status, and that the Pi 5 and Pi 400 can communicate over a dedicated direct Ethernet link. This step must be completed before any hardware component testing begins.

The heartbeat and watchdog protocol is **not implemented in M1**. The direct Ethernet link is established and ping-verified only. Protocol implementation is deferred to a later milestone.

---

## Scope

- Host PC SSH access to Raspberry Pi 5
- Host PC SSH access to Raspberry Pi 400 (if an OS is installed)
- Raspberry Pi 5 OS version documented
- Raspberry Pi 400 OS status documented (QNX or Linux fallback noted honestly)
- Direct Ethernet link configured between Pi 5 and Pi 400
- Static IPs assigned and verified with ping in both directions
- Repository cloned or synced to Pi 5
- VS Code Remote SSH workflow to Pi 5 documented

---

## Preferred Network Topology

```
┌──────────────┐    Wi-Fi / LAN / USB-Ethernet    ┌──────────────────┐
│   Host PC    │ ─────────────────────────────────►│  Raspberry Pi 5  │
│  (dev, SSH)  │ ─────────────────────────────────►│  Raspberry Pi 400│
└──────────────┘                                   └──────────────────┘

                   Dedicated direct Ethernet cable
                   (supervisor/watchdog link — M1: ping only)
                   ┌──────────────────┐
                   │  Raspberry Pi 5  │ eth0: 192.168.50.10/24
                   │                  │
                   │  Raspberry Pi 400│ eth0: 192.168.50.20/24
                   └──────────────────┘
```

**Development access** (host PC → each Pi) uses whatever is available: Wi-Fi, home LAN, or a USB Ethernet adapter. This is independent of the supervisor link.

**Supervisor Ethernet link** (Pi 5 ↔ Pi 400) is a dedicated direct cable. In M1 it is used for ping verification only. The heartbeat/watchdog protocol is not implemented yet.

---

## Static IP Plan — Direct Supervisor Ethernet Link

| Board | Interface | Static IP | Subnet |
|---|---|---|---|
| Raspberry Pi 5 | eth0 (or eth1) | 192.168.50.10 | /24 |
| Raspberry Pi 400 | eth0 | 192.168.50.20 | /24 |

These addresses are used exclusively for the Pi 5 ↔ Pi 400 supervisor link. Development SSH access uses a separate interface or network.

---

## Host PC Development Access Assumptions

- Host PC runs Linux, macOS, or Windows with SSH client available.
- Pi 5 is reachable from the host PC via hostname or IP (Wi-Fi, LAN, or USB Ethernet).
- Pi 400 is reachable from the host PC if an OS is installed.
- VS Code with the Remote — SSH extension is installed on the host PC.
- No VPN or firewall blocks SSH on port 22 to either Pi.

---

## Required Hardware

| Item | Purpose |
|---|---|
| Raspberry Pi 5 | Primary development board (Linux/ROS2 domain) |
| Raspberry Pi 400 | Supervisor board (QNX planned / Linux fallback) |
| microSD card (Pi 5) | Ubuntu 22.04 LTS OS |
| microSD card or storage (Pi 400) | OS installation (Linux or QNX if available) |
| Ethernet cable | Direct Pi 5 ↔ Pi 400 link |
| USB-C power supplies (×2) | One per board |
| Host PC with SSH client | Development access |

---

## Step-by-Step Checklist

### 1. Pi 5 Initial Setup

- [ ] Insert microSD with Ubuntu 22.04 LTS (or Raspberry Pi OS 64-bit)
- [ ] Boot Pi 5 and confirm it reaches the login prompt
- [ ] Connect Pi 5 to home LAN or Wi-Fi for host PC access
- [ ] Enable SSH: `sudo systemctl enable ssh && sudo systemctl start ssh`
- [ ] Find Pi 5 IP address: `hostname -I`
- [ ] From host PC: `ssh <user>@<pi5-ip>` — confirm login

### 2. Pi 400 Initial Setup

- [ ] Insert microSD with chosen OS (Linux recommended; QNX if available)
- [ ] Boot Pi 400 and confirm it reaches the login prompt
- [ ] Connect Pi 400 to home LAN or Wi-Fi for host PC access
- [ ] Enable SSH (Linux): `sudo systemctl enable ssh && sudo systemctl start ssh`
- [ ] Find Pi 400 IP address: `hostname -I`
- [ ] From host PC: `ssh <user>@<pi400-ip>` — confirm login
- [ ] If QNX is not available: document Linux fallback decision in logbook

### 3. Capture OS Versions

**On Pi 5:**
```bash
cat /etc/os-release
uname -r
hostname
```

**On Pi 400 (Linux):**
```bash
cat /etc/os-release
uname -r
hostname
```

**On Pi 400 (QNX — if applicable):**
```
uname -a
```

### 4. Configure Direct Ethernet Link (Pi 5 ↔ Pi 400)

Connect an Ethernet cable directly between the Pi 5 Ethernet port and the Pi 400 Ethernet port.

**On Pi 5** — configure static IP on the direct Ethernet interface:
```bash
# Identify the correct interface name
ip link show

# Using nmcli (Ubuntu)
sudo nmcli con add type ethernet ifname eth0 con-name supervisor-link \
  ipv4.method manual ipv4.addresses 192.168.50.10/24

sudo nmcli con up supervisor-link
```

**On Pi 400 (Linux):**
```bash
ip link show

sudo nmcli con add type ethernet ifname eth0 con-name supervisor-link \
  ipv4.method manual ipv4.addresses 192.168.50.20/24

sudo nmcli con up supervisor-link
```

Adjust `eth0` to the actual interface name if it differs (e.g. `enp1s0`, `eth1`).

### 5. Verify Ping in Both Directions

**From Pi 5:**
```bash
ping -c 4 192.168.50.20
```

**From Pi 400:**
```bash
ping -c 4 192.168.50.10
```

Both pings must succeed. Record round-trip time.

### 6. Repository Clone / Sync to Pi 5

```bash
# On Pi 5
git clone https://github.com/tipou82/safety-supervised-edge-ai-demo.git
cd safety-supervised-edge-ai-demo
git log --oneline -5
```

Or if already cloned, sync with:
```bash
git pull origin master
```

### 7. VS Code Remote SSH

- On host PC, open VS Code
- Press `F1` → `Remote-SSH: Connect to Host`
- Enter `ssh <user>@<pi5-ip>`
- Verify VS Code connects and the repository folder opens
- Document VS Code version and Remote SSH extension version in logbook

---

## Pass/Fail Evidence Table

| Check | Command / Method | Expected Result | Pass/Fail | Notes |
|---|---|---|---|---|
| Host PC → Pi 5 SSH | `ssh user@<pi5-ip>` | Login prompt | | |
| Host PC → Pi 400 SSH | `ssh user@<pi400-ip>` | Login prompt | | N/A if no OS |
| Pi 5 OS version | `cat /etc/os-release` | Ubuntu 22.04 or similar | | |
| Pi 400 OS status | `cat /etc/os-release` or manual | Linux or QNX noted | | |
| Pi 5 static IP set | `ip addr show eth0` | 192.168.50.10/24 | | |
| Pi 400 static IP set | `ip addr show eth0` | 192.168.50.20/24 | | |
| Pi 5 → Pi 400 ping | `ping -c 4 192.168.50.20` | 4/4 received | | |
| Pi 400 → Pi 5 ping | `ping -c 4 192.168.50.10` | 4/4 received | | |
| Repo clone on Pi 5 | `git log --oneline -5` | Shows recent commits | | |
| VS Code Remote SSH | VS Code UI | Folder opens | | |

---

## Open Issues

Record any blockers or deviations here during execution:

| ID | Issue | Status |
|---|---|---|
| | | |

---

## Notes

- The heartbeat/watchdog protocol is **not implemented in M1**. The Ethernet link is verified by ping only.
- QNX supervisor setup must not block M1 progress. If QNX is unavailable, document the Linux fallback and continue.
- Actual Ethernet interface names may differ from `eth0`. Confirm with `ip link show` before configuring.
- The supervisor Ethernet link (192.168.50.x/24) is separate from the development access network.
