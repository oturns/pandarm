"""
Benchmark harness for pandarm preprocessing and query latency.

Usage:
    conda run -n pandarm python tests/bench_network.py

Measures wall-clock time (time.perf_counter) for:
  - Network construction + CH preprocessing
  - nodes_in_range (range query)
  - shortest_path_length (single-pair query)
  - shortest_path_lengths (batch query)
  - nearest_pois (POI nearest-neighbor)
"""

import pathlib
import time

import numpy as np
import pandas as pd

import pandarm.network as pdna

H5_PATH = pathlib.Path(__file__).parent / "osm_sample.h5"
N_WARMUP = 2
N_REPEAT = 5


def load_graph_data():
    store = pd.HDFStore(H5_PATH, "r")
    nodes = store.nodes
    edges = store.edges
    store.close()
    return nodes, edges


def build_network(nodes, edges, precompute_dist):
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        net = pdna.Network(nodes.x, nodes.y, edges["from"], edges.to, edges[["weight"]])
    net.precompute(precompute_dist)
    return net


def bench(label, fn, n_repeat=N_REPEAT):
    # warmup
    for _ in range(N_WARMUP):
        fn()
    times = []
    for _ in range(n_repeat):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    arr = np.array(times) * 1000  # ms
    print(f"  {label:50s}  mean={arr.mean():.2f}ms  min={arr.min():.2f}ms  max={arr.max():.2f}ms")


def main():
    print("Loading graph data...")
    nodes, edges = load_graph_data()
    rng = np.random.default_rng(42)

    # --- Build + precompute ---
    print("\n[Build]")
    precompute_dist = 2000

    def _build():
        build_network(nodes, edges, precompute_dist)

    times = []
    for _ in range(N_REPEAT):
        t0 = time.perf_counter()
        _build()
        times.append((time.perf_counter() - t0) * 1000)
    arr = np.array(times)
    print(f"  {'Network() + precompute(2000)':50s}  mean={arr.mean():.2f}ms  min={arr.min():.2f}ms  max={arr.max():.2f}ms")

    # Build one network for query benchmarks
    net = build_network(nodes, edges, precompute_dist)

    # Identify connected nodes (largest subgraph)
    net.set(pd.Series(net.node_ids))
    counts = net.aggregate(10000, func="COUNT")
    max_count = counts.max()
    connected = counts[counts == max_count].index.values
    if len(connected) < 10:
        connected = net.node_ids  # fallback

    src = pd.Series(rng.choice(connected, 60, replace=False))
    dst = pd.Series(rng.choice(connected, 60, replace=False))

    # --- Range queries ---
    print("\n[Range queries]")
    snap_nodes = pd.Series(rng.choice(connected, 10, replace=False))

    bench("nodes_in_range(10 sources, dist=500)", lambda: net.nodes_in_range(snap_nodes, 500))
    bench("nodes_in_range(10 sources, dist=1000)", lambda: net.nodes_in_range(snap_nodes, 1000))
    bench("nodes_in_range(10 sources, dist=2000)", lambda: net.nodes_in_range(snap_nodes, 2000))

    # --- Shortest path queries ---
    print("\n[Shortest path queries]")
    single_src, single_dst = int(src.iloc[0]), int(dst.iloc[0])

    bench("shortest_path_length (1 pair)", lambda: net.shortest_path_length(single_src, single_dst))

    bench("shortest_path_lengths (50 pairs)", lambda: net.shortest_path_lengths(src[:50], dst[:50]))

    bench("shortest_path (1 pair, full path)", lambda: net.shortest_path(single_src, single_dst))

    bench("shortest_paths (20 pairs, full paths)", lambda: net.shortest_paths(src[:20], dst[:20]))

    # --- POI queries ---
    print("\n[POI queries]")
    import warnings

    bbox = net.bbox
    px = pd.Series(np.random.uniform(bbox[0], bbox[2], 50))
    py = pd.Series(np.random.uniform(bbox[1], bbox[3], 50))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        net.set_pois("bench_cat", 2000, 10, px, py)

    bench("nearest_pois(50 POIs, maxdist=2000, num_pois=5)", lambda: net.nearest_pois(2000, "bench_cat", num_pois=5))
    bench("nearest_pois(50 POIs, maxdist=2000, num_pois=10)", lambda: net.nearest_pois(2000, "bench_cat", num_pois=10))


if __name__ == "__main__":
    main()
