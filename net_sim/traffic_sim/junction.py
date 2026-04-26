"""
junction.py - Traffic junction (2/3/4-way).

A Junction:
  - Accepts vehicles arriving on incoming roads
  - Schedules which road services (round-robin or priority by queue length)
  - Forwards vehicles to the correct outgoing road based on route
  - Supports 2-way, 3-way, and 4-way configurations automatically
"""

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .road import Road
    from .vehicle import Vehicle


class Junction:
    """
    Multi-way junction node.

    Scheduling policy:
        "round_robin"  - service incoming roads in rotation (default)
        "longest_queue" - always service the road with the most waiting vehicles
        "fifo"         - global FIFO across all incoming queues

    At each simulation step the junction is allowed to forward up to
    `throughput` vehicles (one per incoming road being serviced).
    """

    def __init__(
        self,
        junction_id: str,
        position: tuple = (0.0, 0.0),
        scheduling: str = "round_robin",
        throughput: int = 1,
    ):
        self.junction_id = junction_id
        self.position = position          # (x, y) for visualisation
        self.scheduling = scheduling
        self.throughput = throughput      # vehicles forwarded per step

        # Registered roads
        self._incoming: Dict[str, "Road"] = {}   # road_id -> Road
        self._outgoing: Dict[str, "Road"] = {}   # road_id -> Road

        # Round-robin state
        self._rr_index: int = 0

        # Local waiting queue (vehicles that arrived but outgoing road full)
        self._holding: List["Vehicle"] = []

        # Stats
        self.total_forwarded: int = 0
        self.total_received: int = 0
        self.cumulative_wait: float = 0.0
        self._steps: int = 0

    # ------------------------------------------------------------------
    # Road registration
    # ------------------------------------------------------------------

    def add_incoming(self, road: "Road"):
        self._incoming[road.road_id] = road

    def add_outgoing(self, road: "Road"):
        self._outgoing[road.road_id] = road

    @property
    def way(self) -> int:
        """Number of incoming roads (determines junction type)."""
        return len(self._incoming)

    @property
    def incoming_roads(self) -> List["Road"]:
        return list(self._incoming.values())

    @property
    def outgoing_roads(self) -> List["Road"]:
        return list(self._outgoing.values())

    # ------------------------------------------------------------------
    # Outgoing road selection
    # ------------------------------------------------------------------

    def _pick_outgoing(self, vehicle: "Vehicle") -> Optional["Road"]:
        """
        Select the correct outgoing road for a vehicle based on its route.
        vehicle.next_node gives the next junction/sink to head toward.
        """
        next_node = vehicle.next_node
        if next_node is None:
            return None
        for road in self._outgoing.values():
            if road.end_node == next_node:
                return road
        return None

    # ------------------------------------------------------------------
    # Core step
    # ------------------------------------------------------------------

    def step(self, current_step: int):
        """
        Process junction for one time step:
        1. Pull vehicles from incoming road exit-queues according to schedule.
        2. Try to forward them onto outgoing roads.
        3. Re-queue blocked vehicles in holding buffer.
        4. Try to flush holding buffer.
        """
        self._steps += 1

        # --- Try to flush holding buffer first ---
        still_holding = []
        for vehicle in self._holding:
            out_road = self._pick_outgoing(vehicle)
            if out_road and out_road.try_enter(vehicle, current_step):
                vehicle.advance_route()
                self.total_forwarded += 1
            else:
                still_holding.append(vehicle)
        self._holding = still_holding

        # --- Pull from incoming roads ---
        serviced = 0
        incoming_list = list(self._incoming.values())
        if not incoming_list:
            return

        if self.scheduling == "longest_queue":
            incoming_list = sorted(
                incoming_list, key=lambda r: r.queue_length, reverse=True
            )
        elif self.scheduling == "round_robin":
            # Rotate the list so we start from rr_index
            n = len(incoming_list)
            incoming_list = (
                incoming_list[self._rr_index:] + incoming_list[: self._rr_index]
            )
            self._rr_index = (self._rr_index + 1) % n

        for road in incoming_list:
            if serviced >= self.throughput:
                break
            vehicle = road.peek_next_vehicle()
            if vehicle is None:
                continue

            self.total_received += 1

            # The vehicle's current next_node should equal THIS junction.
            # Advance past it so next_node points to the NEXT hop.
            if vehicle.next_node == self.junction_id:
                vehicle.advance_route()

            # Check if vehicle has now reached its final destination here
            if vehicle.destination == self.junction_id or vehicle.next_node is None:
                road.pop_next_vehicle()
                vehicle.arrived = True
                vehicle.arrival_step = current_step
                serviced += 1
                self.total_forwarded += 1
                continue

            # Try to route vehicle to next outgoing road
            out_road = self._pick_outgoing(vehicle)
            if out_road is None:
                # No outgoing road toward next hop — drop vehicle (misconfigured network)
                road.pop_next_vehicle()
                vehicle.arrived = False  # lost
                serviced += 1
                continue

            if out_road.try_enter(vehicle, current_step):
                road.pop_next_vehicle()
                self.total_forwarded += 1
                serviced += 1
            else:
                # Outgoing road full – vehicle stays in exit queue (waits)
                # Undo the route advance so routing is consistent on retry
                vehicle.route_index -= 1
                vehicle.wait_steps += 1

    # ------------------------------------------------------------------
    # Snapshot for visualisation
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        total_queue = sum(r.queue_length for r in self._incoming.values())
        return {
            "junction_id": self.junction_id,
            "position": self.position,
            "way": self.way,
            "total_queue": total_queue,
            "holding": len(self._holding),
            "total_forwarded": self.total_forwarded,
        }

    def __repr__(self):
        return (
            f"Junction({self.junction_id!r}, {self.way}-way, "
            f"in={list(self._incoming)}, out={list(self._outgoing)})"
        )
