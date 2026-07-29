"""Admin for the controlled-vocabulary tables."""

from django.contrib import admin

from core.admin import TaxonomyTermAdmin
from mdm.models import (
    DocumentType,
    EmploymentType,
    ItemCategory,
    OrganizationType,
    Role,
    Skill,
    Topic,
)

for _model in (
    OrganizationType,
    EmploymentType,
    ItemCategory,
    DocumentType,
    Role,
    Skill,
    Topic,
):
    admin.site.register(_model, TaxonomyTermAdmin)
