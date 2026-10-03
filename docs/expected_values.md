# Hand-Calculated and Verified Reference Values

This document records the exact expected values for test assertions across all algorithm modules in upcoming phases. All values have been hand-calculated and cross-verified via independent scripts.

---

## 1. Worked Example Network (`worked_example.json`)

### Network Overview
- **Nodes**:
  - `LT` (Laptop, Endpoint, criticality 2, status compromised)
  - `P` (Printer, Peripheral, criticality 1, status compromised)
  - `A` (App Server, App, criticality 7, status healthy)
  - `B` (Backup, Backup, criticality 8, status healthy)
  - `L` (Login Server, Auth, criticality 9, status healthy)
  - `D` (Database, Database, criticality 10, status healthy)
  - `W` (Web Server, Web, criticality 6, status healthy)
  - `critical_threshold` = 8 (Critical assets: `B`, `L`, `D`)
- **Network Edges**:
  - `LT -> L` ($p = 0.8$)
  - `LT -> A` ($p = 0.4$)
  - `L -> D` ($p = 0.7$)
  - `A -> D` ($p = 0.6$)
  - `L -> B` ($p = 0.5$)
- **Dependency Edges** (source requires target):
  - `A -> D` ($A$ requires $D$)
  - `A -> L` ($A$ requires $L$)
  - `W -> A` ($W$ requires $A$)
- **Incidents**:
  - `INC-1` on `LT`: severity = 3, confidence = 0.8
  - `INC-2` on `P`: severity = 9, confidence = 0.9

---

### A. Blast Radius from `LT`
Traversing directed `network` edges:
| Target Node | BFS Hops | Path(s) | Path Probabilities | Best Reach Probability ($P$) |
|---|---|---|---|---|
| `L` | 1 | `LT -> L` | $0.80$ | **0.80** |
| `A` | 1 | `LT -> A` | $0.40$ | **0.40** |
| `D` | 2 | `LT -> L -> D`<br>`LT -> A -> D` | $0.8 \times 0.7 = 0.56$<br>$0.4 \times 0.6 = 0.24$ | **0.56** (via `L`) |
| `B` | 2 | `LT -> L -> B` | $0.8 \times 0.5 = 0.40$ | **0.40** |

*Note: Blast radius of `P` is empty (`{}`) as `P` has no outgoing network edges.*

---

### B. Impact & Priority Scores
Formula:
$$\text{impact} = \text{own\_criticality} + \sum_{v \in \text{blast}} \big(\text{criticality}(v) \times \text{reach\_prob}(v)\big)$$
$$\text{score} = \text{severity} \times \text{confidence} \times \text{impact}$$

#### For Incident `INC-1` on `LT`:
- $\text{own\_criticality} = 2$
- Reachable weighted criticality:
  $$\text{reach\_weighted} = (9 \times 0.80) + (7 \times 0.40) + (10 \times 0.56) + (8 \times 0.40)$$
  $$\text{reach\_weighted} = 7.20 + 2.80 + 5.60 + 3.20 = 18.80$$
- $\text{impact}(\text{LT}) = 2 + 18.80 = \mathbf{20.80}$
- $\text{score}(\text{INC-1}) = 3 \times 0.8 \times 20.80 = \mathbf{49.92}$

#### For Incident `INC-2` on `P`:
- $\text{own\_criticality} = 1$
- $\text{reach\_weighted} = 0.0$
- $\text{impact}(\text{P}) = \mathbf{1.00}$
- $\text{score}(\text{INC-2}) = 9 \times 0.9 \times 1.00 = \mathbf{8.10}$

#### Strategy Ranking Comparison:
- **Graph-Aware Order**: `INC-1` (49.92) > `INC-2` (8.10) $\implies$ **`INC-1` handled first**.
- **Severity-Only Order**: `INC-2` (severity 9) > `INC-1` (severity 3) $\implies$ **`INC-2` handled first**.

---

### C. Most Probable Attack Path: `LT -> D`
Additive edge weights: $w = -\ln(p)$.
- Route 1 (`LT -> L -> D`):
  $$w = -\ln(0.8) + -\ln(0.7) \approx 0.22314 + 0.35667 = 0.57982$$
  $$P = \exp(-0.57982) = \mathbf{0.56}$$
- Route 2 (`LT -> A -> D`):
  $$w = -\ln(0.4) + -\ln(0.6) \approx 0.91629 + 0.51083 = 1.42712$$
  $$P = \exp(-1.42712) = \mathbf{0.24}$$
- **Shortest Path**: `['LT', 'L', 'D']` with probability **0.56**.

---

