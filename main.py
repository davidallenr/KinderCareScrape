import requests
import os
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
from datetime import datetime
from time import sleep
from decouple import config


# These values are stored in the .env that you must create
WEBDRIVER_PATH = config("WEBDRIVER_PATH")
LOGIN_URL = config("LOGIN_URL")
USERNAME = config("ACCOUNT_USERNAME")
PASSWORD = config("PASSWORD")
WAIT_TIME = config("WAIT_TIME", default=0)
CHILDS_NAME = config("CHILDS_NAME")
HEADLESS = config("HEADLESS", default=False)
CORE_COUNT = config("CORE_COUNT", default = 1)  ## Set this to the physical core count on your cpu
MAX_WORKER = 2 * int(CORE_COUNT) + 1
LAST_DATE_FILENAME = "last_date.txt"

def retrieve_media_from_container_of_links(container_of_links_and_path):
    href = container_of_links_and_path['href']
    path = container_of_links_and_path['path']

    # If that file does NOT exist then retrieve
    try:
        if not os.path.exists(path):
            response = requests.get(href)
            with open(path, 'wb') as f:
                f.write(response.content)
    except requests.exceptions.HTTPError:
        print("Unable to retrieve file:" + path)

def concurrently_retrieve_media_from_container_of_links(container_of_links_and_path):
    with tqdm(total=len(container_of_links_and_path), desc='Download Progress') as pbar:
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKER) as executor:
            for _ in executor.map(retrieve_media_from_container_of_links, container_of_links_and_path, timeout=60):
                pbar.update()


# Read the last date from the file
def read_last_date():
    if os.path.exists(LAST_DATE_FILENAME):
        with open(LAST_DATE_FILENAME, "r") as f:
            return f.read()
    return None

# Write the last date to the file
def write_last_date(last_date):
    with open(LAST_DATE_FILENAME, "w") as f:
        f.write(last_date)

def add_links_and_path_to_containers(list_of_links, driver, image_container, video_container):
    item_count = 1
    last_date = read_last_date()
    count = 0
    for link in list_of_links:
        # Get the date from the TD element related to the object
        webdate = driver.find_element(
            By.XPATH, "//*/table/tbody/tr[" + str(item_count) + "]/td[2]"
        ).text.replace("/", "-")
    
        date_obj = datetime.strptime(webdate, '%m-%d-%y')   
        date = str(date_obj.date())
    
        # Increment the count if the date is the same as the last item
        if date == last_date:
            count += 1
        else:
            count = 0
            last_date = date
            write_last_date(last_date)

        if link.get_attribute("title") == "Download Image":
            image_container.append({
                "href": link.get_attribute("href"),
                "path": "img/" + date + "_" + CHILDS_NAME + "_" + str(count) + ".jpg"
            })

        if link.get_attribute("title") == "Download Video":
            video_container.append({
                "href": link.get_attribute("href"),
                "path": "mov/" + date + "_" + CHILDS_NAME + "_" + str(count) + ".mov"
            })

        item_count += 1

def login(driver):
    elem_user_login = driver.find_element(By.NAME, "user[login]")
    elem_user_password = driver.find_element(By.NAME, "user[password]")
    elem_user_login.clear()
    elem_user_login.send_keys(USERNAME)
    elem_user_password.clear()
    elem_user_password.send_keys(PASSWORD)
    elem_user_password.send_keys(Keys.RETURN)

def return_last_page(driver):
    div = driver.find_element(By.XPATH, "//*[@class='pagination']/li[last()]/a")
    temp_last_page_arr = div.get_attribute("href").split("=")
    last_page = temp_last_page_arr[1]

    return int(last_page)

def main():
    chrome_options = Options()

    if HEADLESS:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(WEBDRIVER_PATH, options=chrome_options)
    driver.implicitly_wait(WAIT_TIME)

    driver.get(LOGIN_URL)

    assert "KinderCare" in driver.title

    # Find the username and password elements
    # Fill out username and password then send the return key
    # LOGIN SECTION
    print("Logging into kindercare")
    login(driver)

    # wait for the page to load
    sleep(.25)

    # Close popup window
    driver.find_element(By.CLASS_NAME, "contacts-close-button").click()

    # Navigate to Entries
    sleep(.25)
    print("Navigating to correct page to begin link scraping")
    driver.find_element(By.LINK_TEXT, "Entries").click()

    current_page = 1
    last_page = return_last_page(driver)

    image_container = []
    video_container = []

    for current_page in tqdm(range(1, last_page), desc='Scraping Progress'):
        # Code for scraping the links from the website goes here
        try:
            next_found_on_page = driver.find_element(By.XPATH, "//*[@class='pagination']/li/a[@rel='next']") 
            if next_found_on_page is not None:
                next_found_on_page.click()
                # print("Scraping links from page: " + str(current_page) + " of " + str(last_page) + "Progress: " + str(current_page/last_page * 100) + "%")
                # Store all image and video links
                list_of_images = driver.find_elements(By.XPATH, "//*[@title='Download Image' or @title='Download Video']")
                
                add_links_and_path_to_containers(list_of_images, driver, image_container, video_container)

                current_page += 1
        except:
            print("Unable to find next button on page: " + str(current_page))
            break

    print("Beginning video retrieval")
    concurrently_retrieve_media_from_container_of_links(video_container)
    print("Beginning image retrieval")
    concurrently_retrieve_media_from_container_of_links(image_container)
    
    sleep(1)
    driver.quit()


if __name__ == "__main__":
    main()
