.. pandana documentation master file, created by
   sphinx-quickstart on Mon Aug 18 15:50:17 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pandarm
=======

Pandarm is a Python library for network analysis that uses `contraction hierarchies <https://en.wikipedia.org/wiki/Contraction_hierarchies>`_ to calculate super-fast travel accessibility metrics and shortest paths. The numerical code is in C++.


Acknowledgments
---------------

The Pandarm package is a friendly fork of Pandana, which was created by Fletcher Foti, with subsequent contributions from Matt Davis, Federico Fernandez, Sam Maurer, and others. It relies on contraction hierarchy code from Dennis Luxen and his `OSRM project <https://github.com/DennisOSRM/Project-OSRM>`_.

A `paper on Pandana <http://onlinepubs.trb.org/onlinepubs/conferences/2012/4thITM/Papers-A/0117-000062.pdf>`_
was presented at the Transportation Research Board Annual Conference in 2012. Please cite this paper when referring to the methodology implemented by this library:

* **Foti, F., Waddell, P., & Luxen, D.** (2012). `A Generalized Computational Framework for Accessibility: From the Pedestrian to the Metropolitan Scale`. Transportation Research Board Annual Conference, 1–14. https://onlinepubs.trb.org/onlinepubs/conferences/2012/4thITM/Papers-A/0117-000062.pdf

If you would like to cite this package, you can do so using the `Zenodo DOI <https://doi.org/10.5281/zenodo.18728076>`_. If you do so, we ask that you also please cite the original paper/implementation listed above.

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   introduction
   tutorial
   network
   loaders
   utilities

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

