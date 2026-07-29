"""Employment: a Person's business role at an Organization (schema.org ``OrganizationRole``).

Deliberately holds *business* data only (job title, work email, manager, dates),
never personal data — that stays on Person.
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from core.models import BaseModel


class Employment(BaseModel):
    schema_type = "OrganizationRole"

    person = models.ForeignKey(
        "mdm.Person", on_delete=models.CASCADE, related_name="employments"
    )
    organization = models.ForeignKey(
        "mdm.Organization", on_delete=models.CASCADE, related_name="employments"
    )
    department = models.ForeignKey(
        "mdm.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employments",
    )
    job_title = models.CharField(max_length=200, blank=True, default="")
    employment_type = models.ForeignKey(
        "mdm.EmploymentType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employments",
    )
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
        help_text="This employee's manager (another Employment record).",
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True, help_text="Blank = currently active.")

    # ── Business contact details ──────────────────────────────────────────────
    work_email = models.EmailField(blank=True, default="")
    extension = models.CharField(max_length=20, blank=True, default="")
    office = models.CharField(max_length=120, blank=True, default="", help_text="Office / desk label.")
    office_location = models.ForeignKey(
        "mdm.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="offices",
    )
    is_primary = models.BooleanField(
        default=False, help_text="This person's primary/current employment."
    )

    class Meta:
        ordering = ["-is_primary", "-start_date"]
        indexes = [
            models.Index(fields=["person"]),
            models.Index(fields=["organization"]),
            models.Index(fields=["end_date"]),
        ]

    def __str__(self) -> str:
        title = self.job_title or "Role"
        return f"{self.person} — {title} @ {self.organization}"

    @property
    def display_name(self) -> str:
        return str(self)

    @property
    def is_current(self) -> bool:
        return self.end_date is None or self.end_date >= timezone.localdate()

    def jsonld_properties(self) -> dict:
        return {
            "roleName": self.job_title,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "endDate": self.end_date.isoformat() if self.end_date else None,
            "worksFor": self.organization.get_uri() if self.organization_id else None,
            "member": self.person.get_uri() if self.person_id else None,
        }
