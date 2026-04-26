"""
main.py - Traffic Simulation: Sample 7-Junction Network

Network topology (planar, < 10 junctions, < 20 directional roads):

         S1 ──► J1 ──► J2 ──► SINK_E
                 │      │
                 ▼      ▼
         S2 ──► J3 ──► J4 ──► SINK_S
                 │      │
                 ▼      ▼
                J5 ──► J6 ──► SINK_W
                 │
                 ▼
               SINK_N

This is the PLACEHOLDER network. On the last day of the module,
ONLY THIS FILE needs to be modified to define the actual network.
All library code in traffic_sim/ remains unchanged.

Usage:  python3 main.py
"""

import os
import sys

# ── Ensure traffic_sim package is importable ──────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from traffic_sim import (
    Road, Junction, TrafficSource, Sink, Router, SimEngine, Visualizer
)

# ═══════════════════════════════════════════════════════════════════════════════
#  SIMULATION PARAMETERS  (modify as needed)
# ═══════════════════════════════════════════════════════════════════════════════
SIM_STEPS       = 120       # total simulation time steps
VEHICLE_RATE    = 0.4       # vehicles per step per source (Poisson mean)
SPAWN_MODE      = "poisson" # "poisson" or "constant"
RECORD_EVERY    = 1         # snapshot every N steps (1 = every step)
ANIMATION_FPS   = 10        # frames per second in output GIF
MAX_ANIM_FRAMES = 180       # cap animation length
OUTPUT_DIR      = "output"  # directory for output files

# ═══════════════════════════════════════════════════════════════════════════════
#  NETWORK DEFINITION
#  ─────────────────────────────────────────────────────────────────────────────
#  To adapt for the actual assignment topology on the last day:
#    1. Define node positions (x, y)
#    2. Create Junction / Sink / TrafficSource objects
#    3. Create Road objects connecting them
#    4. Register everything with the engine
# ═══════════════════════════════════════════════════════════════════════════════

