Current test status : https://travis-ci.org/crim-ca/RESTPackage.svg?branch=master

This package offers helper modules for exposing services working in a
distributed Service architecture through a REST interface. The work being
executed by these services might be an annotation process or a form of
conversion process taking a significant amount of time thereby benefiting from
a distributed processing system with a REST interface.

Messages are communicated through a `Celery <http://www.celeryproject.org/>`_
distributed processing queue system.

This package offers basic functionality yet is meant to be wrapped by a higher
level package which will offer a full application package.

Known examples of applications which use this package are:

* Vesta Load Balancer (alias Service Gateway or SG)
* Multimedia Storage System

Installation of this package can be done as follows::

   pip install VestaRestPackage
