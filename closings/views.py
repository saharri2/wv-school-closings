from django.shortcuts import render
from .models import County
import json
import os
from django.conf import settings

def map_view(request):
    """Display the interactive map of school closings"""
    
    # Get all counties from the database
    counties = County.objects.all()
    
    # Convert to a format we can use in JavaScript
    counties_data = {}
    for county in counties:
        school_closings = []
        if county.specific_school_closings:
            try:
                school_closings = json.loads(county.specific_school_closings)
            except json.JSONDecodeError:
                school_closings = []

        school_dismissals = []
        if county.specific_school_dismissals:
            try:
                school_dismissals = json.loads(county.specific_school_dismissals)
            except json.JSONDecodeError:
                school_dismissals = []
        
        school_delays = []
        if county.specific_school_delays:
            try:
                school_delays = json.loads(county.specific_school_delays)
            except json.JSONDecodeError:
                school_delays = []
        
        counties_data[county.name] = {
            'name': county.name,
            'status': county.get_status(),
            'color': county.get_status_color(),
            'closings': county.closings,
            'delays': county.delays,
            'delay_duration': county.delay_duration,
            'dismissals': county.dismissals,
            'non_traditional': county.non_traditional,
            'last_update': county.last_update,
            'school_closings': school_closings,
            'school_dismissals': school_dismissals,
            'school_delays': school_delays,
        }
    
    # Read SVG file
    svg_path = os.path.join(settings.BASE_DIR, 'closings', 'static', 'closings', 'wv-map.svg')
    with open(svg_path, 'r') as f:
        svg_content = f.read()
    
    # Pass data to template
    context = {
        'counties_json': json.dumps(counties_data),
        'svg_content': svg_content,
    }
    
    return render(request, 'closings/map.html', context)