def build_network(engine: SimEngine):
    """
    Define and register the road network.

    Current topology — a 2×3 grid of junctions with 2 sources and 4 sinks:

        S1(0,4) ──r1──► J1(2,4) ──r3──► J2(4,4) ──r5──► SINK_E(6,4)
                          │  ▲            │  ▲
                          r6  r7          r8  r9
                          ▼  │            ▼  │
        S2(0,2) ──r2──► J3(2,2) ──r10──► J4(4,2) ──r11──► SINK_S(6,2)
                          │                │
                          r12              r13
                          ▼                ▼
                         J5(2,0) ──r14──► J6(4,0) ──r15──► SINK_W(6,0)
                          │
                          r16
                          ▼
                        SINK_N(2,-2)
    """

    # ── Junctions ────────────────────────────────────────────────────────────
    J1 = Junction("J1", position=(2, 4), scheduling="round_robin", throughput=2)
    J2 = Junction("J2", position=(4, 4), scheduling="round_robin", throughput=2)
    J3 = Junction("J3", position=(2, 2), scheduling="longest_queue", throughput=2)
    J4 = Junction("J4", position=(4, 2), scheduling="round_robin", throughput=2)
    J5 = Junction("J5", position=(2, 0), scheduling="round_robin", throughput=1)
    J6 = Junction("J6", position=(4, 0), scheduling="round_robin", throughput=1)

    for j in [J1, J2, J3, J4, J5, J6]:
        engine.add_junction(j)

    # ── Sinks ────────────────────────────────────────────────────────────────
    SINK_E = Sink("SINK_E", position=(6, 4))
    SINK_S = Sink("SINK_S", position=(6, 2))
    SINK_W = Sink("SINK_W", position=(6, 0))
    SINK_N = Sink("SINK_N", position=(2, -2))

    for sk in [SINK_E, SINK_S, SINK_W, SINK_N]:
        engine.add_sink(sk)

    # ── Roads ────────────────────────────────────────────────────────────────
    #  Road(id, start_node, end_node, length, speed_limit, capacity)
    #  travel_time = ceil(length / speed_limit)

    roads = [
        # Sources → first junctions
        Road("r1",  "S1",     "J1",     length=40,  speed_limit=10, capacity=15),
        Road("r2",  "S2",     "J3",     length=40,  speed_limit=10, capacity=15),

        # Horizontal top row
        Road("r3",  "J1",     "J2",     length=50,  speed_limit=10, capacity=12),
        Road("r5",  "J2",     "SINK_E", length=30,  speed_limit=10, capacity=10),

        # Horizontal middle row
        Road("r10", "J3",     "J4",     length=50,  speed_limit=10, capacity=12),
        Road("r11", "J4",     "SINK_S", length=30,  speed_limit=10, capacity=10),

        # Horizontal bottom row
        Road("r14", "J5",     "J6",     length=50,  speed_limit=10, capacity=8),
        Road("r15", "J6",     "SINK_W", length=30,  speed_limit=10, capacity=8),

        # Vertical left column (downward)
        Road("r6",  "J1",     "J3",     length=50,  speed_limit=10, capacity=10),
        Road("r12", "J3",     "J5",     length=50,  speed_limit=10, capacity=10),
        Road("r16", "J5",     "SINK_N", length=40,  speed_limit=10, capacity=8),

        # Vertical right column (downward)
        Road("r8",  "J2",     "J4",     length=50,  speed_limit=10, capacity=10),
        Road("r13", "J4",     "J6",     length=50,  speed_limit=10, capacity=8),

        # Upward links (feedback paths — make routing interesting)
        Road("r7",  "J3",     "J1",     length=50,  speed_limit=8,  capacity=8),
        Road("r9",  "J4",     "J2",     length=50,  speed_limit=8,  capacity=8),
    ]

    for road in roads:
        engine.add_road(road)

    # ── Connect roads to junctions ───────────────────────────────────────────
    # engine.connect(road, start_junction_or_None, end_junction_or_None)
    # Pass None when the endpoint is a Source or Sink (they manage their own roads)

    connections = [
        ("r1",  None, J1),
        ("r2",  None, J3),
        ("r3",  J1,   J2),
        ("r5",  J2,   None),   # ends at SINK_E (sink drains it)
        ("r6",  J1,   J3),
        ("r7",  J3,   J1),
        ("r8",  J2,   J4),
        ("r9",  J4,   J2),
        ("r10", J3,   J4),
        ("r11", J4,   None),   # ends at SINK_S
        ("r12", J3,   J5),
        ("r13", J4,   J6),
        ("r14", J5,   J6),
        ("r15", J6,   None),   # ends at SINK_W
        ("r16", J5,   None),   # ends at SINK_N
    ]

    road_map = engine.roads
    for rid, start_j, end_j in connections:
        engine.connect(road_map[rid], start_j, end_j)

    # Register sink incoming roads
    SINK_E.add_incoming(road_map["r5"])
    SINK_S.add_incoming(road_map["r11"])
    SINK_W.add_incoming(road_map["r15"])
    SINK_N.add_incoming(road_map["r16"])

    # ── Traffic Sources ──────────────────────────────────────────────────────
    destinations = ["SINK_E", "SINK_S", "SINK_W", "SINK_N"]

    S1 = TrafficSource(
        source_id="S1",
        position=(0, 4),
        outgoing_road=road_map["r1"],
        destinations=destinations,
        rate=VEHICLE_RATE,
        mode=SPAWN_MODE,
        router=engine.router,
        start_step=0,
        rng_seed=42,
    )

    S2 = TrafficSource(
        source_id="S2",
        position=(0, 2),
        outgoing_road=road_map["r2"],
        destinations=destinations,
        rate=VEHICLE_RATE * 0.8,   # slightly lower rate on second source
        mode=SPAWN_MODE,
        router=engine.router,
        start_step=5,
        rng_seed=99,
    )

    for src in [S1, S2]:
        engine.add_source(src)

    print(f"[Network] Junctions: {len(engine.junctions)}")
    print(f"[Network] Roads    : {len(engine.roads)}")
    print(f"[Network] Sources  : {len(engine.sources)}")
    print(f"[Network] Sinks    : {len(engine.sinks)}")
    print(f"[Network] Destinations: {destinations}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Initialise engine
    engine = SimEngine()

    # 2. Build the network (roads, junctions, sources, sinks)
    build_network(engine)

    # 3. Pre-warm the router (optional but fast for small networks)
    print("[Router] Pre-computing all-pairs shortest paths …")
    engine.router.all_pairs_shortest_paths()
    print("[Router] Done.")

    # 4. Run simulation
    engine.run(
        num_steps=SIM_STEPS,
        record_every=RECORD_EVERY,
        verbose=True,
    )

    # 5. Visualise
    vis = Visualizer(engine)

    print("[Visualizer] Rendering static network diagram …")
    vis.render_static(os.path.join(OUTPUT_DIR, "network.png"))

    print("[Visualizer] Rendering animated GIF …")
    vis.render_animation(
        os.path.join(OUTPUT_DIR, "traffic.gif"),
        fps=ANIMATION_FPS,
        max_frames=MAX_ANIM_FRAMES,
    )

    print("[Visualizer] Rendering statistics charts …")
    vis.render_stats(os.path.join(OUTPUT_DIR, "stats.png"))

    print(f"\n✓ All outputs saved to: {os.path.abspath(OUTPUT_DIR)}/")
    print("  ├── network.png  — static road network diagram")
    print("  ├── traffic.gif  — animated vehicle simulation")
    print("  └── stats.png    — time-series statistics charts")


if __name__ == "__main__":
    main()
