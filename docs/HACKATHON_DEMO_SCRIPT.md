# DAA Hackathon Presentation & Demonstration Script
**Project**: Firebreak-Cordon (Problem #92: Cyber Incident Response Planner)  
**Target Duration**: 3 to 5 Minutes  
**Audience**: Technical Judges & DAA Evaluators  

---

## 1. The 30-Second Elevator Pitch
> *"In modern enterprise networks, Security Operations Centers are inundated with hundreds of alerts every hour. Conventional incident response systems prioritize alerts solely on raw severity or CVSS scores. This is a fatal flaw: an isolated printer with a 'Critical' severity alert often poses zero threat to enterprise operations, while a 'Low' severity alert on an endpoint connected to your core identity provider or database can lead to a catastrophic total breach.*
>
> *Firebreak-Cordon is an algorithm-centric decision platform that models cyber lateral movement and service dependencies. Using a versioned Max-Heap, Dijkstra shortest paths over logarithmic probability weights, BFS blast radius reachability, and an iterative 3-color DFS topological sorter, it automatically determines response prioritization, identifies optimal containment cutoffs, and generates dependency-safe recovery plans."*

---

## 2. Live Demo Script (Step-by-Step)

### Step 1: The Core Paradox (Priority Queue & Explainability)
1. **Action**: Open the UI at `http://localhost:5173` on the **Worked Example (7 Nodes)** scenario. Point to the **Priority Queue** card on the dashboard.
2. **Talking Point**:
   > *"Notice the incident queue ranking. We have two simultaneous alerts:
   > - `INC-1`: Endpoint Laptop (`LT`) with Severity 3 and Confidence 0.8.
   > - `INC-2`: Peripheral Printer (`P`) with Severity 9 and Confidence 0.9.
   >
   > Under legacy severity-first triaging, the printer would be addressed first. But Firebreak-Cordon ranks `INC-1` as **Rank #1** with a priority score of **49.92**, while `INC-2` is ranked **Rank #2** with a score of **8.10**."*
3. **Action**: Click on the `INC-1` card to expand the mathematical breakdown modal.
4. **Talking Point**:
   > *"Here is the math:
   > $$Score = \text{Severity} \times \text{Confidence} \times (\text{Own Criticality} + \text{Reachable Weighted Criticality})$$
   > The printer has no lateral paths, so its reachable criticality is $0$. The laptop, however, has directed network pathways reaching Login Server `L`, App Server `A`, and Database `D` (criticality 10). The reachable weighted criticality adds $+18.8$, lifting the laptop's impact to $20.8$ and its score to $49.92$."*

---

### Step 2: Lateral Breach Traversal & Optimal Containment
1. **Action**: Switch to the **Attack Paths** tab. Select Source `LT` and Target `D`. Click **Find Path**.
2. **Talking Point**:
   > *"To find the attacker's most probable trajectory towards our critical database, we cannot simply use hop counts. Network pivot edges have probabilities $p \in (0, 1.0]$. To maximize the path product $\prod p_i$, we transform the weights into additive costs:
   > $$w = -\ln(p) \ge 0$$
   > Running Dijkstra yields the exact most probable path: `LT -> L -> D` with cumulative probability $0.56$."*
3. **Action**: Point to the **Containment Recommendation** box below the path.
4. **Talking Point**:
   > *"Rather than severing the database itself, the engine calculates the differential risk reduction across all intermediate nodes. It recommends isolating intermediate node `L`. Isolating `L` removes $65.38\%$ of the attack risk with an acceptable disruption cost."*
5. **Action**: Click **Isolate Node L** on the Cytoscape graph canvas. Show the visual severing of node `L` and the recomputed blast radius.

---

### Step 3: Dependency-Safe Recovery Ordering (Iterative DFS)
1. **Action**: Switch to the **Restore Plan** tab. Point to the step-by-step restoration pipeline.
2. **Talking Point**:
   > *"After containment, how do we bring systems back online safely? If Web Server `W` starts before App Server `A`, or `A` starts before Database `D`, services crash or enter corrupt states.
   > 
   > We model functional requirements as a directed dependency graph where $u \to v$ means $u$ requires $v$. We built an iterative three-color DFS that computes a safe topological restoration order:
   > $$D \to L \to A \to B \to LT \to P \to W$$
   > Notice that dependencies precede dependents: Database $D$ boots before App Server $A$, and App Server $A$ boots before Web Server $W$."*
3. **Talking Point (Robustness)**:
   > *"Crucially, this is an **iterative** DFS using an explicit call stack—meaning it has **zero recursion limit** and can handle arbitrary graph depths without risking Python `RecursionError`. It also actively detects circular dependencies (e.g. $A \to B \to A$) and flags the exact deadlock cycle."*

---

### Step 4: Multi-Strategy Discrete Event Simulation
1. **Action**: Switch to the **Simulation** tab. Click **Run 3-Strategy Comparison**.
2. **Talking Point**:
   > *"Finally, we validated our algorithms using a discrete event simulator with deterministic seeding. We benchmarked three incident response strategies across identical scenarios:
   > 1. **FCFS (First-Come-First-Served)**: Triages incidents chronologically.
   > 2. **Severity-Only**: Triages by raw incident severity.
   > 3. **Graph-Aware (Firebreak-Cordon)**: Triages by reachable graph impact and dynamically re-evaluates risk after each containment step.
   >
   > The results are definitive: Graph-Aware response cuts total accumulated damage by **~40%** compared to Severity-Only triaging."*

---

## 3. Anticipated Judge Questions & Bulletproof Answers

### Q1: *"Did you use external graph libraries like NetworkX for your algorithms?"*
> **Answer**:  
> *"No. The entire core engine in `backend/planner/core/` is implemented from scratch using Python's standard library (`heapq`, `collections.deque`, and `math`). There are zero external dependencies in the core. NetworkX is imported strictly inside our unit tests as an independent mathematical oracle to cross-verify that our Dijkstra and BFS implementations produce 100% identical outputs."*

### Q2: *"Why did you use $-\ln(p)$ as the edge weight in Dijkstra?"*
> **Answer**:  
> *"In probabilistic networks, the probability of traversing a sequence of independent edges is multiplicative: $P = \prod p_i$. Dijkstra's algorithm is designed to minimize additive sums, not products. Since $p \in (0, 1.0]$, taking $-\ln(p)$ produces non-negative numbers $w \ge 0$. Minimizing $\sum -\ln(p_i)$ is mathematically equivalent to maximizing $\prod p_i$. Because weights are strictly non-negative, Dijkstra is guaranteed to terminate in optimal time $O((V + E) \log V)$ without negative-weight cycles."*

### Q3: *"How does your priority queue handle alert score changes or incident cancellations?"*
> **Answer**:  
> *"We implemented a versioned max-heap (`IncidentQueue`). When an incident's score changes—such as when a node is isolated or an incident is resolved—the engine increments that incident's version counter and pushes the new tuple into the heap. Stale entries are lazily discarded when popped if their version does not match the active state. Furthermore, we break score ties deterministically using ISO-8601 timestamps, ensuring deterministic FIFO tie-breaking."*

### Q4: *"Can your DFS handle massive dependency chains without crashing?"*
> **Answer**:  
> *"Yes. Recursive DFS in Python hits `sys.getrecursionlimit()` (typically 1,000 frames) and raises a `RecursionError`. We engineered an iterative DFS using a three-color state machine (Unvisited, Visiting, Visited) maintaining its own heap-allocated frame stack. We tested this explicitly against a 2,500-node linear dependency chain, where it completed in under 5 milliseconds with zero recursion errors."*

### Q5: *"What is the complexity and scalability of the platform?"*
> **Answer**:  
> *"Our scalability benchmarks prove that for enterprise networks up to 1,000 nodes:
> - Blast Radius (BFS + Dijkstra): $< 150\text{ms}$
> - Attack Path Shortest Path: $< 50\text{ms}$
> - Topological Sort & Cycle Detection: $< 50\text{ms}$
> The entire test suite of 61 automated tests and 8 live server smoke tests runs in under half a second."*

---

## 4. Key DAA Concepts Demonstrated Checklist
- [x] **Priority Queue / Max-Heap**: Explainable multi-factor scoring with lazy version invalidation.
- [x] **Graph Traversal (BFS)**: Unweighted lateral hop counting.
- [x] **Shortest Path (Dijkstra)**: Logarithmic probability transformation with predecessor backtracking.
- [x] **Directed Acyclic Graphs (DAG) & Topological Sort**: Safe restoration ordering.
- [x] **Cycle Detection (DFS Three-Coloring)**: Circular dependency deadlock identification.
- [x] **Discrete Event Simulation**: Dynamic graph re-weighting under remediation policies.
