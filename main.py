import urllib.request
import os
from selenium import webdriver
from selenium.webdriver.chrome import options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
HEADLESS = config("HEADLESS", default=True)

def retrieve_media_from_container_of_links(container_of_links_and_path):
    print("Beginning Retrieval of " + str(len(container_of_links_and_path)) + " files...")
    missing_files = 0
    for obj in container_of_links_and_path:
        href = obj['href']
        path = obj['path']

        # If that file does NOT exist then retrieve
        try:
            if not os.path.exists(path):
                urllib.request.urlretrieve(href,path)
        except urllib.error.HTTPError:
            print("Unable to retrieve file:" + path)
            missing_files += 1
    print("Retrieval of " + str(len(container_of_links_and_path) - missing_files) + " files complete")


def add_links_and_path_to_containers(list_of_links, driver, current_page, image_container, video_container):   
    item_count = 1
    for link in list_of_links:
        # Get the date from the TD element related to the object
        webdate = driver.find_element(
            By.XPATH, "//*/table/tbody/tr[" + str(item_count) + "]/td[2]"
        ).text.replace("/", "-")
    
        date_obj = datetime.strptime(webdate, '%m-%d-%y')   
        date = str(date_obj.date())
    
        if link.get_attribute("title") == "Download Image":
            image_container.append({
                "href": link.get_attribute("href"),
                "path": "img/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(item_count) + ".jpg"
            })

        if link.get_attribute("title") == "Download Video":
            video_container.append({
                "href": link.get_attribute("href"),
                "path": "mov/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(item_count) + ".mov"
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

    # Close popup window
    driver.find_element(By.CLASS_NAME, "contacts-close-button").click()

    # Navigate to Entries
    sleep(.25)
    print("Navigating to correct page to begin link scraping")
    driver.find_element(By.LINK_TEXT, "Entries").click()

    current_page = return_last_page(driver)

    # Navigate to Last page
    driver.find_element(By.XPATH, "//*[@class='pagination']/li[last()]/a").click()

    image_container = []
    video_container = []

    while current_page > 0:
        print("Scraping links from page: " + str(current_page))
        # Store all image and video links
        list_of_images = driver.find_elements(By.XPATH, "//*[@title='Download Image' or @title='Download Video']")
        
        add_links_and_path_to_containers(list_of_images, driver, current_page, image_container, video_container)
        
        # Navigate (1) page back until current page = (0)
        if current_page != 1:
            driver.find_element(
                By.XPATH, "//*[@class='pagination']/li/a[@rel='prev']"
            ).click()

        current_page -= 1


    retrieve_media_from_container_of_links(video_container)

    retrieve_media_from_container_of_links(image_container)
    
    sleep(1)
    driver.quit()


if __name__ == "__main__":
    main()
