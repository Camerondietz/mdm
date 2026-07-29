"""MDM admin registrations.

Importing these submodules registers every model with the admin site. Also gives
the admin a friendlier site header/title.
"""

from django.contrib import admin

from mdm.admin import (  # noqa: F401  (imported for their @admin.register side effects)
    catalog,
    geography,
    knowledge,
    organizations,
    people,
    taxonomy,
)

admin.site.site_header = "MDM · Master Data Management"
admin.site.site_title = "MDM Admin"
admin.site.index_title = "Data administration"
