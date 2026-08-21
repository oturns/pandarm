// nanobind binding for the pandarm C++ accessibility engine.
//
// This is a drop-in replacement for the former Cython wrapper (cyaccess.pyx).
// The Python-visible class name remains ``cyaccess`` with identical method
// signatures, so ``pandarm/network.py`` and all tests work unchanged.
//
// Build via CMakeLists.txt (nanobind_add_module) — see pyproject.toml.

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/pair.h>

#include "accessibility.h"

// NumPy C API for direct array access in helper functions
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

#include <cstdint>
#include <string>
#include <vector>

namespace nb = nanobind;
using namespace MTC::accessibility;

// ---------------------------------------------------------------------------
// Helpers — convert std::vector → NumPy arrays with zero-copy where possible
// ---------------------------------------------------------------------------

// Convert a Python str or bytes object to std::string.
// Cython's `string` type accepted bytes; nanobind's std::string caster only
// accepts str, so we handle both here.
static std::string py_to_string(nb::object obj) {
    if (PyBytes_Check(obj.ptr())) {
        return std::string(PyBytes_AsString(obj.ptr()),
                           PyBytes_Size(obj.ptr()));
    }
    if (PyUnicode_Check(obj.ptr())) {
        Py_ssize_t size;
        const char* data = PyUnicode_AsUTF8AndSize(obj.ptr(), &size);
        return std::string(data, size);
    }
    throw std::runtime_error("Expected str or bytes for string argument");
}

// Convert any array-like Python object to a C-contiguous int64 numpy array,
// then copy into a std::vector<int64_t>.  Handles pandas Series.values that
// may be float64 (due to NaN upcasting), non-contiguous arrays, etc.
static std::vector<int64_t> py_to_int64_vector(nb::object obj) {
    nb::object np = nb::module_::import_("numpy");
    nb::object arr = np.attr("ascontiguousarray")(
        np.attr("asarray")(obj).attr("astype")(nb::str("int64")));
    // Use PyArray_API to get the data pointer directly
    PyArrayObject* a = reinterpret_cast<PyArrayObject*>(
        PyArray_FROM_OTF(arr.ptr(), NPY_INT64, NPY_ARRAY_C_CONTIGUOUS));
    if (!a) {
        PyErr_Clear();
        throw std::runtime_error("Failed to convert array to int64");
    }
    npy_intp n = PyArray_SIZE(a);
    int64_t* data = static_cast<int64_t*>(PyArray_DATA(a));
    std::vector<int64_t> result(data, data + n);
    Py_DECREF(a);
    return result;
}

// Same for double arrays.
static std::vector<double> py_to_double_vector(nb::object obj) {
    nb::object np = nb::module_::import_("numpy");
    nb::object arr = np.attr("ascontiguousarray")(
        np.attr("asarray")(obj).attr("astype")(nb::str("float64")));
    PyArrayObject* a = reinterpret_cast<PyArrayObject*>(
        PyArray_FROM_OTF(arr.ptr(), NPY_FLOAT64, NPY_ARRAY_C_CONTIGUOUS));
    if (!a) {
        PyErr_Clear();
        throw std::runtime_error("Failed to convert array to float64");
    }
    npy_intp n = PyArray_SIZE(a);
    double* data = static_cast<double*>(PyArray_DATA(a));
    std::vector<double> result(data, data + n);
    Py_DECREF(a);
    return result;
}

using DblArr = nb::ndarray<double, nb::numpy>;
using Int2D = nb::ndarray<int64_t, nb::numpy, nb::shape<-1, -1>>;
using Dbl2D = nb::ndarray<double, nb::numpy, nb::shape<-1, -1>>;

static auto vec_to_array_1d_dbl(const std::vector<double>& vec) {
    // Copy into a heap-allocated buffer with a proper capsule destructor.
    // The previous version borrowed vec.data() with a no-op capsule, which
    // caused use-after-free when the local vec was destroyed on return.
    double* buf = new double[vec.size()];
    std::copy_n(vec.data(), vec.size(), buf);
    nb::capsule cap(buf, [](void* p) noexcept { delete[] static_cast<double*>(p); });
    return DblArr(buf, {static_cast<size_t>(vec.size())}, std::move(cap));
}

