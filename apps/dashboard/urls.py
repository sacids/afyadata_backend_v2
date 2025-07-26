from django.urls import path
from django.urls.resolvers import URLPattern
from . views import DashboardView

app_name = 'dashboard'

urlpatterns = [ 
    path("summaries", DashboardView.as_view() , name="summaries"),  
 
]