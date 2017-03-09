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

import pytest

from aria.storage.modeling import model_base, structure


@pytest.fixture(autouse=True)
def cleanup_instantiator(request):
    instantiator = MockTemplate.instantiate

    def clear_instantiator():
        MockTemplate.instantiate = instantiator
    request.addfinalizer(clear_instantiator)


class MockTemplate(model_base.template_elements.TemplateBase):
    def __init__(self, template_name):
        self.template_name = template_name


class MockInstnace(structure.ModelMixin):
    def __init__(self, instance_name):
        self.instance_name = instance_name


def test_base_instantiation():
    name = 'my_name'

    @MockTemplate.instantiates(instance_cls=MockInstnace)
    def initiator(self, instance_cls):
        return instance_cls(self.template_name)

    mock_template = MockTemplate(name)
    mock_instance = mock_template.instantiate()

    assert mock_instance.instance_name == mock_template.template_name == name


def test_reinstantiate():

    name = 'my_name'

    @MockTemplate.instantiates(instance_cls=MockInstnace)
    def initiator(self, instance_cls):
        return instance_cls(self.template_name)

    mock_template = MockTemplate(name)
    mock_instance = mock_template.instantiate()
    assert mock_instance.instance_name == mock_template.template_name == name

    def new_initiator(self, instance_cls):
        return instance_cls('new_{0}'.format(self.template_name))

    with pytest.raises(BaseException):
        MockTemplate.instantiates(func=new_initiator, instance_cls=MockInstnace)

    mock_template = MockTemplate(name)
    mock_instance = mock_template.instantiate()
    assert mock_instance.instance_name == mock_template.template_name == name

    MockTemplate.instantiates(func=new_initiator, instance_cls=MockInstnace, override=True)
    mock_template = MockTemplate(name)
    mock_instance = mock_template.instantiate()
    assert mock_template.template_name == name
    assert mock_instance.instance_name == 'new_{0}'.format(name)
