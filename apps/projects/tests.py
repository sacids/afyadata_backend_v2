from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404, QueryDict
from django.test import RequestFactory, SimpleTestCase

from .web_form_service import WebFormDefinitionService, parent_submission_for, related_child_forms
from .web_form_views import WebFormFillView


class ChildWebFormTests(SimpleTestCase):
    def setUp(self):
        self.form = SimpleNamespace(pk="child", project_id="project", form_defn="{}")
        self.parent = SimpleNamespace(
            uuid="parent-record", deleted=0,
            form=SimpleNamespace(children="12, 34, invalid", project_id="project"),
        )
        self.request = RequestFactory().get("/fill?parent_id=parent-record")
        self.request.user = Mock()

    @patch("apps.projects.web_form_service.FormData.objects.select_related")
    def test_parent_summary_is_limited_to_same_project_and_live_records(self, select_related):
        instance = SimpleNamespace(parent_id="parent-record", form=self.form)
        parent_submission_for(instance)
        select_related.assert_called_once_with("form")
        select_related.return_value.filter.assert_called_once_with(
            uuid="parent-record", deleted=0, form__project_id="project",
        )

    @patch("apps.projects.web_form_service.FormData.objects.select_related")
    def test_root_record_has_no_parent_summary(self, select_related):
        self.assertIsNone(parent_submission_for(SimpleNamespace(parent_id=None)))
        select_related.assert_not_called()

    @patch("apps.projects.web_form_service.FormDefinition.objects.filter")
    def test_relationship_uses_codes_and_same_project(self, filter_forms):
        related_child_forms(self.parent.form)
        filter_forms.assert_called_once_with(project_id="project", code__in=[12, 34])

    @patch("apps.projects.web_form_views.get_accessible_web_form_data_or_404")
    @patch("apps.projects.web_form_views.related_child_forms")
    def test_parent_must_have_active_child_relationship(self, children, accessible):
        accessible.return_value = self.parent
        children.return_value.filter.return_value.exists.return_value = False
        with self.assertRaises(Http404):
            WebFormFillView().get_parent_instance(self.request, self.form)
        accessible.assert_called_once_with(self.request.user, "parent-record")

    def test_standalone_form_has_no_parent(self):
        request = RequestFactory().get("/fill")
        self.assertIsNone(WebFormFillView().get_parent_instance(request, self.form))

    @patch("apps.projects.web_form_views.render")
    @patch("apps.projects.web_form_views.WebFormDefinitionService")
    @patch("apps.projects.web_form_views.get_accessible_web_form_or_404")
    def test_open_child_form_does_not_save_or_show_previous_success(self, accessible, service, render):
        self.form.title = "Child form"
        self.form.project = SimpleNamespace(pk="project", title="Project")
        accessible.return_value = self.form
        service.return_value.pages.return_value = []
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)
        messages.success(self.request, "Form submitted successfully.")
        messages.warning(self.request, "A warning to keep.")

        with patch.object(WebFormFillView, "get_parent_instance", return_value=self.parent):
            WebFormFillView().get(self.request, self.form.pk)

        context = render.call_args.args[2]
        self.assertIs(context["parent_instance"], self.parent)
        self.assertFalse(context["is_edit"])
        self.assertEqual([str(message) for message in context["messages"]], ["A warning to keep."])
        service.return_value.validate_and_save.assert_not_called()

    @patch("apps.projects.web_form_views.redirect")
    @patch("apps.projects.web_form_views.WebFormDefinitionService")
    @patch("apps.projects.web_form_views.get_accessible_web_form_or_404")
    def test_success_is_added_only_after_submission(self, accessible, service, redirect):
        accessible.return_value = self.form
        instance = SimpleNamespace(uuid="child-record")
        service.return_value.validate_and_save.return_value = (instance, {})
        request = RequestFactory().post("/fill?parent_id=parent-record", {})
        request.user = self.request.user
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch.object(WebFormFillView, "get_parent_instance", return_value=self.parent):
            WebFormFillView().post(request, self.form.pk)
        self.assertEqual([str(message) for message in messages.get_messages(request)], ["Form submitted successfully."])
        redirect.assert_called_once_with("projects:form-data-instance", data_id="child-record")

    @patch("apps.projects.web_form_service.related_child_forms")
    def test_save_rejects_unrelated_parent(self, children):
        children.return_value.filter.return_value.exists.return_value = False
        service = WebFormDefinitionService(self.form)
        with self.assertRaises(ValueError):
            service.validate_and_save(QueryDict(), {}, parent_instance=self.parent)

    @patch("apps.projects.web_form_service.FormData.objects.create")
    @patch("apps.projects.web_form_service.transaction.atomic", return_value=nullcontext())
    @patch("apps.projects.web_form_service.related_child_forms")
    def test_child_save_stores_parent_record_uuid(self, children, atomic, create):
        children.return_value.filter.return_value.exists.return_value = True
        service = WebFormDefinitionService(self.form)
        with patch.object(service, "_clean_submission_payload", return_value=({"count": 2}, [], {})), \
                patch.object(service, "_submission_title", return_value="Child record"):
            instance, errors = service.validate_and_save(QueryDict(), {}, parent_instance=self.parent)
        self.assertEqual(errors, {})
        self.assertIs(instance, create.return_value)
        self.assertEqual(create.call_args.kwargs["parent_id"], "parent-record")
        self.assertIs(create.call_args.kwargs["form"], self.form)
