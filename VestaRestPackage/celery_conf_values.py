
"""
This module exposes the package configuration values for Celery in a
Celery-compatible format.

The actual values are parsed in by Flask APP.config.from_* so it exposes the
same values as used by other modules in this package.
"""

from .app_objects import APP as __APP__

globals().update(__APP__.config['CELERY'])
