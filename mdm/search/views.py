"""
Web UI (login-required):
  * one unified search page across every entity (PostgreSQL full-text search,
    type filters, sort), and
  * a rich detail page per entity — e.g. an Organization shows its departments
    with the employees in each.
"""

from __future__ import annotations

from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import Paginator
from django.db.models import FloatField, Value
from django.urls import reverse
from django.views.generic import DetailView, TemplateView

from mdm.models import (
    Department,
    Document,
    Employment,
    Item,
    Location,
    Organization,
    Person,
)
from mdm.search.registry import SEARCH_SPECS, SPECS_BY_KEY

RESULTS_PER_PAGE = 25
PER_TYPE_CAP = 300  # safety cap on rows pulled per entity type before merging


class SearchView(LoginRequiredMixin, TemplateView):
    """Master text search over all models with type filters and sorting."""

    template_name = "search/search.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request

        q = request.GET.get("q", "").strip()
        selected_types = [t for t in request.GET.getlist("type") if t in SPECS_BY_KEY]
        sort = request.GET.get("sort") or ("relevance" if q else "updated")

        rows: list[dict] = []
        counts: dict[str, int] = {}

        for spec in SEARCH_SPECS:
            qs = spec.base_queryset(spec.model)
            if q:
                vector = SearchVector(*spec.vector_fields, config="english")
                query = SearchQuery(q, search_type="websearch", config="english")
                qs = qs.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0)
            else:
                qs = qs.annotate(rank=Value(0.0, output_field=FloatField()))

            counts[spec.key] = qs.count()

            # If the user narrowed to specific types, skip the others' rows.
            if selected_types and spec.key not in selected_types:
                continue

            for obj in qs.order_by("-rank", "-updated_at")[:PER_TYPE_CAP]:
                rows.append(
                    {
                        "key": spec.key,
                        "label": spec.label,
                        "icon": spec.icon,
                        "title": spec.title(obj),
                        "subtitle": spec.subtitle(obj),
                        "rank": float(getattr(obj, "rank", 0.0) or 0.0),
                        "updated": obj.updated_at,
                        "url": reverse(spec.detail_route, args=[obj.pk]),
                    }
                )

        if sort == "name":
            rows.sort(key=lambda r: r["title"].lower())
        elif sort == "oldest":
            rows.sort(key=lambda r: r["updated"])
        elif sort == "updated":
            rows.sort(key=lambda r: r["updated"], reverse=True)
        else:  # relevance
            rows.sort(key=lambda r: (r["rank"], r["updated"]), reverse=True)

        paginator = Paginator(rows, RESULTS_PER_PAGE)
        page_obj = paginator.get_page(request.GET.get("page"))

        params = request.GET.copy()
        params.pop("page", None)

        type_facets = [
            {"key": spec.key, "label": spec.label, "icon": spec.icon, "count": counts.get(spec.key, 0)}
            for spec in SEARCH_SPECS
        ]

        ctx.update(
            {
                "q": q,
                "sort": sort,
                "selected_types": selected_types,
                "type_facets": type_facets,
                "total_results": len(rows),
                "page_obj": page_obj,
                "base_qs": params.urlencode(),
            }
        )
        return ctx


# ── Detail views ──────────────────────────────────────────────────────────────
class PersonDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/person_detail.html"
    context_object_name = "person"
    queryset = Person.objects.select_related("primary_location").prefetch_related(
        "roles",
        "skills",
        "parents",
        "children",
        "contacts",
        "identifiers",
        "authored_documents",
        "employments__organization",
        "employments__department",
        "employments__employment_type",
    )


class OrganizationDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/organization_detail.html"
    context_object_name = "organization"
    queryset = Organization.objects.select_related(
        "org_type", "parent", "primary_location"
    ).prefetch_related(
        "locations",
        "subsidiaries",
        "contacts",
        "identifiers",
        "departments__parent",
        "manufactured_items",
        "employments__person",
        "employments__department",
        "employments__employment_type",
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.object

        # Group employees under their department in a single pass (no N+1).
        employees_by_dept: dict = defaultdict(list)
        unassigned: list = []
        current, former = [], []
        for emp in org.employments.all():
            (current if emp.is_current else former).append(emp)
            if emp.department_id:
                employees_by_dept[emp.department_id].append(emp)
            else:
                unassigned.append(emp)

        ctx["departments"] = [
            {"department": dept, "employees": employees_by_dept.get(dept.id, [])}
            for dept in org.departments.all()
        ]
        ctx["unassigned_employees"] = unassigned
        ctx["current_employments"] = current
        ctx["former_employments"] = former
        return ctx


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/department_detail.html"
    context_object_name = "department"
    queryset = Department.objects.select_related("organization", "parent").prefetch_related(
        "children", "contacts", "identifiers", "employments__person", "employments__employment_type"
    )


class EmploymentDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/employment_detail.html"
    context_object_name = "employment"
    queryset = Employment.objects.select_related(
        "person", "organization", "department", "employment_type", "manager__person", "office_location"
    ).prefetch_related("reports__person")


class ItemDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/item_detail.html"
    context_object_name = "item"
    queryset = Item.objects.select_related("manufacturer").prefetch_related(
        "categories", "documents", "related_items", "related_to", "identifiers"
    )


class DocumentDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/document_detail.html"
    context_object_name = "document"
    queryset = Document.objects.select_related("doc_type", "owner").prefetch_related(
        "authors", "topics", "items", "identifiers"
    )


class LocationDetailView(LoginRequiredMixin, DetailView):
    template_name = "search/location_detail.html"
    context_object_name = "location"
    queryset = Location.objects.select_related("parent").prefetch_related(
        "children", "residents", "headquartered_organizations", "located_organizations", "identifiers"
    )
