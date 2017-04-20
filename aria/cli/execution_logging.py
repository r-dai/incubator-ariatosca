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

from .color import StyledString
from . import logger
from .env import env

DEFAULT_FORMATTING = {
    logger.NO_VERBOSE: {'message': '{message}'},
    logger.LOW_VERBOSE: {
        'message': '{timestamp} | {level} | {message}',
        'level': '{level[0]}',
        'timestamp': '%H:%M:%S',
    },
    logger.MEDIUM_VERBOSE: {
        'message': '{timestamp} | {level} | {implementation} | {message} ',
        'level': '{level[0]}',
        'timestamp': '%H:%M:%S'
    },
    logger.HIGH_VERBOSE: {
        'message': '{timestamp} | {level} | {implementation}({inputs}) | {message} ',
        'level': '{level[0]}',
        'timestamp': '%H:%M:%S'
    },
}


def _style_level(level):
    levels_format = {
        'info': (StyledString.fore.LIGHTBLUE_EX, ),
        'debug': (StyledString.fore.LIGHTRED_EX, StyledString.style.DIM),
        'error': (StyledString.fore.RED, )
    }
    return StyledString(level[0], *levels_format.get(level.lower(), []))


def _style_timestamp(timestamp, level):
    timestamp_format = {
        'info': (StyledString.fore.LIGHTBLUE_EX, StyledString.style.DIM),
        'debug': (StyledString.fore.LIGHTBLUE_EX, StyledString.style.DIM),
        'error': (StyledString.fore.RED,)
    }
    return StyledString(timestamp, *timestamp_format.get(level.lower(), []))


def _style_msg(msg, level):
    msg_foramts = {
        'info': (StyledString.fore.LIGHTBLUE_EX, ),
        'debug': (StyledString.fore.LIGHTBLUE_EX, StyledString.style.DIM),
        'error': (StyledString.fore.RED, ),
    }
    return StyledString(msg, *msg_foramts.get(level.lower(), []))


def _style_traceback(traceback):
    return StyledString(traceback, StyledString.fore.RED, StyledString.style.DIM)


def _style_implementation(implementation, level):
    implementation_formats = {
        'info': (StyledString.style.DIM, StyledString.fore.LIGHTBLACK_EX),
        'debug': (StyledString.style.DIM, StyledString.fore.LIGHTBLACK_EX),
        'error': (StyledString.fore.RED, ),
    }
    return StyledString(implementation, *implementation_formats.get(level.lower(), []))

_style_inputs = _style_implementation


def _str(item, formats=None):
    # If no formats are passed we revert to the default formats (per level)
    formats = formats or {}
    formatting = formats.get(env.logging.verbosity_level,
                             DEFAULT_FORMATTING[env.logging.verbosity_level])
    msg = StringIO()
    formatting_kwargs = dict(item=item)

    # level
    formatting_kwargs['level'] = _style_level(item.level)

    # implementation
    if item.task:
        implementation = item.task.implementation
        inputs = dict(i.unwrap() for i in item.task.inputs.values())
    else:
        implementation = item.execution.workflow_name
        inputs = dict(i.unwrap() for i in item.execution.inputs.values())

    formatting_kwargs['implementation'] = _style_implementation(implementation, item.level)
    formatting_kwargs['inputs'] = _style_inputs(inputs, item.level)

    # timestamp
    if 'timestamp' in formatting:
        timestamp = item.created_at.strftime(formatting['timestamp'])
    else:
        timestamp = item.created_at
    formatting_kwargs['timestamp'] = _style_timestamp(timestamp, item.level)

    # message
    formatting_kwargs['message'] = _style_msg(item.msg, item.level)

    msg.write(formatting['message'].format(**formatting_kwargs) + os.linesep)

    # Add the exception and the error msg.
    if item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
        for line in item.traceback.splitlines(True):
            msg.write(_style_traceback('\t' + '|' + line))

    return msg.getvalue()


def log(item, *args, **kwargs):
    return getattr(env.logging.logger, item.level.lower())(_str(item), *args, **kwargs)


def log_list(iterator):
    any_logs = False
    for item in iterator:
        log(item)
        any_logs = True
    return any_logs


