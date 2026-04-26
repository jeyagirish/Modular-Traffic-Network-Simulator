"""
router.py - Shortest-path routing using Dijkstra's algorithm.

The Router builds a weighted graph from Road objects and answers
"what is the shortest path from node A to node B?" queries.

Edge weight = road.travel_time (can be overridden to use distance, etc.)
"""

import heapq
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .road import Road


class Router:
    """
    Pre-computes (or lazily computes) shortest paths between all node pairs.

    Usage
    -----
    router = Router()
    router.add_road(road_object)        # call for each road
    route = router.get_route("A", "D")  # returns ["A", "J1", "J2", "D"]
    """

    def __init__(self):
        # adjacency: {from_node: [(weight, road_id, to_node), ...]}
        self._adj: Dict[str, List[Tuple[float, str, str]]] = {}
        self._road_map: Dict[str, "Road"] = {}
        self._cache: Dict[Tuple[str, str], List[str]] = {}

    def add_road(self, road: "Road"):
        """Register a road into the routing graph."""
        src = road.start_node
        dst = road.end_node
        weight = road.travel_time  # could also use road.length

        if src not in self._adj:
            self._adj[src] = []
        self._adj[src].append((weight, road.road_id, dst))
        self._road_map[road.road_id] = road

        # Ensure destination node exists in adjacency (even if no outgoing edges)
        if dst not in self._adj:
            self._adj[dst] = []

        # Invalidate cache
        self._cache.clear()

    def get_route(self, source: str, destination: str) -> Optional[List[str]]:
        """
        Return the shortest path as an ordered list of node IDs,
        including source and destination.
        Returns None if no path exists.
        """
        if source == destination:
            return [source]

        key = (source, destination)
        if key in self._cache:
            return self._cache[key]

        result = self._dijkstra(source, destination)
        self._cache[key] = result
        return result

    def _dijkstra(self, source: str, destination: str) -> Optional[List[str]]:
        """Standard Dijkstra implementation."""
        dist: Dict[str, float] = {source: 0.0}
        prev: Dict[str, Optional[str]] = {source: None}

        # Priority queue: (cost, node)
        pq = [(0.0, source)]

        while pq:
            cost, node = heapq.heappop(pq)

            if node == destination:
                return self._reconstruct(prev, source, destination)

            if cost > dist.get(node, float("inf")):
                continue

            for weight, road_id, neighbour in self._adj.get(node, []):
                new_cost = cost + weight
                if new_cost < dist.get(neighbour, float("inf")):
                    dist[neighbour] = new_cost
                    prev[neighbour] = node
                    heapq.heappush(pq, (new_cost, neighbour))

        return None  # No path found

    @staticmethod
    def _reconstruct(
        prev: Dict[str, Optional[str]], source: str, destination: str
    ) -> List[str]:
        path = []
        node: Optional[str] = destination
        while node is not None:
            path.append(node)
            node = prev.get(node)
        path.reverse()
        return path if path[0] == source else []

    def all_pairs_shortest_paths(self) -> Dict[Tuple[str, str], Optional[List[str]]]:
        """Compute routes for all node pairs (useful for pre-warming cache)."""
        nodes = list(self._adj.keys())
        result = {}
        for src in nodes:
            for dst in nodes:
                if src != dst:
                    result[(src, dst)] = self.get_route(src, dst)
        return result

    def __repr__(self):
        return f"Router(nodes={list(self._adj.keys())})"
