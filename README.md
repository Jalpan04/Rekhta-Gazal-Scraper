# Rekhta Ghazal Scraper

## Overview

This tool is a specialized web scraper designed to collect the complete collection of Ghazals for any given poet from Rekhta.org. It is engineered for research and data science purposes, creating a clean, structured dataset suitable for Natural Language Processing (NLP) or authorship attribution tasks.

The tool operates in two phases:

1. **Link Discovery** — Uses Selenium to simulate a user scrolling through the poet's profile page to capture all available Ghazal URLs (handling infinite scrolling).
2. **Content Extraction** — Uses a robust HTTP session to visit each link, extract the Hindi verses, and format them into a unified text block.

---

## Features

- **Infinite Scroll Handling** — Automatically scrolls through dynamic pages to ensure 100% of links are captured.
- **Anti-Ban Mechanisms** — Implements session keep-alive, automatic retries, and randomized delays to prevent server disconnections (ConnectionResetError).
- **Clean Formatting** — Aggregates all verses of a single Ghazal into one cell, preserving line breaks. This prevents data fragmentation where single lines appear as separate rows.
- **Rich Terminal UI** — Provides real-time status updates, spinner animations, and progress bars.

---

## Prerequisites

- **Python** — Version 3.8 or higher
- **Google Chrome** — The script requires a standard installation of the Google Chrome browser to perform the Selenium automation

---

## Installation

### Step 1: Clone or Download the Repository

Ensure the script (`rekhta_scraper.py`) and requirements file are in the same directory.

### Step 2: Install Dependencies

Open your terminal or command prompt and run the following command:

```bash
pip install -r requirements.txt
```

---

## Usage

### Step 1: Run the Script

Execute the Python script from your terminal:

```bash
python rekhta_scraper.py
```

### Step 2: Enter Poet Name

When prompted, enter the name of the poet as it appears in the URL or in plain English.

**Examples:**
- `Jaun Eliya`
- `Ada Jafarey`
- `Mirza Ghalib`

### Step 3: Process

- **Phase 1:** A hidden Chrome browser will launch to scan the profile. Wait for the "Phase 1 Complete" message.
- **Phase 2:** The script will download the verses. A progress bar will indicate the status of each file.

---

## Output Data Structure

The script generates a CSV file named `[poet-slug]_dataset.csv` (e.g., `ada-jafarey_dataset.csv`).

The file contains the following columns:

| Column | Description |
|--------|-------------|
| **Poet** | The standardized slug of the poet (e.g., `ada-jafarey`) |
| **Ghazal** | The full text of the poem. Verses are separated by newline characters (`\n`) |
| **URL** | The source URL from where the data was scraped |

---

## Troubleshooting

### Connection Reset / Network Errors

If you see "Connection aborted" or "ConnectionResetError", the server is blocking rapid requests. The script is designed to handle this automatically:

- It will retry the failed request up to 5 times
- It waits randomly between 0.5 to 1.5 seconds between downloads

**Action:** No action needed; let the script finish retrying.

### Selenium / Chrome Errors

If the script fails immediately upon launch with a WebDriver error:

- Ensure Google Chrome is installed on your system
- Ensure your `selenium` library is up to date: `pip install --upgrade selenium`

### Zero Links Found

If Phase 1 completes but finds 0 links:

- Verify the spelling of the poet's name
- Check your internet connection
- Visit Rekhta.org manually to ensure the poet actually has a "Ghazals" section (some poets only have Nazms)

---

## Disclaimer

This tool is intended for educational and research purposes only. Please respect the robots.txt policy of the target website and do not overload their servers with excessive request rates.

---

## License

This project is provided as-is for educational and research purposes.
