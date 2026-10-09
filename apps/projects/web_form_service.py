import os
import re
import uuid

from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from .models import FormData, FormDataFile
from .utils import infer_uploaded_file_type, load_json


INPUT_TYPE_MAP = {
    "text": "text",
    "string": "text",
    "integer": "number",
    "int": "number",
    "decimal": "number",
    "float": "number",
    "date": "date",
    "datetime": "datetime-local",
    "dateTime": "datetime-local",
    "time": "time",
    "email": "email",
    "phone": "tel",
    "tel": "tel",
    "geopoint": "text",
}

FILE_FIELD_TYPES = {
    "file",
    "image",
    "audio",
    "video",
    "binary",
    "signature",
}

SKIPPED_FIELD_TYPES = {
    "calculate",
    "hidden",
    "acknowledge",
}


class WebFormDefinitionService:
    """
    Isolated renderer/parser for filling FormDefinition records through the web.

    This service intentionally writes to the existing FormData and FormDataFile
    models, while keeping the current mobile/API submission flows unchanged.
    """

    def __init__(self, form_definition, user=None, language=None):
        self.form_definition = form_definition
        self.user = user
        self.definition = load_json(form_definition.form_defn or "{}") or {}
        self.language = language or self._default_language()

    def _default_language(self):
        meta_language = self.definition.get("meta", {}).get("default_language")
        if meta_language:
            return meta_language
        languages = self.definition.get("languages", [])
        return languages[0] if languages else "Default"

    def _label(self, item):
        candidates = [
            f"label::{self.language}",
            "label::Default",
            "label::English (en)",
            "label",
            "name",
        ]
        for key in candidates:
            value = item.get(key)
            if value:
                return value
        return ""

    def _hint(self, item):
        candidates = [
            f"hint::{self.language}",
            "hint::Default",
            "hint::English (en)",
            "hint",
        ]
        for key in candidates:
            value = item.get(key)
            if value:
                return value
        return ""

    def _localized_value(self, item, base_key):
        candidates = [
            f"{base_key}::{self.language}",
            f"{base_key}::Default",
            f"{base_key}::English (en)",
            base_key,
        ]
        for key in candidates:
            value = item.get(key)
            if value:
                return value
        return ""

    def _is_required(self, item):
        value = item.get("required")
        if isinstance(value, bool):
            return value
        return str(value or "").strip().lower() in {"yes", "true", "1"}

    def _is_readonly(self, item):
        value = item.get("readonly")
        if isinstance(value, bool):
            return value
        return str(value or "").strip().lower() in {"yes", "true", "1"}

    def _option_label(self, option):
        return self._label(option) or option.get("name") or ""

    def _options(self, item):
        options = item.get("options") or []
        if not isinstance(options, list):
            return []
        return [
            {
                "value": option.get("name"),
                "label": self._option_label(option),
            }
            for option in options
            if option.get("name") is not None
        ]

    def _combine_relevant(self, *expressions):
        parts = [str(item).strip() for item in expressions if str(item or "").strip()]
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return " and ".join(f"({part})" for part in parts)

    def _iter_field_items(self, container, inherited_relevant=""):
        container_relevant = self._combine_relevant(
            inherited_relevant,
            container.get("relevant") or "",
        )
        fields = container.get("fields") or []
        for field_group in fields:
            if not isinstance(field_group, dict):
                continue
            if field_group.get("type") == "group":
                yield from self._iter_field_items(
                    field_group,
                    inherited_relevant=container_relevant,
                )
                continue
            for name, field in field_group.items():
                if isinstance(field, dict):
                    field_copy = dict(field)
                    field_copy["relevant"] = self._combine_relevant(
                        container_relevant,
                        field.get("relevant") or "",
                    )
                    yield name, field_copy

        for page in container.get("pages") or []:
            if isinstance(page, dict):
                yield from self._iter_field_items(
                    page,
                    inherited_relevant=container_relevant,
                )

    def _field_value(self, name, bound_data):
        if not bound_data:
            return ""
        return bound_data.get(name, "")

    def _field_values(self, name, bound_data):
        if not bound_data:
            return []
        if hasattr(bound_data, "getlist"):
            return bound_data.getlist(name)
        value = bound_data.get(name, [])
        return value if isinstance(value, list) else [value]

    def _field_descriptor(self, name, field, bound_data=None):
        field_type = field.get("type") or "text"
        if field_type in SKIPPED_FIELD_TYPES:
            return None

        selected_values = self._field_values(name, bound_data)
        constraint = field.get("constraint") or field.get("body::constraint") or ""
        relevant = field.get("relevant") or ""
        descriptor = {
            "name": name,
            "type": field_type,
            "label": self._label(field) or name.replace("_", " ").title(),
            "hint": self._hint(field),
            "required": self._is_required(field),
            "readonly": self._is_readonly(field),
            "appearance": field.get("appearance") or "",
            "default": field.get("default") or "",
            "relevant": relevant,
            "constraint": constraint,
            "constraint_message": self._localized_value(field, "constraint_message"),
            "options": self._options(field),
            "value": self._field_value(name, bound_data),
            "selected_values": selected_values,
            "input_type": INPUT_TYPE_MAP.get(field_type, "text"),
            "is_note": field_type == "note",
            "is_textarea": field_type in {"textarea", "multiline"},
            "is_select_one": field_type in {"select_one", "select", "select_db"},
            "is_select_multiple": field_type in {"select_multiple", "rank"},
            "is_file": field_type in FILE_FIELD_TYPES,
        }
        return descriptor

    def pages(self, bound_data=None, errors=None):
        errors = errors or {}
        rendered_pages = []
        source_pages = self.definition.get("pages") or []
        for index, page in enumerate(source_pages):
            if not isinstance(page, dict):
                continue
            page_relevant = page.get("relevant") or ""
            fields = []
            for name, field in self._iter_field_items(page):
                descriptor = self._field_descriptor(name, field, bound_data=bound_data)
                if descriptor:
                    descriptor["has_error"] = name in errors
                    fields.append(descriptor)
            if fields:
                rendered_pages.append(
                    {
                        "index": len(rendered_pages),
                        "label": self._label(page) or f"Section {index + 1}",
                        "hint": self._hint(page),
                        "relevant": page_relevant,
                        "fields": fields,
                        "has_errors": any(field["has_error"] for field in fields),
                    }
                )
        return rendered_pages

    def fields(self):
        for page in self.pages():
            yield from page["fields"]

    def _option_values(self, field):
        return {str(option["value"]) for option in field["options"]}

    def _post_values(self, field, post_data):
        if field["is_select_multiple"]:
            return post_data.getlist(field["name"])
        return post_data.get(field["name"], "")

    def _expression_value(self, value):
        if isinstance(value, list):
            return value
        if value in (None, ""):
            return ""
        return value

    def _evaluate_relevant(self, expression, data):
        if not expression:
            return True
        result = self._evaluate_expression(expression, data, current_value="")
        return bool(result)

    def _evaluate_constraint(self, expression, data, current_value):
        if not expression:
            return True
        result = self._evaluate_expression(expression, data, current_value=current_value)
        return bool(result)

    def _evaluate_expression(self, expression, data, current_value=""):
        """
        Small, conservative evaluator for common XLSForm expressions.
        Unsupported expressions are treated as passing so they do not block entry.
        """
        expr = str(expression or "").strip()
        if not expr:
            return True
        expr = strip_wrapping_parentheses(expr)

        try:
            not_match = re.fullmatch(r"not\s*\((?P<inner>.*)\)", expr, flags=re.IGNORECASE)
            if not_match:
                return not self._evaluate_expression(
                    not_match.group("inner"),
                    data,
                    current_value=current_value,
                )

            selected_match = re.fullmatch(
                r"selected\(\s*\$\{(?P<field>[^}]+)\}\s*,\s*['\"](?P<value>[^'\"]+)['\"]\s*\)",
                expr,
                flags=re.IGNORECASE,
            )
            if selected_match:
                values = data.get(selected_match.group("field"), [])
                if not isinstance(values, list):
                    values = normalize_to_list(values)
                return str(selected_match.group("value")) in {str(item) for item in values}

            regex_match = re.fullmatch(
                r"regex\(\s*\.\s*,\s*['\"](?P<pattern>[^'\"]+)['\"]\s*\)",
                expr,
                flags=re.IGNORECASE,
            )
            if regex_match:
                return re.search(regex_match.group("pattern"), str(current_value or "")) is not None

            parts = split_logical_expression(expr)
            if len(parts) > 1:
                result = self._evaluate_expression(parts[0], data, current_value=current_value)
                index = 1
                while index < len(parts):
                    operator = parts[index].lower()
                    next_result = self._evaluate_expression(parts[index + 1], data, current_value=current_value)
                    result = (result and next_result) if operator == "and" else (result or next_result)
                    index += 2
                return result

            comparison = re.fullmatch(
                r"(?P<left>\.|\$\{[^}]+\})\s*(?P<op>=|!=|>=|<=|>|<)\s*(?P<right>.+)",
                expr,
            )
            if comparison:
                left = self._resolve_expression_operand(
                    comparison.group("left"),
                    data,
                    current_value=current_value,
                )
                right = self._resolve_expression_operand(
                    comparison.group("right"),
                    data,
                    current_value=current_value,
                )
                return compare_values(left, comparison.group("op"), right)
        except Exception:
            return True

        return True

    def _resolve_expression_operand(self, operand, data, current_value=""):
        value = str(operand or "").strip()
        if value == ".":
            return current_value
        if value.startswith("${") and value.endswith("}"):
            return self._expression_value(data.get(value[2:-1], ""))
        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            return value[1:-1]
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def _clean_scalar_value(self, field, value):
        if value in (None, ""):
            return ""

        field_type = field["type"]
        if field_type in {"integer", "int"}:
            return int(value)
        if field_type in {"decimal", "float"}:
            return float(value)
        return value

    def validate_and_save(self, post_data, uploaded_files):
        errors = {}
        cleaned_data = {}
        file_payloads = []
        raw_data = {}

        for field in self.fields():
            if field["is_note"]:
                continue
            raw_data[field["name"]] = self._post_values(field, post_data)

        for field in self.fields():
            name = field["name"]

            if field["is_note"]:
                continue

            if not self._evaluate_relevant(field["relevant"], raw_data):
                continue

            if field["is_file"]:
                file_obj = uploaded_files.get(name)
                if field["required"] and not file_obj:
                    errors[name] = "This field is required."
                if file_obj:
                    file_payloads.append((field, file_obj))
                continue

            if field["is_select_multiple"]:
                values = post_data.getlist(name)
                if field["required"] and not values:
                    errors[name] = "This field is required."
                invalid_values = set(values) - self._option_values(field)
                if invalid_values:
                    errors[name] = "Select a valid option."
                cleaned_data[name] = values
                continue

            value = post_data.get(name, "")
            if field["required"] and value in ("", None):
                errors[name] = "This field is required."
                continue

            try:
                cleaned_value = self._clean_scalar_value(field, value)
            except (TypeError, ValueError):
                errors[name] = "Enter a valid value."
                continue

            if field["is_select_one"] and cleaned_value != "":
                if str(cleaned_value) not in self._option_values(field):
                    errors[name] = "Select a valid option."
                    continue

            if cleaned_value != "" and not self._evaluate_constraint(
                field["constraint"],
                {**raw_data, **cleaned_data, name: cleaned_value},
                cleaned_value,
            ):
                errors[name] = field["constraint_message"] or "This value is not valid."
                continue

            if cleaned_value != "":
                cleaned_data[name] = cleaned_value

        if errors:
            return None, errors

        now = timezone.now()
        instance_uuid = str(uuid.uuid4())

        with transaction.atomic():
            instance = FormData.objects.create(
                uuid=instance_uuid,
                original_uuid=instance_uuid,
                form=self.form_definition,
                title=self._submission_title(cleaned_data, now),
                form_data=cleaned_data,
                created_at=now,
                created_by=self.user if getattr(self.user, "is_authenticated", False) else None,
                created_by_name=self._created_by_name(),
                updated_at=now,
                last_updated_at=now,
                submitted_at=now,
                synced=0,
                deleted=0,
            )

            for field, file_obj in file_payloads:
                saved_path = self._save_file(file_obj)
                cleaned_data[field["name"]] = saved_path
                FormDataFile.objects.create(
                    form_data=instance,
                    file=saved_path,
                    file_type=infer_uploaded_file_type(
                        content_type=getattr(file_obj, "content_type", None),
                        filename=getattr(file_obj, "name", None),
                    ),
                    original_name=getattr(file_obj, "name", ""),
                    field_name=field["name"],
                    uploaded_by=self.user if getattr(self.user, "is_authenticated", False) else None,
                )

            if file_payloads:
                update_time = timezone.now()
                FormData.objects.filter(pk=instance.pk).update(
                    form_data=cleaned_data,
                    updated_at=update_time,
                    last_updated_at=update_time,
                )
                instance.form_data = cleaned_data

        return instance, {}

    def _save_file(self, file_obj):
        original_name = os.path.basename(getattr(file_obj, "name", "") or "upload.bin")
        path = f"uploads/{uuid.uuid4().hex}_{original_name}"
        return default_storage.save(path, file_obj)

    def _created_by_name(self):
        if not getattr(self.user, "is_authenticated", False):
            return ""
        return self.user.get_full_name() or self.user.username

    def _submission_title(self, cleaned_data, submitted_at):
        for value in cleaned_data.values():
            if isinstance(value, str) and value.strip():
                return value[:150]
        return f"{self.form_definition.title} - {submitted_at.strftime('%Y-%m-%d %H:%M')}"


