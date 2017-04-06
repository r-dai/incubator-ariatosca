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
import copy
import logging
import logging.config


HIGH_VERBOSE = 3
MEDIUM_VERBOSE = 2
LOW_VERBOSE = 1
NO_VERBOSE = 0

DEFAULT_LOGGER_CONFIG = {
    "version": 1,
    "formatters": {
        "file": {
            "format": "%(asctime)s [%(levelname)s] %(message)s"
        },
        "console": {
            "format": "%(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file",
            "maxBytes": "5000000",
            "backupCount": "20"
        },
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "console"
        }
    }
}


class _SugaredModelLogger(object):
    def __init__(self, base_logger, model_logger_level, model_logger_formats):
        self._logger = base_logger
        self._model_logger_level = model_logger_level
        self._formats = model_logger_formats

    def _set_model_logger_level(self, value):
        self._model_logger_level = logging.INFO if value == NO_VERBOSE else logging.DEBUG

    def log(self, item):
        kwargs = dict(item=item)

        formats = self._formats[self._model_logger_level]

        if 'created_at' in formats:
            kwargs['created_at'] = item.created_at.strftime(formats['created_at'])
        if 'level' in formats:
            kwargs['level'] = formats['level'].format(item.level)
        if 'msg' in formats:
            kwargs['msg'] = formats['msg'].format(item.msg)

        if 'actor' in formats and item.task:
            kwargs['actor'] = formats['actor'].format(item.task.actor)
        if 'execution' in formats:
            kwargs['execution'] = formats['execution'].format(item.execution)

        # If no format was supplied just print out the original msg.
        msg = formats.get('main_msg', '{item.msg}').format(**kwargs)

        # Add the exception and the error msg.
        if item.traceback and self.level > LOW_VERBOSE:
            msg += os.linesep + '------>'
            for line in item.traceback.splitlines(True):
                msg += '\t' + '|' + line

        return getattr(self._logger, item.level.lower())(msg)

    def __getattr__(self, item):
        return getattr(self._logger, item)


class Logging(object):

    def __init__(self, config):
        self._log_file = None
        self._verbosity_level = NO_VERBOSE
        self._all_loggers = []
        self._configure_loggers(config)

        self._lgr = _SugaredModelLogger(
            base_logger=logging.getLogger('aria.cli.main'),
            model_logger_level=self._verbosity_level,
            model_logger_formats={
                logging.INFO: {
                    'main_msg': '{item.msg}',
                },
                logging.DEBUG: {
                    'main_msg': '{created_at} | {item.level[0]} | {item.msg}',
                    'created_at': '%H:%M:%S'
                }
            }
        )

    @property
    def logger(self):
        return self._lgr

    @property
    def log_file(self):
        return self._log_file

    @property
    def verbosity_level(self):
        return self._verbosity_level

    def is_high_verbose_level(self):
        return self.verbosity_level == HIGH_VERBOSE

    @verbosity_level.setter
    def verbosity_level(self, level):
        self._verbosity_level = level
        self._lgr._set_model_logger_level(level)
        if self.is_high_verbose_level():
            for logger_name in self._all_loggers:
                logging.getLogger(logger_name).setLevel(logging.DEBUG)

    def _configure_loggers(self, config):
        loggers_config = config.logging.loggers
        logfile = config.logging.filename

        logger_dict = copy.deepcopy(DEFAULT_LOGGER_CONFIG)
        if logfile:
            # set filename on file handler
            logger_dict['handlers']['file']['filename'] = logfile
            logfile_dir = os.path.dirname(logfile)
            if not os.path.exists(logfile_dir):
                os.makedirs(logfile_dir)
            self._log_file = logfile
        else:
            del logger_dict['handlers']['file']

        # add handlers to all loggers
        loggers = {}
        for logger_name in loggers_config:
            loggers[logger_name] = dict(handlers=list(logger_dict['handlers'].keys()))
        logger_dict['loggers'] = loggers

        # set level for all loggers
        for logger_name, logging_level in loggers_config.iteritems():
            log = logging.getLogger(logger_name)
            level = logging._levelNames[logging_level.upper()]
            log.setLevel(level)
            self._all_loggers.append(logger_name)

        logging.config.dictConfig(logger_dict)


class LogConsumer(object):

    def __init__(self, model_storage, execution_id):
        self._last_visited_id = 0
        self._model_storage = model_storage
        self._execution_id = execution_id

    def __iter__(self):

        for log in self._model_storage.log.iter(filters=dict(
                execution_fk=self._execution_id, id=dict(gt=self._last_visited_id))):
            self._last_visited_id = log.id
            yield log
