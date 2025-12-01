Installation
============

pandarm is a Python package that includes a C++ extension for numerical operations. 


Standard installation
------------------------------

You can install pandarm using Pip::

    pip install pandarm

Or Conda::

    conda install pandarm --channel conda-forge


Compiling from source code
------------------------------

You may want to compile pandarm locally if you're modifying the source code or need to use a version that's missing binary installers for your platform.

Mac users should start by running ``xcode-select --install`` to make sure you have Apple's Xcode command line tools, which are needed behind the scenes. Windows users will need the `Microsoft Visual C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_.

pandarm's build-time requirements are ``cython``, ``numpy``, and a C++ compiler that supports the C++11 standard. Additionally, the compiler needs to support OpenMP to allow pandarm to use multithreading.

The smoothest route is to get the compilers from Conda Forge. The necessary dependencies are listed in the ``environment.yml`` file. Running pandarm's setup script will trigger compilation::

    conda env create
    pip install . -e

You'll see a lot of status messages go by, but hopefully no errors.

MacOS 10.14 (but not newer versions) often needs additional header files installed. If you see a compilation error like ``'wchar.h' file not found`` in MacOS 10.14, you can resolve it by running this command::

    open /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg


Advanced compilation tips
------------------------------

If you prefer not to use Conda, you can skip the ``clang`` and ``llvm-openmp`` packages. Compilation will likely work fine with your system's built-in toolchain. 

The default C++ compiler on Macs doesn't support OpenMP, though, meaning that pandarm won't be able to use multithreading.

You can set the ``CC`` environment variable to specify a compiler of your choice. See writeup in `PR #137 <https://github.com/UDST/pandarm/pull/137>`_ for discussion of this. If you need to make additional modifications, you can edit the compilation script in your local copy of ``setup.py``.


Multithreading
------------------------------

You can check how many threads pandarm is able to use on your machine by running the ``examples/simple_example.py`` script.
