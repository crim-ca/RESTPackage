.. _configuration:

Configuration
=============

The system uses the `Flask internal configuration method
<http://flask.pocoo.org/docs/0.10/config/>`_ to source configuration values
from a Python module which it's path is specified through an environment
variable.

The variable name should be *VRP_CONFIGURATION* and should be set before
instantiating the main REST API application server.

This file can be used to configure the Flask server, the Celery application
through the values of an object called *CELERY*, and a number of
application-specific elements through values defined in the
:py:mod:`~.VestaRestPackage.default_configuration` module.

Any value which exists in the default configuration module and which is not
overridden in the personal configuration file will maintain the value defined
in the default configuration.

This package comes with a :py:mod:`~.VestaRestPackage.print_example_configuration`
module which can print out an example configuration file.

See the `Flask
<http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values>`_ and
:ref:`Celery <celery:configuration>` configuration directives for more details.


.. _celery_config_wrapper:

Celery config values wrapper module
-----------------------------------

Furthermore, a helper module called
:py:mod:`~.VestaRestPackage.celery_conf_values` is available that exposes a
Celery-compatible configuration object for values extracted from the
application configuration file. This can be helpful if one wants to define
values for the application yet reuse those same directives for Celery compliant
modules (e.g.: flower).
