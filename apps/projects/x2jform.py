import pandas
import logging
import json
import uuid
import warnings
import copy
import traceback

from django.conf import settings
from urllib.parse import parse_qs
import os
import pandas as pd


def init_settings(settings):
    setting_map = {}
    for setting in settings:
        setting_map.update(setting)

    return setting_map


def init_choices(choices):
    # print(json.dumps(choices, indent=4))
    choice_map = {}
    choice_map["languages"] = []
    for choice in choices:
        tmp = {}
        for key in choice:
            k = key
            if key == "list_name" and choice[key]:
                list_name = choice[key]
                if list_name not in choice_map:
                    choice_map[list_name] = []
            else:
                if "label" == key:
                    k = "label::Default"
                    if "Default" not in choice_map["languages"]:
                        choice_map["languages"].append("Default")

                if "label::" == key[:7] and key[7:] not in choice_map["languages"]:
                    choice_map["languages"].append(key[7:])

            tmp[k] = choice[key]

        choice_map[list_name].append(tmp)

    return choice_map


def get_item(item, choice_map, row_index=None):
    """
    Process a single item from a survey into a JSON Form item.
    """
    if item is None:
        raise ValueError(f"Item at row {row_index} is None")

    # Check if item is a dictionary
    if not isinstance(item, dict):
        raise TypeError(
            f"Item at row {row_index} is not a dictionary. Got {type(item).__name__}: {item}"
        )

    if "type" not in item:
        # Try to find a name field to identify the problematic row
        name_info = (
            f"name: {item.get('name', 'UNKNOWN')}"
            if isinstance(item, dict)
            else "no name available"
        )
        raise ValueError(
            f"Item at row {row_index} ({name_info}) has no 'type' field. Item content: {item}"
        )

    # Check if type is a string
    if not isinstance(item["type"], str):
        name_info = item.get("name", "UNKNOWN") if isinstance(item, dict) else "UNKNOWN"
        raise TypeError(
            f"Item '{name_info}' at row {row_index} has non-string type field. Got {type(item['type']).__name__}: {item['type']}"
        )

    tmp = item["type"].split()
    if len(tmp) == 0:
        name_info = item.get("name", "UNKNOWN") if isinstance(item, dict) else "UNKNOWN"
        raise ValueError(f"Item '{name_info}' at row {row_index} has empty type field")

    type = tmp[0].strip().lower()
    item["type"] = type
    item["is_relevant"] = True
    item["val"] = ""
    item["error"] = False

    if "label" in item:
        item["label::Default"] = item["label"]

    if "hint" in item:
        item["hint::Default"] = item["hint"]

    if "constraint_message" in item:
        item["constraint_message::Default"] = item["constraint_message"]

    if type in ["select_one", "select", "select_multiple", "rank"]:
        if len(tmp) == 1:
            name_info = item.get("name", "UNKNOWN")
            raise TypeError(
                f"Invalid field '{name_info}' at row {row_index}: select type requires a list name (e.g., 'select_one list_name'). Got: '{item['type']}'"
            )

        if len(tmp) > 1:
            # print('key in select', tmp[1])
            if tmp[1].lower().endswith(".sql"):
                key = tmp[1]
                item["type"] = "select_db"
                if key not in choice_map:
                    raise KeyError(
                        f"Invalid field '{item.get('name', 'UNKNOWN')}' at row {row_index}: SQL file '{key}' not found in choice_map"
                    )
                item["options"] = choice_map[key]
            elif tmp[1].strip() in choice_map:
                key = tmp[1]
                item["options"] = choice_map[key]
            else:
                raise KeyError(
                    f"Invalid field '{item.get('name', 'UNKNOWN')}' at row {row_index}: has no corresponding option list '{tmp[1]}' in choices sheet"
                )

            if len(tmp) == 3 and tmp[2].strip() == "or_other":
                item["or_other"] = "1"

    if type in ["select_one_from_file", "select_multiple_from_file"]:
        if len(tmp) > 1:
            item["options"] = tmp[1].strip()
            if len(tmp) == 3 and tmp[2].strip() == "or_other":
                item["or_other"] = "1"
        else:
            name_info = item.get("name", "UNKNOWN")
            raise TypeError(
                f"Invalid field '{name_info}' at row {row_index}: select_from_file requires a file name (e.g., 'select_one_from_file file.csv')"
            )

    return item


