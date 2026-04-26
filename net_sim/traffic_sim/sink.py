"""
sink.py - Traffic sink (vehicle exit point).

A Sink drains vehicles from an incoming road's exit queue.
Vehicles that reach a sink are marked as arrived and their
journey time is recorded.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .road import Road
    from .vehicle import Vehicle


class Sink:
    """
    Vehicle exit node.

    Parameters
    ----------
    sink_id      : unique identifier (must match vehicles' destination)
    position     : (x, y) for visualisation
    incoming_road: the Road from which vehicles are consumed
    """

    def __init__(
        self,
        sink_id: str,
        position: tuple,
        incoming_road: Optional["Road"] = None,
    ):
        self.sink_id = sink_id
        self.position = position
        self._incoming_roads: List["Road"] = []
        if incoming_road is not None:
            self._incoming_roads.append(incoming_road)

        # Stats
        self.total_absorbed: int = 0
        self._journey_times: List[int] = []

    def add_incoming(self, road: "Road"):
        self._incoming_roads.append(road)

    # ------------------------------------------------------------------
    # Core step
    # ------------------------------------------------------------------

    def step(self, current_step: int) -> List["Vehicle"]:
        """
        Drain all vehicles from incoming roads that have this sink as destination.
        Returns list of vehicles that arrived this step.
        """
        arrived = []
        for road in self._incoming_roads:
            while True:
                vehicle = road.peek_next_vehicle()
                if vehicle is None:
                    break
                if vehicle.destination == self.sink_id:
                    road.pop_next_vehicle()
                    vehicle.arrived = True
                    vehicle.arrival_step = current_step
                    journey_time = current_step - vehicle.spawn_step
                    self._journey_times.append(journey_time)
                    self.total_absorbed += 1
                    arrived.append(vehicle)
                else:
                    break  # Non-matching vehicle – junction will handle it
        return arrived

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def avg_journey_time(self) -> float:
        if not self._journey_times:
            return 0.0
        return sum(self._journey_times) / len(self._journey_times)

    @property
    def min_journey_time(self) -> int:
        return min(self._journey_times) if self._journey_times else 0

    @property
    def max_journey_time(self) -> int:
        return max(self._journey_times) if self._journey_times else 0

    def snapshot(self) -> dict:
        return {
            "sink_id": self.sink_id,
            "position": self.position,
            "total_absorbed": self.total_absorbed,
            "avg_journey_time": round(self.avg_journey_time, 2),
        }

    def __repr__(self):
        return f"Sink({self.sink_id!r}, absorbed={self.total_absorbed})"
