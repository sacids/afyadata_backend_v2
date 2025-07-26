from django.urls import path
from . import views
from . import ajax_datatable_views

app_name = 'projects'

urlpatterns = [
    path('lists', views.ProjectListView.as_view(), name='lists'),
    path('show/<str:pk>', views.ProjectDetailView.as_view(), name='show'),
    path('create', views.ProjectCreateView.as_view(), name='create'),
    path('<str:pk>/edit', views.ProjectUpdateView.as_view(), name='edit'),
    path('<str:pk>/delete', views.ProjectDeleteView.as_view(), name='delete'),

    # project members
    path('<str:pk>/members', views.ProjectMembersListView.as_view(), name='members'),

    # form management
    path('forms/<str:pk>', views.SurveyListView.as_view(), name='forms'),
    path('forms/<str:pk>/upload', views.SurveyCreateView.as_view(), name='upload-form'),
    path('forms/<str:pk>/edit', views.SurveyUpdateView.as_view(), name='edit-form'),
    path('forms/<str:pk>/delete', views.SurveyDeleteView.as_view(), name='delete-form'),


    #ajax datatable views
    path('projects-datatable', ajax_datatable_views.ProjectAjaxDatatableView.as_view(), name="dt-projects"),
    path('members-datatable/<str:pk>', ajax_datatable_views.MembersAjaxDatatableView.as_view(), name="dt-members"),
    path('forms-datatable/<str:pk>', ajax_datatable_views.FormsAjaxDatatableView.as_view(), name="dt-forms"),
]