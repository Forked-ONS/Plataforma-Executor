import logging
import requests


def log(msg, *args, **kwargs):
    logger = logging.getLogger()
    logger.error(msg.format(*args, **kwargs))


class VERBS:
    """HTTP Verbs
    """
    GET  = requests.get
    POST = requests.post
    PUT  = requests.put


class ExecutionResult:
    """HTTP requests friendly result.
    """
    def __init__(self, status_code, has_error=False,
                 error_message=None, data=None):
        self.status_code = status_code
        self.has_error = has_error
        self.error_message = error_message
        self.data = data

    @classmethod
    def ok(cls, status_code=200, data=None):
        return cls(status_code=status_code, data=data)

    @classmethod
    def error(cls, status_code, message, data=None):
        log("""
            HTTP request error
            status code: {status_code}
            message: {message}
            """, status_code=status_code, message=message)

        return cls(
            status_code=status_code,
            has_error=True,
            error_message=message,
            data=data)


class HttpClient:
    """Simple client to interact with HTTP endpoints.
    """
    @staticmethod
    def _request(uri, verb, **kwargs):
        def _error(message, status_code=None):
            return ExecutionResult.error(
                status_code=status_code,
                message=message + f"""
                    host: {uri}
                    args: {kwargs}
                """
            )

        try:
            data = None
            response = verb(uri, **kwargs)
            response.raise_for_status()
            if response.text and response.headers["Content-Type"] == "application/json":
                data = response.json()
            else:
                data = response.text

            return ExecutionResult.ok(
                status_code=response.status_code,
                data=data
            )
        except requests.exceptions.ConnectionError:
            return _error(
                message='Could not connect to host.')
        except requests.exceptions.Timeout:
            return _error(
                message="Request time out.")
        except requests.TooManyRedirects:
            return _error(
                message="Too many redirects.")
        except requests.exceptions.HTTPError:
            return _error(
                message="Request failed.",
                status_code=response.status_code)
        except requests.exceptions.RequestException:
            return _error(
                message="Request failed for unknown reason.")
        except ValueError:
            return _error(
                message="Response body is not a valid json.",
                status_code=response.status_code)

    @classmethod
    def get(cls, uri):
        return cls._request(uri=uri, verb=VERBS.GET)

    @classmethod
    def post(cls, uri, data=None):
        args = {}

        if data:
            args['json'] = data

        return cls._request(uri=uri, verb=VERBS.POST, **args)

    @classmethod
    def put(cls, uri, data=None):
        args = {}

        if data:
            args['json'] = data

        return cls._request(uri=uri, verb=VERBS.PUT, **args)
