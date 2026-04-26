"""
stats.py - Statistics collector and reporter.

Tracks per-step snapshots and aggregates:
  - Vehicle counts (active, arrived, spawned)
  - Per-road queue lengths and occupancy
  - Per-junction throughput
  - Average journey time
  - Network throughput (vehicles/step)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import statistics


@dataclass
class StepRecord:
    step: int
    active_vehicles: int
    arrived_vehicles: int
    total_spawned: int
    avg_queue_length: float
    max_queue_length: int
    network_throughput: float   # arrived this step


class Stats:
    """
    Centralised statistics aggregator for the simulation.
    """

    def __init__(self):
        self.history: List[StepRecord] = []
        self._arrived_vehicles: List[Any] = []   # Vehicle objects
        self._all_vehicles: List[Any] = []

        # Running counters
        self._prev_arrived: int = 0

    def record_step(
        self,
        step: int,
        active_vehicles: List,
        arrived_vehicles: List,
        roads: Dict,
        junctions: Dict,
    ):
        """Record statistics for one simulation step."""
        n_active = len(active_vehicles)
        n_arrived = len(arrived_vehicles)
        throughput = n_arrived - self._prev_arrived
        self._prev_arrived = n_arrived

        queue_lengths = [r.queue_length for r in roads.values()]
        avg_q = sum(queue_lengths) / max(1, len(queue_lengths))
        max_q = max(queue_lengths) if queue_lengths else 0

        record = StepRecord(
            step=step,
            active_vehicles=n_active,
            arrived_vehicles=n_arrived,
            total_spawned=n_active + n_arrived,
            avg_queue_length=round(avg_q, 2),
            max_queue_length=max_q,
            network_throughput=throughput,
        )
        self.history.append(record)

    def register_vehicle(self, vehicle):
        self._all_vehicles.append(vehicle)

    def register_arrived(self, vehicle):
        self._arrived_vehicles.append(vehicle)

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Return a dictionary of aggregate statistics."""
        journey_times = [
            v.arrival_step - v.spawn_step
            for v in self._arrived_vehicles
            if v.arrival_step is not None
        ]
        wait_times = [v.wait_steps for v in self._arrived_vehicles]
        travel_times = [v.travel_steps for v in self._arrived_vehicles]

        total_spawned = len(self._all_vehicles)
        total_arrived = len(self._arrived_vehicles)

        return {
            "total_spawned": total_spawned,
            "total_arrived": total_arrived,
            "completion_rate": round(total_arrived / max(1, total_spawned) * 100, 1),
            "avg_journey_time": round(self._safe_mean(journey_times), 2),
            "median_journey_time": round(self._safe_median(journey_times), 2),
            "min_journey_time": min(journey_times) if journey_times else 0,
            "max_journey_time": max(journey_times) if journey_times else 0,
            "avg_wait_time": round(self._safe_mean(wait_times), 2),
            "peak_active_vehicles": max((r.active_vehicles for r in self.history), default=0),
            "peak_queue_length": max((r.max_queue_length for r in self.history), default=0),
            "avg_queue_length": round(
                self._safe_mean([r.avg_queue_length for r in self.history]), 2
            ),
        }

    def print_summary(self):
        s = self.summary()
        print("\n" + "=" * 50)
        print("  TRAFFIC SIMULATION SUMMARY")
        print("=" * 50)
        print(f"  Vehicles spawned     : {s['total_spawned']}")
        print(f"  Vehicles arrived     : {s['total_arrived']}")
        print(f"  Completion rate      : {s['completion_rate']}%")
        print(f"  Avg journey time     : {s['avg_journey_time']} steps")
        print(f"  Median journey time  : {s['median_journey_time']} steps")
        print(f"  Min / Max journey    : {s['min_journey_time']} / {s['max_journey_time']} steps")
        print(f"  Avg wait time        : {s['avg_wait_time']} steps")
        print(f"  Peak active vehicles : {s['peak_active_vehicles']}")
        print(f"  Peak queue length    : {s['peak_queue_length']}")
        print(f"  Avg queue length     : {s['avg_queue_length']}")
        print("=" * 50 + "\n")

    # ------------------------------------------------------------------
    # Time-series accessors (for plotting)
    # ------------------------------------------------------------------

    @property
    def steps(self) -> List[int]:
        return [r.step for r in self.history]

    @property
    def active_series(self) -> List[int]:
        return [r.active_vehicles for r in self.history]

    @property
    def arrived_series(self) -> List[int]:
        return [r.arrived_vehicles for r in self.history]

    @property
    def queue_series(self) -> List[float]:
        return [r.avg_queue_length for r in self.history]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_mean(data: list) -> float:
        return statistics.mean(data) if data else 0.0

    @staticmethod
    def _safe_median(data: list) -> float:
        return statistics.median(data) if data else 0.0
