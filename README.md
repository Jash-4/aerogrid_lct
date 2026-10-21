# AeroGrid-LCT: Real-Time Dynamic Electrical Network Connectivity and Partitioning Engine for Decentralized Microgrids

An autonomous, zero-database, in-memory electrical topology tracking and islanding detection engine engineered in Python. The system is architected around a single advanced data structure: the **Sleator-Tarjan Link-Cut Tree (LCT)**.

---

## 1. Problem Statement & Real-World Domain
Modern power grids are transitioning into decentralized microgrids with distributed renewable sources (Solar PV, Battery Energy Storage Systems, localized gensets). During electrical faults, physical circuit breakers trip within milliseconds, creating isolated sub-networks ("electrical islands").

Conventional software architectures fail in high-voltage physical grids:
- **Relational / Time-Series Databases:** High I/O, disk logging, and serialization latencies (10–500 ms) violate microsecond arc-fault protection windows.
- **Static Graph Algorithms (BFS/DFS):** Require full $O(V + E)$ graph traversals on every breaker trip, creating computational lag across large feeder networks.
- **Disjoint-Set Union (DSU):** Does not support edge deletions (`cut`) because path compression destroys tree hierarchy.

**AeroGrid-LCT** executes edge insertions (`link`), breaker trips (`cut`), reachability checks (`find_root`), and transmission path bottleneck queries in amortized $O(\log V)$ time with a strict $O(V)$ memory footprint.

---

## 2. Team Architecture & Modular Split

| Member | Module File | Architectural Responsibility |
| :--- | :--- | :--- |
| **Member 1** | `lct_node.py` | Core dynamic node structure, path-parent pointer mechanics, and lazy propagation (`push_down`, `push_up`). |
| **Member 2** | `grid_engine.py` | Link-Cut Tree primitives (`_rotate`, `_splay`, `access`, `make_root`, `link`, `cut`, `find_root`). |
| **Member 3** | `grid_patterns.py` | Software architecture: Command Pattern for breaker rollback (`undo`) and Observer Pattern for safety relay alarms. |
| **Member 4** | `main_simulation.py` | Faculty test verification, edge-case assertions (cycles, invalid cuts), and interactive demo CLI. |

---

## 3. Complexity Comparison Matrix

| Operation | Adjacency List + BFS/DFS | Disjoint Set Union (DSU) | Link-Cut Tree (AeroGrid-LCT) |
| :--- | :--- | :--- | :--- |
| **Add Line (`link`)** | $O(1)$ | $O(\alpha(V))$ | **Amortized $O(\log V)$** |
| **Break Line (`cut`)** | $O(V)$ search + splice | **Unsupported** (Requires full rebuild) | **Amortized $O(\log V)$** |
| **Islanding Check** | $O(V + E)$ full search | $O(\alpha(V))$ | **Amortized $O(\log V)$** |
| **Path Bottleneck Query** | $O(V + E)$ path search | **Unsupported** | **Amortized $O(\log V)$** |
| **Memory Footprint** | $O(V + E)$ dynamic lists | $O(V)$ flat parent array | **$O(V)$ pure node pointers** |

---

## 4. System Architecture & UML Class Diagram

AeroGrid-LCT structures electrical telemetry and protection using two Gang-of-Four (GoF) design patterns:
1. **Command Pattern (`IBreakerCommand`):** Provides reversible switchgear actions (`CloseBreakerCommand`, `TripBreakerCommand`) with `.undo()` support for black-start recovery simulations.
2. **Observer Pattern (`IGridObserver`):** Pushes asynchronous notifications to physical protection relays (`MicrogridSafetyRelay`) upon detecting an electrical islanding condition.

