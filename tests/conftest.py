import os
import pathlib
import tempfile

import pytest


def pytest_configure(config):  # noqa: ARG001
    pytest.no_crs_warning = pytest.warns(UserWarning, match="No CRS was passed to geometry input")

    pytest.h5_osm_sample = pathlib.Path(__file__).parent / "osm_sample.h5"

    # Disable HDF5 file locking so xdist workers can open the same .h5
    # test fixtures concurrently (e.g. test_path_geom.py opens uci_net.h5
    # at module level during collection in every worker).
    os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")


@pytest.fixture
def tmpfile(request):
    with tempfile.NamedTemporaryFile() as f:
        fname = pathlib.Path(f.name)

        def cleanup():
            if fname.exists():
                fname.unlink()

        request.addfinalizer(cleanup)

        return fname
