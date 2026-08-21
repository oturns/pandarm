import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from pandas.testing import assert_index_equal

import pandarm.network as pdna


@pytest.fixture(scope="module")
def sample_osm(request):
    store = pd.HDFStore(pytest.h5_osm_sample, "r")
    nodes, edges = store.nodes, store.edges

    with pytest.no_crs_warning:
        net = pdna.Network(nodes.x, nodes.y, edges["from"], edges.to, edges[["weight"]])

    net.precompute(2000)

    def fin():
        store.close()

    request.addfinalizer(fin)

    return net


# initialize a second network
@pytest.fixture(scope="module")
def second_sample_osm(request):
    store = pd.HDFStore(pytest.h5_osm_sample, "r")
    nodes, edges = store.nodes, store.edges

    with pytest.no_crs_warning:
        net = pdna.Network(nodes.x, nodes.y, edges["from"], edges.to, edges[["weight"]])

    net.precompute(2000)

    def fin():
        store.close()

    request.addfinalizer(fin)

    return net


def random_node_ids(net, ssize):
    return pd.Series(np.random.choice(net.node_ids, ssize))


def random_data(ssize):
    return pd.Series(np.random.random(ssize))


def get_connected_nodes(net):
    net.set(pd.Series(net.node_ids))
    s = net.aggregate(10000, func="COUNT")
    # not all the nodes in the sample network are connected
    # get the nodes in the largest connected subgraph
    # from printing the result out I know the largest subgraph has
    # 477 nodes in the sample data
    connected_nodes = s[s == 477].index.values
    return connected_nodes


def random_connected_nodes(net, ssize):
    return pd.Series(np.random.choice(get_connected_nodes(net), ssize))


def random_x_y(sample_osm, ssize):
    bbox = sample_osm.bbox
    x = pd.Series(np.random.uniform(bbox[0], bbox[2], ssize))
    y = pd.Series(np.random.uniform(bbox[1], bbox[3], ssize))
    return x, y


class TestAggVaraiblesAccuracy:
    @pytest.fixture(autouse=True)
    def setup_method(self, sample_osm):
        self.net = sample_osm

        # test accuracy compared to Pandas functions
        self.distance = 100000
        ssize = 50

        np.random.seed(42)
        self.r = random_data(ssize)
        self.r_sorted = self.r.sort_values()

        self.connected_nodes = get_connected_nodes(self.net)
        nodes = random_connected_nodes(self.net, ssize)
        self.net.set(nodes, variable=self.r)

    ###########################################################################
    # remove decorator and warning catcher when 'type' is removed
    func_or_type = pytest.mark.parametrize("kwarg", ("func", "type"))

    def _catch_warning(self, kwarg_name, kwarg_value):
        """Helper for catch FutureWarning for 'type' deprecation."""

        if kwarg_name == "type":
            with pytest.warns(FutureWarning, match="The 'type' keyword is deprecated "):
                s = self.net.aggregate(self.distance, **{kwarg_name: kwarg_value})
        else:
            s = self.net.aggregate(self.distance, **{kwarg_name: kwarg_value})

        return s.loc[self.connected_nodes]

    ###########################################################################

    @func_or_type
    def test_count(self, kwarg):
        s = self._catch_warning(kwarg, "count")
        assert s.unique().size == 1
        assert s.iloc[0] == 50

    @func_or_type
    def test_ave(self, kwarg):
        s = self._catch_warning(kwarg, "AVE")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r.mean(), atol=1e-3)

    @func_or_type
    def test_mean(self, kwarg):
        s = self._catch_warning(kwarg, "mean")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r.mean(), atol=1e-3)

    @func_or_type
    def test_min(self, kwarg):
        s = self._catch_warning(kwarg, "min")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r.min(), atol=1e-3)

    @func_or_type
    def test_max(self, kwarg):
        s = self._catch_warning(kwarg, "max")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r.max(), atol=1e-3)

    @func_or_type
    def test_median(self, kwarg):
        s = self._catch_warning(kwarg, "median")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r_sorted.iloc[25], atol=1e-2)

    @func_or_type
    def test_25pct(self, kwarg):
        s = self._catch_warning(kwarg, "25pct")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r_sorted.iloc[12], atol=1e-2)

    @func_or_type
    def test_75pct(self, kwarg):
        s = self._catch_warning(kwarg, "75pct")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r_sorted.iloc[37], atol=1e-2)

    @func_or_type
    def test_sum(self, kwarg):
        s = self._catch_warning(kwarg, "SUM")
        assert s.describe()["std"] < 0.05
        assert_allclose(s.mean(), self.r_sorted.sum(), atol=1e-2)

    @func_or_type
    def test_std(self, kwarg):
        s = self._catch_warning(kwarg, "std")
        assert s.describe()["std"] < 0.01
        assert_allclose(s.mean(), self.r_sorted.std(), atol=1e-2)


