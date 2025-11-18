import json
import random
import string
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

from .models import *

# Create your views here.

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
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context
    
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
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context
    

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
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context


class ClinicalResponseListView(generic.ListView):
    # permission_required = ''

    model = ClinicalResponse
    context_object_name = "responses"
    template_name = "responses/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClinicalResponseListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ClinicalResponseListView, self).get_context_data(**kwargs)
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
            "Diseases": reverse_lazy("ohkr:diseases"),
            "Species": reverse_lazy("ohkr:species"),
            "Clinical Signs": reverse_lazy("ohkr:clinical-signs"),
            "Responses": reverse_lazy("ohkr:responses"),
        }

        return context