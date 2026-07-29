"""API URL routing: a DefaultRouter exposing every entity under /api/."""

from rest_framework.routers import DefaultRouter

from mdm.api import viewsets as v

router = DefaultRouter()

# Core entities
router.register("people", v.PersonViewSet)
router.register("organizations", v.OrganizationViewSet)
router.register("departments", v.DepartmentViewSet)
router.register("employments", v.EmploymentViewSet)
router.register("items", v.ItemViewSet)
router.register("documents", v.DocumentViewSet)
router.register("locations", v.LocationViewSet)

# Generic attach-to-anything tables
router.register("contact-points", v.ContactPointViewSet)
router.register("identifiers", v.IdentifierViewSet)
router.register("relationships", v.RelationshipViewSet)

# Taxonomies
router.register("organization-types", v.OrganizationTypeViewSet)
router.register("employment-types", v.EmploymentTypeViewSet)
router.register("item-categories", v.ItemCategoryViewSet)
router.register("document-types", v.DocumentTypeViewSet)
router.register("roles", v.RoleViewSet)
router.register("skills", v.SkillViewSet)
router.register("topics", v.TopicViewSet)

urlpatterns = router.urls
