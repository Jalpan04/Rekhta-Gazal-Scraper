import time
import csv
import sys
import os
import re
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- RICH UI IMPORTS ---
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.theme import Theme

# --- UI SETUP ---
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "poet": "magenta"
})
console = Console(theme=custom_theme)

# --- CONFIGURATION ---
BASE_URL = "https://www.rekhta.org"
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.rekhta.org/',
}

# --- ROBUST SESSION (PREVENTS CONNECTION DROPS) ---
session = requests.Session()
# Retry up to 5 times if the server kicks us out
retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
session.headers.update(REQUEST_HEADERS)

# --- UTILITY FUNCTIONS ---

def clean_text(text):
    text = re.sub(r'\s+', ' ', text.strip())
    return text.replace('&nbsp;', ' ')

def is_hindi(text):
    return bool(re.search(r'[\u0900-\u097F]', text))

def get_poet_slug(user_input):
    # Simply lowercase and hyphenate
    return re.sub(r'\s+', '-', user_input.strip().lower())

# --- PHASE 1: LINK COLLECTION (SELENIUM) ---

def scrape_links_phase(poet_slug):
    url = f"https://www.rekhta.org/poets/{poet_slug}/ghazals?lang=hi"
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3')
    
    console.print(Panel(f"Target URL: [link]{url}[/link]", title="[bold cyan]Phase 1: Link Discovery[/]", border_style="cyan"))

    all_links = set()
    
    with console.status("[bold cyan]Launching Hidden Browser & Scrolling...", spinner="dots") as status:
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(3)
            
            last_height = driver.execute_script("return document.body.scrollHeight")
            no_change_count = 0
            
            while True:
                # Scroll to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Extract links dynamically from current page state
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                anchors = soup.find_all('a', href=True)
                
                for a in anchors:
                    href = a['href']
                    if '/ghazals/' in href:
                        # Exclude media icons/buttons
                        css_classes = a.get('class', [])
                        if any(x in css_classes for x in ['rico-audio', 'rico-youtube', 'favorite', 'rico-favorite']):
                            continue
                        
                        full_link = href if href.startswith('http') else BASE_URL + href
                        
                        # Ensure Hindi param
                        if '?lang=hi' not in full_link:
                            sep = '&' if '?' in full_link else '?'
                            full_link += f"{sep}lang=hi"
                        
                        # Filter junk/short links
                        if len(full_link) > 40:
                            if full_link not in all_links:
                                all_links.add(full_link)

                # Update status spinner
                status.update(f"[bold cyan]Scrolling... Found [bold magenta]{len(all_links)}[/] unique poems so far.")

                # Check if we hit bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        break
                else:
                    no_change_count = 0
                
                last_height = new_height
                if len(all_links) > 3000: break # Safety limit
                    
        except Exception as e:
            console.print(f"[error]Selenium Error: {e}[/]")
        finally:
            if driver: driver.quit()
            
    sorted_links = sorted(list(all_links))
    console.print(f"[success]✔ Found {len(sorted_links)} unique ghazals.[/]\n")
    return sorted_links

# --- PHASE 2: CONTENT EXTRACTION ---

def scrape_ghazal_content(url):
    try:
        # Uses the robust 'session' with retries
        response = session.get(url, timeout=15)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strict Paragraph Selection (Fixes fragmentation)
        verses = []
        content_lines = soup.select('.c p')
        
        for p in content_lines:
            text = clean_text(p.get_text())
            # Validation: Hindi + Length + Not Branding
            if is_hindi(text) and len(text) > 5 and "rekhta" not in text.lower():
                verses.append(text)
        
        # JOIN WITH NEWLINES (Fixes cell formatting)
        if verses:
            return "\n".join(verses)
        return None

    except Exception:
        return None

# --- MAIN ORCHESTRATOR ---

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold white]Rekhta Ghazal Scraper[/]\n[dim]Automated Research Tool v3.0[/]",
        style="bold magenta",
        subtitle="Full Working Script"
    ))
    
    user_input = console.input("[bold yellow]Enter Poet Name (e.g. 'Jaun Eliya'): [/]").strip()
    if not user_input: return

    poet_slug = get_poet_slug(user_input)
    
    # --- PHASE 1: GET LINKS ---
    links = scrape_links_phase(poet_slug)
    
    if not links:
        console.print("[error]❌ No links found. Exiting.[/]")
        sys.exit()

    # --- PHASE 2: DOWNLOAD CONTENT ---
    csv_filename = f"{poet_slug}_dataset.csv"
    console.print(Panel(f"Saving to: [bold green]{csv_filename}[/]", title="[bold cyan]Phase 2: Downloading Verses[/]", border_style="cyan"))

    success_count = 0
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Poet', 'Ghazal', 'URL'])
        
        # Rich Progress Bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(f"[cyan]Downloading...", total=len(links))
            
            for url in links:
                ghazal_text = scrape_ghazal_content(url)
                
                if ghazal_text:
                    writer.writerow([poet_slug, ghazal_text, url])
                    success_count += 1
                    progress.console.print(f"[dim]Saved:[/dim] {url.split('/')[-1][:30]}...", style="dim green")
                else:
                    progress.console.print(f"[dim red]Skipped (No Text):[/] {url.split('/')[-1][:30]}...")

                progress.advance(task)
                # Polite delay to prevent 10054 Connection Reset
                time.sleep(random.uniform(0.5, 1.5))

    console.print(Panel(
        f"🎉 [bold green]Job Complete![/]\n"
        f"📊 Total Links: {len(links)}\n"
        f"✅ Saved Poems: {success_count}\n"
        f"📂 File: [underline]{os.path.abspath(csv_filename)}[/]",
        title="Summary",
        border_style="green"
    ))

if __name__ == "__main__":
    main()