static auto vec2d_to_array_dbl(const std::vector<std::vector<double>>& vec) {
    if (vec.empty()) {
        return Dbl2D(nullptr, {0, 0});
    }
    size_t rows = static_cast<size_t>(vec.size());
    size_t cols = static_cast<size_t>(vec[0].size());

    // nanobind can't borrow a vector<vector<double>> as a contiguous 2-D array
    // (each inner vector is a separate allocation), so we copy into one buffer.
    double* buf = new double[rows * cols];
    for (size_t i = 0; i < rows; ++i) {
        if (static_cast<size_t>(vec[i].size()) != cols) {
            delete[] buf;
            throw std::runtime_error("Inconsistent row sizes in 2-D double vector");
        }
        std::copy_n(vec[i].data(), cols, buf + i * cols);
    }
    nb::capsule cap(buf, [](void* p) noexcept { delete[] static_cast<double*>(p); });
    return Dbl2D(buf, {rows, cols}, std::move(cap));
}

static auto vec2d_to_array_int(const std::vector<std::vector<int64_t>>& vec) {
    if (vec.empty()) {
        return Int2D(nullptr, {0, 0});
    }
    size_t rows = static_cast<size_t>(vec.size());
    size_t cols = static_cast<size_t>(vec[0].size());

    int64_t* buf = new int64_t[rows * cols];
    for (size_t i = 0; i < rows; ++i) {
        if (static_cast<size_t>(vec[i].size()) != cols) {
            delete[] buf;
            throw std::runtime_error("Inconsistent row sizes in 2-D int vector");
        }
        std::copy_n(vec[i].data(), cols, buf + i * cols);
    }
    nb::capsule cap(buf, [](void* p) noexcept { delete[] static_cast<int64_t*>(p); });
    return Int2D(buf, {rows, cols}, std::move(cap));
}

// ---------------------------------------------------------------------------
// Module definition
// ---------------------------------------------------------------------------

