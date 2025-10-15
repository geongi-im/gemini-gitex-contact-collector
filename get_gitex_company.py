# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import csv
import time
import os

def crawl_gitex_exhibitors(start, limit):
    url = "https://exhibitors.gitex.com/gitex-global-2025/Exhibitor/fetchExhibitors"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    files = {
        'limit': (None, str(limit)),
        'start': (None, str(start))
    }

    response = requests.post(url, files=files, headers=headers)
    print(f"Response status: {response.status_code}")
    print(f"Response length: {len(response.text)}")
    return response.text

def get_official_website(profile_url):
    """Fetch official website from profile page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(profile_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        website_elem = soup.find('li', class_='social_website')
        if website_elem:
            link = website_elem.find('a')
            if link and 'href' in link.attrs:
                return link['href']
        return ""
    except Exception as e:
        print(f"Error fetching website for {profile_url}: {e}")
        return ""

def parse_exhibitor_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    exhibitors = []

    items = soup.find_all('div', class_='item col-12 list-group-item')

    for item in items:
        try:
            heading = item.find('h4', class_='heading')
            company_name = heading.text.strip() if heading else ""

            stand_info = item.find('p', style="margin-bottom:0;")
            stand_no = stand_info.text.strip() if stand_info else ""

            description_elem = item.find('p', class_='list-group-item-text')
            description = ""
            if description_elem:
                span = description_elem.find('span')
                description = span.text.strip() if span else ""

            profile_link = item.find('a', href=lambda href: href and 'ExbDetails' in href)
            profile_url = profile_link['href'] if profile_link else ""

            exhibitor = {
                'company_name': company_name,
                'stand_no': stand_no,
                'description': description,
                'profile_url': profile_url
            }

            exhibitors.append(exhibitor)

        except Exception as e:
            print(f"Parsing error: {e}")
            continue

    return exhibitors

def main():
    import sys
    import io

    # Fix encoding for Windows console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # ========== Configuration ==========
    START_INDEX = 1000        # Starting index
    END_INDEX = 1500       # Ending index (up to 1000)
    BATCH_SIZE = 50        # How many to fetch per request (50 is recommended)
    # ===================================

    csv_filename = 'output/gitex_exhibitors.csv'
    fieldnames = ['company_name', 'stand_no', 'description', 'profile_url', 'website']

    print(f"\n{'='*60}")
    print(f"[CONFIGURATION]")
    print(f"  Start Index: {START_INDEX}")
    print(f"  End Index: {END_INDEX}")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Expected Total: ~{(END_INDEX - START_INDEX) // BATCH_SIZE * BATCH_SIZE} records")
    print(f"{'='*60}")

    # Initialize CSV file with header
    file_exists = os.path.exists(csv_filename)
    if not file_exists:
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print(f"[INFO] Created new CSV file: {csv_filename}")
    else:
        print(f"[INFO] Appending to existing CSV file: {csv_filename}")

    total_count = 0

    for start in range(START_INDEX, END_INDEX, BATCH_SIZE):
        print(f"\n{'='*60}")
        print(f"[STEP 1/2] Collecting exhibitors list (start={start})")
        print(f"{'='*60}")
        html = crawl_gitex_exhibitors(start, BATCH_SIZE)

        exhibitors = parse_exhibitor_data(html)
        print(f"\n[INFO] Parsed {len(exhibitors)} exhibitors from response")
        print(f"[STEP 2/2] Fetching official website and saving to CSV...")
        print(f"{'='*60}")

        for idx, exhibitor in enumerate(exhibitors, 1):
            print(f"\n[{idx}/{len(exhibitors)}] Processing: {exhibitor['company_name']}")
            print(f"    Stand: {exhibitor['stand_no']}")

            # Fetch official website from profile page
            if exhibitor['profile_url']:
                print(f"    Fetching website from profile page...")
                website = get_official_website(exhibitor['profile_url'])
                exhibitor['website'] = website
                if website:
                    print(f"    ✓ Website found: {website}")
                else:
                    print(f"    ✗ Website not found")
                time.sleep(0.3)  # Be polite to the server
            else:
                exhibitor['website'] = ""
                print(f"    ✗ No profile URL available")

            # Save to CSV immediately
            with open(csv_filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    'company_name': exhibitor['company_name'],
                    'stand_no': exhibitor['stand_no'],
                    'description': exhibitor['description'],
                    'profile_url': exhibitor['profile_url'],
                    'website': exhibitor['website']
                })

            total_count += 1
            print(f"    💾 Saved to CSV (Total: {total_count} records)")

        print(f"\n[PROGRESS] Total saved so far: {total_count} exhibitors")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] All data saved successfully!")
    print(f"{'='*60}")
    print(f"File: {csv_filename}")
    print(f"Total records: {total_count}")
    print(f"Fields: company_name, stand_no, description, profile_url, website")

if __name__ == "__main__":
    main()
