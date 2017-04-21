# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re
from StringIO import StringIO
from contextlib import contextmanager
from functools import partial

from .color import StyledString
from . import logger
from .env import env


LEVEL = 'level'
TIMESTAMP = 'timestamp'
MESSAGE = 'message'
IMPLEMENTATION = 'implementation'
INPUTS = 'inputs'
TRACEBACK = 'traceback'
MARKER = 'marker'

DEFAULT_FORMATTING = {
    logger.NO_VERBOSE: {'message': '{message}'},
    logger.LOW_VERBOSE: {
        MESSAGE: '{timestamp} | {level} | {message}',
        LEVEL: '{level[0]}',
        TIMESTAMP: '%H:%M:%S',
    },
    logger.MEDIUM_VERBOSE: {
        MESSAGE: '{timestamp} | {level} | {implementation} | {message} ',
        LEVEL: '{level[0]}',
        TIMESTAMP: '%H:%M:%S'
    },
    logger.HIGH_VERBOSE: {
        MESSAGE: '{timestamp} | {level} | {implementation} | {inputs} | {message} ',
        LEVEL: '{level[0]}',
        TIMESTAMP: '%H:%M:%S'
    },
}

DEFAULT_STYLING = {
    LEVEL: {
        'info': (StyledString.FORE.LIGHTMAGENTA_EX,),
        'debug': (StyledString.FORE.LIGHTMAGENTA_EX, StyledString.STYLE.DIM),
        'error': (StyledString.FORE.RED, StyledString.STYLE.BRIGHT)
    },
    TIMESTAMP: {
        'info': (StyledString.FORE.LIGHTMAGENTA_EX,),
        'debug': (StyledString.FORE.LIGHTMAGENTA_EX, StyledString.STYLE.DIM),
        'error': (StyledString.FORE.RED, StyledString.STYLE.BRIGHT)
    },
    MESSAGE: {
        'info': (StyledString.FORE.LIGHTBLUE_EX,),
        'debug': (StyledString.FORE.LIGHTBLUE_EX, StyledString.STYLE.DIM),
        'error': (StyledString.FORE.RED, StyledString.STYLE.BRIGHT),
    },
    IMPLEMENTATION: {
        'info': (StyledString.FORE.LIGHTBLACK_EX,),
        'debug': (StyledString.FORE.LIGHTBLACK_EX, StyledString.STYLE.DIM,),
        'error': (StyledString.FORE.RED, StyledString.STYLE.BRIGHT,),
    },
    INPUTS: {
        'info': (StyledString.FORE.BLUE,),
        'debug': (StyledString.FORE.BLUE, StyledString.STYLE.DIM),
        'error': (StyledString.FORE.RED, StyledString.STYLE.BRIGHT,),
    },
    TRACEBACK: {
      'error':   (StyledString.FORE.RED, )
    },

    MARKER: StyledString.BACK.LIGHTYELLOW_EX
}


class _StylizedLogs(object):

    def __init__(self):
        self._formats = DEFAULT_FORMATTING
        self._styles = DEFAULT_STYLING
        self._mark_pattern = None

    def _push(self, styles=None, formats=None, mark_pattern=None):
        self._styles = styles or self._styles
        self._formats = formats or self._formats
        self._mark_pattern = mark_pattern

    def __getattr__(self, item):
        return partial(self._stylize, style_type=item[1:])

    def _level(self, level):
        return self._stylize(level[0], level, LEVEL)

    def _stylize(self, msg, level, style_type):
        return StyledString(msg, *self._styles[style_type].get(level.lower(), []))

    def _mark(self, str_):
        # TODO; this needs more work. since colors cause the patten not to match (since its not a continuous string)
        if self._mark_pattern is None:
            return str_
        else:
            regex_pattern = re.compile(self._mark_pattern)
            if not re.match(regex_pattern, str_):
                return str_
        marker = self._styles[MARKER]
        modified_str = (
            marker +
            str_.replace(StyledString.STYLE.RESET_ALL, StyledString.STYLE.RESET_ALL + marker) +
            StyledString.STYLE.RESET_ALL
        )
        return modified_str

    def __call__(self, item):
        # If no formats are passed we revert to the default formats (per level)
        formatting = self._formats.get(env.logging.verbosity_level,
                                       DEFAULT_FORMATTING[env.logging.verbosity_level])
        msg = StringIO()
        formatting_kwargs = dict(item=item)

        # level
        formatting_kwargs['level'] = self._level(item.level)

        # implementation
        if item.task:
            # operation task
            implementation = item.task.implementation
            inputs = dict(i.unwrap() for i in item.task.inputs.values())
        else:
            # execution task
            implementation = item.execution.workflow_name
            inputs = dict(i.unwrap() for i in item.execution.inputs.values())

        formatting_kwargs['implementation'] = self._implementation(implementation, item.level)
        formatting_kwargs['inputs'] = self._inputs(inputs, item.level)

        # timestamp
        if 'timestamp' in formatting:
            timestamp = item.created_at.strftime(formatting['timestamp'])
        else:
            timestamp = item.created_at
        formatting_kwargs['timestamp'] = self._timestamp(timestamp, item.level)

        # message
        formatting_kwargs['message'] = self._message(item.msg, item.level)

        # The message would be marked out if containing the provided pattern
        msg.write(self._mark(formatting['message'].format(**formatting_kwargs)))

        # Add the exception and the error msg.
        if item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
            msg.write(os.linesep)
            for line in item.traceback.splitlines(True):
                msg.write(self._traceback('\t' + '|' + line, item.level))

        return msg.getvalue()


stylize_log = _StylizedLogs()


@contextmanager
def format(styles=None, formats=None, mark_pattern=None):
    original_styles = stylize_log._styles
    original_formats = stylize_log._formats
    stylize_log._push(styles=styles, formats=formats, mark_pattern=mark_pattern)
    yield
    stylize_log._push(styles=original_styles, formats=original_formats, mark_pattern=None)


def log(item, *args, **kwargs):
    return getattr(env.logging.logger, item.level.lower())(stylize_log(item), *args, **kwargs)


def log_list(iterator):
    any_logs = False
    for item in iterator:
        log(item)
        any_logs = True
    return any_logs