def test_non_integer_nodeids(request):
    store = pd.HDFStore(pytest.h5_osm_sample, "r")
    nodes, edges = store.nodes, store.edges

    # convert to string!
    nodes.index = nodes.index.astype("str")
    edges["from"] = edges["from"].astype("str")
    edges["to"] = edges["to"].astype("str")

    with pytest.no_crs_warning:
        net = pdna.Network(nodes.x, nodes.y, edges["from"], edges.to, edges[["weight"]])

    def fin():
        store.close()

    request.addfinalizer(fin)

    # test accuracy compared to Pandas functions
    ssize = 50
    np.random.seed(42)
    r = random_data(ssize)
    connected_nodes = get_connected_nodes(net)
    random_nodes = random_connected_nodes(net, ssize)
    net.set(random_nodes, variable=r)

    s = net.aggregate(100000, func="count").loc[connected_nodes]
    assert list(nodes.index), list(s.index)


def test_agg_variables(sample_osm):
    net = sample_osm

    ssize = 50
    np.random.seed(42)
    net.set(random_node_ids(sample_osm, ssize), variable=random_data(ssize))

    for _type in net.aggregations:
        for decay in net.decays:
            for distance in [5, 10, 20]:
                t = _type
                d = decay
                s = net.aggregate(distance, func=t, decay=d)
                assert s.describe()["std"] > 0

    # testing w/o setting variable
    ssize = 50
    net.set(random_node_ids(sample_osm, ssize))

    for _type in net.aggregations:
        for decay in net.decays:
            for distance in [5, 10, 20]:
                t = _type
                d = decay
                s = net.aggregate(distance, func=t, decay=d)
                if t != "std":
                    assert s.describe()["std"] > 0
                else:
                    # no variance in data
                    assert s.describe()["std"] == 0


def test_non_float_node_values(sample_osm):
    net = sample_osm

    ssize = 50
    np.random.seed(42)
    net.set(
        random_node_ids(sample_osm, ssize),
        variable=(random_data(ssize) * 100).astype(np.int64),
    )

    for _type in net.aggregations:
        for decay in net.decays:
            for distance in [5, 10, 20]:
                t = _type
                d = decay
                s = net.aggregate(distance, func=t, decay=d)
                assert s.describe()["std"] > 0


def test_exp_constant_default(sample_osm):
    # test that exponential decay parameter defaults to 1/distance
    net = sample_osm

    ssize = 75
    np.random.seed(1)
    net.set(random_connected_nodes(sample_osm, ssize), variable=random_data(ssize))

    distance = 2000
    implicit = net.aggregate(distance, func="sum", decay="exp")
    explicit = net.aggregate(distance, func="sum", decay="exp", exp_constant=1 / distance)

    assert_allclose(implicit.values, explicit.values)


def test_exp_constant_changes_exponential_decay(sample_osm):
    net = sample_osm

    ssize = 75
    np.random.seed(2)
    net.set(random_connected_nodes(sample_osm, ssize), variable=random_data(ssize))

    distance = 2000
    low_decay = net.aggregate(distance, func="sum", decay="exp", exp_constant=0.0001)
    high_decay = net.aggregate(distance, func="sum", decay="exp", exp_constant=0.01)

    assert np.all(high_decay.values <= low_decay.values + 1e-12)
    assert np.any(high_decay.values < low_decay.values - 1e-12)


def test_exp_constant_ignored_for_non_exponential_decay(sample_osm):
    net = sample_osm

    ssize = 75
    np.random.seed(3)
    net.set(random_connected_nodes(sample_osm, ssize), variable=random_data(ssize))

    distance = 2000
    linear_a = net.aggregate(distance, func="sum", decay="linear", exp_constant=0.0001)
    linear_b = net.aggregate(distance, func="sum", decay="linear", exp_constant=10.0)

    assert_allclose(linear_a.values, linear_b.values)


def test_missing_nodeid(sample_osm):
    np.random.seed(42)
    node_ids = random_node_ids(sample_osm, 50)
    # non-existing value
    node_ids.iloc[0] = -1
    sample_osm.set(node_ids)


def test_assign_nodeids(sample_osm):
    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(sample_osm, ssize)
    node_ids1 = sample_osm.get_node_ids(x, y)
    assert len(node_ids1) == ssize
    # check a couple of assignments for accuracy
    assert node_ids1.loc[48] == 1840703798
    assert node_ids1.loc[43] == 257739973
    assert_index_equal(x.index, node_ids1.index)

    # test with max distance - this max distance is in decimal degrees
    node_ids2 = sample_osm.get_node_ids(x, y, 0.0005)
    assert 0 < len(node_ids2) < ssize
    assert len(node_ids2) < len(node_ids1), "Max distance not working"
    assert len(node_ids2) == 14

    node_ids3 = sample_osm.get_node_ids(x, y, 0)
    assert len(node_ids3) == 0


