from aria.cli.env import Environment
from base_test import TestCliBase
from aria.modeling.models import ServiceTemplate


class MockStorage(object):

    def __init__(self):
        self.service_template = MockServiceTemplateStorage()


class MockServiceTemplateStorage(object):

    def get(self, id_):
        if id_ == '1':  # a service-template with no description and no services.
            st = ServiceTemplate()
            st.name = 'test_st'
            st.services = []
            return st


class TestServiceTemplatesShow(TestCliBase):

    def test_show_no_services_no_description(self, monkeypatch):
        # reroute the logger to a special location, and check it's content.
        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        outcome = self.invoke('service_templates show 1')
