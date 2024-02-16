import hashlib
import json
import os
import requests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
from decouple import config
import hashlib
import concurrent.futures


# Configuration and Setup
LOGIN_URL = config("LOGIN_URL")
USERNAME = config("ACCOUNT_USERNAME")
PASSWORD = config("PASSWORD")
CHILD_NAME = config("CHILD_NAME")
WEBDRIVER_PATH = config("WEBDRIVER_PATH")
HEADLESS = config("HEADLESS", default="False").lower() in ["true", "1", "t", "y", "yes"]
DOWNLOAD_DIR = "downloads"
HASH_RECORDS = "downloaded_files.json"
MAX_WORKERS = config("MAX_WORKERS", default=4, cast=int)


# Ensure the download directory and hash records file exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.path.exists(HASH_RECORDS):
    with open(HASH_RECORDS, "w") as f:
        json.dump({}, f)


def load_downloaded_hashes():
    with open(HASH_RECORDS, "r") as f:
        return json.load(f)


def save_downloaded_hash(file_name, file_hash):
    hashes = load_downloaded_hashes()
    hashes[file_name] = file_hash
    with open(HASH_RECORDS, "w") as f:
        json.dump(hashes, f, indent=4)


def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    if HEADLESS:
        chrome_options.add_argument("--headless")

    # Suppress DevTools logs
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Add this to suppress console errors
    chrome_options.add_argument("--log-level=3")

    service = Service(WEBDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def login(driver):
    print("Attempting to log in...")
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "user[login]"))
    )
    driver.find_element(By.NAME, "user[login]").send_keys(USERNAME)
    print("Sending username")
    driver.find_element(By.NAME, "user[password]").send_keys(PASSWORD)
    print("Sending password")
    driver.find_element(By.NAME, "user[password]").submit()

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "contacts-close-button"))
        ).click()
        print("Logged in, Popup closed.")
    except Exception as e:
        print(f"No popup to close or error closing popup: {e}")

    # Navigate to Entries
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Entries"))
        ).click()
        print("Navigated to Entries page.")
    except TimeoutException:
        print("Failed to navigate to Entries page.")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*/table/tbody/tr/td[2]"))
        )
        print("Successfully logged in and on the correct page.")
    except Exception as e:
        print(f"Unsuccessfully logged in and/or on the incorrect page.: {e}")


def get_media_links_and_dates(driver):
    media_links_and_dates = []
    elements = driver.find_elements(
        By.XPATH, "//*[@title='Download Image' or @title='Download Video']"
    )
    dates = driver.find_elements(By.XPATH, "//*/table/tbody/tr/td[2]")

    for i, element in enumerate(elements):
        date_text = dates[i].text.strip()
        try:
            date_object = datetime.strptime(date_text, "%m/%d/%y")
            formatted_date = date_object.strftime("%Y-%m-%d")
        except ValueError:
            formatted_date = datetime.now().strftime("%Y-%m-%d")

        # Determine file extension based on the element's title attribute
        title = element.get_attribute("title")
        if "Download Image" in title:
            file_extension = "jpg"
        elif "Download Video" in title:
            file_extension = "mp4"
        else:
            file_extension = "unknown"

        media_links_and_dates.append(
            {
                "url": element.get_attribute("href"),
                "date": formatted_date,
                "extension": file_extension,  # Include the determined file extension in the dict
            }
        )

    return media_links_and_dates


def download_media(media_info, pbar=None):
    url = media_info["url"]
    date = media_info["date"]
    file_extension = media_info["extension"]
    file_name = f"{date}_{CHILD_NAME}_{content_hash[:8]}.{file_extension}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content_hash = hashlib.md5(response.content).hexdigest()
            file_path = os.path.join(DOWNLOAD_DIR, file_name)

            downloaded_hashes = load_downloaded_hashes()
            if content_hash not in downloaded_hashes.values():
                with open(file_path, "wb") as file:
                    file.write(response.content)
                save_downloaded_hash(file_name, content_hash)
        else:
            if pbar:
                pbar.write(
                    f"Failed to download {url}: HTTP status {response.status_code}"
                )
    except Exception as e:
        if pbar:
            pbar.write(f"Failed to download {url}: {e}")


def return_last_page(driver):
    div = driver.find_element(By.XPATH, "//*[@class='pagination']/li[last()]/a")
    temp_last_page_arr = div.get_attribute("href").split("=")
    last_page = temp_last_page_arr[1]

    return int(last_page)


def concurrently_retrieve_media_from_container_of_links(all_media_info):
    with tqdm(total=len(all_media_info), desc="Download Progress") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(download_media, info, pbar) for info in all_media_info
            ]
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)


def get_most_recent_download_date():
    hashes = load_downloaded_hashes()
    dates = [
        datetime.strptime(info.split("_")[0], "%Y-%m-%d") for info in hashes.keys()
    ]
    return max(dates) if dates else None


def main():
    print("Script started.")
    driver = setup_driver()
    try:
        login(driver)

        most_recent_download_date = get_most_recent_download_date()
        buffer_date = (
            most_recent_download_date - timedelta(days=1)
            if most_recent_download_date
            else datetime.min
        )

        all_media_info = []
        total_pages = return_last_page(driver)
        actual_pages_navigated = 0

        with tqdm(desc="Navigating Pages", unit="page") as pbar:
            for page in range(1, total_pages + 1):
                page_media_info = get_media_links_and_dates(driver)
                # Filter out already downloaded or older items
                new_media_info = [
                    item
                    for item in page_media_info
                    if datetime.strptime(item["date"], "%Y-%m-%d") > buffer_date
                ]

                # If there are new items, extend all_media_info; otherwise, stop
                if new_media_info:
                    all_media_info.extend(new_media_info)
                    actual_pages_navigated += 1
                    pbar.update(1)  # Increment the progress bar
                else:
                    pbar.write(
                        f"All new media up to {buffer_date.strftime('%Y-%m-%d')} has been downloaded. No further pages will be navigated."
                    )
                    break  # Stop if no new media is found

                # Attempt to navigate to the next page if there's more to process
                if page < total_pages and new_media_info:
                    try:
                        pbar.write("Navigating to the next page...")
                        next_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//*[@class='pagination']/li/a[@rel='next']")
                            )
                        )
                        next_button.click()
                    except TimeoutException:
                        pbar.write(
                            "No more pages to scrape or next page button not found."
                        )
                        break

            pbar.total = actual_pages_navigated
            pbar.n = actual_pages_navigated
            pbar.refresh()

        print(f"Total pages navigated: {actual_pages_navigated}")

        if all_media_info:
            print(f"Starting download of {len(all_media_info)} items...")
            concurrently_retrieve_media_from_container_of_links(all_media_info)
        else:
            print("No new media information gathered to download.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print("Script finished.")


if __name__ == "__main__":
    main()
