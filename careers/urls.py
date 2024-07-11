from django.urls import path
from . import views

urlpatterns = [
    path("careers/", views.CareerListAPIView.as_view(), name="career_list_api"),
    path(
        "apply-for-job/",
        views.JobApplicationCreateAPIView.as_view(),
        name="apply_for_job_api",
    ),
]
