#!/usr/bin/env python
# coding:utf-8

"""
This module defines authorization helper functions using JWT.
"""

# -- Standard lib ------------------------------------------------------------
import logging

# -- Project specific --------------------------------------------------------
from .vesta_exceptions import SettingsException
from .vesta_exceptions import VRPException
from .jwt_ import validate_token


def validate_authorisation(request, security_settings,
                           simple_private_key=None,
                           allow_security_bypass=True):
    """
    Validate authorization.

    :param request: Instance of :py:class:`flask.request`.
    :param security_settings: Python dictionary object containing security
                              settings. Example of security object.
                              AUTHORISATION_KEY and BYPASS_SECURITY are
                              optional.

    For example:

    .. code-block:: python

       SECURITY = {
          'AUTHORISATION_KEY': "aed9yhfapgaegaeg"
          'JWT': {
          'JWT_SIGNATURE_KEY': "vJmMvm44x6RJcVXNPy6UDcSfJHOHNHrT1tKpo4IQ4MU=",
          'JWT_AUDIENCE': "vlbTest",
          'JWT_ALGORITHM': "HS512",
          'JWT_DURATION': 600  # The following is specified in seconds.
         }
       }


    Currently, request is authorised if one of these 3 conditions is met:

    #. security_settings["BYPASS_SECURITY"]=True and
       allow_security_bypass=True. In this case no security checks are made.
    #. authorisation_key = security_settings["AUTHORISATION_KEY"] &&
       authorisation_key != None.
    #. Requests headers contains an autorisation field with a token
       'Authorization'. JWT will validate this token.

    .. note:: Does not check if security or request object are valid. Will crash
       if they are not.
    """
    logger = logging.getLogger(__name__)

    if security_settings is None:
        raise SettingsException('Security Settings object is empty')

    if "BYPASS_SECURITY" in security_settings:
        if allow_security_bypass and security_settings["BYPASS_SECURITY"]:
            return

    if "AUTHORISATION_KEY" in security_settings:
        if simple_private_key is not None and\
           simple_private_key == security_settings["AUTHORISATION_KEY"]:
            return

    authorisation_token = request.headers.get("Authorization")
    logger.debug("Token %s", authorisation_token)
    if authorisation_token is None:
        raise VRPException("Authorisation token is empty")
    validate_token(authorisation_token,
                   security_settings["JWT"]["JWT_SIGNATURE_KEY"],
                   security_settings["JWT"]["JWT_AUDIENCE"])
