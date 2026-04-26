"""
traffic_sim - A modular traffic simulation library.

Components:
    - Road: Directional road with capacity
    - Junction: 2/3/4-way junctions with traffic scheduling
    - Vehicle: Agent with source, destination, and routing
    - TrafficSource: Generates vehicles (constant or Poisson)
    - Sink: Removes vehicles from the network
    - Router: Shortest-path routing (Dijkstra)
    - SimEngine: Discrete time-step simulation engine
    - Stats: Statistics collector
    - Visualizer: Network + vehicle animation
"""

from .road import Road
from .junction import Junction
from .vehicle import Vehicle
from .source import TrafficSource
from .sink import Sink
from .router import Router
from .engine import SimEngine
from .stats import Stats
from .visualizer import Visualizer

__all__ = [
    "Road", "Junction", "Vehicle", "TrafficSource",
    "Sink", "Router", "SimEngine", "Stats", "Visualizer",
]
