"""
road.py - Directional road with capacity, speed limit, and vehicle queue.

A Road connects two nodes (Junction or Source/Sink) directionally.
Vehicles travel along a road and queue at the end waiting to enter
the next junction. Travel time = length / speed_limit (in time steps).
"""

from collections import deque
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .vehicle import Vehicle


class Road:
    """
    Directional road segment.

    Attributes:
        road_id     : unique string identifier
        start_node  : id of originating junction/source
        end_node    : id of destination junction/sink
        length      : road length in metres
        speed_limit : free-flow speed in m/step
        capacity    : max vehicles that can be *in transit* simultaneously
        travel_time : steps needed to traverse (= ceil(length/speed_limit))
    """

    def __init__(
        self,
        road_id: str,
        start_node: str,
        end_node: str,
        length: float = 100.0,
        speed_limit: float = 10.0,
        capacity: int = 20,
    ):
        self.road_id = road_id
        self.start_node = start_node
        self.end_node = end_node
        self.length = length
        self.speed_limit = speed_limit
        self.capacity = capacity
        self.travel_time: int = max(1, int(length / speed_limit))

        # Vehicles currently in transit: list of (vehicle, arrival_step)
        self._in_transit: List[tuple] = []

        # Queue of vehicles that have completed travel and wait to enter end_node
        self._exit_queue: deque = deque()

        # Stats
        self.total_entered: int = 0
        self.total_exited: int = 0
        self.cumulative_queue_length: float = 0.0
        self._steps_recorded: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def occupancy(self) -> int:
        """Total vehicles on road (in transit + waiting at exit)."""
        return len(self._in_transit) + len(self._exit_queue)

    @property
    def is_full(self) -> bool:
        return self.occupancy >= self.capacity

    @property
    def exit_queue(self) -> deque:
        return self._exit_queue

    @property
    def queue_length(self) -> int:
        return len(self._exit_queue)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def try_enter(self, vehicle: "Vehicle", current_step: int) -> bool:
        """
        Attempt to place a vehicle onto this road.
        Returns True if successful, False if road is full.
        """
        if self.is_full:
            return False
        arrival_step = current_step + self.travel_time
        self._in_transit.append((vehicle, arrival_step))
        vehicle.current_road = self.road_id
        self.total_entered += 1
        return True

    def step(self, current_step: int):
        """
        Advance simulation by one step:
        Move vehicles whose arrival_step <= current_step into exit queue.
        """
        still_in_transit = []
        for vehicle, arrival_step in self._in_transit:
            if current_step >= arrival_step:
                self._exit_queue.append(vehicle)
            else:
                still_in_transit.append((vehicle, arrival_step))
        self._in_transit = still_in_transit

        # Record stats
        self.cumulative_queue_length += len(self._exit_queue)
        self._steps_recorded += 1

    def pop_next_vehicle(self) -> Optional["Vehicle"]:
        """Return (and remove) the next vehicle from the exit queue."""
        if self._exit_queue:
            self.total_exited += 1
            return self._exit_queue.popleft()
        return None

    def peek_next_vehicle(self) -> Optional["Vehicle"]:
        """Peek at the next vehicle without removing."""
        if self._exit_queue:
            return self._exit_queue[0]
        return None

    # ------------------------------------------------------------------
    # Snapshot for visualisation
    # ------------------------------------------------------------------

    def snapshot(self, current_step: int) -> dict:
        """Return a serialisable snapshot of road state."""
        return {
            "road_id": self.road_id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "in_transit": len(self._in_transit),
            "queue": len(self._exit_queue),
            "occupancy": self.occupancy,
            "capacity": self.capacity,
            "vehicles_in_transit": [
                {
                    "vid": v.vehicle_id,
                    "dest": v.destination,
                    "progress": 1.0 - max(0.0, (arr - current_step) / self.travel_time),
                }
                for v, arr in self._in_transit
            ],
        }

    @property
    def avg_queue_length(self) -> float:
        if self._steps_recorded == 0:
            return 0.0
        return self.cumulative_queue_length / self._steps_recorded

    def __repr__(self):
        return (
            f"Road({self.road_id!r}: {self.start_node}→{self.end_node}, "
            f"occ={self.occupancy}/{self.capacity})"
        )