def make_jform_recursive(
    survey,
    choice_map,
    settings_map,
    in_group=False,
    group_context=None,
    parent_name=None,
    depth=0,
):
    def process_item(item, choice_map, row_index):
        try:
            if (
                item["type"] == "calculate"
                and item.get("body::calculation") is not None
            ):
                item["calculation"] = item["body::calculation"]
            return get_item(item, choice_map, row_index)
        except Exception as e:
            # Re-raise with more context
            raise type(e)(f"[Row {row_index}] {str(e)}")

    def handle_begin(item, type, parent_group, row_index):
        try:
            tmp = item
            tmp["type"] = "group"
            tmp["repeat"] = type.strip()[6:] == "repeat"
            tmp["is_relevant"] = True
            if "label" in item:
                item["label::Default"] = item["label"]
            if "hint" in item:
                item["hint::Default"] = item["hint"]
            tmp["fields"] = [{}]

            if parent_group:
                if "pages" in parent_group:
                    parent_group["pages"].append(tmp)
                else:
                    parent_group["fields"].append(tmp)
            else:
                survey_map["pages"].append(tmp)
            return tmp
        except Exception as e:
            raise ValueError(
                f"[Row {row_index}] Error handling 'begin_{type}' for group '{item.get('name', 'UNKNOWN')}': {e}"
            )

    def handle_other(item, type, uItem, parent_group, row_index):
        try:
            name = item["name"].strip()
            tmp = {
                "type": "group",
                "val": "",
                "error": False,
                "relevant": uItem.get("relevant", ""),
                "body::round": None,
                "body::value": None,
                "body::type": None,
                "body::is_incident": None,
                "body::columns": 0,
                "fields": [
                    {name: uItem},
                ],
            }
            if parent_group:
                if "pages" in parent_group:
                    parent_group["pages"].append(tmp)
                else:
                    parent_group["fields"][0][name] = uItem
            else:
                survey_map["pages"].append(tmp)
        except Exception as e:
            raise ValueError(
                f"[Row {row_index}] Error handling field '{item.get('name', 'UNKNOWN')}' of type '{type}': {e}"
            )

    if not in_group:
        survey_map = {
            "meta": settings_map,
            "pages": [],
            "attachments": [],
            "workflow": {},
            "languages": choice_map["languages"],
        }
    else:
        survey_map = group_context

    row_index = 0
    try:
        while survey:
            item = survey.pop(0)
            row_index += 1

            # Skip if item is not a dictionary
            if not isinstance(item, dict):
                raise TypeError(
                    f"Item at row {row_index} is not a dictionary. Got {type(item).__name__}: {item}"
                )

            type = item.get("type")
            if type is None:
                # This might be an empty row, skip it
                continue

            # Ensure type is string
            if not isinstance(type, str):
                raise TypeError(
                    f"Field '{item.get('name', 'UNKNOWN')}' at row {row_index} has non-string type. Got {type(type).__name__}: {type}"
                )

            type = type.strip()

            # Skip empty type strings
            if not type:
                continue

            if type[:6] == "begin_":
                parent_group = survey_map if not in_group else group_context
                new_group = handle_begin(item, type, parent_group, row_index)
                make_jform_recursive(
                    survey,
                    choice_map,
                    settings_map,
                    in_group=True,
                    group_context=new_group,
                    parent_name=item.get("name", "unnamed_group"),
                    depth=depth + 1,
                )
            elif type[:4] == "end_":
                return survey_map
            else:
                uItem = process_item(item, choice_map, row_index)
                type = uItem["type"]

                if type in [
                    "end",
                    "start",
                    "today",
                    "deviceid",
                    "phonenumber",
                    "username",
                    "email",
                    "audit",
                ]:
                    survey_map["meta"][type] = ""
                else:
                    parent_group = survey_map if not in_group else group_context
                    handle_other(item, type, uItem, parent_group, row_index)
    except Exception as e:
        # Add more context about where we are in the form
        location = f"in group '{parent_name}'" if parent_name else "at top level"
        raise RuntimeError(
            f"Error processing survey {location} at row {row_index}: {str(e)}\n{traceback.format_exc()}"
        )

    return survey_map


