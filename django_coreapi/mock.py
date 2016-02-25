import functools
import coreapi
import django_coreapi.client


_responses = []


def get_match(document, keys):
    """
    Find the first matching response in the current set
    :param keys: the key path to be matched
    :return: the matching response or None
    """
    for response in _responses:
        if response[:2] == (document.url, keys):
            return response[-1]


class Mock(object):
    """
    Can be used as a context manager. Takes handler functions as arguments, which are evaluated in order in place of
    """
    def __init__(self):
        super(Mock, self).__init__()

    def __enter__(self):
        # prepare and inject the mock methods to coreapi's session
        self._real_action = coreapi.Client.action
        self._real_django_client_action = django_coreapi.client.DjangoCoreAPIClient.action

        def fake_action(client, document, keys, *args, **kwargs):
            res = get_match(document, keys)
            if res is not None:
                return res
            raise Exception("No such mocked action")

        coreapi.Client.action = fake_action
        django_coreapi.client.DjangoCoreAPIClient.action = fake_action

    def __exit__(self, exc_type, value, tb):
        global _responses
        # replace the real methods
        coreapi.Client.action = self._real_action
        django_coreapi.client.DjangoCoreAPIClient.action = self._real_django_client_action
        # clear out the match list
        _responses = []


def activate(f):
    """
    A decorator which mocks the coreapi and django_coreapi clients, allowing use of `add`
    :param f: the function to be wrapped
    :return: the wrapped function
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        with Mock():
            return f(*args, **kwargs)

    return decorated


def add(document, keys, response):
    global _responses
    _responses.append((document.url, keys, response))
