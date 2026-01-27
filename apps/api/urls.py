from django.urls import path
from django.urls.resolvers import URLPattern
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from .v1.accounts import RegisterView, CustomTokenObtainPairView
from .v1.ohkr import *
from .v1.projects import *
from .v1.surveys import *
from .v1.form_data import *
from .v1.chat import *

urlpatterns = [
    # Accounts
    path('v1/register', RegisterView.as_view(), name='v1.register'),
    path("v1/token/", CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # OHKR 
    path('v1/species', SpecieView.as_view({'get': 'lists'})),
    path('v1/species/create', SpecieView.as_view({'post': 'create'})),
    path('v1/diseases', DiseaseView.as_view({'get': 'lists'})),
    path('v1/diseases/create', DiseaseView.as_view({'post': 'create'})),
    path('v1/clinical-responses', ClinicalResponseView.as_view({'get': 'lists'})),
    path('v1/clinical-signs', ClinicalSignView.as_view({'get': 'lists'})),
    path('v1/clinical-signs/create', ClinicalSignView.as_view({'post': 'create'})),
    path('v1/specie-responses', SpecieResponseView.as_view({'get': 'lists'})),
    path("v1/specie-responses/<str:specie_id>", SpecieResponseView.as_view({"get": "retrieve"})),

    # Projects
    path('v1/projects', ProjectView.as_view({'get': 'lists'})),
    path('v1/projects/<str:tags>', ProjectView.as_view({'get': 'retrieve'})),
    path('v1/project/detail/<str:pk>', ProjectView.as_view({'get': 'details'})),
    path('v1/project/request-access', ProjectView.as_view({'post': 'request_access'})),
    path('v1/project/unsubscribe', ProjectView.as_view({'post': 'unsubscribe'})),
    path('v1/project/create', ProjectView.as_view({'post': 'create'})),

    # Form definition
    path("v1/all-form-definition/<str:project_id>",FormDefinitionView.as_view({"get": "lists", "post": "create"})),
    path("v1/form-defn-meta/<str:project_id>", FormDefinitionView.as_view({"post": "listMeta"})),
    path("v1/form-definition/<str:project_id>", FormDefinitionView.as_view({"get": "retrieve"})),
    path("v1/form-definition/detail/<str:pk>",FormDefinitionView.as_view({"get": "getForm"}),),

    # Form data
    path("v1/form-data", FormDataView.as_view({"get": "retrieve", "post": "create"})),
    path("v1/form-data/<str:pk>", FormDataView.as_view({"get": "detail"})),

    # chat
    path("v1/chat/conversations", ConversationView.as_view({"get": "retrieve", "post": "create"})),
    path("v1/chat/conversations/<str:pk>/messages", ConversationView.as_view({"get": "messages", "post": "messages"})),
    path("v1/chat/conversations/<str:pk>/mark-read", ConversationView.as_view({"post": "mark_read"})),

  
]