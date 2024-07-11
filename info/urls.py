from django.urls import path
from .views import (
    ImageListCreateAPIView,
    ImageRetrieveUpdateDestroyAPIView,
    CarouselListCreateAPIView,
    CarouselRetrieveUpdateDestroyAPIView,
    AboutUsListCreateAPIView,
    AboutUsRetrieveUpdateDestroyAPIView,
    WhyChooseUsListCreateAPIView,
    WhyChooseUsRetrieveUpdateDestroyAPIView,
    TeamListCreateAPIView,
    TeamRetrieveUpdateDestroyAPIView,
    ContactListCreateAPIView,
    ContactRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path("images/", ImageListCreateAPIView.as_view(), name="image-list-create"),
    path(
        "images/<int:pk>/",
        ImageRetrieveUpdateDestroyAPIView.as_view(),
        name="image-retrieve-update-destroy",
    ),
    path(
        "carousels/", CarouselListCreateAPIView.as_view(), name="carousel-list-create"
    ),
    path(
        "carousels/<int:pk>/",
        CarouselRetrieveUpdateDestroyAPIView.as_view(),
        name="carousel-retrieve-update-destroy",
    ),
    path("aboutus/", AboutUsListCreateAPIView.as_view(), name="aboutus-list-create"),
    path(
        "aboutus/<int:pk>/",
        AboutUsRetrieveUpdateDestroyAPIView.as_view(),
        name="aboutus-retrieve-update-destroy",
    ),
    path(
        "whychooseus/",
        WhyChooseUsListCreateAPIView.as_view(),
        name="whychooseus-list-create",
    ),
    path(
        "whychooseus/<int:pk>/",
        WhyChooseUsRetrieveUpdateDestroyAPIView.as_view(),
        name="whychooseus-retrieve-update-destroy",
    ),
    path("teams/", TeamListCreateAPIView.as_view(), name="team-list-create"),
    path(
        "teams/<int:pk>/",
        TeamRetrieveUpdateDestroyAPIView.as_view(),
        name="team-retrieve-update-destroy",
    ),
    path("contacts/", ContactListCreateAPIView.as_view(), name="contact-list-create"),
    path(
        "contacts/<int:pk>/",
        ContactRetrieveUpdateDestroyAPIView.as_view(),
        name="contact-retrieve-update-destroy",
    ),
]
