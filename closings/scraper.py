import requests
from bs4 import BeautifulSoup
import feedparser
import re
from .models import County
import json

def parse_rss_feed():
    """
    Parse the RSS feed and extract delay durations and other details.
    Returns a dictionary with county names as keys.
    """
    rss_data = {}
    
    try:
        feed = feedparser.parse('https://wveis.k12.wv.us/closings/rss.php')
        
        for entry in feed.entries:
            # Extract county name from title: "All schools in Hampshire County"
            title = entry.title
            description = entry.description
            if not isinstance(description, str):
                continue

            if 'All schools' in title:
                county_match = re.search(r'All schools in (.+?) County', title)
            
                if county_match:
                    county_name = county_match.group(1)
                    description = entry.description
                    
                    # Make sure description is a string (fix Pylance warning)
                    if not isinstance(description, str):
                        continue
                    
                    # Extract delay duration (2-hour, 3-hour, etc.)
                    delay_match = re.search(r'(\d+)-hour delay', description, re.IGNORECASE)
                    delay_duration = delay_match.group(0) if delay_match else ""
                    
                    # Extract the reason if present
                    reason_match = re.search(r'due to (.+?)\.', description)
                    reason = reason_match.group(1) if reason_match else ""
                    
                    if county_name not in rss_data:
                        rss_data[county_name] = {
                            'delay_duration': delay_duration,
                            'reason': reason,
                            'full_description': description,
                            'school_closings': [],
                            'school_dismissals': [],
                        }
                    else:
                        # County already exists just update the delay info
                        rss_data[county_name]['delay_duration'] = delay_duration
                        rss_data[county_name]['reason'] = reason
                        rss_data[county_name]['full_description'] = description
                    
                    print(f"RSS: {county_name} - {delay_duration if delay_duration else 'No delay info'}")

            else:
                school_match = re.search(r'(.+?) in (.+?) County', title)

                if school_match:
                    school_name = school_match.group(1)
                    county_name = school_match.group(2)

                    if county_name not in rss_data:
                        rss_data[county_name] = {
                            'delay_duration': '',
                            'reason': '',
                            'full_description': '',
                            'school_closings': [],
                            'school_dismissals': [],
                        }

                    if 'school_closings' not in rss_data[county_name]:
                        rss_data[county_name]['school_closings'] = []
                    if 'school_dismissals' not in rss_data[county_name]:
                        rss_data[county_name]['school_dismissals'] = []
                    if 'school_delays' not in rss_data[county_name]:
                        rss_data[county_name]['school_delays'] = []

                    if 'closing at' in description.lower() or 'will be closing' in description.lower():
                        rss_data[county_name]['school_dismissals'].append({
                            'name': school_name,
                            'description': description.strip()
                        })
                        print(f"RSS: Individual dismissal - {school_name} in {county_name}")
                    elif 'delay' in description.lower():
                        rss_data[county_name]['school_delays'].append({
                            'name': school_name,
                            'description': description.strip()
                        })
                        print(f"RSS: Individual delay - {school_name} in {county_name}")
                    else:
                        rss_data[county_name]['school_closings'].append({
                            'name': school_name,
                            'description': description.strip()
                        })

                        print(f"RSS: Individual school - {school_name} in {county_name}")
        
        return rss_data
    
    except Exception as e:
        print(f"Error parsing RSS feed: {e}")
        return {}

