from django.urls import path
from . import views, utils
from . import ajax_datatable_views

app_name = 'projects'

urlpatterns = [
    path('lists', views.ProjectListView.as_view(), name='lists'),
    path('show/<str:pk>', views.ProjectDetailView.as_view(), name='show'),
    path('create', views.ProjectCreateView.as_view(), name='create'),
    path('<str:pk>/edit', views.ProjectUpdateView.as_view(), name='edit'),
    path("<str:pk>/delete-confirm/", views.ProjectDeleteConfirmView.as_view(), name="delete-confirm"),
    path('<str:pk>/delete', views.ProjectDeleteView.as_view(), name='delete'),
    path('<str:pk>/activate', views.ProjectActivateView.as_view(), name='activate'),
    path('<str:pk>/data', views.ProjectDataView.as_view(), name='data'),

    # project members
    path('<str:pk>/members', views.ProjectMembersListView.as_view(), name='members'),

    # form management
    path('forms/<str:pk>', views.SurveyListView.as_view(), name='forms'),
    path('forms/<str:pk>/upload', views.SurveyCreateView.as_view(), name='upload-form'),
    path('forms/<str:pk>/edit', views.SurveyUpdateView.as_view(), name='edit-form'),
    path('forms/<str:pk>/delete', views.SurveyDeleteView.as_view(), name='delete-form'),
    path("forms/<str:pk>/definition", views.form_definition, name="form-definition"),

    # rules + OHKR
    path('forms/<str:pk>/rules', views.SurveyRulesView.as_view(), name='form-rules'),

    # form data
    path('forms/<str:pk>/data', views.SurveyDataView.as_view(), name='form-data'),
    path('forms/<str:pk>/data/export', views.SurveyDataExportView.as_view(), name="form-data-export"),
    path('forms/<str:data_id>/data/instance', views.SurveyDataInstanceView.as_view(), name="form-data-instance"),

    path('forms/<str:pk>/data/charts', views.ChartsDataView.as_view(), name='form-data-charts'),
    path('forms/<str:pk>/data/map', views.MapDataView.as_view(), name='form-data-map'),
    path("forms/<str:form_id>/data/points", views.form_points, name="form-data-point"),

    #ajax datatable views
    path('projects-datatable', ajax_datatable_views.ProjectAjaxDatatableView.as_view(), name="dt-projects"),
    path('members-datatable/<str:pk>', ajax_datatable_views.MembersAjaxDatatableView.as_view(), name="dt-members"),
    path('forms-datatable/<str:pk>', ajax_datatable_views.FormsAjaxDatatableView.as_view(), name="dt-forms"),
]