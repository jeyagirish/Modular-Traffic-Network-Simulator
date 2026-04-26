"""
visualizer.py - Network visualisation and animation.

Produces:
  1. A static network diagram (PNG) showing nodes and roads.
  2. An animated GIF / MP4 showing vehicles moving over time.
  3. Statistics plots (time-series charts).

Dependencies: matplotlib (+ Pillow for GIF, ffmpeg optional for MP4)
"""

import math
import os
from typing import Dict, List, Any, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors


# Palette for destinations
DEST_PALETTE = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#e91e63",
    "#00bcd4", "#8bc34a", "#ff5722", "#607d8b",
]

NODE_COLORS = {
    "junction": "#2c3e50",
    "source":   "#27ae60",
    "sink":     "#c0392b",
}


class Visualizer:
    """
    Handles all visualisation for a completed SimEngine run.

    Usage
    -----
    vis = Visualizer(engine)
    vis.render_static("network.png")
    vis.render_animation("traffic.gif", fps=10)
    vis.render_stats("stats.png")
    """

    def __init__(self, engine):
        self.engine = engine
        self._node_positions: Dict[str, Tuple[float, float]] = {}
        self._node_types: Dict[str, str] = {}
        self._dest_colors: Dict[str, str] = {}
        self._all_destinations: List[str] = []
        self._build_node_map()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _build_node_map(self):
        for jid, j in self.engine.junctions.items():
            self._node_positions[jid] = j.position
            self._node_types[jid] = "junction"
        for sid, s in self.engine.sources.items():
            self._node_positions[sid] = s.position
            self._node_types[sid] = "source"
        for sk_id, sk in self.engine.sinks.items():
            self._node_positions[sk_id] = sk.position
            self._node_types[sk_id] = "sink"

        # Build destination colour map
        sinks = list(self.engine.sinks.keys())
        self._all_destinations = sinks
        for i, dest in enumerate(sinks):
            self._dest_colors[dest] = DEST_PALETTE[i % len(DEST_PALETTE)]

    def _dest_color(self, dest: str) -> str:
        return self._dest_colors.get(dest, "#ffffff")

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _get_all_positions(self):
        xs = [p[0] for p in self._node_positions.values()]
        ys = [p[1] for p in self._node_positions.values()]
        return xs, ys

    def _pad_limits(self, xs, ys, pad=0.15):
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        dx = max(xmax - xmin, 1) * pad
        dy = max(ymax - ymin, 1) * pad
        return xmin - dx, xmax + dx, ymin - dy, ymax + dy

    # ------------------------------------------------------------------
    # Static network diagram
    # ------------------------------------------------------------------

    def render_static(self, filepath: str = "network.png", dpi: int = 150):
        """Render a static diagram of the road network."""
        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        self._draw_network(ax, highlight_roads=True)

        xs, ys = self._get_all_positions()
        xl, xr, yb, yt = self._pad_limits(xs, ys)
        ax.set_xlim(xl, xr)
        ax.set_ylim(yb, yt)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("Traffic Network", color="white", fontsize=16, pad=12)

        self._add_legend(ax)
        plt.tight_layout()
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Visualizer] Static diagram saved: {filepath}")

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def render_animation(
        self,
        filepath: str = "traffic.gif",
        fps: int = 8,
        max_frames: int = 200,
        dpi: int = 100,
    ):
        """Render an animated GIF of the simulation."""
        snapshots = self.engine.snapshots
        n_frames = min(len(snapshots), max_frames)
        step_indices = list(range(0, len(snapshots)))[:n_frames]

        xs, ys = self._get_all_positions()
        xl, xr, yb, yt = self._pad_limits(xs, ys)

        fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1a1a2e")
        ax.set_facecolor("#0d0d1a")

        # Draw static network once
        self._draw_network(ax)

        # Dynamic artists
        scatter = ax.scatter([], [], s=60, zorder=10, alpha=0.92)
        step_text = ax.text(
            0.02, 0.97, "", transform=ax.transAxes,
            color="white", fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#16213e", alpha=0.8)
        )
        count_text = ax.text(
            0.98, 0.97, "", transform=ax.transAxes,
            color="#a8d8ea", fontsize=9, va="top", ha="right",
        )

        ax.set_xlim(xl, xr)
        ax.set_ylim(yb, yt)
        ax.set_aspect("equal")
        ax.axis("off")
        self._add_legend(ax)

        def _init():
            import numpy as np
            scatter.set_offsets(np.empty((0, 2)))
            scatter.set_color([])
            return scatter, step_text, count_text

        def _update(frame_idx):
            snap_idx = step_indices[frame_idx]
            positions = self.engine.get_vehicle_positions(snap_idx)
            snap = self.engine.snapshots[snap_idx]
            step = snap["step"]

            if positions:
                import numpy as np
                coords = np.array([[p["x"], p["y"]] for p in positions])
                colors = [self._dest_color(p["dest"]) for p in positions]
                scatter.set_offsets(coords)
                scatter.set_color(colors)
            else:
                import numpy as np
                scatter.set_offsets(np.empty((0, 2)))
                scatter.set_color([])

            step_text.set_text(f"Step: {step}")
            count_text.set_text(
                f"Active: {snap['active_count']}  |  Arrived: {snap['arrived_count']}"
            )
            return scatter, step_text, count_text

        anim = FuncAnimation(
            fig, _update, frames=n_frames,
            init_func=_init, blit=False, interval=1000 // fps,
        )

        writer = PillowWriter(fps=fps)
        anim.save(filepath, writer=writer, dpi=dpi)
        plt.close(fig)
        print(f"[Visualizer] Animation saved: {filepath}")

    # ------------------------------------------------------------------
    # Statistics charts
    # ------------------------------------------------------------------

    def render_stats(self, filepath: str = "stats.png", dpi: int = 120):
        """Render time-series statistics charts."""
        stats = self.engine.stats
        steps = stats.steps
        if not steps:
            print("[Visualizer] No stats to plot.")
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor="#1a1a2e")
        fig.suptitle("Simulation Statistics", color="white", fontsize=16, y=0.98)

        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12"]

        datasets = [
            (stats.active_series, "Active Vehicles", colors[0]),
            (stats.arrived_series, "Cumulative Arrived", colors[1]),
            (stats.queue_series, "Avg Queue Length (roads)", colors[2]),
        ]

        # Throughput: diff of arrived
        arrived = stats.arrived_series
        throughput = [0] + [max(0, arrived[i] - arrived[i-1]) for i in range(1, len(arrived))]

        ax_flat = axes.flatten()
        for i, (data, title, color) in enumerate(datasets):
            ax = ax_flat[i]
            ax.set_facecolor("#0d0d1a")
            ax.plot(steps, data, color=color, linewidth=1.5)
            ax.fill_between(steps, data, alpha=0.15, color=color)
            ax.set_title(title, color="white", fontsize=11)
            ax.tick_params(colors="gray")
            for spine in ax.spines.values():
                spine.set_edgecolor("#333355")
            ax.set_xlabel("Step", color="gray", fontsize=8)
            ax.yaxis.label.set_color("gray")
            ax.grid(True, color="#222244", linewidth=0.5)

        # Throughput chart
        ax = ax_flat[3]
        ax.set_facecolor("#0d0d1a")
        ax.bar(steps, throughput, color=colors[3], alpha=0.8, width=1.0)
        ax.set_title("Per-Step Throughput", color="white", fontsize=11)
        ax.tick_params(colors="gray")
        for spine in ax.spines.values():
            spine.set_edgecolor("#333355")
        ax.set_xlabel("Step", color="gray", fontsize=8)
        ax.grid(True, color="#222244", linewidth=0.5, axis="y")

        # Summary text box
        s = stats.summary()
        summary_text = (
            f"Spawned: {s['total_spawned']}  |  Arrived: {s['total_arrived']}  |  "
            f"Completion: {s['completion_rate']}%\n"
            f"Avg Journey: {s['avg_journey_time']} steps  |  "
            f"Avg Wait: {s['avg_wait_time']} steps  |  "
            f"Peak Queue: {s['peak_queue_length']}"
        )
        fig.text(
            0.5, 0.01, summary_text, ha="center", color="#a8d8ea",
            fontsize=9, bbox=dict(boxstyle="round", facecolor="#16213e", alpha=0.7)
        )

        plt.tight_layout(rect=[0, 0.05, 1, 0.96])
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Visualizer] Stats chart saved: {filepath}")

    # ------------------------------------------------------------------
    # Internal drawing helpers
    # ------------------------------------------------------------------

    def _draw_network(self, ax, highlight_roads: bool = False):
        """Draw roads (arrows) and nodes onto ax."""

        # Draw roads as curved/straight arrows
        for road in self.engine.roads.values():
            start = self._node_positions.get(road.start_node)
            end = self._node_positions.get(road.end_node)
            if start is None or end is None:
                continue
            self._draw_road_arrow(ax, start, end, road, highlight_roads)

        # Draw nodes
        for node_id, pos in self._node_positions.items():
            ntype = self._node_types.get(node_id, "junction")
            color = NODE_COLORS[ntype]
            size = 220 if ntype == "junction" else 300

            ax.scatter(*pos, s=size, color=color, zorder=5, edgecolors="white", linewidths=1.2)

            # Label
            label_color = "#ecf0f1"
            ax.annotate(
                node_id,
                xy=pos,
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=label_color,
                fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="#0d0d1a")],
                zorder=6,
            )

            # Type badge
            badge = {"junction": "J", "source": "S", "sink": "K"}[ntype]
            ax.text(
                pos[0], pos[1], badge,
                ha="center", va="center",
                fontsize=6, color="white", fontweight="bold",
                zorder=7,
            )

    def _draw_road_arrow(self, ax, start, end, road, highlight: bool):
        """Draw a directional road arrow with slight offset for parallel roads."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            return

        # Perpendicular offset to avoid overlapping bidirectional roads
        nx, ny = -dy / length * 0.04, dx / length * 0.04
        sx, sy = start[0] + nx, start[1] + ny
        ex, ey = end[0] + nx, end[1] + ny

        # Road line
        line_color = "#4a4a6a" if not highlight else "#6a6a9a"
        ax.annotate(
            "",
            xy=(ex, ey),
            xytext=(sx, sy),
            arrowprops=dict(
                arrowstyle="-|>",
                color=line_color,
                lw=1.5,
                mutation_scale=12,
            ),
            zorder=3,
        )

        # Road label (travel time)
        mx, my = (sx + ex) / 2 + nx * 1.5, (sy + ey) / 2 + ny * 1.5
        ax.text(
            mx, my,
            f"t={road.travel_time}",
            fontsize=6,
            color="#888899",
            ha="center",
            va="center",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="#0d0d1a")],
            zorder=4,
        )

    def _add_legend(self, ax):
        """Add node type and destination colour legend."""
        legend_elements = [
            mpatches.Patch(color=NODE_COLORS["source"], label="Source"),
            mpatches.Patch(color=NODE_COLORS["sink"], label="Sink"),
            mpatches.Patch(color=NODE_COLORS["junction"], label="Junction"),
        ]
        for dest, color in self._dest_colors.items():
            legend_elements.append(
                Line2D([0], [0], marker="o", color="w", label=f"→ {dest}",
                       markerfacecolor=color, markersize=8)
            )

        legend = ax.legend(
            handles=legend_elements,
            loc="lower right",
            fontsize=7.5,
            facecolor="#16213e",
            edgecolor="#333355",
            labelcolor="white",
            framealpha=0.85,
        )
