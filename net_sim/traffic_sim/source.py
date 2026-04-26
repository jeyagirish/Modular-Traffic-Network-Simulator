"""
source.py - Traffic source (vehicle generator).

A TrafficSource generates vehicles at a configurable rate and places
them onto an outgoing road.  Supports:
  - constant rate   : exactly `rate` vehicles per step (fractional via accumulator)
  - poisson process : Poisson-distributed arrivals (lambda = rate per step)

Each spawned vehicle is assigned a random destination from the provided
list and a pre-computed route via the supplied Router.
"""

import random
import math
from typing import List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .vehicle import Vehicle
    from .road import Road
    from .router import Router


class TrafficSource:
    """
    Vehicle generator node.

    Parameters
    ----------
    source_id    : unique identifier (used as the route start node)
    position     : (x, y) for visualisation
    outgoing_road: the Road vehicles are placed onto at spawn
    destinations : list of valid destination node IDs
    rate         : vehicles per time step (float; < 1 is fine)
    mode         : "constant" or "poisson"
    router       : Router instance to compute routes
    start_step   : simulation step at which to begin generating
    end_step     : simulation step at which to stop (None = never)
    """

    def __init__(
        self,
        source_id: str,
        position: tuple,
        outgoing_road: "Road",
        destinations: List[str],
        rate: float,
        mode: str = "poisson",
        router: Optional["Router"] = None,
        start_step: int = 0,
        end_step: Optional[int] = None,
        rng_seed: Optional[int] = None,
    ):
        self.source_id = source_id
        self.position = position
        self.outgoing_road = outgoing_road
        self.destinations = destinations
        self.rate = rate
        self.mode = mode
        self.router = router
        self.start_step = start_step
        self.end_step = end_step

        self._rng = random.Random(rng_seed)
        self._accumulator: float = 0.0   # fractional vehicle accumulator (constant mode)

        # Stats
        self.total_spawned: int = 0
        self.total_blocked: int = 0      # vehicles that couldn't enter (road full)
        self._spawned_vehicles: List["Vehicle"] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _vehicles_to_spawn(self, current_step: int) -> int:
        """Determine how many vehicles to spawn this step."""
        if current_step < self.start_step:
            return 0
        if self.end_step is not None and current_step >= self.end_step:
            return 0

        if self.mode == "constant":
            self._accumulator += self.rate
            count = int(self._accumulator)
            self._accumulator -= count
            return count
        elif self.mode == "poisson":
            return self._rng.poisson_approx(self.rate)
        return 0

    # ------------------------------------------------------------------
    # Core step
    # ------------------------------------------------------------------

    def step(self, current_step: int) -> List["Vehicle"]:
        """
        Called each simulation step.
        Returns list of newly spawned Vehicle objects.
        """
        from .vehicle import Vehicle

        n = self._count_arrivals(current_step)
        spawned = []

        for _ in range(n):
            if not self.destinations:
                continue
            dest = self._rng.choice(self.destinations)

            # Compute route
            route: List[str] = []
            if self.router is not None:
                route = self.router.get_route(self.source_id, dest) or []

            vehicle = Vehicle(
                source=self.source_id,
                destination=dest,
                spawn_step=current_step,
                route=route,
            )

            if self.outgoing_road.try_enter(vehicle, current_step):
                # Route index 0 = source (already there), advance to index 1
                vehicle.route_index = 1
                vehicle.current_node = self.source_id
                self._spawned_vehicles.append(vehicle)
                self.total_spawned += 1
                spawned.append(vehicle)
            else:
                self.total_blocked += 1

        return spawned

    def _count_arrivals(self, current_step: int) -> int:
        """Determine how many vehicles to spawn this step."""
        if current_step < self.start_step:
            return 0
        if self.end_step is not None and current_step >= self.end_step:
            return 0

        if self.mode == "constant":
            self._accumulator += self.rate
            count = int(self._accumulator)
            self._accumulator -= count
            return count
        elif self.mode == "poisson":
            # Poisson approximation: sample using numpy-free method
            L = math.exp(-self.rate)
            k = 0
            p = 1.0
            while p > L:
                p *= self._rng.random()
                k += 1
            return k - 1
        return 0

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "source_id": self.source_id,
            "position": self.position,
            "total_spawned": self.total_spawned,
            "total_blocked": self.total_blocked,
            "rate": self.rate,
            "mode": self.mode,
        }

    def __repr__(self):
        return (
            f"TrafficSource({self.source_id!r}, rate={self.rate}, "
            f"mode={self.mode}, spawned={self.total_spawned})"
        )