def test_named_variable(sample_osm):
    net = sample_osm

    ssize = 50
    np.random.seed(42)
    net.set(random_node_ids(sample_osm, ssize), variable=random_data(ssize), name="foo")

    net.aggregate(500, func="sum", decay="linear", name="foo")


"""
def test_plot(sample_osm):
    net = sample_osm

    ssize = 50
    net.set(random_node_ids(sample_osm, ssize),
            variable=random_data(ssize))

    s = net.aggregate(500, type="sum", decay="linear")

    sample_osm.plot(s)
"""


def test_shortest_path(sample_osm):
    np.random.seed(42)
    for _ in range(10):
        ids = random_connected_nodes(sample_osm, 2)
        path = sample_osm.shortest_path(ids[0], ids[1])
        assert path.size >= 2
        assert ids[0] == path[0]
        assert ids[1] == path[-1]


def test_shortest_paths(sample_osm):
    np.random.seed(42)
    nodes = random_connected_nodes(sample_osm, 100)
    vec_paths = sample_osm.shortest_paths(nodes[0:50], nodes[50:100])

    for i in range(50):
        path = sample_osm.shortest_path(nodes[i], nodes[i + 50])
        assert np.array_equal(vec_paths[i], path)

    # check mismatched OD lists
    try:
        vec_paths = sample_osm.shortest_paths(nodes[0:51], nodes[50:100])
        assert 0
    except ValueError:
        pass


def test_shortest_path_length(sample_osm):
    np.random.seed(42)
    for _ in range(10):
        ids = random_connected_nodes(sample_osm, 2)
        _len = sample_osm.shortest_path_length(ids[0], ids[1])
        assert _len >= 0


def test_shortest_path_lengths(sample_osm):
    np.random.seed(42)
    nodes = random_connected_nodes(sample_osm, 100)
    lens = sample_osm.shortest_path_lengths(nodes[0:50], nodes[50:100])
    for _len in lens:
        assert _len >= 0

    # check mismatched OD lists
    try:
        lens = sample_osm.shortest_path_lengths(nodes[0:51], nodes[50:100])
        assert 0
    except ValueError:
        pass


def test_pois_a(sample_osm):
    net = sample_osm
    np.random.seed(42)
    x, y = random_x_y(sample_osm, 100)
    x.index = ["lab{i}" for i in range(len(x))]
    y.index = x.index
    net.set_pois("restaurants", 2000, 10, x, y)
    net.nearest_pois(2000, "restaurants", num_pois=10, include_poi_ids=True)


def test_pois_b(sample_osm):
    net = sample_osm
    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(sample_osm, ssize)

    net.set_pois("restaurants", 2000, 10, x_col=x, y_col=y.astype(float))
    net.nearest_pois(2000, "restaurants", num_pois=10)


def test_pois_c(sample_osm):
    net = sample_osm
    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(sample_osm, ssize)
    net.set_pois("restaurants", 2000, 10, x_col=x, y_col=y)
    with pytest.raises(ValueError):
        net.nearest_pois(2000, "restaurants", num_pois=11)


def test_pois2(second_sample_osm):
    net2 = second_sample_osm

    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(second_sample_osm, ssize)

    # make sure POI searches work on second graph
    net2.set_pois("restaurants", 2000, 10, x, y)

    net2.nearest_pois(2000, "restaurants", num_pois=10)


def test_pois_pandarm3(second_sample_osm):
    net2 = second_sample_osm

    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(second_sample_osm, ssize)

    # make sure POI searches work on second graph
    net2.set_pois(category="restaurants", maxdist=2000, maxitems=10, x_col=x, y_col=y)

    net2.nearest_pois(2000, "restaurants", num_pois=10)


def test_pois_pandarm3_pos_args(second_sample_osm):
    net2 = second_sample_osm

    ssize = 50
    np.random.seed(0)
    x, y = random_x_y(second_sample_osm, ssize)

    # make sure poi searches work on second graph
    net2.set_pois("restaurants", maxdist=2000, maxitems=10, x_col=x, y_col=y)

    net2.nearest_pois(2000, "restaurants", num_pois=10)


# test items are sorted


def test_sorted_pois(sample_osm):
    net = sample_osm

    ssize = 1000
    np.random.seed(42)
    x, y = random_x_y(sample_osm, ssize)

    # set two categories
    net.set_pois("restaurants", 2000, 10, x, y)

    test = net.nearest_pois(2000, "restaurants", num_pois=10)

    for _, row in test.iterrows():
        # make sure it's sorted
        assert_allclose(row, row.sort_values())


