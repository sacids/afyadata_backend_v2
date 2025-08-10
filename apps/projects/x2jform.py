import pandas
import json
import uuid
import warnings

from django.conf import settings
from urllib.parse import parse_qs
import os


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


def get_item(item, choice_map):
    """
    Process a single item from a survey into a JSON Form item.
    """
    if item is None:
        raise ValueError("Item is None")

    if "type" not in item:
        raise ValueError(f"Item {item} has no type")

    tmp = item["type"].split()
    if len(tmp) == 0:
        raise ValueError(f"Item {item} has no type")
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
        if len(tmp) == 0:
            raise ValueError(f"Item {item} has no options")
        if len(tmp) > 1:
            #print('key in select', tmp[1])
            if tmp[1].lower().endswith('.sql'):
                key = tmp[1]
                item["type"] = "select_db"
                item["options"] = choice_map[key]
            elif tmp[1].strip() in choice_map:
                key = tmp[1]
                item["options"] = choice_map[key]
            else:
                raise ValueError(
                    "Invalid Field " + item["name"] + " has no corresponding option"
                )

            if len(tmp) == 3 and tmp[2].strip() == "or_other":
                item["or_other"] = "1"
        else:
            raise TypeError("Invalid field : Incorect syntax " + item["name"])

    if type in ["select_one_from_file", "select_one_from_file"]:
        if len(tmp) > 1:
            item["options"] = tmp[1].strip()
            if len(tmp) == 3 and tmp[2].strip() == "or_other":
                item["or_other"] = "1"
        else:
            raise TypeError("Invalid field : Incorect syntax " + item["name"])
    return item


def make_jform(survey, choice_map, settings_map):
    survey_map = {
        "meta": settings_map,
        "pages": [],
        "workflow": {},
        "languages": choice_map["languages"],
    }
    page_count = 0
    in_group = False
    # print("STARTING LOOPING SURVEY")
    for item in survey:
        # print(item)
        if item["type"] == "calculate" and item["body::calculation"] != None:
            # print('setting calculation')
            item["calculation"] = item["body::calculation"]

        type = item["type"]
        if type == None:
            continue
        elif type.strip()[:5] == "begin":
            in_group = True
            tmp = item
            tmp["type"] = "group"
            tmp["repeat"] = type.strip()[6:] == "repeat"
            tmp["is_relevant"] = True
            if "label" in item:
                item["label::Default"] = item["label"]
            if "hint" in item:
                item["hint::Default"] = item["hint"]

            tmp["fields"] = [{}]
            survey_map["pages"].append(tmp)
        elif type.strip()[:3] == "end":
            in_group = False
            page_count = page_count + 1
        else:
            name = item["name"].strip()
            uItem = get_item(item, choice_map)
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
                pass
            elif in_group:
                survey_map["pages"][page_count]["fields"][0][name] = uItem
            else:
                tmp = {
                    "type": "group",
                    "val": "",
                    "error": False,
                    "relevant": uItem["relevant"],
                    "body::round": None,
                    "body::value": None,
                    "body::type": None,
                    "body::is_incident": None,
                    "body::columns": 0,
                    "fields": [
                        {
                            name: uItem,
                        }
                    ],
                }
                survey_map["pages"].append(tmp)
                in_group = False
                page_count = page_count + 1

    return survey_map


def make_jform_recursive(survey, choice_map, settings_map, in_group=False, group_context=None):
    def process_item(item, choice_map):
        try:
            if item["type"] == "calculate" and item.get("body::calculation") is not None:
                item["calculation"] = item["body::calculation"]
            return get_item(item, choice_map)
        except Exception as e:
            raise ValueError(f"Error processing item {json.dumps(item, indent=4)}: {e}")

    def handle_begin(item, type, parent_group):
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
                if 'pages' in parent_group:
                    parent_group['pages'].append(tmp)
                else:
                    parent_group["fields"].append(tmp)
            else:
                survey_map["pages"].append(tmp)
            return tmp
        except Exception as e:
            raise ValueError(f"Error handling 'begin' for item {item}: {e}")

    def handle_other(item, type, uItem, parent_group):
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
                if 'pages' in parent_group:
                    parent_group['pages'].append(tmp)
                else:
                    parent_group["fields"][0][name] = uItem
            else:
                survey_map["pages"].append(tmp)
        except Exception as e:
            raise ValueError(f"Error handling other item {item}: {e}")

    if not in_group:
        survey_map = {
            "meta": settings_map,
            "pages": [],
            "workflow": {},
            "languages": choice_map["languages"],
        }
    else:
        survey_map = group_context

    try:
        while survey:
            item = survey.pop(0)
            type = item.get("type")
            if type is None:
                continue

            type = type.strip()
            if type[:6] == "begin_":
                parent_group = survey_map if not in_group else group_context
                new_group = handle_begin(item, type, parent_group)
                make_jform_recursive(survey, choice_map, settings_map, in_group=True, group_context=new_group)
            elif type[:4] == "end_":
                return survey_map
            else:
                uItem = process_item(item, choice_map)
                type = uItem["type"]
                if type in [
                    "end", "start", "today", "deviceid", "phonenumber",
                    "username", "email", "audit"
                ]:
                    survey_map["meta"][type] = ""
                else:
                    parent_group = survey_map if not in_group else group_context
                    handle_other(item, type, uItem, parent_group)
    except Exception as e:
        raise RuntimeError(f"Error processing survey: {e}")

    return survey_map


def x2jform(filename, title):

    xlsform = os.path.join(settings.MEDIA_ROOT, filename)
    warnings.simplefilter(action="ignore", category=UserWarning)
    #xlsform = filename

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)

            choice_df = pandas.read_excel(xlsform, sheet_name="choices")
            choice_obj = json.loads(choice_df.to_json(orient="records"))
            choice_map = init_choices(choice_obj)
            #print(json.dumps(choice_map, indent=4))

            settings_df = pandas.read_excel(xlsform, sheet_name="settings")
            settings_obj = json.loads(settings_df.to_json(orient="records"))
            settings_map = init_settings(settings_obj)

            survey_df = pandas.read_excel(xlsform, sheet_name="survey")
            #print(survey_df)

            survey_obj = json.loads(survey_df.to_json(orient="records"))
            #print(json.dumps(survey_obj, indent=4))

            #survey_map = make_jform(survey_obj, choice_map, settings_map)
            survey_map = make_jform_recursive(survey_obj, choice_map, settings_map)

            survey_map["meta"]["title"] = title
            survey_map["meta"]["description"] = ""
            survey_map["meta"]["status"] = "blank"

            survey_map["meta"]["start"] = ""
            survey_map["meta"]["end"] = ""

            if "form_id" not in settings_map or settings_map["form_id"] == None:
                settings_map["form_id"] = str(uuid.uuid4())
                survey_map["form_id"] = settings_map["form_id"]

            #print(json.dumps(survey_map['pages'], indent=4))
            #return
        
        dest = os.path.join(
            settings.MEDIA_ROOT, "jform/defn/", settings_map["form_id"] + ".json"
        )

        f = open(dest, "w")
        json.dump(survey_map, f)
        f.close()

        return survey_map

    except Exception as error:
        print("An exception occurred:", error)
        return 0


x2jform("sample3.xlsx", "my title")

