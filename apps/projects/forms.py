from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from .models import *
from apps.esb.models import FormPayloadConfig, FormPayloadFieldMap, FormValueMapping


class ProjectForm(forms.ModelForm):
    """
    A class to create form
    """

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = Project
        exclude = ["created_by", "updated_by", "deleted", "tags", "code"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write short description...",
                    "rows": 2,
                }
            ),
            "access": forms.Select(
                attrs={
                    "class": (
                        "w-full text-sm leading-tight "
                        "h-10 "
                        "bg-white "
                        "border border-gray-300 "
                        "rounded-md "
                        "px-3 pr-10 "
                        "text-gray-700 "
                        "appearance-none "
                        "bg-none "
                    ),
                    "id": "access",
                }
            ),
            "auto_join": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_join"}
            ),
            "accept_member": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_member"}
            ),
            "accept_data": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_data"}
            ),
        }


class SurveyAddForm(forms.ModelForm):
    """
    A class to create form
    """

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super(SurveyAddForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"
        self.fields["children"] = forms.MultipleChoiceField(
            required=False,
            label="Children Forms",
            choices=[],
            widget=forms.SelectMultiple(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "children",
                    "data-placeholder": "Select child forms...",
                }
            ),
        )

        if project:
            child_choices = [
                (
                    str(form.code),
                    f"{form.code} - {form.title}",
                )
                for form in FormDefinition.objects.filter(project=project)
                .exclude(code__isnull=True)
                .order_by("code", "title")
            ]
            self.fields["children"].choices = child_choices

        current_children = getattr(self.instance, "children", None)
        if current_children and not self.is_bound:
            self.initial["children"] = [
                child.strip() for child in current_children.split(",") if child.strip()
            ]

    class Meta:
        model = FormDefinition
        fields = [
            "title",
            "short_title",
            "code",
            "icon_type",
            "is_root",
            "children",
            "xlsform",
            "description",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "short_title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "short_title",
                    "placeholder": "Write short title...",
                    "required": "",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "code",
                    "placeholder": "Write code...",
                    "required": "",
                }
            ),
            "icon_type": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "icon_type",
                    "placeholder": "Write icon for app display...",
                }
            ),
            "is_root": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "is_root"}
            ),
            "xlsform": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel",
                    "required": "",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write description...",
                    "rows": 2,
                }
            ),
        }

    def clean_children(self):
        children = self.cleaned_data.get("children") or []
        return ",".join(children)


class SurveyUpdateForm(forms.ModelForm):
    """
    A class to edit form
    """

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super(SurveyUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"
        self.fields["children"] = forms.MultipleChoiceField(
            required=False,
            label="Children Forms",
            choices=[],
            widget=forms.SelectMultiple(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "children",
                    "data-placeholder": "Select child forms...",
                }
            ),
        )

        if project:
            child_queryset = FormDefinition.objects.filter(project=project).exclude(
                code__isnull=True
            )
            if self.instance.pk:
                child_queryset = child_queryset.exclude(pk=self.instance.pk)
            self.fields["children"].choices = [
                (str(form.code), f"{form.code} - {form.title}")
                for form in child_queryset.order_by("code", "title")
            ]

        current_children = getattr(self.instance, "children", None)
        if current_children and not self.is_bound:
            self.initial["children"] = [
                child.strip() for child in current_children.split(",") if child.strip()
            ]

    class Meta:
        model = FormDefinition
        fields = [
            "title",
            "short_title",
            "icon_type",
            "is_root",
            "children",
            "xlsform",
            "response",
            "description",
        ]
        tailwind_css = "text-xs rounded-md"

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "short_title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "short_title",
                    "placeholder": "Write short title...",
                    "required": "",
                }
            ),
            "icon_type": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "icon_type",
                    "placeholder": "Write icon for app display...",
                }
            ),
            "is_root": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "is_root"}
            ),
            "sort_order": forms.NumberInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "sort_order",
                    "required": "",
                }
            ),
            "xlsform": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel",
                    "required": "",
                }
            ),
            "response": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "response",
                    "placeholder": "Write default response...",
                }
            ),
            "short_description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "short_description",
                    "placeholder": "Write short description...",
                    "rows": 1,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write description...",
                    "rows": 2,
                }
            ),
        }

    def clean_children(self):
        children = self.cleaned_data.get("children") or []
        return ",".join(children)


class SurveyAttachmentForm(forms.ModelForm):
    """
    A class to create attachment
    """

    def __init__(self, *args, **kwargs):
        super(SurveyAttachmentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = FormAttachment
        fields = ["title", "type", "attachment"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write attachment title...",
                    "required": "",
                }
            ),
            "type": forms.Select(
                attrs={"class": "font-normal text-sm rounded-md", "id": "children"}
            ),
            "attachment": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "required": "",
                }
            ),
        }


class FormPayloadConfigForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormPayloadConfigForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = FormPayloadConfig
        fields = ["endpoint", "method", "headers", "is_active"]
        widgets = {
            "endpoint": forms.URLInput(
                attrs={
                    "class": "w-full font-normal text-sm rounded-md",
                    "placeholder": "https://api.example.com/endpoint",
                }
            ),
            "method": forms.Select(
                choices=[("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH")],
                attrs={"class": "w-full font-normal text-sm rounded-md"},
            ),
            "headers": forms.Textarea(
                attrs={
                    "class": "w-full font-normal text-sm rounded-md",
                    "rows": 4,
                    "placeholder": '{"Authorization": "Bearer ..."}',
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded-md"}),
        }

    def clean_headers(self):
        headers = self.cleaned_data.get("headers") or {}
        if headers and not isinstance(headers, dict):
            raise forms.ValidationError("Headers must be a valid JSON object.")
        return headers


class FormPayloadFieldMapForm(forms.ModelForm):
    class Meta:
        model = FormPayloadFieldMap
        fields = [
            "payload_field",
            "form_data_path",
            "default_value",
            # "required",
            "transform",
        ]
        widgets = {
            "payload_field": forms.TextInput(
                attrs={"class": "w-full font-normal text-sm rounded-md", "placeholder": "payload_field"}
            ),
            "form_data_path": forms.TextInput(
                attrs={
                    "class": "w-full font-normal text-sm rounded-md",
                    "placeholder": "form_path...",
                }
            ),
            "default_value": forms.TextInput(
                attrs={"class": "w-full font-normal text-sm rounded-md", "placeholder": "default_value"}
            ),
            # "required": forms.CheckboxInput(attrs={"class": "rounded-md"}),
            "transform": forms.Select(attrs={"class": "w-full font-normal text-sm rounded-md"}),
        }


FormPayloadFieldMapFormSet = inlineformset_factory(
    FormPayloadConfig,
    FormPayloadFieldMap,
    form=FormPayloadFieldMapForm,
    extra=1,
    can_delete=True,
)


class FormValueMappingForm(forms.ModelForm):
    class Meta:
        model = FormValueMapping
        fields = ["entity_type", "source_value", "target_value"]
        widgets = {
            "entity_type": forms.Select(attrs={"class": "w-full font-normal text-sm rounded-md"}),
            "source_value": forms.TextInput(
                attrs={"class": "w-full font-normal text-sm rounded-md", "placeholder": "source value"}
            ),
            "target_value": forms.TextInput(
                attrs={"class": "w-full font-normal text-sm rounded-md", "placeholder": "target value"}
            ),
        }


FormValueMappingFormSet = inlineformset_factory(
    FormPayloadConfig,
    FormValueMapping,
    form=FormValueMappingForm,
    extra=1,
    can_delete=True,
)
