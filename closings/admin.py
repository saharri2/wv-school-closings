from django.contrib import admin
from.models import County

# Register your models here.
@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    """Admin interface for County model"""

    # What columns to show in the list view
    list_display = [
        "name",
        "get_status",
        "closings",
        "delays",
        "dismissals",
        "non_traditional",
        "last_update"
        ]
    
    # Add filters to the right sidebar
    list_filter = ["closings", "delays", "non_traditional"]

    # Add a search box
    search_fields = ["name"]

    # Make the fields read-only
    readonly_fields = ["updated_at"]

    # Order fields in the edit form
    fields = [
        "name",
        "closings",
        "delays",
        "dismissals",
        "non_traditional",
        "bus_info",
        "last_update",
        "updated_at"
    ]