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


def generate_token(signature_key, audience, algorithm, duration):
    """
    Generate a JWT for the current Token configuration values.

    :param duration: Token duration in seconds.
    :returns: Signed Token
    """
    logger = logging.getLogger(__name__)
    delta = timedelta(duration)

    decoded_signature = base64.b64decode(signature_key)
    token = {'aud': audience,
             'exp': datetime.utcnow() + delta}
    signed_token = jwt.encode(token, decoded_signature, algorithm=algorithm)
    logger.info("Generated JWT")
    return signed_token


def validate_token(signed_token, signature_key, audience):
    """
    Check the validity of a token.

    :param Signed Token, HS512: HMAC using SHA-512 hash algorithm
    """
    logger = logging.getLogger(__name__)

    decoded_signature = base64.b64decode(signature_key)

    claim = jwt.decode(signed_token,
                       decoded_signature,
                       audience=audience,
                       leeway=10)
    logger.info("Successfully validated JWT : %s", claim)


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

    from .app_objects import APP

    signature_key = APP.config['SECURITY']['JWT']['JWT_SIGNATURE_KEY']
    audience = APP.config['SECURITY']['JWT']['JWT_AUDIENCE']
    algorithm = APP.config['SECURITY']['JWT']['JWT_ALGORITHM']

    token = generate_token(signature_key,
                           audience,
                           algorithm,
                           duration=options.token_duration)
    print(token)

if __name__ == '__main__':
    main()
