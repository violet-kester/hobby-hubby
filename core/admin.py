from django.contrib import admin
from django.contrib.admin import AdminSite


class HobbyHubbyAdminSite(AdminSite):
    """
    Custom admin site for Hobby Hubby.
    """
    site_header = "Hobby Hubby Administration"
    site_title = "Hobby Hubby Admin"
    index_title = "Welcome to Hobby Hubby Administration"


# Create custom admin site instance
hobby_hubby_admin = HobbyHubbyAdminSite(name='hobby_hubby_admin')

# Use the default admin site for now
admin.site.site_header = "Hobby Hubby Administration"
admin.site.site_title = "Hobby Hubby Admin"
admin.site.index_title = "Welcome to Hobby Hubby Administration"
