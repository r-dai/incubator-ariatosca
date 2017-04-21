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
from StringIO import StringIO

import colorama


class StyledString(object):

    FORE = colorama.Fore
    BACK = colorama.Back
    STYLE = colorama.Style

    def __init__(self, str_to_stylize, *style_args):
        """
        
        :param str_to_stylize: 
        :param style_args: 
        :param kwargs:
            to_close: specifies if end the format on the current line. default to True
        """
        colorama.init()
        self._original_str = str_to_stylize
        self._args = style_args
        self._apply_style()

    def __str__(self):
        return self._stylized_str

    def _apply_style(self):
        assert all(self._is_valid(arg) for arg in self._args)

        styling_str = StringIO()
        for arg in self._args:
            styling_str.write(arg)
        styling_str.write(self._original_str)
        styling_str.write(self.STYLE.RESET_ALL)
        self._stylized_str = styling_str.getvalue()

    def _is_valid(self, value):
        return any(value in vars(type).values() for type in (self.FORE, self.BACK, self.STYLE))
