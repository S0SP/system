import os
import sys
import re
import json
import time
import random
import argparse
from playwright.sync_api import sync_playwright
import assets_handler
import dashboard_generator
import zip_archive

# Constants
WORKSPACE_DIR = "d:\\wa\\neokim"
README_PATH = os.path.join(WORKSPACE_DIR, "README.md")
CHROME_PROFILE_DIR = os.path.join(WORKSPACE_DIR, "chrome_profile")
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archive")
CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, "checkpoint.json")

def parse_readme(readme_path):
    """
    Parses the README.md file to categorize links and associate filenames.
    """
    if not os.path.exists(readme_path):
        print(f"Error: README.md not found at {readme_path}")
        return {}

    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    category_map = {
        "System Design Case Study": "case-studies",
        "System Design Fundamentals": "fundamentals",
        "System Design Interview": "interview",
        "AI Engineering": "ai-engineering",
        "Software White Papers": "white-papers"
    }
    
    current_category = ""
    url_mapping = {}
    
    for line in lines:
        line_strip = line.strip()
        
        # Detect category headers
        header_match = re.match(r'^##\s+(.+)$', line_strip)
        if header_match:
            header_text = header_match.group(1).strip()
            if header_text in category_map:
                current_category = category_map[header_text]
                
        # Match markdown links: - [Text](URL)
        link_match = re.search(r'-\s+\[([^\]]+)\]\((https?://[^\)]+)\)', line_strip)
        if link_match and current_category:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip().rstrip('/')
            
            # Extract slug
            slug = url.split('/')[-1]
            if not slug or "systemdesign" in slug:
                # Clean up title for fallback slug
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            
            filename = f"{slug}.html"
            url_mapping[url] = {
                "title": title,
                "category": current_category,
                "filename": filename,
                "url": url
            }
            
    return url_mapping

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_checkpoint(completed_urls):
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(list(completed_urls), f, indent=2)

def run_login_mode():
    """
    Opens a visible browser context so the user can log in manually.
    Saves the session state to the persistent chrome profile folder.
    """
    print("\n" + "="*50)
    print("      SYSTEM DESIGN ACADEMY ARCHIVER - LOGIN MODE")
    print("="*50)
    print("Launching Chrome...")
    print("Please follow these steps:")
    print("1. Log in to your Substack account (via Gmail, OTP, etc.).")
    print("2. Navigate to one of the paid/subscription articles to ensure it renders fully.")
    print("3. CLOSE the browser window when you are logged in and ready.")
    print("="*50 + "\n")
    
    with sync_playwright() as p:
        # Launch Chromium using persistent context with a standard viewport
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        page.goto("https://newsletter.systemdesign.one")
        
        print("Waiting for you to close the browser window...")
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
                
    print("\nSession saved successfully. You can now run in Archive Mode.")

def is_paywall_present(page):
    """
    Checks the loaded page DOM to determine if a paywall is active.
    """
    paywall_selectors = [
        ".subscription-gate",
        ".paywall-wrapper",
        ".paywall",
        ".subscribe-widget-preamble",
        "text='This post is for paid subscribers only'"
    ]
    for selector in paywall_selectors:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            pass
    return False

def scroll_page(page):
    """
    Scrolls down the page progressively to trigger lazy loading of images/diagrams.
    """
    # Get current page height
    scroll_height = page.evaluate("document.body.scrollHeight")
    current_position = 0
    step = 400
    
    while current_position < scroll_height:
        page.evaluate(f"window.scrollTo(0, {current_position})")
        time.sleep(0.15) # Wait briefly
        current_position += step
        # Re-evaluate height in case content loaded and expanded height
        scroll_height = page.evaluate("document.body.scrollHeight")
        
    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.2)