def test_repeat_pois(sample_osm):
    def get_nearest_nodes(x, y, x2=None, y2=None):
        coords_dict = [{"x": x, "y": y, "var": 1} for i in range(2)]
        if x2 and y2:
            coords_dict.append({"x": x2, "y": y2, "var": 1})
        df = pd.DataFrame(coords_dict)
        sample_osm.set_pois("restaurants", 2000, 10, df["x"], df["y"])
        res = sample_osm.nearest_pois(2000, "restaurants", num_pois=5, include_poi_ids=True)
        return res

    # these are the min-max values of the network
    # -122.3383688 -122.2962223
    # 47.5950005 47.6150548

    test1 = get_nearest_nodes(-122.31, 47.60)
    test2 = get_nearest_nodes(-122.254116, 37.869361)
    assert not test1.equals(test2)
    # Same coords as the first call, should yield same result
    test3 = get_nearest_nodes(-122.31, 47.60)
    assert test1.equals(test3)

    test4 = get_nearest_nodes(-122.31, 47.60, -122.32, 47.61)
    assert_allclose(test4.loc[53114882], [7, 13, 13, 2000, 2000, 2, 0, 1, np.nan, np.nan])
    assert_allclose(test4.loc[53114880], [6, 14, 14, 2000, 2000, 2, 0, 1, np.nan, np.nan])
    assert_allclose(
        test4.loc[53227769],
        [2000, 2000, 2000, 2000, 2000, np.nan, np.nan, np.nan, np.nan, np.nan],
    )


def test_nodes_in_range(sample_osm):
    net = sample_osm

    np.random.seed(0)
    ssize = 10
    x, y = random_x_y(net, ssize)
    snaps = net.get_node_ids(x, y)

    test1 = net.nodes_in_range(snaps, 1)
    net.precompute(ssize)
    test5 = net.nodes_in_range(snaps, 5)
    test11 = net.nodes_in_range(snaps, 11)
    assert test1.weight.max() == 1
    assert test5.weight.max() == 5
    assert test11.weight.max() == 11

    focus_id = snaps[0]
    with pytest.warns(
        UserWarning,
        match="Unsigned integer: shortest path distance is trying to be calculated",
    ):
        all_distances = net.shortest_path_lengths([focus_id] * len(net.node_ids), net.node_ids)
    all_distances = np.asarray(all_distances)
    assert (all_distances <= 1).sum() == len(test1.query(f"source == {focus_id}"))
    assert (all_distances <= 5).sum() == len(test5.query(f"source == {focus_id}"))
    assert (all_distances <= 11).sum() == len(test11.query(f"source == {focus_id}"))

    # restore the fixture's precompute state (precompute(ssize) above
    # overwrote the precompute(2000) set by the sample_osm fixture)
    net.precompute(2000)


def test_k_nearest_nodes(sample_osm):
    net = sample_osm

    np.random.seed(0)
    ssize = 10
    x, y = random_x_y(net, ssize)
    snaps = net.get_node_ids(x, y)
    k = 5

    result = net.k_nearest_nodes(snaps, k, max_radius=0)

    # Returns a DataFrame with the expected columns
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["source", "destination", "weight"]

    # Each source has at most k rows; sources not in result are isolated nodes
    counts = result.groupby("source").size()
    assert (counts <= k).all()

    # No source appears as its own destination
    assert (result["source"] == result["destination"]).sum() == 0

    # Distances are non-negative
    assert (result["weight"] >= 0).all()

    # Distances are sorted ascending within each source group
    for src, group in result.groupby("source"):
        assert group["weight"].is_monotonic_increasing, (
            f"Distances not sorted for source {src}"
        )

    # With a tight radius, results are a subset of the unlimited-radius results
    result_tight = net.k_nearest_nodes(snaps, k, max_radius=5)
    assert set(zip(result_tight["source"], result_tight["destination"])).issubset(
        set(zip(result["source"], result["destination"]))
    )
    # Tight-radius distances all respect the bound
    assert (result_tight["weight"] <= 5).all()

    # Results are consistent with nodes_in_range: the k distances returned by
    # k_nearest_nodes should equal the k smallest distances from nodes_in_range
    # (excluding the source itself; comparing distances to be robust to tie-breaking)
    focus_id = snaps[0]
    if focus_id in result["source"].values:
        knn_dists = np.sort(
            result.loc[result["source"] == focus_id, "weight"].values
        )
        nir = net.nodes_in_range([focus_id], radius=2000)
        nir_others = nir[nir["destination"] != focus_id]
        nir_top_k_dists = np.sort(nir_others.nsmallest(k, "weight")["weight"].values)
        assert_allclose(knn_dists, nir_top_k_dists)

