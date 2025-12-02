from django.core.management.base import BaseCommand
from closings.scraper import scrape_wveis

class Command(BaseCommand):
    help = 'Scrapes school closings data from WVEIS'

    def handle(self, *args, **options):
        self.stdout.write('Starting scrape...')

        count, error = scrape_wveis()

        if error:
            self.stdout.write(self.style.ERROR(f'Scraping failed: {error}'))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated {count} counties!"))
            