### D. Containment Simulation: Isolating Node `L`
When `L` and its incident network edges (`LT -> L`, `L -> D`, `L -> B`) are removed:
- Remaining reachable from `LT`:
  - `A`: hops = 1, $p = 0.40$
  - `D`: hops = 2 (via `LT -> A -> D`), $p = 0.4 \times 0.6 = 0.24$
- Recalculated impact on `LT`:
  $$\text{impact}_{\text{after}} = 2 + (7 \times 0.40) + (10 \times 0.24) = 2 + 2.80 + 2.40 = \mathbf{7.20}$$
- Recalculated score for `INC-1`:
  $$\text{score}_{\text{after}} = 3 \times 0.8 \times 7.20 = \mathbf{17.28}$$
- Risk reduction:
  $$\Delta \text{Risk} = \frac{49.92 - 17.28}{49.92} = \frac{32.64}{49.92} \approx \mathbf{65.3846\%} \quad (\approx 65.4\%)$$
- Disruption cost = criticality(`L`) = **9**.

---

### E. Dependency-Safe Restore Order
Functional dependencies:
- $A \to D$ ($A$ requires $D$) $\implies D$ must be restored before $A$.
- $A \to L$ ($A$ requires $L$) $\implies L$ must be restored before $A$.
- $W \to A$ ($W$ requires $A$) $\implies A$ must be restored before $W$.
- Nodes $B, \text{LT}, P$ have no functional dependencies.
- **Validation Rule**: Any valid topological sort must satisfy:
  $$\text{index}(D) < \text{index}(A), \quad \text{index}(L) < \text{index}(A), \quad \text{index}(A) < \text{index}(W)$$
  Example valid sequences:
  - `['D', 'L', 'A', 'W', 'B', 'LT', 'P']`
  - `['L', 'D', 'B', 'LT', 'P', 'A', 'W']`

---

## 2. Enterprise Demo Network (`demo_network.json`)

### Network Summary
- 20 nodes representing corporate DMZ, web frontends, app clusters, AD authentication, databases, endpoints, and peripherals.
- Critical threshold: 8 (Critical nodes: `APP-02` [8], `AUTH-AD` [9], `BASTION-HOST` [9], `DB-PRIMARY` [10], `DB-REPLICA` [9], `BACKUP-VAULT` [8]).
- Incidents:
  - `INC-DEMO-01` on `LAPTOP-ENG` (severity 3, confidence 0.85)
  - `INC-DEMO-02` on `PRINTER-HR` (severity 10, confidence 0.95)

### Expected Metrics:
- **`LAPTOP-ENG` Blast Radius**:
  - `VPN-GATEWAY`: hops = 1, $p = 0.9000$ (crit 6, wt = 5.4000)
  - `AUTH-AD`: hops = 2, $p = 0.7200$ (crit 9, wt = 6.4800)
  - `INTERNAL-DNS`: hops = 2, $p = 0.7200$ (crit 5, wt = 3.6000)
  - `BASTION-HOST`: hops = 3, $p = 0.5040$ (crit 9, wt = 4.5360)
  - `APP-01`: hops = 3, $p = 0.4320$ (crit 7, wt = 3.0240)
  - `MONITOR-SIEM`: hops = 3, $p = 0.4320$ (crit 6, wt = 2.5920)
  - `DB-PRIMARY`: hops = 4, $p = 0.4284$ (crit 10, wt = 4.2840)
  - `DB-REPLICA`: hops = 5, $p = 0.38556$ (crit 9, wt = 3.4700)
  - `BACKUP-VAULT`: hops = 5, $p = 0.2142$ (crit 8, wt = 1.7136)
- **Sum Reachable Weighted Criticality**: $35.0996$
- **Impact (`LAPTOP-ENG`)**: $2 + 35.0996 = \mathbf{37.10}$
- **Score (`INC-DEMO-01`)**: $3 \times 0.85 \times 37.0996 = \mathbf{94.60}$
- **`PRINTER-HR`**: Isolated peripheral, $\text{impact} = 1.00$, $\text{score}(\text{INC-DEMO-02}) = 10 \times 0.95 \times 1.00 = \mathbf{9.50}$.
- **Prioritization**:
  - Graph-aware ranking: `INC-DEMO-01` (#1, score 94.60) > `INC-DEMO-02` (#2, score 9.50)
  - Severity-only ranking: `INC-DEMO-02` (#1, severity 10) > `INC-DEMO-01` (#2, severity 3)
- **Most Probable Path `LAPTOP-ENG -> DB-PRIMARY`**:
  - `['LAPTOP-ENG', 'VPN-GATEWAY', 'AUTH-AD', 'BASTION-HOST', 'DB-PRIMARY']`
  - Total Probability: $0.9 \times 0.8 \times 0.7 \times 0.85 = \mathbf{0.4284}$ ($w = 0.8477$)
