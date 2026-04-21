import json
import requests
import logging
import random
import string
from decouple import config
from datetime import datetime, date
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.db import transaction
from .models import *
from .utils import sync_locations, sync_reference_values
from apps.esb.services import get_auth_headers
from apps.projects.models import FormDefinition


class OHKRPermissionMixin(PermissionRequiredMixin):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(OHKRPermissionMixin, self).dispatch(*args, **kwargs)


def get_reference_form(request):
    form_id = request.GET.get("form_id")
    if not form_id:
        return None
    return FormDefinition.objects.get(pk=form_id)


# Create your views here.
class LocationListView(OHKRPermissionMixin, generic.ListView):
    permission_required = "ohkr.view_location"

    model = Location
    context_object_name = "locations"
    template_name = "locations/lists.html"

    def get_context_data(self, *args, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        context["title"] = "Locations"
        context["page_title"] = "Locations"
        context["can_sync"] = self.request.user.has_perm("ohkr.change_location")
        context["can_manage"] = self.request.user.has_perm("ohkr.change_location")

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "OHKR", "url": reverse_lazy("ohkr:locations")},
            {"name": "Locations", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Locations": reverse_lazy("ohkr:locations"),
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context


class LocationSyncView(OHKRPermissionMixin, generic.CreateView):
    """Pull locations from FAO RDS API and insert/update locally"""
    permission_required = "ohkr.change_location"
    model = Location

    def get(self, *args, **kwargs):
        tza_country_id = 'fdd6e49b-b1ed-4c38-923c-be3b7bbb3b1c' #TZA country_id
        api_url = f"{config('FAO_BASE_URL')}/geographical_data/countries/{tza_country_id}"

        # config headers
        headers = {"accept": "application/json"}

        # pass authorization header
        if not headers.get("Authorization"):
            headers.update(get_auth_headers())

        try:
            target_form = get_reference_form(self.request)

            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            # result
            result = sync_locations(
                remote_data,
                source="RDS",
                active=True,
                form=target_form,
            )

            # return response
            return JsonResponse(
                {
                    "success": True,
                    "success_msg": "Location reference data synced"
                    if target_form
                    else "Location synced",
                    "created": result['created'],
                    "updated": result['updated']
                }
            )

        except FormDefinition.DoesNotExist:
            return JsonResponse(
                {"success": False, "error_msg": "Reference form not found."}, status=404
            )
        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync location: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class DiseaseListView(OHKRPermissionMixin, generic.ListView):
    permission_required = "ohkr.view_disease"

    model = Disease
    context_object_name = "diseases"
    template_name = "diseases/lists.html"

    def get_context_data(self, *args, **kwargs):
        context = super(DiseaseListView, self).get_context_data(**kwargs)
        context["title"] = "Diseases"
        context["page_title"] = "Diseases"
        context["can_sync"] = self.request.user.has_perm("ohkr.change_disease")
        context["can_manage"] = self.request.user.has_perm("ohkr.change_disease")

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "OHKR", "url": reverse_lazy("ohkr:diseases")},
            {"name": "Diseases", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Locations": reverse_lazy("ohkr:locations"),
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context


class DiseaseSyncView(OHKRPermissionMixin, generic.CreateView):
    """Pull diseases from FAO RDS API and insert/update locally"""
    permission_required = "ohkr.change_disease"

    model = Disease

    def get(self, *args, **kwargs):
        api_url = f"{config('FAO_BASE_URL')}/api/diseases/"
        headers = {"accept": "application/json"}

        try:
            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            created, updated = 0, 0
            with transaction.atomic():
                for item in remote_data["values"]:
                    obj, was_created = Disease.objects.update_or_create(
                        external_id=item["id"],
                        defaults={
                            "name": item["name"],
                            "source": "RDS",
                            "language_code": item["language_code"],
                        },
                    )
                    # increment created and updated
                    created += was_created
                    updated += not was_created

            # return response
            return JsonResponse(
                {
                    "success": True,
                    "success_msg": "Diseases synced",
                    "created": created,
                    "updated": updated,
                }
            )

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync diseases: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class SpecieListView(OHKRPermissionMixin, generic.ListView):
    permission_required = "ohkr.view_specie"

    model = Specie
    context_object_name = "species"
    template_name = "species/lists.html"

    def get_context_data(self, *args, **kwargs):
        context = super(SpecieListView, self).get_context_data(**kwargs)
        context["title"] = "Species"
        context["page_title"] = "Species"
        context["can_sync"] = self.request.user.has_perm("ohkr.change_specie")
        context["can_manage"] = self.request.user.has_perm("ohkr.change_specie")

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "OHKR", "url": reverse_lazy("ohkr:diseases")},
            {"name": "Species", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Locations": reverse_lazy("ohkr:locations"),
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context


class SpecieSyncView(OHKRPermissionMixin, generic.CreateView):
    """Pull species from FAO RDS  API and insert/update locally"""
    permission_required = "ohkr.change_specie"
    model = Specie

    def get(self, *args, **kwargs):
        api_url = f"{config('FAO_BASE_URL')}/species/"
        headers = {"accept": "application/json"}

        # pass authorization header
        if not headers.get("Authorization"):
            headers.update(get_auth_headers())

        try:
            target_form = get_reference_form(self.request)

            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            if target_form:
                result = sync_reference_values(
                    remote_data.get("values", []),
                    form=target_form,
                    rd_type="specie",
                    source="RDS",
                    active=True,
                )
                created = result["created"]
                updated = result["updated"]
            else:
                created, updated = 0, 0
                with transaction.atomic():
                    for item in remote_data["values"]:
                        _, was_created = Specie.objects.update_or_create(
                            external_id=item["id"],
                            defaults={
                                "name": item["name"],
                                "source": "RDS",
                                "language_code": item["language_code"],
                            },
                        )
                        created += was_created
                        updated += not was_created

            # return response
            return JsonResponse(
                {
                    "success": True,
                    "success_msg": "Species reference data synced"
                    if target_form
                    else "Species synced",
                    "created": created,
                    "updated": updated,
                }
            )

        except FormDefinition.DoesNotExist:
            return JsonResponse(
                {"success": False, "error_msg": "Reference form not found."}, status=404
            )
        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync species: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class ClinicalSignListView(OHKRPermissionMixin, generic.ListView):
    permission_required = "ohkr.view_clinicalsign"

    model = ClinicalSign
    context_object_name = "clinical_signs"
    template_name = "clinical_signs/lists.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ClinicalSignListView, self).get_context_data(**kwargs)
        context["title"] = "Clinical Signs"
        context["page_title"] = "Clinical Signs"
        context["can_sync"] = self.request.user.has_perm("ohkr.change_clinicalsign")
        context["can_manage"] = self.request.user.has_perm("ohkr.change_clinicalsign")

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "OHKR", "url": reverse_lazy("ohkr:diseases")},
            {"name": "Clinical Signs", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Locations": reverse_lazy("ohkr:locations"),
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context


class ClinicalSignSyncView(OHKRPermissionMixin, generic.CreateView):
    """Pull clinical signs from FAO RDS API and insert/update locally"""
    permission_required = "ohkr.change_clinicalsign"
    model = ClinicalSign

    def get(self, *args, **kwargs):
        api_url = f"{config('FAO_BASE_URL')}/clinical-signs/"
        headers = {"accept": "application/json"}

        # pass authorization header
        if not headers.get("Authorization"):
            headers.update(get_auth_headers())

        try:
            target_form = get_reference_form(self.request)

            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            if target_form:
                result = sync_reference_values(
                    remote_data.get("values", []),
                    form=target_form,
                    rd_type="clinical_sign",
                    source="RDS",
                    active=True,
                    code_key="code",
                )
                created = result["created"]
                updated = result["updated"]
            else:
                created, updated = 0, 0
                with transaction.atomic():
                    for item in remote_data["values"]:
                        _, was_created = ClinicalSign.objects.update_or_create(
                            external_id=item["id"],
                            defaults={
                                "name": item["name"],
                                "source": "RDS",
                                "language_code": item["language_code"],
                            },
                        )
                        created += was_created
                        updated += not was_created

            # return response
            return JsonResponse(
                {
                    "success": True,
                    "success_msg": "Clinical sign reference data synced"
                    if target_form
                    else "Clinical signs synced",
                    "created": created,
                    "updated": updated,
                }
            )

        except FormDefinition.DoesNotExist:
            return JsonResponse(
                {"success": False, "error_msg": "Reference form not found."}, status=404
            )
        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync clinical signs: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class ResponseListView(OHKRPermissionMixin, generic.ListView):
    permission_required = "ohkr.view_response"

    model = Response
    context_object_name = "responses"
    template_name = "responses/lists.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ResponseListView, self).get_context_data(**kwargs)
        context["title"] = "Responses"
        context["page_title"] = "Responses"
        context["can_manage"] = self.request.user.has_perm("ohkr.change_response")

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "OHKR", "url": reverse_lazy("ohkr:diseases")},
            {"name": "Responses", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Locations": reverse_lazy("ohkr:locations"),
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context
