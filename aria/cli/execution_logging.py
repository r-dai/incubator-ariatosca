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
from contextlib import contextmanager

from . import logger
from .env import env

DEFAULT_FORMATTING = {
    logger.NO_VERBOSE: {'main_msg': '{item.msg}'},
    logger.LOW_VERBOSE: {
        'main_msg': '{created_at} | {item.level[0]} | {item.msg}',
        'created_at': '%H:%M:%S'
    }
}


class _ExecutionLogging(object):

    def __init__(self, item, formats=None):
        self._item = item
        self._formats = formats or DEFAULT_FORMATTING

    def __repr__(self):
        # Only NO_VERBOSE and LOW_VERBOSE are configurable formats. configuring
        # the low verbose level should affect any higher level.
        formats = self._formats[min(env.logging.verbosity_level, logger.LOW_VERBOSE)]

        kwargs = dict(item=self._item)
        if 'created_at' in formats:
            kwargs['created_at'] = self._item.created_at.strftime(formats['created_at'])
        if 'level' in formats:
            kwargs['level'] = formats['level'].format(self._item.level)
        if 'msg' in formats:
            kwargs['msg'] = formats['msg'].format(self._item.msg)

        if 'actor' in formats and self._item.task:
            kwargs['actor'] = formats['actor'].format(self._item.task.actor)
        if 'execution' in formats:
            kwargs['execution'] = formats['execution'].format(self._item.execution)

        # If no format was supplied just print out the original msg.
        msg = formats.get('main_msg', '{item.msg}').format(**kwargs)

        # Add the exception and the error msg.
        if self._item.traceback and env.logging.verbosity_level >= logger.MEDIUM_VERBOSE:
            msg += os.linesep + '------>'
            for line in self._item.traceback.splitlines(True):
                msg += '\t' + '|' + line

        return msg

    def log(self, *args, **kwargs):
        return getattr(env.logging.logger, self._item.level.lower())(self)


load = _ExecutionLogging