def run_archive_mode(url_mapping, visible=False):
    """
    Iterates through the mapped URLs and downloads them using Playwright.
    """
    print("\n" + "="*50)
    print("      SYSTEM DESIGN ACADEMY ARCHIVER - ARCHIVE MODE")
    print("="*50)
    
    completed_urls = load_checkpoint()
    urls_to_crawl = [url for url in url_mapping if url not in completed_urls]
    
    if not urls_to_crawl:
        print("All articles are already archived! Nothing to do.")
        return
        
    print(f"Total Unique Articles: {len(url_mapping)}")
    print(f"Already Archived:      {len(completed_urls)}")
    print(f"Remaining to Crawl:    {len(urls_to_crawl)}")
    print("Starting crawler in 3 seconds...")
    time.sleep(3)
    
    with sync_playwright() as p:
        # Launch Chromium using the authenticated profile
        context = p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_DIR,
            headless=not visible,
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        # Set a default timeout
        page.set_default_timeout(30000)
        
        count = len(completed_urls)
        for i, url in enumerate(urls_to_crawl, start=1):
            count += 1
            print(f"\n[{count}/{len(url_mapping)}] Crawling: {url}")
            
            # Fetch article info
            info = url_mapping[url]
            category = info["category"]
            filename = info["filename"]
            title = info["title"]
            
            # Destination path
            category_dir = os.path.join(ARCHIVE_DIR, category)
            os.makedirs(category_dir, exist_ok=True)
            output_file = os.path.join(category_dir, filename)
            
            # Skip if already exists
            if os.path.exists(output_file):
                print(f"-> File already exists locally. Skipping network fetch.")
                completed_urls.add(url)
                save_checkpoint(completed_urls)
                continue
                
            try:
                # Go to page
                page.goto(url, wait_until="domcontentloaded")
                
                # Check for paywalls
                if is_paywall_present(page):
                    print("⚠️ WARNING: A paywall / subscription gate was detected on this page!")
                    print("This means either your session has expired, or this browser instance isn't authenticated.")
                    print("Please close this crawler and run in --login mode again to re-authenticate.")
                    
                    # Pause to let user review or re-login if visible mode is enabled
                    if visible:
                        input("Press Enter to continue anyway, or Ctrl+C to abort and re-login...")
                    else:
                        sys.exit(1)
                
                # Scroll to load dynamic assets
                scroll_page(page)
                
                # Get rendered HTML
                html_content = page.content()
                
                # Run the asset download and DOM rewrite
                local_html = assets_handler.process_assets(
                    html_content=html_content,
                    page_url=url,
                    base_archive_dir=ARCHIVE_DIR,
                    category_subfolder=category,
                    urls_mapping=url_mapping
                )
                
                # Save sanitized page
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(local_html)
                    
                print(f"✅ Successfully archived: {title} -> {category}/{filename}")
                
                # Update checkpoint
                completed_urls.add(url)
                save_checkpoint(completed_urls)
                
                # Random delay to mimic human reading and bypass rate limits
                delay = random.uniform(4.0, 10.0)
                print(f"Waiting {delay:.2f} seconds before next request...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")
                print("Skipping for now and moving to next...")
                time.sleep(5)
                
        # Close browser
        context.close()
        
    print("\nCrawling session complete.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="System Design Academy Offline Archiver")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--login', action='store_true', help='Launch browser manually to login and save session')
    group.add_argument('--archive', action='store_true', help='Download all system design articles using saved session')
    parser.add_argument('--visible', action='store_true', help='Run browser in windowed mode during archiving')
    
    args = parser.parse_args()
    
    # Pre-parse README
    url_mapping = parse_readme(README_PATH)
    if not url_mapping:
        print("Error: No URLs parsed from README.md.")
        sys.exit(1)
        
    if args.login:
        run_login_mode()
    elif args.archive:
        run_archive_mode(url_mapping, visible=args.visible)
        
        print("\nGenerating index dashboard...")
        dashboard_generator.generate_dashboard(url_mapping, ARCHIVE_DIR)
        
        print("\nCompiling ZIP archive...")
        zip_archive.zip_archive()
        
        print("\nAll tasks completed successfully!")
