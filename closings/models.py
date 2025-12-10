from django.db import models

# Create your models here.
class County(models.Model):
    """Represents a West Virginia county and its school status"""

    # This is the county name
    name = models.CharField(max_length=100, unique=True)

    # Status fields - "None", "All", or specific details
    closings = models.CharField(max_length=100, default=None)
    delays = models.CharField(max_length=100, default=None)
    dismissals = models.CharField(max_length=100, default=None)
    non_traditional = models.CharField(max_length=100, default=None)
    delay_duration = models.CharField(max_length=100, blank=True, default="")
    specific_school_closings = models.TextField(blank=True, default='')
    specific_school_dismissals = models.TextField(blank=True, default ='')

    # Last update of the data
    last_update = models.CharField(max_length=100, blank=True)

    # Automatic timestamp for when the data was scraped
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"] # Always list alphabetically
        verbose_name_plural = "Counties" # Fix plural in admin

    """How this object appears in the admin shell"""
    def __str__(self):
        return self.name

    def get_status(self):
        """Returns primary status of the county"""
        
        if self.closings == "Some":
            return "PARTIAL"
        elif self.closings != "None":
            return "CLOSED"
        elif self.delays != "None":
            if "3-hour" in self.delay_duration.lower() or "3 hour" in self.delay_duration.lower():
                return "DELAYED-3HR"
            else:
                return "DELAYED"
        elif self.non_traditional != "None":
            return "NON-TRADITIONAL"
        elif self.dismissals == "Some":
            return "PARTIAL-DISMISSAL"
        elif self.dismissals != "None":
            return "DISMISSED"
        else:
            return "NORMAL"
    
    def get_status_color(self):
        """Return status color for the map based on status"""

        status = self.get_status()
        colors = {
            "CLOSED": "#ef4444", # red
            "PARTIAL": "#f97316", # orange
            "DELAYED": "#fbbf24", # green
            "DELAYED-3HR": "#4c00b0", # purple
            "NON-TRADITIONAL": "#3b82f6", # blue
            "DISMISSED": "#0fcf8f", # sea green
            "PARTIAL-DISMISSAL": "#0fcf8f", # sea green
            "NORMAL": "#9ca3af" # gray
        }

        return colors.get(status, "#9ca3af")