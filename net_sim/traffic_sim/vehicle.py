"""
vehicle.py - Vehicle agent.

Each vehicle has:
  - A unique ID
  - A source node and destination node
  - A pre-computed route (list of node IDs)
  - Tracking of time spent waiting vs travelling
"""

from typing import List, Optional


class Vehicle:
    """
    A single vehicle travelling through the network.

    Route is stored as an ordered list of node IDs from source to destination.
    The vehicle maintains a pointer (route_index) to its current position.
    """

    _counter = 0

    def __init__(
        self,
        source: str,
        destination: str,
        spawn_step: int,
        route: Optional[List[str]] = None,
    ):
        Vehicle._counter += 1
        self.vehicle_id: str = f"V{Vehicle._counter:04d}"
        self.source: str = source
        self.destination: str = destination
        self.spawn_step: int = spawn_step
        self.route: List[str] = route or []   # list of node IDs
        self.route_index: int = 0              # index of NEXT node to reach

        # State tracking
        self.current_road: Optional[str] = None   # road currently on
        self.current_node: Optional[str] = source  # node currently at
        self.arrived: bool = False
        self.arrival_step: Optional[int] = None

        # Time accounting
        self.wait_steps: int = 0     # steps spent queuing at junctions
        self.travel_steps: int = 0   # steps spent in transit on roads

    # ------------------------------------------------------------------
    # Route helpers
    # ------------------------------------------------------------------

    @property
    def next_node(self) -> Optional[str]:
        """Next node in route, or None if at destination."""
        if self.route_index < len(self.route):
            return self.route[self.route_index]
        return None

    def advance_route(self):
        """Mark the current next_node as reached."""
        self.route_index += 1
        if self.route_index < len(self.route):
            self.current_node = self.route[self.route_index - 1]
        else:
            self.current_node = self.destination

    @property
    def has_route(self) -> bool:
        return len(self.route) > 0

    @property
    def progress(self) -> float:
        """Fraction of route completed (0.0–1.0)."""
        if not self.route:
            return 0.0
        return self.route_index / max(1, len(self.route) - 1)

    # ------------------------------------------------------------------
    # Colour for visualisation (by destination)
    # ------------------------------------------------------------------

    DEST_COLORS = [
        "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
        "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
        "#00bcd4", "#8bc34a",
    ]

    @classmethod
    def color_for_destination(cls, dest: str, all_destinations: list) -> str:
        if dest in all_destinations:
            idx = all_destinations.index(dest)
            return cls.DEST_COLORS[idx % len(cls.DEST_COLORS)]
        return "#ffffff"

    def __repr__(self):
        return (
            f"Vehicle({self.vehicle_id}: {self.source}→{self.destination}, "
            f"step={self.spawn_step}, arrived={self.arrived})"
        )
