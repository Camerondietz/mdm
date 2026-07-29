"""MDM domain models.

Split across modules for readability but registered under the single ``mdm`` app.
Import order is not significant — inter-model foreign keys use string references.
"""

from mdm.models.document import Document
from mdm.models.employment import Employment
from mdm.models.geography import Location
from mdm.models.item import Item
from mdm.models.organization import Department, Organization
from mdm.models.person import Person
from mdm.models.taxonomy import (
    DocumentType,
    EmploymentType,
    ItemCategory,
    OrganizationType,
    Role,
    Skill,
    Topic,
)

__all__ = [
    "Document",
    "DocumentType",
    "Department",
    "Employment",
    "EmploymentType",
    "Item",
    "ItemCategory",
    "Location",
    "Organization",
    "OrganizationType",
    "Person",
    "Role",
    "Skill",
    "Topic",
]
