This package offers helper modules for exposing services working in a
distributed Service architecture through a REST interface. The work being
executed by these services might be an annotation process or a form of
conversion process taking a significant amount of time thereby benefiting from
a distributed processing system with a REST interface.

Messages are communicated through a Celery distributed processing queue system.

Requirements / installation
---------------------------

The class was developed on/for Scientific Linux release 6.4 (Carbon) though it
should work with most recent Linux distributions.

The main interface uses Python version 2.x.x .

Python requirements are in file «requirements.txt» and can be installed with
the following command::

    pip install -r requirements.pip

This package is meant to be used in-place, meaning it does offer an
installation procedure to be used as a standalone distribution. When creating a
new project, simply clone this package in your source tree and refer to the
proper package with the Python *import* statement.