```mermaid
classDiagram
    direction TB

    %% ==========================================
    %% 1. CORE DATA STRUCTURE LAYER
    %% ==========================================
    class LCTNode {
        +int bus_id
        +str name
        +float capacity_kva
        +float min_capacity
        +bool is_reversed
        +Optional~LCTNode~ left
        +Optional~LCTNode~ right
        +Optional~LCTNode~ parent
        +__init__(bus_id, name, capacity_kva)
        +is_root() bool
        +push_down() void
        +push_up() void
    }

    %% ==========================================
    %% 2. TOPOLOGY & ALGORITHMIC ENGINE LAYER
    %% ==========================================
    class AeroGridEngine {
        -Optional~IGridObserver~ _observer
        +__init__()
        +set_observer(observer: IGridObserver) void
        +link(u: LCTNode, v: LCTNode) bool
        +cut(u: LCTNode, v: LCTNode) bool
        +is_connected(u: LCTNode, v: LCTNode) bool
        +query_bottleneck(u: LCTNode, v: LCTNode) float
        +find_root(x: LCTNode) LCTNode
        +make_root(x: LCTNode) void
        +access(x: LCTNode) Optional~LCTNode~
        -_rotate(x: LCTNode) void
        -_splay(x: LCTNode) void
        -_push_all_down(x: LCTNode) void
    }

    %% ==========================================
    %% 3. OBSERVER PATTERN LAYER (Safety Relays)
    %% ==========================================
    class IGridObserver {
        <<interface>>
        +on_islanding(bus_a: LCTNode, bus_b: LCTNode, island_root: LCTNode)* void
        +on_grid_restored(bus_a: LCTNode, bus_b: LCTNode)* void
    }

    class MicrogridSafetyRelay {
        +on_islanding(bus_a: LCTNode, bus_b: LCTNode, island_root: LCTNode) void
        +on_grid_restored(bus_a: LCTNode, bus_b: LCTNode) void
    }

    %% ==========================================
    %% 4. COMMAND PATTERN LAYER (Switchgear Control)
    %% ==========================================
    class IBreakerCommand {
        <<interface>>
        +execute()* bool
        +undo()* bool
    }

    class CloseBreakerCommand {
        -AeroGridEngine engine
        -LCTNode u
        -LCTNode v
        -_was_executed: bool
        +__init__(engine, u, v)
        +execute() bool
        +undo() bool
    }

    class TripBreakerCommand {
        -AeroGridEngine engine
        -LCTNode u
        -LCTNode v
        -_was_executed: bool
        +__init__(engine, u, v)
        +execute() bool
        +undo() bool
    }

    %% ==========================================
    %% 5. EXPLICIT RELATIONSHIPS & CARDINALITIES
    %% ==========================================

    %% Self-association within the Link-Cut Tree
    LCTNode "0..1" --> "0..1" LCTNode : left / right (Auxiliary Tree)
    LCTNode "0..1" --> "0..1" LCTNode : parent / path-parent

    %% Engine relationships
    AeroGridEngine "1" o-- "0..1" IGridObserver : aggregates (_observer)
    AeroGridEngine ..> LCTNode : manipulates via access / link / cut

    %% Observer realization & method parameters
    IGridObserver <|.. MicrogridSafetyRelay : realizes
    IGridObserver ..> LCTNode : passes in event parameters

    %% Command realization & associations
    IBreakerCommand <|.. CloseBreakerCommand : realizes
    IBreakerCommand <|.. TripBreakerCommand : realizes

    CloseBreakerCommand "many" --> "1" AeroGridEngine : invokes link() / cut()
    CloseBreakerCommand "many" --> "2" LCTNode : targets bus u, v
    TripBreakerCommand "many" --> "1" AeroGridEngine : invokes cut() / link()
    TripBreakerCommand "many" --> "2" LCTNode : targets bus u, v
```

---

## 5. How to Run
Ensure Python 3.8+ is installed:

```bash
# Verify base node implementation
python lct_node.py

# Verify engine primitives
python grid_engine.py

# Verify design patterns
python grid_patterns.py

# Run complete simulation and interactive CLI
python main_simulation.py
```