NB_MODULE(cyaccess, m) {
    // Initialize NumPy C API (import_array expands to return NULL on failure,
    // but NB_MODULE wraps it in a void function, so use the _no_op variant)
    if (_import_array() < 0) {
        PyErr_Print();
        PyErr_SetString(PyExc_ImportError, "numpy.core.multiarray failed to import");
        return;
    }
    // The module is named ``cyaccess`` so the import ``from .cyaccess import cyaccess``
    // in pandarm/network.py continues to work. The class below is also ``cyaccess``.

    nb::class_<Accessibility>(m, "cyaccess")
        .def(
            "__init__",
            // Match the Cython wrapper's 5-arg Python signature.
            // Accept everything as nb::object and convert via numpy to
            // ensure C-contiguous arrays with correct dtypes. This handles
            // pandas DataFrame.values which may be Fortran-ordered.
            [](Accessibility* ptr,
               nb::object node_ids_obj,
               nb::object /*node_xys*/,
               nb::object edges_obj,
               nb::object weights_obj,
               nb::object twoway_obj) {
                // Convert to C-contiguous numpy arrays via np.ascontiguousarray
                nb::object np = nb::module_::import_("numpy");
                nb::object ascontig = np.attr("ascontiguousarray");

                nb::object ni_arr = ascontig(node_ids_obj.attr("astype")(nb::str("int64")));
                nb::object ed_arr = ascontig(edges_obj.attr("astype")(nb::str("int64")));
                nb::object wt_arr = ascontig(weights_obj.attr("astype")(nb::str("float64")));

                // Cast to nanobind ndarrays (now guaranteed C-contiguous)
                auto ni = nb::cast<nb::ndarray<int64_t, nb::numpy>>(ni_arr);
                auto ed = nb::cast<nb::ndarray<int64_t, nb::numpy, nb::ndim<2>>>(ed_arr);
                auto wt = nb::cast<nb::ndarray<double, nb::numpy, nb::ndim<2>>>(wt_arr);

                // Convert to std::vector<std::vector<...>>
                size_t e_rows = (size_t) ed.shape(0);
                size_t e_cols = (size_t) ed.shape(1);
                std::vector<std::vector<int64_t>> edges(e_rows, std::vector<int64_t>(e_cols));
                for (size_t i = 0; i < e_rows; ++i)
                    for (size_t j = 0; j < e_cols; ++j)
                        edges[i][j] = ed(i, j);

                size_t w_rows = (size_t) wt.shape(0);
                size_t w_cols = (size_t) wt.shape(1);
                std::vector<std::vector<double>> ew(w_rows, std::vector<double>(w_cols));
                for (size_t i = 0; i < w_rows; ++i)
                    for (size_t j = 0; j < w_cols; ++j)
                        ew[i][j] = wt(i, j);

                // Convert twoway to bool (handles numpy.bool_ too)
                bool twoway = PyObject_IsTrue(twoway_obj.ptr());

                new (ptr) Accessibility(
                    static_cast<int64_t>(ni.size()),
                    edges, ew, twoway);
            },
            nb::arg("node_ids"),
            nb::arg("node_xys"),
            nb::arg("edges"),
            nb::arg("edge_weights"),
            nb::arg("twoway") = true,
            "Create the underlying C++ Accessibility engine.\n\n"
            "Parameters mirror the former Cython wrapper exactly."
        )
        .def(
            "initialize_category",
            [](Accessibility& self, double maxdist, int64_t maxitems,
               nb::object category_obj,
               nb::object node_ids_obj) {
                std::string category = py_to_string(category_obj);
                std::vector<int64_t> ids = py_to_int64_vector(node_ids_obj);
                self.initializeCategory(maxdist, maxitems, category, ids);
            },
            nb::arg("maxdist"),
            nb::arg("maxitems"),
            nb::arg("category"),
            nb::arg("node_ids")
        )
        .def(
            "find_all_nearest_pois",
            [](Accessibility& self, float radius, int64_t num_of_pois,
               nb::object category_obj, int64_t impno) {
                std::string category = py_to_string(category_obj);
                auto ret = self.findAllNearestPOIs(radius, num_of_pois, category, impno);
                return nb::make_tuple(vec2d_to_array_dbl(ret.first),
                                      vec2d_to_array_int(ret.second));
            },
            nb::arg("radius"),
            nb::arg("num_of_pois"),
            nb::arg("category"),
            nb::arg("impno") = 0
        )
        .def(
            "initialize_access_var",
            [](Accessibility& self, nb::object category_obj,
               nb::object node_ids_obj,
               nb::object values_obj) {
                std::string category = py_to_string(category_obj);
                std::vector<int64_t> ids = py_to_int64_vector(node_ids_obj);
                std::vector<double> vals = py_to_double_vector(values_obj);
                self.initializeAccVar(category, ids, vals);
            },
            nb::arg("category"),
            nb::arg("node_ids"),
            nb::arg("values")
        )
        .def(
            "get_available_aggregations",
            [](Accessibility& self) {
                return self.aggregations;
            }
        )
        .def(
            "get_available_decays",
            [](Accessibility& self) {
                return self.decays;
            }
        )
        .def(
            "get_all_aggregate_accessibility_variables",
            [](Accessibility& self, double radius,
               nb::object category_obj, nb::object aggtyp_obj, nb::object decay_obj,
               int64_t impno, double exp_constant) {
                std::string category = py_to_string(category_obj);
                std::string aggtyp = py_to_string(aggtyp_obj);
                std::string decay = py_to_string(decay_obj);
                auto ret = self.getAllAggregateAccessibilityVariables(
                    radius, category, aggtyp, decay, impno, exp_constant);
                return vec_to_array_1d_dbl(ret);
            },
            nb::arg("radius"),
            nb::arg("category"),
            nb::arg("aggtyp"),
            nb::arg("decay"),
            nb::arg("impno") = 0,
            nb::arg("exp_constant") = 0.0
        )
        .def(
            "shortest_path",
            [](Accessibility& self, int64_t src, int64_t tgt, int64_t impno) {
                return self.Route(src, tgt, impno);
            },
            nb::arg("srcnode"),
            nb::arg("destnode"),
            nb::arg("impno") = 0
        )
        .def(
            "shortest_paths",
            [](Accessibility& self,
               nb::object srcnodes_obj,
               nb::object destnodes_obj,
               int64_t impno) {
                std::vector<int64_t> srcs = py_to_int64_vector(srcnodes_obj);
                std::vector<int64_t> dsts = py_to_int64_vector(destnodes_obj);
                return self.Routes(srcs, dsts, impno);
            },
            nb::arg("srcnodes"),
            nb::arg("destnodes"),
            nb::arg("impno") = 0
        )
        .def(
            "shortest_path_distance",
            [](Accessibility& self, int64_t src, int64_t tgt, int64_t impno) {
                return self.Distance(src, tgt, impno);
            },
            nb::arg("srcnode"),
            nb::arg("destnode"),
            nb::arg("impno") = 0
        )
        .def(
            "shortest_path_distances",
            [](Accessibility& self,
               nb::object srcnodes_obj,
               nb::object destnodes_obj,
               int64_t impno) {
                std::vector<int64_t> srcs = py_to_int64_vector(srcnodes_obj);
                std::vector<int64_t> dsts = py_to_int64_vector(destnodes_obj);
                auto ret = self.Distances(srcs, dsts, impno);
                return vec_to_array_1d_dbl(ret);
            },
            nb::arg("srcnodes"),
            nb::arg("destnodes"),
            nb::arg("impno") = 0
        )
        .def(
            "precompute_range",
            [](Accessibility& self, double radius) {
                self.precomputeRangeQueries(static_cast<float>(radius));
            },
            nb::arg("radius")
        )
        .def(
            "nodes_in_range",
            [](Accessibility& self,
               nb::object srcnodes_obj,
               float radius, int64_t impno,
               nb::object ext_ids_obj) {
                std::vector<int64_t> srcnodes = py_to_int64_vector(srcnodes_obj);
                std::vector<int64_t> ids = py_to_int64_vector(ext_ids_obj);
                auto ret = self.Range(srcnodes, radius, impno, ids);
                // Each element is vector<pair<int64_t,float>> → convert to
                // a list of (destination, distance) pairs to match the
                // Cython wrapper's return type (list of lists of tuples).
                nb::list outer;
                for (auto& inner : ret) {
                    nb::list row;
                    for (auto& pr : inner) {
                        row.append(nb::make_tuple(pr.first, pr.second));
                    }
                    outer.append(row);
                }
                return outer;
            },
            nb::arg("srcnodes"),
            nb::arg("radius"),
            nb::arg("impno"),
            nb::arg("ext_ids")
        )
        .def(
            "k_nearest_nodes",
            [](Accessibility& self,
               nb::object srcnodes_obj,
               int64_t k, double max_radius,
               nb::object ext_ids_obj,
               int64_t impno) {
                std::vector<int64_t> srcnodes = py_to_int64_vector(srcnodes_obj);
                std::vector<int64_t> ids = py_to_int64_vector(ext_ids_obj);
                auto raw = self.KNearestNodes(srcnodes, k, max_radius, impno, ids);

                size_t rows = static_cast<size_t>(raw.size());
                size_t cols = static_cast<size_t>(k);
                double* dists_buf = new double[rows * cols];
                int64_t* ids_buf = new int64_t[rows * cols];
                std::fill_n(dists_buf, rows * cols, std::numeric_limits<double>::infinity());
                std::fill_n(ids_buf, rows * cols, -1);

                for (size_t i = 0; i < rows; ++i) {
                    for (size_t j = 0; j < static_cast<size_t>(raw[i].size()); ++j) {
                        ids_buf[i * cols + j] = raw[i][j].first;
                        dists_buf[i * cols + j] = raw[i][j].second;
                    }
                }

                nb::capsule dists_cap(dists_buf, [](void* p) noexcept {
                    delete[] static_cast<double*>(p);
                });
                nb::capsule ids_cap(ids_buf, [](void* p) noexcept {
                    delete[] static_cast<int64_t*>(p);
                });

                return nb::make_tuple(
                    Dbl2D(dists_buf, {rows, cols}, std::move(dists_cap)),
                    Int2D(ids_buf, {rows, cols}, std::move(ids_cap))
                );
            },
            nb::arg("srcnodes"),
            nb::arg("k"),
            nb::arg("max_radius"),
            nb::arg("ext_ids"),
            nb::arg("impno") = 0
        );
}