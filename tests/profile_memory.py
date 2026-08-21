"""
Memory profiling for pandarm CH preprocessing.

Generates synthetic grid graphs of increasing size and reports
peak Python-side allocations during Network() construction and
precompute(). This checks that the contractor hash cache introduced
for duplicate-edge detection does not cause unbounded memory growth
on denser graphs.

Usage:
    conda run -n pandarm python tests/profile_memory.py
"""

import tracemalloc
import warnings

import numpy as np
import pandas as pd

import pandarm.network as pdna


def make_grid_graph(rows, cols, edge_weight=100.0):
    """Generate a 2D grid graph with bidirectional edges."""
    n = rows * cols
    node_idx = np.arange(n)
    x = (node_idx % cols).astype(float)
    y = (node_idx // cols).astype(float)

    frm, to, weight = [], [], []
    for r in range(rows):
        for c in range(cols):
            nid = r * cols + c
            # right neighbor
            if c + 1 < cols:
                nb = r * cols + (c + 1)
                frm += [nid, nb]
                to += [nb, nid]
                weight += [edge_weight, edge_weight]
            # down neighbor
            if r + 1 < rows:
                nb = (r + 1) * cols + c
                frm += [nid, nb]
                to += [nb, nid]
                weight += [edge_weight, edge_weight]

    return (
        pd.Series(x, index=node_idx),
        pd.Series(y, index=node_idx),
        pd.Series(frm, dtype=np.int64),
        pd.Series(to, dtype=np.int64),
        pd.DataFrame({"weight": weight}),
    )


def profile_build(rows, cols, precompute_dist=5000):
    x, y, frm, to, edges_df = make_grid_graph(rows, cols)
    n_nodes = rows * cols
    n_edges = len(frm)

    tracemalloc.start()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        net = pdna.Network(x, y, frm, to, edges_df)
    net.precompute(precompute_dist)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return n_nodes, n_edges, peak


def main():
    sizes = [(10, 10), (20, 20), (30, 30), (40, 40), (50, 50)]

    print(f"{'Grid':>10}  {'Nodes':>8}  {'Edges':>8}  {'Peak MB':>10}")
    print("-" * 44)
    for rows, cols in sizes:
        n_nodes, n_edges, peak_bytes = profile_build(rows, cols)
        peak_mb = peak_bytes / (1024 * 1024)
        print(f"  {rows}x{cols:>3}   {n_nodes:>8}  {n_edges:>8}  {peak_mb:>10.3f}")


if __name__ == "__main__":
    main()
