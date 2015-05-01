#!/usr/bin/env python
# coding:utf-8

"""
Helper module to handle JWT.
"""

# -- Standard lib ------------------------------------------------------------
from datetime import datetime, timedelta
import optparse
import logging
import base64

# -- 3rd party ---------------------------------------------------------------
import jwt

# -- Project specific --------------------------------------------------------
from .generic_rest_api import APP


def generate_token(duration=None):
    """
    Generate a JWT for the current Token configuration values.

    :param duration: Token duration in seconds.
    :returns: Signed Token
    """
    logger = logging.getLogger(__name__)
    signature_key = APP.config['JWT_SIGNATURE_KEY']
    audience = APP.config['JWT_AUDIENCE']
    algorithm = APP.config['JWT_ALGORITHM']
    if not duration:
        duration = APP.config['JWT_DURATION']
    delta = timedelta(duration)

    decoded_signature = base64.b64decode(signature_key)
    token = {'aud': audience,
             'exp': datetime.utcnow() + delta}
    signed_token = jwt.encode(token, decoded_signature, algorithm=algorithm)
    logger.info(u"Generated JWT")
    return signed_token


def validate_token(signed_token):
    """
    Check the validity of a token.

    :param Signed Token, HS512: HMAC using SHA-512 hash algorithm
    """
    logger = logging.getLogger(__name__)

    signature_key = APP.config['JWT_SIGNATURE_KEY']
    audience = APP.config['JWT_AUDIENCE']

    decoded_signature = base64.b64decode(signature_key)

    claim = jwt.decode(signed_token,
                       decoded_signature,
                       audience=audience,
                       leeway=10)
    logger.info(u"Successfully validated JWT : {0}".format(claim))


def main():
    """
    Script entry point.

    Simple entry point to generate a JWT and print out to STDOUT.
    """
    logging.basicConfig(level=logging.DEBUG)
    usage = "%prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-l",
                      action='store',
                      default=600,
                      dest='token_duration',
                      help='Set token duration')
    options = parser.parse_args()[0]

    token = generate_token(duration=options.token_duration)
    print token

if __name__ == '__main__':
    main()
