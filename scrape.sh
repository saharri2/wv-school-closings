#!/bin/bash

source venv/bin/activate

echo "------------------------------" >> scraper.log
echo "Scrape started at $(date)" >> scraper.log

python manage.py scrape_closings >> scraper.log 2>&1

echo "Scrape completed at $(date)" >> scraper.log 