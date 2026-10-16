"""Min-cost max-flow over a Graph.

Routes as much supply to demand as edge capacities allow, and among all ways
of moving that much, picks the one with the lowest total cost.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

from graph import Edge, Graph

EPS = 1e-9

# Demand is met in tiers: every node's first share before anyone's next one.
# (share of demand, priority); within a tier the cheapest routes win.
DEFAULT_TIERS = ((0.5, 3.0), (0.3, 2.0), (0.2, 1.0))

# A supply is either an amount, or tranches of (amount, cost per unit), so a
# source can offer extra volume at a higher price.
Supply = float | Sequence[tuple[float, float]]


@dataclass
class FlowResult:
    edge_flow: dict[tuple[str, str], float]  # (source, target) -> net flow; negative = reversed
    supplied: dict[str, float]               # node -> supply actually used
    delivered: dict[str, float]              # node -> demand actually met
    total_cost: float                        # sum of |flow| x cost over edges

    @property
    def total_delivered(self) -> float:
        return sum(self.delivered.values())


def min_cost_flow(
    graph: Graph,
    supply: dict[str, Supply],
    demand: dict[str, float],
    capacity: Callable[[Edge], float] = lambda e: e.capacity,
    cost: Callable[[Edge], float] = lambda e: e.weight,
    reverse_capacity: Callable[[Edge], float] = lambda e: 0.0,
    tiers: tuple[tuple[float, float], ...] = DEFAULT_TIERS,
    node_tiers: dict[str, tuple[tuple[float, float], ...]] | None = None,
) -> FlowResult:
    """Successive shortest paths on the residual graph (Bellman-Ford/SPFA).

    A virtual source feeds each supply node through its tranches, and each
    demand node drains to a virtual sink up to its demand, split into
    ``tiers``. Each tier carries a reward larger than any route's or tranche's
    cost, so higher tiers are filled first everywhere before cost matters.
    ``node_tiers`` overrides the tiers for particular demand nodes.
    Edges with a ``reverse_capacity`` can also carry flow backwards. Supply
    that can't reach any demand is left unused; demand nothing reaches is unmet.
    """
    source, sink = "__source__", "__sink__"
    ids = [n.id for n in graph.nodes] + [source, sink]
    index = {node_id: i for i, node_id in enumerate(ids)}

    # Residual arcs in parallel lists; arc a and its reverse are a and a ^ 1.
    head: list[int] = []
    cap: list[float] = []
    arc_cost: list[float] = []
    out_arcs: list[list[int]] = [[] for _ in ids]

    def add_arc(u: str, v: str, c: float, w: float) -> int:
        a = len(head)
        for frm, to, cc, ww in ((u, v, c, w), (v, u, 0.0, -w)):
            out_arcs[index[frm]].append(len(head))
            head.append(index[to])
            cap.append(cc)
            arc_cost.append(ww)
        return a

    tranches = {n: [(s, 0.0)] if isinstance(s, (int, float)) else list(s)
                for n, s in supply.items()}
    edges = graph.edges
    # Rewards must outweigh any route plus any tranche premium, even for
    # priorities down to 0.5.
    reward_unit = 2 * (sum(cost(e) for e in edges)
                       + max((c for ts in tranches.values() for _, c in ts), default=0.0) + 1.0)
    node_tiers = node_tiers or {}

    edge_arcs: dict[tuple[str, str], tuple[int | None, int | None]] = {}
    for e in edges:
        fwd, back = capacity(e), reverse_capacity(e)
        edge_arcs[(e.source, e.target)] = (
            add_arc(e.source, e.target, fwd, cost(e)) if fwd > EPS else None,
            add_arc(e.target, e.source, back, cost(e)) if back > EPS else None,
        )
    supply_arcs = {n: [add_arc(source, n, amt, c) for amt, c in ts if amt > EPS]
                   for n, ts in tranches.items()}
    demand_arcs = {n: [add_arc(n, sink, amt * share, -priority * reward_unit)
                       for share, priority in node_tiers.get(n, tiers)]
                   for n, amt in demand.items() if amt > EPS}

    s, t = index[source], index[sink]
    while True:
        dist = [math.inf] * len(ids)
        via = [-1] * len(ids)
        queued = [False] * len(ids)
        dist[s] = 0.0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            queued[u] = False
            for a in out_arcs[u]:
                v = head[a]
                if cap[a] > EPS and dist[u] + arc_cost[a] < dist[v] - EPS:
                    dist[v] = dist[u] + arc_cost[a]
                    via[v] = a
                    if not queued[v]:
                        queued[v] = True
                        queue.append(v)
        if dist[t] == math.inf:
            break

        push, v = math.inf, t
        while v != s:
            push = min(push, cap[via[v]])
            v = head[via[v] ^ 1]
        v = t
        while v != s:
            cap[via[v]] -= push
            cap[via[v] ^ 1] += push
            v = head[via[v] ^ 1]

    def used(a: int | None) -> float:
        if a is None:
            return 0.0
        flow = cap[a ^ 1]
        return flow if flow > EPS else 0.0

    edge_flow = {key: used(fwd) - used(back) for key, (fwd, back) in edge_arcs.items()}
    costs = {(e.source, e.target): cost(e) for e in edges}
    return FlowResult(
        edge_flow=edge_flow,
        supplied={n: sum(used(a) for a in arcs) for n, arcs in supply_arcs.items()},
        delivered={n: sum(used(a) for a in arcs) for n, arcs in demand_arcs.items()},
        total_cost=sum(abs(f) * costs[key] for key, f in edge_flow.items()),
    )