def x2jform(filename, title):

    xlsform = os.path.join(settings.MEDIA_ROOT, filename)
    warnings.simplefilter(action="ignore", category=UserWarning)

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)

            # Read choices sheet
            try:
                choice_df = pandas.read_excel(xlsform, sheet_name="choices")
                choice_obj = json.loads(choice_df.to_json(orient="records"))
                choice_map = init_choices(choice_obj)
            except Exception as e:
                raise ValueError(f"Failed to read 'choices' sheet: {e}")

            # Read settings sheet
            try:
                settings_df = pandas.read_excel(xlsform, sheet_name="settings")
                settings_obj = json.loads(settings_df.to_json(orient="records"))
                settings_map = init_settings(settings_obj)
            except Exception as e:
                raise ValueError(f"Failed to read 'settings' sheet: {e}")

            # Read survey sheet
            try:
                survey_df = pandas.read_excel(xlsform, sheet_name="survey")
                # Print column info for debugging
                print(f"Survey sheet columns: {list(survey_df.columns)}")
                print(f"Number of rows in survey sheet: {len(survey_df)}")

                # Check for NaN values in critical columns
                for idx, row in survey_df.iterrows():
                    if pd.isna(row.get("type")) and pd.isna(row.get("name")):
                        # Skip completely empty rows
                        continue
                    if pd.isna(row.get("type")):
                        print(
                            f"Warning: Row {idx + 2} (Excel row number) has missing 'type' but has name: {row.get('name', 'UNKNOWN')}"
                        )
                    if pd.isna(row.get("name")) and not pd.isna(row.get("type")):
                        if str(row.get("type")).strip() not in [
                            "begin_group",
                            "end_group",
                            "begin_repeat",
                            "end_repeat",
                        ]:
                            print(
                                f"Warning: Row {idx + 2} has type '{row.get('type')}' but missing 'name'"
                            )

                survey_obj = json.loads(survey_df.to_json(orient="records"))
                orig_survey_obj = copy.deepcopy(survey_obj)

                # Validate each survey item before processing
                for idx, item in enumerate(survey_obj):
                    if not isinstance(item, dict):
                        raise TypeError(
                            f"Survey item at index {idx} (Excel row {idx + 2}) is not a dictionary. Got {type(item).__name__}: {item}"
                        )

                    # Check for NaN values and convert to None/empty string as appropriate
                    for key, value in item.items():
                        if pd.isna(value):
                            item[key] = None

            except Exception as e:
                raise ValueError(f"Failed to read 'survey' sheet: {e}")

            # Process the survey
            try:
                survey_map = make_jform_recursive(survey_obj, choice_map, settings_map)
            except Exception as e:
                raise ValueError(f"Failed to process survey structure: {e}")

            survey_map["meta"]["title"] = title
            survey_map["meta"]["description"] = ""
            survey_map["meta"]["status"] = "blank"
            survey_map["meta"]["start"] = ""
            survey_map["meta"]["end"] = ""

            # Process attachments
            for obj in orig_survey_obj:
                if not isinstance(obj, dict):
                    continue
                type_val = obj.get("type", "")
                if isinstance(type_val, str):
                    tmp = type_val.split(" ")
                    if tmp and tmp[0] in [
                        "select_one_from_file",
                        "select_multiple_from_file",
                    ]:
                        if len(tmp) > 1:
                            survey_map["attachments"].append(tmp[1])

            if "form_id" not in settings_map or settings_map["form_id"] is None:
                settings_map["form_id"] = str(uuid.uuid4())
                survey_map["form_id"] = settings_map["form_id"]

            # Ensure output directory exists
            dest_dir = os.path.join(settings.MEDIA_ROOT, "jform/defn/")
            os.makedirs(dest_dir, exist_ok=True)

            dest = os.path.join(dest_dir, settings_map["form_id"] + ".json")

            with open(dest, "w") as f:
                json.dump(survey_map, f, indent=2)

            return survey_map

    except Exception as error:
        # Provide a more detailed error message
        error_msg = f"Form processing failed: {str(error)}"
        print(error_msg)
        print(traceback.format_exc())
        raise ValueError(error_msg)  # Re-raise with better message
