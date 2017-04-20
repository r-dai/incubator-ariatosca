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

colorama.init()


class StyledString(str):

    fore = colorama.Fore
    back = colorama.Back
    style = colorama.Style

    def __init__(self, str_, *args):
        super(StyledString, self).__init__()
        # TODO: raise proper exception
        if not all(self._is_valid(arg) for arg in args):
            raise Exception("bla bla bla")
        self._str = str_
        self._args = args
        self._stylized_str = None

    def __str__(self):
        if self._stylized_str is None:
            styling_str = StringIO()
            for arg in self._args:
                styling_str.write(arg)
            styling_str.write(self._str)
            styling_str.write(self.style.RESET_ALL)
            self.stylized_str = styling_str.getvalue()

        return self.stylized_str

    def _is_valid(self, value):
        return any(value in vars(instance).values()
                   for instance in (self.fore, self.back, self.style))
