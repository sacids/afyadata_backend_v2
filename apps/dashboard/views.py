from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, FileResponse
from django.db.models import Q
import logging


# Create your views here.
class DashboardView(generic.TemplateView):
    template_name = "dashboard/index.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)