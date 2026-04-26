"""
engine.py - Discrete time-step simulation engine.

The SimEngine orchestrates the entire simulation:
  1. Advance roads (move in-transit vehicles to exit queues)
  2. Advance junctions (route vehicles between roads)
  3. Advance sinks (absorb arriving vehicles)
  4. Advance sources (spawn new vehicles)
  5. Record statistics
  6. Store per-step snapshots for visualisation
"""

from typing import Dict, List, Optional, Any
from .road import Road
from .junction import Junction
from .source import TrafficSource
from .sink import Sink
from .router import Router
from .stats import Stats


class SimEngine:
    """
    Central simulation engine.

    Build the network by adding components, then call .run() or .step().
    """

    def __init__(self):
        self.roads: Dict[str, Road] = {}
        self.junctions: Dict[str, Junction] = {}
        self.sources: Dict[str, TrafficSource] = {}
        self.sinks: Dict[str, Sink] = {}
        self.router: Router = Router()
        self.stats: Stats = Stats()

        self.current_step: int = 0
        self._active_vehicles: List = []
        self._arrived_vehicles: List = []

        # Per-step snapshot storage (for animation)
        self.snapshots: List[Dict[str, Any]] = []
        self._record_every: int = 1   # record every N steps

    # ------------------------------------------------------------------
    # Network construction helpers
    # ------------------------------------------------------------------

    def add_road(self, road: Road) -> Road:
        self.roads[road.road_id] = road
        self.router.add_road(road)
        return road

    def add_junction(self, junction: Junction) -> Junction:
        self.junctions[junction.junction_id] = junction
        return junction

    def add_source(self, source: TrafficSource) -> TrafficSource:
        self.sources[source.source_id] = source
        return source

    def add_sink(self, sink: Sink) -> Sink:
        self.sinks[sink.sink_id] = sink
        return sink

    def connect(self, road: Road, start_junction: Optional[Junction], end_junction: Optional[Junction]):
        """
        Register a road's connections to junctions.
        Pass None for start/end if it's connected to a Source or Sink instead.
        """
        if start_junction is not None:
            start_junction.add_outgoing(road)
        if end_junction is not None:
            end_junction.add_incoming(road)

    # ------------------------------------------------------------------
    # Simulation execution
    # ------------------------------------------------------------------

    def run(
        self,
        num_steps: int,
        record_every: int = 1,
        verbose: bool = False,
    ):
        """Run the simulation for num_steps time steps."""
        self._record_every = record_every
        print(f"[SimEngine] Starting simulation: {num_steps} steps")

        for _ in range(num_steps):
            self.step(verbose=verbose)

        print(f"[SimEngine] Simulation complete. Steps: {self.current_step}")
        self.stats.print_summary()

    def step(self, verbose: bool = False):
        """Execute one simulation time step."""
        t = self.current_step

        # 1. Advance roads: move in-transit vehicles to exit queues
        for road in self.roads.values():
            road.step(t)

        # 2. Advance junctions: route vehicles
        for junction in self.junctions.values():
            junction.step(t)

        # 3. Advance sinks: absorb vehicles that reached destination
        for sink in self.sinks.values():
            arrived_this_step = sink.step(t)
            for v in arrived_this_step:
                self._arrived_vehicles.append(v)
                if v in self._active_vehicles:
                    self._active_vehicles.remove(v)
                self.stats.register_arrived(v)

        # 4. Advance sources: spawn new vehicles
        for source in self.sources.values():
            new_vehicles = source.step(t)
            for v in new_vehicles:
                self._active_vehicles.append(v)
                self.stats.register_vehicle(v)

        # 5. Record stats
        self.stats.record_step(
            t,
            self._active_vehicles,
            self._arrived_vehicles,
            self.roads,
            self.junctions,
        )

        # 6. Snapshot for visualisation
        if t % self._record_every == 0:
            self.snapshots.append(self._take_snapshot(t))

        if verbose and t % 10 == 0:
            print(
                f"  Step {t:4d} | Active: {len(self._active_vehicles):4d} | "
                f"Arrived: {len(self._arrived_vehicles):4d}"
            )

        self.current_step += 1

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def _take_snapshot(self, t: int) -> Dict[str, Any]:
        """Capture full network state for this step."""
        return {
            "step": t,
            "roads": {rid: r.snapshot(t) for rid, r in self.roads.items()},
            "junctions": {jid: j.snapshot() for jid, j in self.junctions.items()},
            "sources": {sid: s.snapshot() for sid, s in self.sources.items()},
            "sinks": {sk_id: sk.snapshot() for sk_id, sk in self.sinks.items()},
            "active_count": len(self._active_vehicles),
            "arrived_count": len(self._arrived_vehicles),
        }

    # ------------------------------------------------------------------
    # Convenience: get vehicle positions (for animation)
    # ------------------------------------------------------------------

    def get_vehicle_positions(self, step_index: int) -> List[Dict]:
        """
        Extract interpolated vehicle positions from a snapshot.
        Returns list of {x, y, dest, progress} dicts.
        """
        if step_index >= len(self.snapshots):
            return []

        snap = self.snapshots[step_index]
        positions = []

        # Build node position lookup
        node_pos = {}
        for jid, j in self.junctions.items():
            node_pos[jid] = j.position
        for sid, s in self.sources.items():
            node_pos[sid] = s.position
        for sk_id, sk in self.sinks.items():
            node_pos[sk_id] = sk.position

        for road_data in snap["roads"].values():
            start = node_pos.get(road_data["start_node"], (0, 0))
            end = node_pos.get(road_data["end_node"], (0, 0))
            for v_data in road_data["vehicles_in_transit"]:
                p = v_data["progress"]
                x = start[0] + (end[0] - start[0]) * p
                y = start[1] + (end[1] - start[1]) * p
                positions.append({
                    "x": x,
                    "y": y,
                    "dest": v_data["dest"],
                    "vid": v_data["vid"],
                    "progress": p,
                })

        return positions
