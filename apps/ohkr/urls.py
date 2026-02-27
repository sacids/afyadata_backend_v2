from django.urls import path
from . import views
from . import ajax_datatable_views

app_name = 'ohkr'

urlpatterns = [
    path('locations', views.LocationListView.as_view(), name='locations'),
    path('locations/sync', views.LocationSyncView.as_view(), name='locations.sync'),

    path('diseases', views.DiseaseListView.as_view(), name='diseases'),
    path('diseases/sync', views.DiseaseSyncView.as_view(), name='diseases.sync'),

    path('species', views.SpecieListView.as_view(), name='species'),
    path('species/sync', views.SpecieSyncView.as_view(), name='species.sync'),

    path('clinical-signs', views.ClinicalSignListView.as_view(), name='clinical-signs'),
    path('clinical-signs/sync', views.ClinicalSignSyncView.as_view(), name='clinical-signs.sync'),
    
    path('responses', views.ResponseListView.as_view(), name='responses'),

    #ajax datatable views
    path('locations-datatable', ajax_datatable_views.LocationAjaxDatatableView.as_view(), name="dt-locations"),
    path('diseases-datatable', ajax_datatable_views.DiseaseAjaxDatatableView.as_view(), name="dt-diseases"),
    path('species-datatable', ajax_datatable_views.SpecieAjaxDatatableView.as_view(), name="dt-species"),
    path('clinical-signs-datatable', ajax_datatable_views.ClinicalSignAjaxDatatableView.as_view(), name="dt-clinical-signs"),
    path('responses-datatable', ajax_datatable_views.ResponseAjaxDatatableView.as_view(), name="dt-responses"),
]