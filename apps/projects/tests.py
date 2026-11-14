from contextlib import nullcontext
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404, QueryDict
from django.test import RequestFactory, SimpleTestCase

from .web_form_service import WebFormDefinitionService, parent_submission_for, related_child_forms
from .web_form_views import WebFormFillView
from .web_form_calculations import CalculationError, calculation_value, compile_expression


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
        service.return_value.calculation_plan.return_value = []
        service.return_value.choice_filters.return_value = []
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


class WebFormCalculationTests(SimpleTestCase):
    def service(self, fields):
        definition = {"pages": [{"fields": [{field["name"]: field} for field in fields]}]}
        form = SimpleNamespace(form_defn=json.dumps(definition))
        return WebFormDefinitionService(form)

    def test_actual_location_expressions(self):
        for name, prefix in [("district", "D"), ("ward", "W123"), ("village", "V123456"), ("hamlet", "H123456789")]:
            with self.subTest(name=name):
                tree = compile_expression(f"int(substr(${{{name}}}, {len(prefix)}))")
                self.assertEqual(calculation_value(tree, {name: prefix + "42"}), 42)

    def test_hidden_calculations_are_saved_and_cannot_be_forged(self):
        service = self.service([
            {"type": "integer", "name": "young"},
            {"type": "integer", "name": "adult"},
            {"type": "calculate", "name": "total", "calculation": "${young} + ${adult}"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("young=2&adult=3&total=999"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["total"], 5)
        self.assertNotIn("total", [field["name"] for field in service.pages()[0]["fields"]])

    def test_reverse_dependencies_and_constraints_use_computed_values(self):
        service = self.service([
            {"type": "integer", "name": "value", "constraint": ". <= ${total}"},
            {"type": "calculate", "name": "total", "calculation": "${subtotal} * 2"},
            {"type": "calculate", "name": "subtotal", "body::calculation": "${value} + 1"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("value=3&subtotal=0&total=0"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["total"], 8)
        self.assertEqual(cleaned["subtotal"], 4)

    def test_calculated_visible_field_is_readonly_and_recomputed_on_edit(self):
        service = self.service([
            {"type": "integer", "name": "quantity"},
            {"type": "decimal", "name": "price", "calculation": "${quantity} * 2.5"},
        ])
        self.assertTrue(service.pages()[0]["fields"][1]["readonly"])
        cleaned, _, errors = service._clean_submission_payload(
            QueryDict("quantity=4&price=999"), {}, existing_data={"price": 2.5},
        )
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["price"], 10)

    def test_missing_inputs_do_not_become_zero(self):
        tree = compile_expression("${a} + ${b}")
        self.assertEqual(calculation_value(tree, {"a": 0, "b": 0}), 0)
        self.assertEqual(calculation_value(tree, {"a": 0, "b": ""}), "")
        self.assertEqual(calculation_value(compile_expression("1 div 0"), {}), "")

    def test_conditions_and_quoted_text(self):
        tree = compile_expression("if(${count} > 0, concat('div if ${literal}', ${count}), 'none')")
        self.assertEqual(calculation_value(tree, {"count": 2}), "div if ${literal}2")
        self.assertEqual(calculation_value(tree, {"count": 0}), "none")

    def test_boolean_conversion_handles_blank_and_invalid_numbers(self):
        cases = [
            ("if(number(${missing}), 1, 0)", {}, 0),
            ("if(number(${amount}), 1, 0)", {"amount": "invalid"}, 0),
            ("not(number(${missing}))", {}, True),
            ("number(${missing}) and true()", {}, False),
            ("number(${missing}) or false()", {}, False),
            ("if(${items}, 1, 0)", {"items": []}, 0),
            ("if(number(${amount}), 1, 0)", {"amount": "0"}, 0),
            ("if(number(${amount}), 1, 0)", {"amount": "2"}, 1),
        ]
        for expression, values, expected in cases:
            with self.subTest(expression=expression, values=values):
                self.assertEqual(calculation_value(compile_expression(expression), values), expected)

    def test_typed_equality_preserves_identifiers_and_converts_numbers(self):
        cases = [
            ("${amount} = 1", {"amount": "1.0"}, True),
            ("${amount} != 1", {"amount": "1.0"}, False),
            ("${amount} = 0", {"amount": ""}, False),
            ("${code} = '01'", {"code": "01"}, True),
            ("${code} = '1'", {"code": "01"}, False),
            ("false() = number(${missing})", {}, True),
            ("true() = number(${missing})", {}, False),
        ]
        for expression, values, expected in cases:
            with self.subTest(expression=expression, values=values):
                self.assertEqual(calculation_value(compile_expression(expression), values), expected)

    def test_saved_calculation_uses_numeric_equality(self):
        service = self.service([
            {"type": "decimal", "name": "amount"},
            {"type": "calculate", "name": "result", "calculation": "if(${amount} = 1, 'yes', 'no')"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("amount=1.0"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["result"], "yes")

    def test_unsupported_and_circular_calculations_block_saving(self):
        for expression in ["unknown(${value})", "${total} + 1"]:
            service = self.service([{"type": "calculate", "name": "total", "calculation": expression}])
            _, _, errors = service._clean_submission_payload(QueryDict(), {})
            self.assertIn("total", errors)

    def test_unsafe_expressions_are_rejected(self):
        for expression in ["__import__('os').system('id')", "[x for x in []]", "${a}.__class__"]:
            with self.assertRaises(CalculationError):
                compile_expression(expression)

    def test_irrelevant_calculation_is_not_saved(self):
        service = self.service([
            {"type": "integer", "name": "count"},
            {"type": "calculate", "name": "total", "calculation": "${count} * 2", "relevant": "${count} > 0"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("count=0&total=100"), {})
        self.assertEqual(errors, {})
        self.assertNotIn("total", cleaned)

    def test_medical_codes_ignore_inactive_diagnosis_answers(self):
        service = self.service([
            {"type": "select_one", "name": "record_type", "options": [{"name": "diagnosis"}, {"name": "test"}]},
            {"type": "select_one", "name": "disease_major", "relevant": "${record_type} = 'diagnosis'", "options": [{"name": "MAJ01"}]},
            {"type": "calculate", "name": "disease_major_code", "calculation": "int(substr(${disease_major}, 3))"},
        ])
        for record_type, expected in [("diagnosis", 1), ("test", None)]:
            with self.subTest(record_type=record_type):
                cleaned, _, errors = service._clean_submission_payload(
                    QueryDict(f"record_type={record_type}&disease_major=MAJ01&disease_major_code=999"),
                    {}, existing_data={"disease_major_code": 1},
                )
                self.assertEqual(errors, {})
                self.assertEqual(cleaned.get("disease_major_code"), expected)

    def test_inactive_sources_are_blank_for_calculation_fallbacks(self):
        service = self.service([
            {"type": "integer", "name": "enabled"},
            {"type": "integer", "name": "count", "relevant": "${enabled} = 1"},
            {"type": "calculate", "name": "total", "calculation": "coalesce(${count}, 0) * 2"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("enabled=0&count=99"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["total"], 0)

    def test_transitively_inactive_sources_cannot_feed_calculations(self):
        service = self.service([
            {"type": "integer", "name": "enabled"},
            {"type": "integer", "name": "amount", "relevant": "${selector} = 1"},
            {"type": "integer", "name": "selector", "relevant": "${enabled} = 1"},
            {"type": "calculate", "name": "total", "calculation": "${amount} * 2"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("enabled=0&selector=1&amount=9"), {})
        self.assertEqual(errors, {})
        self.assertNotIn("total", cleaned)

    def test_calculated_relevance_dependencies_are_evaluated_before_sources(self):
        service = self.service([
            {"type": "calculate", "name": "total", "calculation": "${amount} * 2"},
            {"type": "integer", "name": "amount", "relevant": "${enabled} = 1"},
            {"type": "calculate", "name": "enabled", "calculation": "1"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("amount=9"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["total"], 18)


class WebFormChoiceFilterTests(SimpleTestCase):
    def service(self, fields):
        definition = {"pages": [{"fields": [{field["name"]: field} for field in fields]}]}
        return WebFormDefinitionService(SimpleNamespace(form_defn=json.dumps(definition)))

    def location_service(self):
        return self.service([
            {"type": "select_one", "name": "district", "options": [{"name": "D01"}, {"name": "D02"}]},
            {"type": "select_one", "name": "ward", "choice_filter": "filter_one = ${district}",
             "options": [{"name": "D01W01", "filter_one": "D01"}, {"name": "D02W01", "filter_one": "D02"}]},
            {"type": "select_one", "name": "village", "choice_filter": "filter_two = ${ward}",
             "options": [{"name": "D01W01V01", "filter_two": "D01W01"}, {"name": "D02W01V01", "filter_two": "D02W01"}]},
            {"type": "calculate", "name": "ward_id", "calculation": "int(substr(${ward}, 4))"},
        ])

    def test_metadata_and_dependencies_are_available_to_browser(self):
        filters = self.location_service().choice_filters()
        self.assertEqual(filters[0]["dependencies"], ["district"])
        self.assertEqual(filters[0]["options"][0]["attributes"]["filter_one"], "D01")
        self.assertEqual(filters[0]["tree"][0], "op")

    def test_valid_cascade_and_calculation_are_saved(self):
        cleaned, _, errors = self.location_service()._clean_submission_payload(
            QueryDict("district=D01&ward=D01W01&village=D01W01V01"), {},
        )
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["ward_id"], 1)

    def test_forged_selections_are_rejected_at_each_level(self):
        for data, invalid_field in [
            ("district=D01&ward=D02W01", "ward"),
            ("district=D01&ward=D01W01&village=D02W01V01", "village"),
            ("ward=D01W01", "ward"),
        ]:
            with self.subTest(data=data):
                cleaned, _, errors = self.location_service()._clean_submission_payload(QueryDict(data), {})
                self.assertIsNone(cleaned)
                self.assertEqual(errors[invalid_field], "Select a valid option.")

    def test_edits_reject_old_child_selection_after_parent_changes(self):
        _, _, errors = self.location_service()._clean_submission_payload(
            QueryDict("district=D02&ward=D01W01"), {},
            existing_data={"district": "D01", "ward": "D01W01"},
        )
        self.assertIn("ward", errors)

    def test_multiple_selection_filter_uses_option_attributes(self):
        service = self.service([
            {"type": "select_multiple", "name": "categories", "options": [{"name": "a"}, {"name": "b"}]},
            {"type": "select_multiple", "name": "items", "choice_filter": "selected(${categories}, category) and enabled = 1",
             "options": [{"name": "a1", "category": "a", "enabled": 1}, {"name": "b1", "category": "b", "enabled": 1}]},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("categories=a&items=a1"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["items"], ["a1"])
        _, _, errors = service._clean_submission_payload(QueryDict("categories=a&items=a1&items=b1"), {})
        self.assertIn("items", errors)

    def test_filters_support_calculated_parent_values(self):
        service = self.service([
            {"type": "integer", "name": "quantity"},
            {"type": "calculate", "name": "category", "calculation": "if(${quantity} > 5, 'large', 'small')"},
            {"type": "select_one", "name": "item", "choice_filter": "category = ${category}",
             "options": [{"name": "small1", "category": "small"}, {"name": "large1", "category": "large"}]},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("quantity=10&item=large1"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["category"], "large")

    def test_unsupported_filters_fail_closed_for_active_fields(self):
        service = self.service([
            {"type": "select_one", "name": "item", "choice_filter": "unknown(filter_one)", "options": [{"name": "a"}]},
        ])
        _, _, errors = service._clean_submission_payload(QueryDict("item=a"), {})
        self.assertIn("item", errors)

    def test_irrelevant_filters_do_not_block_submission(self):
        service = self.service([
            {"type": "integer", "name": "enabled"},
            {"type": "select_one", "name": "item", "relevant": "${enabled} = 1", "choice_filter": "unknown(filter_one)", "options": [{"name": "a"}]},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("enabled=0&item=a"), {})
        self.assertEqual(errors, {})
        self.assertNotIn("item", cleaned)

    def test_farm_hamlet_without_configured_choices_is_optional(self):
        service = self.service([
            {"type": "select_one", "name": "village", "options": [{"name": "D01W01V02"}, {"name": "D01W03V01"}]},
            {"type": "select_one", "name": "hamlet", "choice_filter": "filter_three = ${village}",
             "options": [{"name": "D01W03V01H01", "filter_three": "D01W03V01"}]},
            {"type": "calculate", "name": "hamlet_id", "calculation": "int(substr(${hamlet}, 10))"},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("village=D01W01V02"), {})
        self.assertEqual(errors, {})
        self.assertNotIn("hamlet_id", cleaned)
        _, _, errors = service._clean_submission_payload(QueryDict("village=D01W01V02&hamlet=D01W03V01H01"), {})
        self.assertIn("hamlet", errors)
        cleaned, _, errors = service._clean_submission_payload(
            QueryDict("village=D01W03V01&hamlet=D01W03V01H01"), {},
        )
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["hamlet_id"], 1)

    def test_numeric_metadata_filter_accepts_equivalent_decimal(self):
        service = self.service([
            {"type": "decimal", "name": "category"},
            {"type": "select_one", "name": "item", "choice_filter": "category = ${category}",
             "options": [{"name": "one", "category": 1}]},
        ])
        cleaned, _, errors = service._clean_submission_payload(QueryDict("category=1.0&item=one"), {})
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["item"], "one")
