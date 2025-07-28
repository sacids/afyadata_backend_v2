import json
import calendar
from datetime import date, datetime
from django.http import JsonResponse

from .models import FormDefinition, FormData
from django.utils.dateformat import DateFormat

from django.db.models import Q, F
from django.db.models.functions import Cast, Coalesce
import operator
from functools import reduce
import ast
from django.core.serializers.json import DjangoJSONEncoder

from django.db.models import Case, Value, When, CharField


def get_key_at_index(dictionary, n):
    for i, key in enumerate(dictionary.keys()):
        if i == n:
            return key
    raise IndexError(f"Dictionary index {n} out of range (size: {len(dictionary)})")

def form_data_list(request, pk):
    """AJAX endpoint for DataTables with foreign key support"""
    # Get DataTables parameters
    start = int(request.POST.get("start", 0))
    length = int(request.POST.get("length", 10))
    draw = int(request.POST.get("draw", 1))
    search_val = request.POST.get("search[value]")
    sort_col = int(request.POST.get("order[0][column]", 0))
    sort_dir = request.POST.get("order[0][dir]", "asc")

    # Get form definition and columns
    aDefn = FormDefinition.objects.get(id=pk)
    cols = get_table_config(aDefn.form_defn)
    
    # Get all foreign key field names
    fk_fields = [
        f.name for f in FormData._meta.get_fields() 
        if f.is_relation and f.many_to_one and f.concrete
    ]
    
    # Base queryset with select_related for foreign keys
    adata = FormData.objects.filter(form_id=pk).order_by('-created_at').select_related(*fk_fields)

    # Apply search
    if search_val:
        or_filter = []
        for field_name in cols:
            if field_name in [f.name for f in FormData._meta.fields]:
                or_filter.append(Q(**{f"{field_name}__icontains": search_val}))
            else:
                or_filter.append(Q(**{f"form_data__{field_name}__icontains": search_val}))
        adata = adata.filter(reduce(operator.or_, or_filter))

    # Apply date range filtering
    min_date = request.POST.get("min_date")
    max_date = request.POST.get("max_date")
    if min_date:
        adata = adata.filter(created_on__gte=datetime.strptime(min_date, "%Y-%m-%d"))
    if max_date:
        adata = adata.filter(created_on__lte=datetime.strptime(max_date, "%Y-%m-%d"))

    # Apply sorting
    if sort_col < len(cols):
        sort_field = get_key_at_index(cols, sort_col)
        
        if sort_field in [f.name for f in FormData._meta.fields]:
            # Regular model field sorting
            sort_expr = F(sort_field)
            if sort_dir == "desc":
                adata = adata.order_by(sort_expr.desc(nulls_last=True))
            else:
                adata = adata.order_by(sort_expr.asc(nulls_first=True))
        else:
            # JSON field sorting
            # if sort_dir == "desc":
            #     sd = "-" + "form_data__" + sort_field
            # else:
            #     sd = "form_data__" + sort_field
            
            # adata = adata.order_by(sd)
            sort_case = Case(
                *[When(form_data__has_key=sort_field, then=Value(1))],
                default=Value(0),
                output_field=CharField()
            )

            if sort_dir == "desc":
                adata = adata.annotate(
                    sort_present=sort_case
                ).order_by('-sort_present', f"-form_data__{sort_field}")
            else:
                adata = adata.annotate(
                    sort_present=sort_case
                ).order_by('sort_present', f"form_data__{sort_field}")

    # Get counts
    records_total = FormData.objects.filter(form_id=pk).count()
    records_filtered = adata.count()

    # Apply pagination
    paginated_data = adata[start:start + length]

    # Prepare response data
    final_data = []
    for record in paginated_data:
        try:
            form_data = record.form_data if record.form_data else {}
        except json.JSONDecodeError:
            form_data = {}

        row = [record.id]
        
        for field_name in cols:
            if field_name in fk_fields:
                # Handle foreign key fields
                related_obj = getattr(record, field_name)
                row.append(str(related_obj) if related_obj else "")
            elif hasattr(record, field_name):
                # Regular model fields
                row.append(str(getattr(record, field_name)))
            else:
                # JSON fields
                row.append(str(form_data.get(field_name, "")))

        # Add metadata
        row.extend([
            record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else "",
            f"{record.created_by.first_name} {record.created_by.last_name}".strip() if record.created_by else "",
            record.created_by.username if record.created_by else ""
        ])
        final_data.append(row)

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": final_data
    }, encoder=DjangoJSONEncoder)



def get_table_header(jform):
    header = {}    
    for item in jform["pages"]:
        if item["type"] == "group":
            for k,v in item['fields'][0].items():
                header[k] = v['label']
    return header

def get_table_config1(jForm):
    config = {}
    #print(jForm["pages"])
    for item in jForm["pages"]:
        if item["type"] == "group":
            for k,v in item['fields'][0].items():
                config[k] = v
    return config


def get_table_config(jForm):
    """
    Extract table configuration from form definition.
    Handles both string JSON and already-parsed dict input.
    """
    config = {}
    
    # If jForm is a string, parse it to dict
    if isinstance(jForm, str):
        try:
            jForm = json.loads(jForm)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # Ensure we have the expected structure
    if not isinstance(jForm, dict) or 'pages' not in jForm:
        raise ValueError("Invalid form definition format")
    
    # Process pages
    for item in jForm["pages"]:
        if item.get("type") == "group" and 'fields' in item and item['fields']:
            # Handle both list of fields and direct field dictionary
            fields = item['fields'][0] if isinstance(item['fields'], list) else item['fields']
            
            for field_name, field_config in fields.items():
                config[field_name] = {
                    'type': field_config.get('type'),
                    'label': field_config.get('label'),
                    'required': field_config.get('required'),
                    'options': field_config.get('options', []),
                    # Add other relevant field properties
                }
    
    return config

def load_json(json_data):
    """Load and parse JSON data."""
    try:
        data = json.loads(json_data)
        return data
    except json.JSONDecodeError as e:
        print(f"Error loading JSON: {e}")
        return None

#handle file uploading  
def handle_uploaded_file(f):
    """handle upload of a file"""
    with open('assets/uploads/photos/' + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return "photos/" + f.name