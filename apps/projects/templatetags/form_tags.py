from django import template

import json
from ..utils import map_codes_to_labels, normalize_select_multiple

register = template.Library()


@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter(name="getattr")
def get_attribute(obj, attr_name):
    return getattr(obj, attr_name, "")


@register.filter(name="getForeignAttr")
def getForeignAttr(obj, attr_name):
    if attr_name == "id":
        return obj.id
    else:
        return getattr(obj, attr_name + "_id", "")


@register.filter(name="replace")
def replace(value, arg):
    """
    Replaces all occurrences of the first argument with the second argument
    Usage: {{ value|replace:"old,new" }}
    """
    old, new = arg.split(",")
    return value.replace(old, new)


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name="format_field_value")
def format_field_value(data, value):
    try:
        # If data is a string, parse it as JSON
        if isinstance(data, str):
            data = json.loads(data)
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            return "Invalid data format"

        # Get the raw value for the field name
        field_value = data.get(value.get("name"))
        if field_value is None or field_value == "":
            return ""

        # Handle select_one type
        if value.get("type") == "select_one" and value.get("options"):
            for option in value.get("options"):
                # Convert option['name'] to string for comparison, as field_value might be string (e.g., "10505")
                if str(option.get("name")) == str(field_value):
                    return option.get("label::Default", field_value)
            return field_value  # Fallback to raw value if no matching option

        # Handle select_multiple type
        if value.get("type") == "select_multiple" and value.get("options"):
            try:
                # If field_value is a JSON string (e.g., "[\"cautioned_about_activity\"]"), parse it
                if isinstance(field_value, str):
                    field_value = json.loads(field_value)
                if not isinstance(field_value, list):
                    return field_value  # Fallback if not a list

                # Map each value to its label::Default
                labels = []
                for val in field_value:
                    for option in value.get("options"):
                        if str(option.get("name")) == str(val):
                            labels.append(option.get("label::Default", val))
                            break
                    else:
                        labels.append(val)  # Fallback to raw value if no match
                return ", ".join(labels) if labels else "No value provided"
            except json.JSONDecodeError:
                return field_value  # Fallback to raw value if parsing fails

        # For all other types, return the raw value
        return field_value

    except (json.JSONDecodeError, TypeError, AttributeError):
        return "Error processing data"