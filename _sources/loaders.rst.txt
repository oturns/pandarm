Loaders
=======

Pandas HDF5
-----------

Saving a ``Network`` to HDF5 is a way to share a ``Network`` or to preserve
it between sessions. For example. you can build a ``Network`` using the
OpenStreetMap API, then save the ``Network`` to HDF5 so you can reuse it
without querying OSM again.
Users will typically use the
:py:meth:`~pandarm.network.Network.save_hdf5` and
:py:meth:`~pandarm.network.Network.from_hdf5` methods.

.. note::
   Only the nodes and edges of the network are saved.
   Points-of-interest and data attached to nodes via the
   :py:meth:`~pandarm.network.Network.set` method are not included.

   You may find the
   `Pandas HDFStore <http://pandas.pydata.org/pandas-docs/stable/io.html#io-hdf5>`__
   useful to save POI and other data.

When saving a ``Network`` to HDF5 it's possible to exclude certain nodes.
This can be useful when refining a network so that it includes only
validated nodes.
(In the current design of pandarm it's not possible to modify a
``Network`` in place.)
As an example, you can use the
:py:meth:`~pandarm.network.Network.low_connectivity_nodes` method
to identify nodes that may not be connected to the larger network,
then exclude those nodes when saving to HDF5::

    lcn = network.low_connectivity_nodes(10000, 10, imp_name='distance')
    network.save_hdf5('mynetwork.h5', rm_nodes=lcn)

Pandas HDF5 API
---------------

.. automethod:: pandarm.network.Network.save_hdf5
   :noindex:

.. automethod:: pandarm.network.Network.from_hdf5
   :noindex:

.. autofunction:: pandarm.loaders.pandash5.network_to_pandas_hdf5

.. autofunction:: pandarm.loaders.pandash5.network_from_pandas_hdf5

