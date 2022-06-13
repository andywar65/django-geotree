from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import (  # noqa
    AuthorListView,
    BaseListView,
    ElementAuthorListView,
    ElementDetailView,
    ElementFamilyListView,
    ElementListView,
    ElementRedirectView,
    FamilyListView,
)

app_name = "geotree"
urlpatterns = [
    path("", BaseListView.as_view(), name="base_list"),
    path(_("families"), FamilyListView.as_view(), name="family_list"),
    path(_("authors"), AuthorListView.as_view(), name="author_list"),
    path(_("author/<username>"), ElementAuthorListView.as_view(), name="author_detail"),
    path(
        _("authors/<username>/family/<pk>"),
        ElementFamilyListView.as_view(),
        name="family_detail",
    ),
    path(
        _("author/<username>/element/<pk>"),
        ElementDetailView.as_view(),
        name="element_detail",
    ),
]
