# 🚦 Traffic Simulator (Modular Road Network Simulation)

A modular, extensible traffic simulation framework for modeling vehicle flow across a network of directional roads and junctions. Designed for easy adaptation to different network topologies, with visualization and performance statistics.

---

# 📌 Overview

This simulator models a road network using a **discrete time-step engine**, where vehicles move through roads and junctions while respecting capacity, routing, and scheduling constraints.

It is built with a **clean modular architecture**, so that on the final day you only modify `main.py` to define a new network.

---

# 🧱 Architecture

At each simulation step:

```
Roads → Junctions → Sinks → Sources
```

This pipeline ensures:

* Vehicles move along roads
* Junctions route vehicles
* Sinks collect completed vehicles
* Sources inject new vehicles

---

# 📁 Project Structure

```
traffic_sim/
    road.py
    junction.py
    vehicle.py
    source.py
    sink.py
    router.py
    engine.py
    stats.py
    visualizer.py

main.py
```

---

# 📦 Component Breakdown

## 🚗 `vehicle.py` — Vehicle

Represents a moving entity in the network.

* Stores:

  * Source and destination
  * Precomputed route (list of node IDs)
  * Route index (current position)
* Tracks:

  * Travel time
  * Waiting time
* Color-coded by destination (for visualization)

---

## 🛣️ `road.py` — Road

Directional connection between two nodes.

* Vehicles enter via `try_enter()`
* Each vehicle gets an `arrival_step`
* `step()` moves vehicles to an **exit queue**

📌 **Queuing happens here**:
Vehicles wait at the end of roads if the junction is congested.

---

## 🚥 `junction.py` — Junction

Handles routing and scheduling.

* Supports:

  * 2-way, 3-way, 4-way intersections
* Scheduling policies:

  * `round_robin`
  * `fifo`
  * `longest_queue`
* Routes vehicles based on their next destination node
* Handles blocking when outgoing roads are full

---

## 🏁 `sink.py` — Sink

Destination node where vehicles exit.

* Absorbs vehicles matching its ID
* Records journey time

---

## 🚘 `source.py` — Traffic Source

Generates vehicles.

Supports:

* **Constant rate** (deterministic)
* **Poisson process** (random, realistic)

Each vehicle:

* Gets a random destination
* Is assigned a route via the router

---

## 🧭 `router.py` — Router

Computes shortest paths.

* Uses **Dijkstra’s algorithm**
* Graph built from roads
* Routes cached for efficiency

---

## ⚙️ `engine.py` — Simulation Engine

Core orchestrator.

* Runs simulation loop
* Maintains global time
* Stores snapshots for animation
* Connects all components

---

## 📊 `stats.py` — Statistics

Tracks and computes:

* Completion rate
* Average / min / max journey time
* Waiting time
* Throughput
* Queue lengths

---

## 🎥 `visualizer.py` — Visualization

Outputs:

1. **Network diagram (PNG)**
2. **Animated simulation (GIF)**
3. **Statistics plots (PNG)**

Features:

* Vehicles shown as moving dots
* Color-coded by destination
* Smooth interpolation between nodes

---

## 🧪 `main.py` — Entry Point (IMPORTANT)

This is the **only file you modify**.

Defines:

* Junctions
* Roads
* Sources
* Sinks
* Network connections

---

# ▶️ How to Run

## 1. Install dependencies

```
pip install matplotlib networkx
```

## 2. Run simulation

```
python main.py
```

---

# 🧪 Testing Strategy

## ✅ Basic Test

* Simple linear network (A → B → C)
* Verify vehicles reach destination

## ✅ Capacity Test

* Reduce road capacity
* Observe queue buildup

## ✅ Congestion Test

* Increase source rate
* Observe delays and blocking

## ✅ Multi-Path Routing

* Add alternate routes
* Verify routing works

## ✅ Multi-Source Test

* Add multiple sources/destinations
* Observe mixed traffic

---

# 🧠 Key Design Decisions

| Problem                      | Solution                               |
| ---------------------------- | -------------------------------------- |
| Where does queuing happen?   | On roads (exit queue)                  |
| How are junctions scheduled? | Configurable policies (RR, FIFO, etc.) |
| How is routing done?         | Dijkstra shortest path                 |
| Simulation type              | Time-step based                        |
| Vehicle movement             | Pipeline (road → junction → sink)      |

---

# 📊 Example Output

* Animated vehicle movement
* Network diagram
* Stats:

  * Vehicles completed
  * Average travel time
  * Peak congestion

---

# 🚀 Extensibility

You can easily extend this to include:

* 🚦 Traffic lights
* 🧠 Congestion-aware routing
* 🚗 Multi-lane roads
* 📈 Real-time analytics
* 🎬 MP4 video export

---

# 🎯 Final Day Usage

When given a new topology:

✔ Modify only `main.py`
✔ Define:

* Nodes (junctions/sinks)
* Roads
* Sources

✔ Run:

```
python main.py
```

✔ Show:

* Animation
* Stats output

---

# 💡 Demo Tips

While presenting:

* Explain pipeline flow
* Highlight routing logic
* Show congestion effects
* Discuss scalability

---

# ✅ Summary

This simulator provides:

* Modular design
* Multi-junction support
* Realistic traffic behavior
* Visualization + analytics

Perfect for demonstrating **network flow, routing, and congestion dynamics** in a clean and extensible way.

---