def normalize_to_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def coerce_comparable(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return ""
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def compare_values(left, operator, right):
    left_value = coerce_comparable(left)
    right_value = coerce_comparable(right)

    if operator == "=":
        return str(left_value) == str(right_value)
    if operator == "!=":
        return str(left_value) != str(right_value)
    if operator == ">":
        return left_value > right_value
    if operator == "<":
        return left_value < right_value
    if operator == ">=":
        return left_value >= right_value
    if operator == "<=":
        return left_value <= right_value
    return True


def strip_wrapping_parentheses(expression):
    expr = expression.strip()
    while expr.startswith("(") and expr.endswith(")"):
        depth = 0
        wraps_entire_expression = True
        for index, char in enumerate(expr):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(expr) - 1:
                    wraps_entire_expression = False
                    break
        if not wraps_entire_expression:
            break
        expr = expr[1:-1].strip()
    return expr


def split_logical_expression(expression):
    parts = []
    depth = 0
    quote = ""
    buffer = []
    index = 0
    expr = str(expression or "")

    while index < len(expr):
        char = expr[index]
        if quote:
            buffer.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue

        if char == "(":
            depth += 1
            buffer.append(char)
            index += 1
            continue

        if char == ")":
            depth = max(depth - 1, 0)
            buffer.append(char)
            index += 1
            continue

        if depth == 0:
            match = re.match(r"\s+(and|or)\s+", expr[index:], flags=re.IGNORECASE)
            if match:
                parts.append("".join(buffer).strip())
                parts.append(match.group(1).lower())
                buffer = []
                index += match.end()
                continue

        buffer.append(char)
        index += 1

    if buffer:
        parts.append("".join(buffer).strip())

    return parts if len(parts) > 1 else [expr]
