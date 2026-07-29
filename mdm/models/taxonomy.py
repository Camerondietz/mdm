"""
Controlled-vocabulary / taxonomy tables.

Each is a concrete, hierarchical term list built on ``core.TaxonomyTerm``. Keeping
these as data (not hard-coded choices) means non-developers can extend the
vocabularies from the admin, and terms carry stable codes for cross-system mapping.
"""

from __future__ import annotations

from core.models import TaxonomyTerm


class OrganizationType(TaxonomyTerm):
    """e.g. Corporation, LLC, Nonprofit, Government Agency, Sole Proprietorship."""

    class Meta:
        ordering = ["name"]
        verbose_name = "organization type"
        verbose_name_plural = "organization types"


class EmploymentType(TaxonomyTerm):
    """e.g. Full-time, Part-time, Contractor, Intern, Temporary, Volunteer."""

    class Meta:
        ordering = ["name"]
        verbose_name = "employment type"
        verbose_name_plural = "employment types"


class ItemCategory(TaxonomyTerm):
    """Hierarchical product/asset categories (e.g. Electronics > Networking > Routers)."""

    class Meta:
        ordering = ["name"]
        verbose_name = "item category"
        verbose_name_plural = "item categories"


class DocumentType(TaxonomyTerm):
    """e.g. Contract, Invoice, Report, Policy, Manual, Specification, Article."""

    class Meta:
        ordering = ["name"]
        verbose_name = "document type"
        verbose_name_plural = "document types"


class Role(TaxonomyTerm):
    """
    A party's role within your data universe (e.g. Customer, Supplier, Employee,
    Partner, Family, Friend). Distinct from a job title, which lives on Employment.
    """

    class Meta:
        ordering = ["name"]
        verbose_name = "role"
        verbose_name_plural = "roles"


class Skill(TaxonomyTerm):
    """A competency held by a Person (e.g. Python, Welding, Project Management)."""

    class Meta:
        ordering = ["name"]
        verbose_name = "skill"
        verbose_name_plural = "skills"


class Topic(TaxonomyTerm):
    """A subject/theme a Document is about (e.g. Finance, Security, Onboarding)."""

    class Meta:
        ordering = ["name"]
        verbose_name = "topic"
        verbose_name_plural = "topics"
