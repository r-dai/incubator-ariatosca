from aria.cli import service_template_utils
from aria.cli.env import Environment
from aria.cli.exceptions import AriaCliError
from aria.core import Core
from aria.storage import exceptions as storage_exceptions
from tests.cli.base_test import TestCliBase, assert_exception_raised, raise_exception
from tests.mock import models

import pytest


@pytest.fixture
def mock_object(mocker):
    return mocker.MagicMock()


class MockStorage(object):

    def __init__(self):
        self.service_template = MockServiceTemplateStorage


class MockServiceTemplateStorage(object):

    @staticmethod
    def list(**_):
        return [models.create_service_template('test_st'),
                models.create_service_template('test_st2')]

    @staticmethod
    def get(id):
        st = models.create_service_template('test_st')
        if id == '1':  # no services and no description.
            st.services = []
        if id == '2':  # no services, but an description
            st.description = 'test_description'
            st.services = []
        if id == '3':  # one service, and a description
            service = models.create_service(st, 'test_s')
            st.description = 'test_description'
            st.services = [service]
        if id == '4':  # one service, and a description
            service = models.create_service(st, 'test_s')
            st.services = [service]
        return st


class TestServiceTemplatesShow(TestCliBase):

    def test_show_no_services_no_description(self, monkeypatch):

        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        self.invoke('service_templates show 1')

        assert 'Description:' not in self.logger_output_string
        assert 'Existing services:\n[]' in self.logger_output_string

    def test_show_no_services_yes_description(self, monkeypatch):

        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        self.invoke('service_templates show 2')

        assert 'Description:\ntest_description' in self.logger_output_string
        assert 'Existing services:\n[]' in self.logger_output_string

    def test_show_one_service_yes_description(self, monkeypatch):

        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        self.invoke('service_templates show 3')

        assert 'Description:\ntest_description' in self.logger_output_string
        assert "Existing services:\n['test_s']" in self.logger_output_string

    def test_show_one_service_no_description(self, monkeypatch):

        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        self.invoke('service_templates show 4')

        assert 'Description:' not in self.logger_output_string
        assert "Existing services:\n['test_s']" in self.logger_output_string

    def test_show_exception_raise_when_no_service_template_with_given_id(self):

        # TODO consider removing as it does not seem to test the cli but rather the message received
        # from the storage
        outcome = self.invoke('service_templates show 5')
        assert_exception_raised(
            outcome,
            expected_exception=storage_exceptions.NotFoundError,
            expected_msg='Requested `ServiceTemplate` with ID `5` was not found')


class TestServiceTemplatesList(TestCliBase):

    def test_list_one_service_template(self, monkeypatch):

        monkeypatch.setattr(Environment, 'model_storage', MockStorage())
        self.invoke('service_templates list')
        assert 'test_st' in self.logger_output_string
        assert 'test_st2' in self.logger_output_string

    def test_list_ascending(self, monkeypatch, mock_object):

        monkeypatch.setattr(Environment, 'model_storage', mock_object)
        self.invoke('service_templates list --sort-by name')
        mock_object.service_template.list.assert_called_with(sort={'name': 'asc'})

    def test_list_descending(self, monkeypatch, mock_object):

        monkeypatch.setattr(Environment, 'model_storage', mock_object)
        self.invoke('service_templates list --sort-by name --descending')
        mock_object.service_template.list.assert_called_with(sort={'name': 'desc'})

    def test_list_default_sorting(self, monkeypatch, mock_object):

        monkeypatch.setattr(Environment, 'model_storage', mock_object)
        self.invoke('service_templates list')
        mock_object.service_template.list.assert_called_with(sort={'created_at': 'asc'})


class TestServiceTemplatesStore(TestCliBase):

    def test_store_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(Core, 'create_service_template', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        self.invoke('service_templates store stubpath test_st')
        assert 'Service template test_st stored' in self.logger_output_string

    def test_store_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(Core,
                            'create_service_template',
                            raise_exception(storage_exceptions.NotFoundError,
                                            msg='UNIQUE constraint failed'))

        outcome = self.invoke('service_templates store stubpath test_st')
        assert_exception_raised(
            outcome,
            expected_exception=AriaCliError,
            expected_msg='Could not store service template `test_st`\n'
                         'There already a exists a service template with the same name')
