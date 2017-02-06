import future

# -- Standard lib ------------------------------------------------------------
import http.client as httplib

# -- Project specific --------------------------------------------------------
from . import singleton


class ExceptionInfo:
    """
    Exception information to show useful responses to user when they happen.
    """

    def __init__(self, code, exc_type,
                 status=httplib.INTERNAL_SERVER_ERROR,
                 msg=None):
        """
        Constructor.

        :param code: Vesta exception code
        :param exc_type: Exception type
        :param status: HTTP status code to send with the request response
        :param msg: Generic message to show for a particular exception
                    If None, the specific message contains in the exception
                    will be used. So if a generic one is provided the
                    specific message will be overridden with it.
        """
        self.code = code
        self.exc_type = exc_type
        self.status = status
        self.msg = msg


@singleton.Singleton
class VestaExceptions(object):
    """
    Exceptions register class.
    """

    def __init__(self):
        """
        Populate the known exceptions list.
        """

        self._known_exceptions = [
            # -----------------------------------------------------------------
            # 1xx exception codes are reserved for built-in exceptions
            # -----------------------------------------------------------------
            ExceptionInfo(code=100, exc_type='NoneType'),
            ExceptionInfo(code=101, exc_type='Exception'),
            ExceptionInfo(code=102, exc_type='sqlite3.Error'),
            ExceptionInfo(code=103, exc_type='ConfigParser.Error'),
            ExceptionInfo(code=104, exc_type='TypeError'),
            ExceptionInfo(code=105, exc_type='ValueError'),
            ExceptionInfo(code=106, exc_type='socket.gaierror'),
            ExceptionInfo(code=107, exc_type='IOError'),
            ExceptionInfo(code=108, exc_type='KeyError'),
            ExceptionInfo(code=109, exc_type='TaskRevokedError'),

            # -----------------------------------------------------------------
            # 2xx exception codes are reserved for VRP package
            # -----------------------------------------------------------------
            ExceptionInfo(code=200, exc_type='SettingsException'),
            ExceptionInfo(code=201, exc_type='VersionException'),
            ExceptionInfo(code=202, exc_type='UnknownServiceError',
                          status=httplib.BAD_REQUEST),
            ExceptionInfo(code=203, exc_type='UnknownUUIDError',
                          status=httplib.BAD_REQUEST),
            ExceptionInfo(code=204, exc_type='VersionMismatchError'),
            ExceptionInfo(code=205, exc_type='AMQPError',
                          status=httplib.REQUEST_TIMEOUT),
            ExceptionInfo(code=206, exc_type='MissingParameterError',
                          status=httplib.BAD_REQUEST),
            ExceptionInfo(code=207, exc_type='DocumentUrlNotValidException',
                          status=httplib.BAD_REQUEST),

            # -----------------------------------------------------------------
            # 3xx exception codes are reserved for Service package
            # -----------------------------------------------------------------
            ExceptionInfo(code=300, exc_type='InvalidAnnotationFormat'),
            ExceptionInfo(code=301, exc_type='DownloadError'),
            ExceptionInfo(code=302, exc_type='UploadError'),
            ExceptionInfo(code=303, exc_type='ConfigFileNotFound'),
            ExceptionInfo(code=304, exc_type='InvalidDocumentPath'),
            ExceptionInfo(code=305, exc_type='InvalidDocumentType'),
            ExceptionInfo(code=306, exc_type='RuntimeError'),

            # -----------------------------------------------------------------
            # 4xx exception codes are reserved for VLB package
            # -----------------------------------------------------------------
            ExceptionInfo(code=400, exc_type='InsufficientResources'),
            ExceptionInfo(code=401, exc_type='MinimumWorkersReached'),

            # -----------------------------------------------------------------
            # 5xx exception codes are reserved for MSS package
            # -----------------------------------------------------------------
            ExceptionInfo(code=500, exc_type='OverflowError'),
            ExceptionInfo(code=501, exc_type='NotImplementedError'),
            ExceptionInfo(code=502, exc_type='FFMpegError'),
            ExceptionInfo(code=503, exc_type='FFMpegConvertError'),
            ExceptionInfo(code=504, exc_type='ConverterError'),
            ExceptionInfo(code=505, exc_type='TranscoderError'),
            # A message must absolutely be set here because specific message
            # contains sensible data
            ExceptionInfo(code=506, exc_type='SwiftException',
                          msg='Cannot renew the swift token'),

            # -----------------------------------------------------------------
            # 600 and above exceptions codes are free to be used by workers
            # -----------------------------------------------------------------

            # 600-620 exceptions codes are taken by transition/face worker
            ExceptionInfo(code=600, exc_type='CInternalError'),

            # 630-639 onwards shared by diarization, STT, TextMatching.
            ExceptionInfo(code=630, exc_type="WavPathInvalid"),
            ExceptionInfo(code=631, exc_type="WavFormatInvalid"),
            ExceptionInfo(code=632, exc_type="WavHeaderInvalid"),
            ExceptionInfo(code=633, exc_type="SubprocessProblem",
                          msg="Diarisation worker internal problem"),

            # 640 onwards taken by STT.
            ExceptionInfo(code=640, exc_type="PathInvalidError"),
            ExceptionInfo(code=641, exc_type="SegmentsTooLongException"),
            ExceptionInfo(code=642, exc_type="SubprocessError"),
            ExceptionInfo(code=643, exc_type="TranscriptionEmptyError"),
        ]

        # Make an exception dict based on exception type from the list above
        self._known_exceptions_dict = dict((exc.exc_type, exc) for
                                           exc in self._known_exceptions)

    def __find_matching_exception(self, exception):
        """
        Try to find a matching exception class in the known exception
        dictionary.

        :param exception: The exception class
        :returns: An exception object (A generic one is returned if not found)
        """
        exception_type_name = type(exception).__name__

        # First, try a direct match
        if exception_type_name in self._known_exceptions_dict:
            return self._known_exceptions_dict[exception_type_name]

        # Then make a search including some or all of the module directories
        try:
            module_dirs = exception.__module__.split('.')
            for mod_dir in reversed(module_dirs):
                exception_type_name = ''.join([mod_dir,
                                               '.',
                                               exception_type_name])
                if exception_type_name in self._known_exceptions_dict:
                    return self._known_exceptions_dict[exception_type_name]
        except AttributeError:
            # Not all exceptions have a __module__ attribute
            pass

        # Return a generic exception to handle this unknown exception
        return self._known_exceptions_dict['Exception']

    def get_exception_code(self, exception):
        """
        Returns the Vesta exception code associated to this exception.

        :param exception: Exception instance
        :returns: Exception code
        """
        return self.__find_matching_exception(exception).code

    def get_html_status(self, exception):
        """
        Returns the html status code associated to this exception.

        :param exception: Exception instance
        :returns: HTML status code
        """
        return self.__find_matching_exception(exception).status

    def get_generic_message(self, exception):
        """
        Returns the generic message associated to this exception.

        :param exception: Exception instance
        :returns: Exception message
        """
        return self.__find_matching_exception(exception).msg


