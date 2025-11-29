# pandarm

A pandas-centric interface to highly performant travel network analysis leveraging [contraction hierarchies](https://en.wikipedia.org/wiki/Contraction_hierarchies) provided by code from the Open Source Routing Machine (OSRM). Hence, the *pandas routing machine*, `pandarm`. This package is a friendly fork of the [pandana](https://github.com/UDST/pandana) library, originally written by Fletcher Foti and UrbanSim Inc. Despite fantastic work by the original authors, maintaining open-source software is a great deal of work and the pandana library is [no longer compatible](https://github.com/UDST/pandana/pull/196) with the current pydata stack (specifically as of numpy version 2.0). This fork reinstates compatibility and brings along a few new modern touches and enhancements. Pull requests are very welcome. 


## Features

Main features of the package include 

- multi-threaded calculation of shortest path routes and distances
- network aggregations (i.e. accessibility metrics)
- network-based isochrones

See more in the [example notebook](examples/example_notebook.ipynb)

### Aggregations

![Access to Restaurants in D.C.](docs/source/img/dc_restaurants.png)

### Shortest Path

![Shortest Path from UCI School of Social Ecology to Rancho San Joaquin M.S.](docs/source/img/sse_path.png)

### Isochrones

![Destinations Within 2km of UCI Langson Library](docs/source/img/langson_iso.png)


## Installation

Install from either PyPI or Conda Forge (though the latter is recommended).

- `pip install pandarm`
- `conda install pandarm --channel conda-forge`

## Development

To install a development version of the package (with proper multithreading) you need an OpenMP compatible C++ compiler. The best way to do this is by installing everything from conda-forge using

```bash
conda env create
conda activate pandarm
pip install -e .
```

This will install all necessary package dependencies, including the platform-appropriate compiler, then build the C++ extension and install the package in editable mode

## Why this fork?

Apart from bringing compatibility with numpy>=2 and the rest of the pydata stack, I have a few feature goals to merge into the codebase that make things easier to do, given today's toolset. When the original `pandana` was written 10 years ago, geopandas was fairly immature, and `osmnx` was not yet written; both of these make life much easier. 

- download OSM networks from `osmnx` instead of `OSMNet` (the former is more performant and easier to work with)
- store network geometries using geopandas
  - allow geopandas-based plotting
  - allow reprojecting node x/y coordinates (particularly important for snapping destinations to the network)
- move isochrone polygons [from geosnap](https://oturns.github.io/geosnap-guide/isochrone_example.html)

## Acknowledgments

The original pandana package from which this fork was derived was created by [Fletcher Foti](https://github.com/fscottfoti), with subsequent contributions from [Matt Davis](https://github.com/jiffyclub), [Federico Fernandez](https://github.com/federicofernandez), [Sam Maurer](https://github.com/smmaurer), and others. The package relies on contraction hierarchy code from [Dennis Luxen](https://github.com/DennisOSRM) and his [OSRM project](https://github.com/DennisOSRM/Project-OSRM).


## Academic literature

A [paper on Pandana](http://onlinepubs.trb.org/onlinepubs/conferences/2012/4thITM/Papers-A/0117-000062.pdf) was presented at the Transportation Research Board Annual Conference in 2012. Please cite this paper when referring to the methods implemented by this library.


## Related packages

Note the original pandana is still available but can only be used with older versions of numpy. Alternatively, Fletcher has recently released a *pure Python* library, `pandana2`, which calculates network-based aggregations, albeit at a bit of a performance cost, though it (currently at least) lacks routing and shortest-path functionality.

- [OSMnet](https://github.com/udst/osmnet)
- [UrbanAccess](https://github.com/udst/urbanaccess)
- [pandana](https://github.com/udst/pandana)
- [pandana2](https://github.com/mapcraftlabs/pandana2)
