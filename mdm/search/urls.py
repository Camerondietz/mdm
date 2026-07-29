"""URL routes for the web search UI and entity detail pages."""

from django.urls import path

from mdm.search import views

app_name = "search"

urlpatterns = [
    path("", views.SearchView.as_view(), name="home"),
    path("person/<uuid:pk>/", views.PersonDetailView.as_view(), name="person_detail"),
    path("organization/<uuid:pk>/", views.OrganizationDetailView.as_view(), name="organization_detail"),
    path("department/<uuid:pk>/", views.DepartmentDetailView.as_view(), name="department_detail"),
    path("employment/<uuid:pk>/", views.EmploymentDetailView.as_view(), name="employment_detail"),
    path("item/<uuid:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("document/<uuid:pk>/", views.DocumentDetailView.as_view(), name="document_detail"),
    path("location/<uuid:pk>/", views.LocationDetailView.as_view(), name="location_detail"),
]