class VRPException(Exception):
    """
    Base exception type for current package.
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class UnknownServiceError(VRPException):
    """
    Indicates that a Service name is of unknown type.
    """
    def __init__(self, service):
        msg = ('The request has been made for a service that is not supported'
               ' : {service}'.format(service=service))
        super(UnknownServiceError, self).__init__(msg)


class UnknownUUIDError(VRPException):
    """
    Indicates that the requested UUID is not yet registered.
    """
    def __init__(self, uuid):
        msg = ('User requested a UUID which did not exist : {uuid}'
               .format(uuid=uuid))
        super(UnknownUUIDError, self).__init__(msg)


class MissingParameterError(VRPException):
    """
    Indicates that a required parameter is missing.
    """
    def __init__(self, method, uri, missing_param):
        msg = ('A {method} on the URI "{uri}" requires the following '
               'parameter : {param}'.format(method=method,
                                            uri=uri,
                                            param=missing_param))
        super(MissingParameterError, self).__init__(msg)


class VersionMismatchError(VRPException):
    """
    Indicates that a service version declared in the REST configuration
    mismatches the version obtained from worker message payload.
    """
    pass


class AMQPError(VRPException):
    """
    Indicates that communications with AMQP failed.
    """
    def __init__(self):
        msg = "AMQP backend didn't response quickly enough."
        super(AMQPError, self).__init__(msg)


class DocumentUrlNotValidException(VRPException):
    """
    Indicates that given URL for a document is invalid.
    """
    def __init__(self, invalid_url):
        msg = ('User provided an invalid source URL : {url}'
               .format(url=invalid_url))
        super(DocumentUrlNotValidException, self).__init__(msg)


class SettingsException(VRPException):
    """
    Indicates that an error occurred during settings parsing.
    """
    pass


class VersionException(VRPException):
    """
    Indicates that a version mismatch was found.
    """
    pass
