from StringIO import StringIO

import runner
from utils import setup_logger


class TestCliBase(object):

    logger_output = StringIO()
    setup_logger(logger_name='aria.cli.main', output_stream=logger_output)

    def invoke(self, command):
        return runner.invoke(command)
