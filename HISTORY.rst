Release notes
=============

1.9.3
-----

* Added configurable timeout value for AMQP async calls

1.9.2
-----

* fixed query for statistics

1.9.1
-----

* fixed packaging and upgraded flask to 0.12.4

1.9.0
-----

* switched stats backend to MongoDB instead of sqlite3

1.8.2
-----

* update flask version and VestaService version

1.8.0
-----

* Adding a command line tool to call a service in a blocking mode

1.7.9
-----

* Fix handling of exceptions with messages encoded in utf-8.

1.7.8
-----

* Configuration directive no_params_needed is now optionnal.

1.7.7
-----

* Handle error cases for JSON submittal with arguments.

1.7.6
-----

* Add configuration to service which permits use without any arguments.

1.7.5
-----

* Bug fix for error handling.

1.7.4
-----

* AMQP routes are explicitly specified when submitting tasks so that we can have a same task name on diffrent queues.

1.7.3
-----

* Work-around for PyPi package listing restriction. Functionnaly equivalent.

1.7.2
-----

* DB schema is now part of distributed package.

1.7.1
-----

* Log formatting. Default location of database relative to CWD by default.
* Add default entry point to print default configuration.

1.7.0
-----

* Packaged and uploaded to PyPi.
