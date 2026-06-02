import logging
import json
import re
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.projects.serializers import *
from apps.projects.models import FormData, FormDefinition, ProjectMember, FormDataFilter
from apps.projects.utils import snapshot_uploaded_files
from apps.projects.tasks import save_formdata_files_task
from apps.accounts.utils import is_admin_user


class FormDataView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    default_page_size = 50
    max_page_size = 200

    """API List for Form Data"""

    def get_serializer_class(self):
        if self.action in ["list", "featured"]:
            return FormDataSerializer
        return super().get_serializer_class()

    def lists(self, request):
        """Get all form data"""
        form_data = FormData.objects.order_by("created_at").all()
        serializer = FormDataSerializer(form_data, many=True)
        return Response(serializer.data)

    def detail(self, request, pk=None):
        """Get form data information"""
        try:
            form_data = FormData.objects.get(pk=pk)
            serializer = FormDataSerializer(form_data)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def _parse_positive_int(self, value, field_name, default=None):
        if value in (None, ""):
            return default

        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be an integer") from exc

        if parsed < 1:
            raise ValueError(f"{field_name} must be greater than 0")

        return parsed

    def _parse_modified_after(self, value):
        if not value:
            return None

        modified_after = parse_datetime(value)
        if modified_after is None:
            raise ValueError("modified_after must be a valid ISO datetime")

        if timezone.is_naive(modified_after):
            modified_after = timezone.make_aware(
                modified_after, timezone.get_current_timezone()
            )

        return modified_after

    def _parse_uuid_list(self, value):
        if not value:
            return []

        return [item.strip() for item in value.split(",") if item.strip()]

    def _get_project_id(self, request):
        project_id = (request.query_params.get("project_id") or "").strip()
        if not project_id:
            raise ValueError("project_id is required")
        return project_id

    def _validate_project_access(self, user, project_id):
        if is_admin_user(user):
            return

        is_member = ProjectMember.objects.filter(
            project_id=project_id,
            member=user,
            active=True,
        ).exists()
        if not is_member:
            raise PermissionError("You do not have access to this project")

    def _parse_odk_filter_clause1(self, filter_text, user):
        """
        Parses ODK-style filter strings like:
        ${form_data.created_by} = 24 and ${form_data.region} = 'rukwa' and ${deleted} = 0
        """
        if not filter_text or not filter_text.strip():
            return Q()

        # Handle special dynamic context substitutions
        filter_text = filter_text.replace("current_user_id", str(user.id))
        filter_text = filter_text.replace("current_user_username", f"'{user.username}'")

        # Split multiple clauses separated by case-insensitive ' and '
        clauses = re.split(r'\s+and\s+', filter_text, flags=re.IGNORECASE)
        clause_query = Q()

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Regex mapping: ${field_name} operator value
            match = re.match(r'^\$\{(?P<field>[^}]+)\}\s*(?P<operator>=|!=|>=|<=|>|<)\s*(?P<value>.+)$', clause)
            if not match:
                logging.warning(f"Failed to parse ODK statement clause: {clause}")
                continue

            field_path = match.group('field').strip()
            operator = match.group('operator').strip()
            raw_value = match.group('value').strip()

            # Strip string wrapper quotes
            if (raw_value.startswith("'") and raw_value.endswith("'")) or \
               (raw_value.startswith('"') and raw_value.endswith('"')):
                value = raw_value[1:-1]
            else:
                # Cast string values to correct types dynamically
                try:
                    value = int(raw_value)
                except ValueError:
                    try:
                        value = float(raw_value)
                    except ValueError:
                        value = raw_value

            # Route json fields vs native database table columns
            if field_path.startswith("form_data."):
                json_key = field_path.replace("form_data.", "").replace(".", "__")
                django_lookup = f"form_data__{json_key}"
            else:
                django_lookup = field_path.replace(".", "__")

            # Map typical SQL relational operators to Django lookups
            lookup_map = {
                "=": django_lookup,
                "!=": f"{django_lookup}__ne",
                ">": f"{django_lookup}__gt",
                "<": f"{django_lookup}__lt",
                ">=": f"{django_lookup}__gte",
                "<=": f"{django_lookup}__lte"
            }
            
            lookup = lookup_map.get(operator, django_lookup)
            
            if operator == "!=":
                clause_query &= ~Q(**{django_lookup: value})
            else:
                clause_query &= Q(**{lookup: value})

        return clause_query

    def _parse_odk_filter_clause(self, filter_text, user):
        """
        Parses ODK-style filter strings with extended operators like:
        ${form_data.name} icontains 'john' and ${form_data.region} iexact 'RUKWA'
        """
        if not filter_text or not filter_text.strip():
            return Q()

        # Handle special dynamic context substitutions
        filter_text = filter_text.replace("current_user_id", str(user.id))
        filter_text = filter_text.replace("current_user_username", f"'{user.username}'")

        # Split multiple clauses separated by case-insensitive ' and '
        clauses = re.split(r'\s+and\s+', filter_text, flags=re.IGNORECASE)
        clause_query = Q()

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Expanded Regex: captures words like 'contains', 'icontains', 'iexact', 'like', 'ilike'
            match = re.match(
                r'^\$\{(?P<field>[^}]+)\}\s*(?P<operator>=|!=|>=|<=|>|<|contains|icontains|iexact|like|ilike)\s*(?P<value>.+)$', 
                clause, 
                flags=re.IGNORECASE
            )
            if not match:
                logging.warning(f"Failed to parse ODK statement clause: {clause}")
                continue

            field_path = match.group('field').strip()
            operator = match.group('operator').strip().lower()  # Normalize operator to lower-case
            raw_value = match.group('value').strip()

            # Strip string wrapper quotes
            if (raw_value.startswith("'") and raw_value.endswith("'")) or \
            (raw_value.startswith('"') and raw_value.endswith('"')):
                value = raw_value[1:-1]
            else:
                # Cast string values to correct types dynamically
                try:
                    value = int(raw_value)
                except ValueError:
                    try:
                        value = float(raw_value)
                    except ValueError:
                        value = raw_value

            # Route json fields vs native database table columns
            if field_path.startswith("form_data."):
                json_key = field_path.replace("form_data.", "").replace(".", "__")
                django_lookup = f"form_data__{json_key}"
            else:
                django_lookup = field_path.replace(".", "__")

            # Dynamic query generation logic based on expanded operators
            if operator == "=":
                # Check if value is a string to decide between case-insensitive 'iexact' vs strict default '='
                if isinstance(value, str):
                    clause_query &= Q(**{f"{django_lookup}__iexact": value})
                else:
                    clause_query &= Q(**{django_lookup: value})
                    
            elif operator == "!=":
                if isinstance(value, str):
                    clause_query &= ~Q(**{f"{django_lookup}__iexact": value})
                else:
                    clause_query &= ~Q(**{django_lookup: value})
                    
            elif operator in ["contains", "like"]:
                clause_query &= Q(**{f"{django_lookup}__contains": value})
                
            elif operator in ["icontains", "ilike"]:
                clause_query &= Q(**{f"{django_lookup}__icontains": value})
                
            elif operator == "iexact":
                clause_query &= Q(**{f"{django_lookup}__iexact": value})
                
            else:
                # Map typical SQL relational math operators to Django lookups
                lookup_map = {
                    ">": f"{django_lookup}__gt",
                    "<": f"{django_lookup}__lt",
                    ">=": f"{django_lookup}__gte",
                    "<=": f"{django_lookup}__lte"
                }
                lookup = lookup_map.get(operator, django_lookup)
                clause_query &= Q(**{lookup: value})

        return clause_query

    def _build_global_permissions_query(self, user, project_id):
        """
        Builds a comprehensive matrix of allowed records:
        (form_id = Form_A AND (Filter_A1 AND Filter_A2)) OR (form_id = Form_B AND (Filter_B1))
        """
        # Admins bypass data filtering layers entirely
        if is_admin_user(user):
            return Q()

        user_groups = user.groups.all()
        print(f"=== user groups: {user_groups} ===")
        # Fetch all filter configurations assigned to this user or their groups
        filters = FormDataFilter.objects.filter(
            form__project_id=project_id
        ).filter(
            Q(permitted_users=user) | Q(permitted_groups__in=user_groups)
        ).distinct().select_related('form')

        print("=== applicable filters for user ===")
        print(filters)
        
        if not filters.exists():
            print("=== no filters found for user, denying access to all records ===")
            # Non-admin user with no configured filters across the project has access to nothing
            return Q(pk__in=[])

        # Group operational filter criteria strings by form_id
        filters_by_form = {}
        for f_obj in filters:
            if f_obj.filter_text and f_obj.filter_text.strip():
                filters_by_form.setdefault(str(f_obj.form_id), []).append(f_obj.filter_text)

        # Build combined logical permission tree
        global_or_query = Q()
        for form_uuid, text_list in filters_by_form.items():
            # Multiple filters targeting the exact same form_id are joined via AND
            form_and_query = Q(form_id=form_uuid)
            for filter_text in text_list:
                parsed_q = self._parse_odk_filter_clause(filter_text, user)
                form_and_query &= parsed_q
            
            # Distinct forms permissions are joined via OR
            global_or_query |= form_and_query

        return global_or_query

    def _build_queryset(self, request):
        project_id = self._get_project_id(request)
        self._validate_project_access(request.user, project_id)

        modified_after = self._parse_modified_after(
            request.query_params.get("modified_after")
        )
        uuids = self._parse_uuid_list(request.query_params.get("uuids"))

        queryset = FormData.objects.filter(
            form__project_id=project_id,
            deleted=0,
        ).select_related("form")

        # Apply data synchronization modifiers
        sync_filters = Q()
        if modified_after is not None:
            sync_filters |= Q(updated_at__gt=modified_after) | Q(last_updated_at__gt=modified_after)
        if uuids:
            sync_filters |= Q(uuid__in=uuids)

        if sync_filters:
            queryset = queryset.filter(sync_filters)

        # Enforce global security matrix constraint rule
        permissions_query = self._build_global_permissions_query(request.user, project_id)
        queryset = queryset.filter(permissions_query)
        
        print(queryset)

        return queryset.order_by("updated_at", "created_at", "id")

    def _paginate_queryset(self, queryset, request):
        page = self._parse_positive_int(
            request.query_params.get("page"),
            "page",
            default=1,
        )
        page_size = self._parse_positive_int(
            request.query_params.get("page_size"),
            "page_size",
            default=self.default_page_size,
        )
        page_size = min(page_size, self.max_page_size)
        offset = (page - 1) * page_size

        total_count = queryset.count()
        results = queryset[offset : offset + page_size]

        return results, {
            "X-Total-Count": str(total_count),
            "X-Page": str(page),
            "X-Page-Size": str(page_size),
        }

    def retrieve(self, request):
        """Get project-scoped form data for mobile sync."""
        try:
            queryset = self._build_queryset(request)
            page_results, headers = self._paginate_queryset(queryset, request)
            serializer = FormDataSerializer(page_results, many=True)
            return Response(serializer.data, headers=headers, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logging.exception("Failed to retrieve form data")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def head(self, request):
        """Return form data sync metadata without a response body."""
        try:
            queryset = self._build_queryset(request)
            _, headers = self._paginate_queryset(queryset, request)
            return Response(headers=headers, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            logging.exception("Failed to retrieve form data headers")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _normalize_request_data(self, request):
        raw_data = request.data
        if hasattr(raw_data, "dict"):
            return raw_data.dict()
        return dict(raw_data)

    def _parse_form_data(self, value):
        if value is None:
            return {}

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return {}

            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid JSON in form_data") from exc

            if not isinstance(parsed, dict):
                raise ValueError("form_data must be a JSON object")

            return parsed

        if not isinstance(value, dict):
            raise ValueError("form_data must be a JSON object")

        return value

    def _parse_created_at(self, data):
        created_on_str = data.get("created_on") or data.get("created_at")
        if not created_on_str:
            return timezone.now()

        created_on = parse_datetime(created_on_str)
        if created_on is None:
            raise ValueError("Invalid created_on datetime")

        if timezone.is_naive(created_on):
            created_on = timezone.make_aware(
                created_on, timezone.get_current_timezone()
            )

        return created_on

    def create(self, request, *args, **kwargs):
        """Create new form data coming from mobile app"""
        if not request.data:
            return Response(
                {"success": False, "message": "Request body is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logging.info("== incoming data ==")
        logging.info(request.data)
        data = self._normalize_request_data(request)
        logging.info("== normalized data ==")
        logging.info(data)

        try:
            def to_bool(val, default=False):
                if val is None:
                    return default
                return str(val).lower() in ("1", "true", "yes")

            uuid = (data.get("uuid") or "").strip()
            if not uuid:
                raise ValueError("uuid is required")

            form_id = data.get("form")
            if not form_id:
                raise ValueError("form is required")

            if not FormDefinition.objects.filter(pk=form_id).exists():
                raise ValueError("Invalid form")

            data["form_data"] = self._parse_form_data(data.get("form_data"))
            created_on = self._parse_created_at(data)
            deleted = to_bool(data.get("deleted"), default=False)

            file_snapshots = (
                snapshot_uploaded_files(request.FILES) if request.FILES else []
            )

            now = timezone.now()
            defaults = {
                "form_data": data["form_data"],
                "original_uuid": data.get("original_uuid", uuid),
                "parent_id": data.get("parent_uuid"),
                "title": data.get("title", ""),
                "created_by_name": data.get("created_by_name", ""),
                "form_id": form_id,
                "gps": data.get("gps"),
                "created_at": created_on,
                "created_by": request.user if request.user.is_authenticated else None,
                "updated_at": now,
                "last_updated_at": now,
                "submitted_at": now,
                "deleted": deleted,
                "synced": 1,
            }

            with transaction.atomic():
                instance, created_flag = FormData.objects.update_or_create(
                    uuid=uuid,
                    defaults=defaults,
                )
                if file_snapshots:
                    transaction.on_commit(
                        lambda: save_formdata_files_task.delay(
                            instance.pk,
                            file_snapshots,
                            request.user.pk if request.user.is_authenticated else None,
                        )
                    )

            logging.info("== inserted/updated form data ==")
            logging.info(
                {"id": instance.id, "uuid": instance.uuid, "created": created_flag}
            )

            instance.refresh_from_db()

            if getattr(instance.form, "response", None):
                response_payload = {
                    "uuid": instance.uuid,
                    "synced": 1,
                    "message": instance.form.response,
                }
            else:
                response_payload = {
                    "uuid": instance.uuid,
                    "synced": 1,
                    "message": (
                        "Form data created successfully"
                        if created_flag
                        else "Form data updated successfully"
                    ),
                }

            return Response(
                {"success": True, "data": response_payload},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )