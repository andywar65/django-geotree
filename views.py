from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.dates import DayArchiveView, MonthArchiveView, YearArchiveView

from .forms import ElementCreateForm
from .models import Element, Family, Tag

User = get_user_model()


class HxPageTemplateMixin:
    """Switches template depending on request.htmx"""

    def get_template_names(self):
        if not self.request.htmx:
            return [self.template_name.replace("htmx/", "")]
        else:
            return [self.template_name]


class BaseListView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/base_list.html"

    def get_queryset(self):
        qs = Element.objects.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lines"] = Family.objects.all()
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class FamilyListView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/family_list.html"

    def get_queryset(self):
        qs = Element.objects.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        families = Family.objects.all()
        roots = families.filter(depth=1)
        list = []
        for root in roots:
            annotated = Family.get_annotated_list(parent=root)
            list.append(annotated)
        context["families"] = list
        context["lines"] = families
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class AuthorListView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/author_list.html"

    def get_queryset(self):
        qs = Element.objects.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        authors = Element.objects.values_list("user__username", flat=True)
        context["authors"] = list(dict.fromkeys(authors))
        context["lines"] = Family.objects.all()
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class TagListView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/tag_list.html"

    def get_queryset(self):
        qs = Element.objects.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["lines"] = Family.objects.all()
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class AuthorDetailView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/author_detail.html"

    def setup(self, request, *args, **kwargs):
        super(AuthorDetailView, self).setup(request, *args, **kwargs)
        self.author = get_object_or_404(User, username=self.kwargs["username"])

    def get_queryset(self):
        qs = Element.objects.filter(user_id=self.author.uuid, private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = self.author
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class FamilyDetailView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/family_detail.html"

    def setup(self, request, *args, **kwargs):
        super(FamilyDetailView, self).setup(request, *args, **kwargs)
        self.family = get_object_or_404(Family, id=self.kwargs["pk"])

    def get_queryset(self):
        list = [self.family.id]
        children = self.family.get_descendants()
        for child in children:
            list.append(child.id)
        qs = Element.objects.filter(family_id__in=list, private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(
                user_id=self.request.user.uuid, family_id__in=list, private=True
            )
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["family"] = self.family
        # combine descendants and self family querysets
        context["lines"] = self.family.get_descendants() | Family.objects.filter(
            id=self.family.id
        )
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class TagDetailView(HxPageTemplateMixin, ListView):
    model = Element
    context_object_name = "elements"
    template_name = "djeotree/htmx/tag_detail.html"

    def setup(self, request, *args, **kwargs):
        super(TagDetailView, self).setup(request, *args, **kwargs)
        self.tag = get_object_or_404(Tag, id=self.kwargs["pk"])

    def get_queryset(self):
        e_values = self.tag.element_tag_value
        list = e_values.values_list("element_id", flat=True)
        qs = Element.objects.filter(id__in=list, private=False)
        if self.request.user.is_authenticated:
            qs2 = Element.objects.filter(
                user_id=self.request.user.uuid, id__in=list, private=True
            )
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class ElementDetailView(HxPageTemplateMixin, DetailView):
    model = Element
    context_object_name = "element"
    template_name = "djeotree/htmx/element_detail.html"

    def get_object(self, queryset=None):
        self.object = super(ElementDetailView, self).get_object(queryset=None)
        user = get_object_or_404(User, username=self.kwargs["username"])
        if user != self.object.user:
            raise Http404(_("Element does not belong to User"))
        if self.object.private and self.object.user != self.request.user:
            raise PermissionDenied
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["family"] = self.object.family
        context["author"] = self.object.user
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        context["main_gal_slug"] = get_random_string(7)
        context["images"] = self.object.element_image.all()
        return context


class ElementDayArchiveView(HxPageTemplateMixin, DayArchiveView):
    model = Element
    date_field = "date"
    context_object_name = "elements"
    year_format = "%Y"
    month_format = "%m"
    day_format = "%d"
    allow_empty = True
    template_name = "djeotree/htmx/day_detail.html"

    def get_queryset(self):
        original = super(ElementDayArchiveView, self).get_queryset()
        qs = original.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = original.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class ElementMonthArchiveView(HxPageTemplateMixin, MonthArchiveView):
    model = Element
    date_field = "date"
    context_object_name = "elements"
    year_format = "%Y"
    month_format = "%m"
    allow_empty = True
    template_name = "djeotree/htmx/month_detail.html"

    def get_queryset(self):
        original = super(ElementMonthArchiveView, self).get_queryset()
        qs = original.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = original.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class ElementYearArchiveView(HxPageTemplateMixin, YearArchiveView):
    model = Element
    date_field = "date"
    make_object_list = True
    context_object_name = "elements"
    year_format = "%Y"
    allow_empty = True
    template_name = "djeotree/htmx/year_detail.html"

    def get_queryset(self):
        original = super(ElementYearArchiveView, self).get_queryset()
        qs = original.filter(private=False)
        if self.request.user.is_authenticated:
            qs2 = original.filter(user_id=self.request.user.uuid, private=True)
            qs = qs | qs2
        return qs.order_by("family", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapbox_token"] = settings.MAPBOX_TOKEN
        return context


class ElementCreateView(LoginRequiredMixin, HxPageTemplateMixin, CreateView):
    model = Element
    form_class = ElementCreateForm
    template_name = "djeotree/htmx/element_create.html"

    def get_initial(self):
        initial = super(ElementCreateView, self).get_initial()
        initial["user"] = self.request.user
        return initial

    def form_valid(self, form):
        if form.instance.user != self.request.user:
            raise PermissionDenied
        return super(ElementCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            "geotree:author_detail", kwargs={"username": self.request.user.username}
        )


class ElementUpdateView(LoginRequiredMixin, HxPageTemplateMixin, UpdateView):
    model = Element
    form_class = ElementCreateForm
    template_name = "djeotree/htmx/element_update.html"

    def get_object(self, queryset=None):
        self.object = super(ElementUpdateView, self).get_object(queryset=None)
        user = get_object_or_404(User, username=self.kwargs["username"])
        if user != self.object.user:
            raise Http404(_("Element does not belong to User"))
        if self.object.private and self.object.user != self.request.user:
            raise PermissionDenied
        return self.object

    def form_valid(self, form):
        if form.instance.user != self.request.user:
            raise PermissionDenied
        return super(ElementUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            "geotree:author_detail", kwargs={"username": self.request.user.username}
        )
