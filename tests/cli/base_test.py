from StringIO import StringIO

import runner
from utils import setup_logger


class TestCliBase(object):

    _logger_output = StringIO()
    setup_logger(logger_name='aria.cli.main', output_stream=_logger_output)

    def invoke(self, command):
        self._logger_output.truncate(0)
        return runner.invoke(command)

    @property
    def logger_output_string(self):
        return self._logger_output.getvalue()


def assert_exception_raised(outcome, expected_exception, expected_msg):
    assert isinstance(outcome.exception, expected_exception)
    assert expected_msg == str(outcome.exception)


# This exists as I wanted to mocked a function using monkeypatch to return a function that raises an
# exception. I tried doing that using a lambda in-place, but this can't be accomplished in a trivial
# way it seems. So I wrote this silly function instead
def raise_exception(exception, msg=''):

    def inner(*args, **kwargs):
        raise exception(msg)

    return inner




