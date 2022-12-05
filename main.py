from selenium import webdriver
from selenium.webdriver.chrome import options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import urllib.request
import os
from time import sleep
from decouple import config


# These values are stored in the .env that you must create
WEBDRIVER_PATH = config("WEBDRIVER_PATH")
LOGIN_URL = config("LOGIN_URL")
DEBUG = config("DEBUG", default=True)
USERNAME = config("USERNAME")
PASSWORD = config("PASSWORD")
WAIT_TIME = config("WAIT_TIME", default=0)
CHILDS_NAME = config("CHILDS_NAME")
HEADLESS = config("HEADLESS", default=True)


def main():

    chrome_options = Options()

    if HEADLESS:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(WEBDRIVER_PATH, options=chrome_options)
    driver.implicitly_wait(WAIT_TIME)

    if DEBUG:
        print("Driver loaded")

    driver.get(LOGIN_URL)

    if DEBUG:
        print("Getting URL: https://classroom.kindercare.com/login")
        if driver.title != "KinderCare - Log In":
            print("Title does not Match")
        else:
            print("Title Matches:" + " KinderCare - Log In ")
    assert "KinderCare" in driver.title

    # Find the username and password elements
    # Fill out username and password then send the return key
    # LOGIN SECTION
    elem_user_login = driver.find_element(By.NAME, "user[login]")
    elem_user_password = driver.find_element(By.NAME, "user[password]")
    elem_user_login.clear()
    elem_user_login.send_keys(USERNAME)
    elem_user_password.clear()
    elem_user_password.send_keys(PASSWORD)
    elem_user_password.send_keys(Keys.RETURN)

    # Close popup window
    driver.find_element(By.CLASS_NAME, "contacts-close-button").click()
    if DEBUG:
        print("Closing PopUp")

    # Navigate to Entries
    sleep(1)
    driver.find_element(By.LINK_TEXT, "Entries").click()
    if DEBUG:
        print("Navigating to Entries")

    # div = driver.find_element(By.ID, "paginator")
    div = driver.find_element(By.XPATH, "//*[@class='pagination']/li[last()]/a")
    if DEBUG:
        print("Last Pagination Found: " + div.get_attribute("href"))

    temp_last_page_arr = div.get_attribute("href").split("=")
    last_page = temp_last_page_arr[1]
    current_page = int(last_page)
    if DEBUG:
        print("Last Page: " + last_page)

    # Navigate to Last page
    driver.find_element(By.XPATH, "//*[@class='pagination']/li[last()]/a").click()

    while current_page > 0:
        # Store all image and video links
        objects = driver.find_elements(By.XPATH, "//*[@title='Download Image' or @title='Download Video']")
        #images = driver.find_elements(By.XPATH, "//*[@title='Download Image']")
        #videos = driver.find_elements(By.XPATH, "//*[@title='Download Video']")
        
        i = 1

        for obj in objects:
            sleep(0.2)
            # Get the date from the TD element related to the object
            webdate = driver.find_element(
                By.XPATH, "//*/table/tbody/tr[" + str(i) + "]/td[2]"
            ).text.replace("/", "-")
        
            date_obj = datetime.strptime(webdate, '%m-%d-%y')   
            date = str(date_obj.date())
        
            # If that file does NOT exist then grab photo
            try:
                if obj.get_attribute("title") == "Download Image":
                    if not os.path.exists(
                        "img/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(i) + ".jpg"
                    ):
                        urllib.request.urlretrieve(
                            obj.get_attribute("href"),
                            "img/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(i) + ".jpg",
                        )
            except urllib.error.HTTPError:
                print("Error")
            
            try:
                if obj.get_attribute("title") == "Download Video":
                    if not os.path.exists(
                        "img/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(i) + ".mov"
                    ):
                        urllib.request.urlretrieve(
                            obj.get_attribute("href"),
                            "img/" + date + "_" + str(current_page) + "_" + CHILDS_NAME + "_" + str(i) + ".mov",
                        )
        
            except urllib.error.HTTPError:
                print("Error")
            i += 1

        #for img in images:
        #    sleep(0.2)
        #    i = 1 
        #    # Get the date from the TD element related to the picture
        #    webdate = driver.find_element(
        #        By.XPATH, "//*/table/tbody/tr[" + str(i) + "]/td[2]"
        #    ).text.replace("/", "-")
        #
        #    date = str(datetime.strptime(webdate, '%m-%d-%y'))
        #
        #    try:
        #    # If that file does NOT exist then grab photo
        #        if not os.path.exists(
        #            "img/" + date + "_" + CHILDS_NAME + "_" + str(i) + ".jpg"
        #        ):
        #            urllib.request.urlretrieve(
        #                img.get_attribute("href"),
        #                "img/" + date + "_" + CHILDS_NAME + "_" + str(i) + ".jpg",
        #            )
        #    except urllib.error.HTTPError:
        #        print("Error")
        #    i += 1
        #
        #for vid in videos:
        #    sleep(0.2)
        #    i = 1 
        #    # Get the date from the TD element related to the video
        #    date = driver.find_element(
        #        By.XPATH, "//*/table/tbody/tr[" + str(i) + "]/td[2]"
        #    ).text.replace("/", "-")
        #
        #    date = str(datetime.strptime(webdate, '%m-%d-%y'))
        #
        #    try:
        #    # If that file does NOT exist then grab photo
        #        if not os.path.exists(
        #            "img/" + date + "_" + CHILDS_NAME + "_" + str(i) + ".mov"
        #        ):
        #            urllib.request.urlretrieve(
        #                vid.get_attribute("href"),
        #                "img/" + date + "_" + CHILDS_NAME + "_" + str(i) + ".mov",
        #            )
        #    except urllib.error.HTTPError:
        #        print("Error")
        #    i += 1

        # Navigate (1) page back until current page = (0)
        if current_page != 1:
            driver.find_element(
                By.XPATH, "//*[@class='pagination']/li/a[@rel='prev']"
            ).click()
        sleep(0.5)
        current_page -= 1

        if DEBUG:
            print("Current Page: " + str(current_page))

    sleep(1)
    driver.quit()


if __name__ == "__main__":
    main()
