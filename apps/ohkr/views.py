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

from django.db import transaction
from .models import *
from .utils import sync_locations

# Create your views here.
class LocationListView(generic.ListView):
    # permission_required = ''

    model = Location
    context_object_name = "locations"
    template_name = "locations/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LocationListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        context["title"] = "Locations"
        context["page_title"] = "Locations"

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


class LocationSyncView(generic.CreateView):
    """Pull locations from FAO RDS API and insert/update locally"""
    model = Location

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LocationSyncView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        api_url = f"{config("FAO_BASE_URL")}/api/geographical_data/countries/TZA"
        headers = {"accept": "application/json"}

        try:
            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            result = sync_locations(remote_data, source="RDS", active=True)
            print(result)

            # return response
            return JsonResponse(
                {
                    "success": True,
                    "success_msg": "Location synced",
                    # "created": created,
                    # "updated": updated,
                }
            )

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync location: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class DiseaseListView(generic.ListView):
    # permission_required = ''

    model = Disease
    context_object_name = "diseases"
    template_name = "diseases/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DiseaseListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(DiseaseListView, self).get_context_data(**kwargs)
        context["title"] = "Diseases"
        context["page_title"] = "Diseases"

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


class DiseaseSyncView(generic.CreateView):
    """Pull diseases from FAO RDS API and insert/update locally"""

    model = Disease

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DiseaseSyncView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        api_url = f"{config("FAO_BASE_URL")}/api/diseases/"
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


class SpecieListView(generic.ListView):
    # permission_required = ''

    model = Specie
    context_object_name = "species"
    template_name = "species/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SpecieListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(SpecieListView, self).get_context_data(**kwargs)
        context["title"] = "Species"
        context["page_title"] = "Species"

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


class SpecieSyncView(generic.CreateView):
    """Pull species from FAO RDS  API and insert/update locally"""

    model = Disease

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SpecieSyncView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        api_url = f"{config("FAO_BASE_URL")}/api/species/"
        headers = {"accept": "application/json"}

        try:
            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            created, updated = 0, 0
            with transaction.atomic():
                for item in remote_data["values"]:
                    obj, was_created = Specie.objects.update_or_create(
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
                    "success_msg": "Species synced",
                    "created": created,
                    "updated": updated,
                }
            )

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync species: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class ClinicalSignListView(generic.ListView):
    # permission_required = ''

    model = ClinicalSign
    context_object_name = "clinical_signs"
    template_name = "clinical_signs/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClinicalSignListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ClinicalSignListView, self).get_context_data(**kwargs)
        context["title"] = "Clinical Signs"
        context["page_title"] = "Clinical Signs"

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


class ClinicalSignSyncView(generic.CreateView):
    """Pull clinical signs from FAO RDS API and insert/update locally"""

    model = Disease

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClinicalSignSyncView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        api_url = f"{config("FAO_BASE_URL")}/api/clinical-signs/"
        headers = {"accept": "application/json"}

        try:
            # Fetch data from remote service
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            remote_data = response.json()

            created, updated = 0, 0
            with transaction.atomic():
                for item in remote_data["values"]:
                    obj, was_created = ClinicalSign.objects.update_or_create(
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
                    "success_msg": "Clinical signs synced",
                    "created": created,
                    "updated": updated,
                }
            )

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error_msg": f"Failed to sync clinical signs: {str(e)}"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error_msg": str(e)},
            )


class ResponseListView(generic.ListView):
    # permission_required = ''

    model = Response
    context_object_name = "responses"
    template_name = "responses/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ResponseListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ResponseListView, self).get_context_data(**kwargs)
        context["title"] = "Responses"
        context["page_title"] = "Responses"

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
