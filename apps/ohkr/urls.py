from django.urls import path
from . import views
from . import ajax_datatable_views

app_name = 'ohkr'

urlpatterns = [
    path('diseases', views.DiseaseListView.as_view(), name='diseases'),
    path('species', views.SpecieListView.as_view(), name='species'),
    path('clinical-signs', views.ClinicalSignListView.as_view(), name='clinical-signs'),
    path('responses', views.ClinicalResponseListView.as_view(), name='responses'),

    #ajax datatable views
    path('diseases-datatable', ajax_datatable_views.DiseaseAjaxDatatableView.as_view(), name="dt-diseases"),
    path('species-datatable', ajax_datatable_views.SpecieAjaxDatatableView.as_view(), name="dt-species"),
    path('clinical-signs-datatable', ajax_datatable_views.ClinicalSignAjaxDatatableView.as_view(), name="dt-clinical-signs"),
    path('responses-datatable', ajax_datatable_views.ClinicalResponseAjaxDatatableView.as_view(), name="dt-responses"),
]