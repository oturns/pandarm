#pragma once

#include <iostream>
#include <cstdlib>
#include <vector>
#include <string>
#include <utility>
#include <map>
#include "shared.h"
#include "graphalg.h"
#include <cstdint>

namespace MTC {
namespace accessibility {

using std::vector;
using std::string;
using std::set;
using std::map;

class Accessibility {
 public:
    Accessibility(
        int64_t numnodes,
        vector< vector<int64_t> > edges,
        vector< vector<double> >  edgeweights,
        bool twoway);

    // initialize the category number with POIs at the node_id locations
    void initializeCategory(const double maxdist, const int64_t maxitems, string category, vector<int64_t> node_idx);

    // find the nearest pois for all nodes in the network
    pair<vector<vector<double>>, vector<vector<int64_t>>>
    findAllNearestPOIs(float maxradius, unsigned maxnumber,
                       string category, int64_t graphno = 0);

    void initializeAccVar(string category, vector<int64_t> node_idx,
                          vector<double> values);

    // computes the accessibility for every node in the network
    vector<double>
    getAllAggregateAccessibilityVariables(
        float radius,
        string index,
        string aggtyp,
        string decay,
        int64_t graphno = 0);

    // get nodes with a range for a specific list of source nodes
    vector<vector<pair<int64_t, float>>> Range(vector<int64_t> srcnodes, float radius, 
                                            int64_t graphno, vector<int64_t> ext_ids);

    // shortest path between two points
    vector<int64_t> Route(int64_t src, int64_t tgt, int64_t graphno = 0);

    // shortest path between list of origins and destinations
    vector<vector<int64_t>> Routes(vector<int64_t> sources, vector<int64_t> targets,  
                               int64_t graphno = 0);

    // shortest path distance between two points
    double Distance(int64_t src, int64_t tgt, int64_t graphno = 0);
    
    // shortest path distances between list of origins and destinations
    vector<double> Distances(vector<int64_t> sources, vector<int64_t> targets,  
                             int64_t graphno = 0);

    // precompute the range queries and reuse them
    void precomputeRangeQueries(float radius);

    // aggregation types
    vector<string> aggregations;

    // decay types
    vector<string> decays;

 private:
    double maxdist;
    int64_t maxitems;

    // a vector of graphs - all these graphs share the same nodes, and
    // thus it shares the same accessibility_vars_t as well -
    // this is used e.g. for road networks where we have congestion
    // by time of day
    vector<std::shared_ptr<Graphalg> > ga;

    // accessibility_vars_t is a vector of floating point values
    // assigned to each node - the first level of the data structure
    // is dereferenced by node index
    typedef vector<vector<float> > accessibility_vars_t;
    map<string, accessibility_vars_t> accessibilityVars;
    // this is a map for pois so we can keep track of how many
    // pois there are at each node - for now all the values are
    // set to one, but I can imagine using floating point values
    // here eventually - e.g. find the 3 nearest values similar to
    // a knn tree in 2D space
    std::map<POIKeyType, accessibility_vars_t> accessibilityVarsForPOIs;

    // this stores the nodes within a certain range - we have the option
    // of precomputing all the nodes in a radius if we're going to make
    // lots of aggregation queries on the same network
    float dmsradius;
    vector<vector<DistanceVec> > dms;

    int64_t numnodes;

    void addGraphalg(MTC::accessibility::Graphalg *g);

    vector<pair<double, int64_t>>
    findNearestPOIs(int64_t srcnode, float maxradius, unsigned maxnumber,
                    string cat, int64_t graphno = 0);

    // aggregate a variable within a radius
    double
    aggregateAccessibilityVariable(
        int64_t srcnode,
        float radius,
        accessibility_vars_t &vars,
        string aggtyp,
        string gravity_func,
        int64_t graphno = 0);

    double
    quantileAccessibilityVariable(
        DistanceVec &distances,
        accessibility_vars_t &vars,
        float quantile,
        float radius);
};
}  // namespace accessibility
}  // namespace MTC