def scrape_wveis():
    """
    Scrapes the WVEIS school closings page and updates the database.
    Also pulls delay duration info from RSS feed.
    Returns a tuple of (success_count, error_message)
    """
    url = "https://wveis.k12.wv.us/closings/"
    
    try:
        # First, get RSS feed data
        print("Parsing RSS feed for delay durations...")
        rss_data = parse_rss_feed()

        # Ensure all 55 counties exist in database
        all_counties = [
            'Barbour', 'Berkeley', 'Boone', 'Braxton', 'Brooke', 'Cabell', 'Calhoun',
            'Clay', 'Doddridge', 'Fayette', 'Gilmer', 'Grant', 'Greenbrier', 'Hampshire',
            'Hancock', 'Hardy', 'Harrison', 'Jackson', 'Jefferson', 'Kanawha', 'Lewis',
            'Lincoln', 'Logan', 'Marion', 'Marshall', 'Mason', 'McDowell', 'Mercer',
            'Mineral', 'Mingo', 'Monongalia', 'Monroe', 'Morgan', 'Nicholas', 'Ohio',
            'Pendleton', 'Pleasants', 'Pocahontas', 'Preston', 'Putnam', 'Raleigh',
            'Randolph', 'Ritchie', 'Roane', 'Summers', 'Taylor', 'Tucker', 'Tyler',
            'Upshur', 'Wayne', 'Webster', 'Wetzel', 'Wirt', 'Wood', 'Wyoming'
        ]

        for county_name in all_counties:
            County.objects.get_or_create(
                name=county_name,
                defaults={
                    'closings': 'None',
                    'delays': 'None',
                    'dismissals': 'None',
                    'non_traditional': 'None',
                    'delay_duration': '',
                    'last_update': '',
                    'specific_school_closings': '',
                    'specific_school_dismissals': '',
                    'specific_school_delays': '',
                }
            )

        # Then scrape the main page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        print(f"Fetching data from {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='closings-table')
        
        if not table:
            # WVEIS reset their site for the day - clear data
            print("Table not found - resetting all counties to default status (end of day)")
            County.objects.all().update(
                closings='None',
                delays='None',
                dismissals='None',
                non_traditional='None',
                delay_duration='',
                specific_school_closings='',
                specific_school_dismissals='',
                specific_school_delays = '',
                last_update='',
            )
            return (0, "Table not found - all counties reset to default status")
        
        rows = table.find_all('tr')[1:]  # Skip header
        updated_count = 0
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) < 7:
                continue
            
            county_link = cells[0].find('a')
            if not county_link:
                continue
            
            county_name = county_link.get_text(strip=True)
            closings = cells[1].get_text(strip=True)
            delays = cells[2].get_text(strip=True)
            dismissals = cells[3].get_text(strip=True)
            non_traditional = cells[4].get_text(strip=True)
            last_update = cells[6].get_text(strip=True)
            
            if not county_name:
                continue
            
            # Get delay duration from RSS if available
            delay_duration = ""
            school_closings_json = ""
            school_dismissals_json = ""
            school_delays_json = ""

            if county_name in rss_data:
                try:
                    if delays != "None":
                        delay_duration = rss_data[county_name].get('delay_duration', '')

                    if rss_data[county_name].get("school_closings"):
                        school_closings_json = json.dumps(rss_data[county_name]['school_closings'])
                    
                    if rss_data[county_name].get("school_dismissals"):
                        school_dismissals_json = json.dumps(rss_data[county_name]['school_dismissals'])

                    if rss_data[county_name].get("school_delays"):
                        school_delays_json = json.dumps(rss_data[county_name]['school_delays'])
                except (KeyError, TypeError) as e:
                    print(f"Warning: Error processing RSS data for {county_name}: {e}")

            # Update or create the county in database
            county, created = County.objects.update_or_create(
                name=county_name,
                defaults={
                    'closings': closings,
                    'delays': delays,
                    'dismissals': dismissals,
                    'non_traditional': non_traditional,
                    'last_update': last_update,
                    'delay_duration': delay_duration,
                    'specific_school_closings': school_closings_json,
                    'specific_school_dismissals': school_dismissals_json,
                    'specific_school_delays': school_delays_json,
                }
            )
            
            action = "Created" if created else "Updated"
            duration_info = f" ({delay_duration})" if delay_duration else ""
            school_info = f" - {len(json.loads(school_closings_json)) if school_closings_json else 0} individual schools" if school_closings_json else ""
            dismissal_info = f" - {len(json.loads(school_dismissals_json)) if school_dismissals_json else 0} dismissals" if school_dismissals_json else ""
            delay_info = f" - {len(json.loads(school_delays_json)) if school_delays_json else 0} delays" if school_delays_json else ""
            print(f"{action}: {county_name} - {county.get_status()}{duration_info}{school_info}{dismissal_info}{delay_info}")
            updated_count += 1
        
        return (updated_count, None)
    
    except requests.RequestException as e:
        return (0, f"Network error: {str(e)}")
    except Exception as e:
        return (0, f"Error: {str(e)}")