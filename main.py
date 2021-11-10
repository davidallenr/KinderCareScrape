from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
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


def main():

    driver = webdriver.Chrome(WEBDRIVER_PATH)
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
        # Store all image links
        images = driver.find_elements(By.XPATH, "//*[@title='Download Image']")

        i = 0
        for img in images:
            sleep(0.5)
            if not os.path.exists(
                "img/" + CHILDS_NAME + "_" + str(current_page) + "_" + str(i) + ".jpg"
            ):
                urllib.request.urlretrieve(
                    img.get_attribute("href"),
                    "img/"
                    + CHILDS_NAME
                    + "_"
                    + str(current_page)
                    + "_"
                    + str(i)
                    + ".jpg",
                )
            i += 1

        # Navigate (1) page back until current page = (0)
        if current_page != 1:
            driver.find_element(
                By.XPATH, "//*[@class='pagination']/li/a[@rel='prev']"
            ).click()
        sleep(1)
        current_page -= 1

        if DEBUG:
            print("Current Page: " + str(current_page))

    sleep(20)
    driver.quit()


if __name__ == "__main__":
    main()
