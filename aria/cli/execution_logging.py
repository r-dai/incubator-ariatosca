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
from StringIO import StringIO
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

DEFAULT_STYLES = {
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
    }
}


class _StylizedLogs(object):

    def __init__(self, styles=None):
        self._styles = styles or DEFAULT_STYLES

    def set_styles(self, styles):
        self._styles = styles

    def unset_styles(self, to_defaults=False):
        self._styles = DEFAULT_STYLES if to_defaults else {}

    def __getattr__(self, item):
        return partial(self._style, style_type=item)

    def level(self, level):
        return self._style(level[0], level, LEVEL)

    def _style(self, msg, level, style_type):
        return StyledString(msg, *self._styles[style_type].get(level.lower(), []))


stylized_log = _StylizedLogs()


def _str(item, formats=None):
    # If no formats are passed we revert to the default formats (per level)
    formats = formats or {}
    formatting = formats.get(env.logging.verbosity_level,
                             DEFAULT_FORMATTING[env.logging.verbosity_level])
    msg = StringIO()
    formatting_kwargs = dict(item=item)

    # level
    formatting_kwargs['level'] = stylized_log.level(item.level)

    # implementation
    if item.task:
        # operation task
        implementation = item.task.implementation
        inputs = dict(i.unwrap() for i in item.task.inputs.values())
    else:
        # execution task
        implementation = item.execution.workflow_name
        inputs = dict(i.unwrap() for i in item.execution.inputs.values())

    formatting_kwargs['implementation'] = stylized_log.implementation(implementation, item.level)
    formatting_kwargs['inputs'] = stylized_log.inputs(inputs, item.level)

    # timestamp
    if 'timestamp' in formatting:
        timestamp = item.created_at.strftime(formatting['timestamp'])
    else:
        timestamp = item.created_at
    formatting_kwargs['timestamp'] = stylized_log.timestamp(timestamp, item.level)

    # message
    formatting_kwargs['message'] = stylized_log.message(item.msg, item.level)

    msg.write(formatting['message'].format(**formatting_kwargs))

    # Add the exception and the error msg.
    if item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
        msg.write(os.linesep)
        for line in item.traceback.splitlines(True):
            msg.write(stylized_log.traceback('\t' + '|' + line, item.level))

    return msg.getvalue()


def log(item, *args, **kwargs):
    return getattr(env.logging.logger, item.level.lower())(_str(item), *args, **kwargs)


def log_list(iterator):
    any_logs = False
    for item in iterator:
        log(item)
        any_logs = True
    return any_logs


