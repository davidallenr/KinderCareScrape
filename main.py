from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from decouple import config


# These values are stored in the .env that you must create
WEBDRIVER_PATH = config("WEBDRIVER_PATH")
LOGIN_URL = config("LOGIN_URL")
DEBUG = config("DEBUG", default=False)
USERNAME = config("USERNAME")
PASSWORD = config("PASSWORD")
WAIT_TIME = config("WAIT_TIME", default=0)


def main():

    driver = webdriver.Chrome(WEBDRIVER_PATH)
    driver.implicitly_wait(WAIT_TIME)

    if DEBUG:
        print("Driver loaded")

    driver.get(LOGIN_URL)

    if DEBUG:
        print("Getting URL: https://classroom.kindercare.com/login \n ")
        if driver.title != "KinderCare - Log In":
            print("Title does not Match")
        else:
            print("Title Matches:" + " KinderCare - Log In ")
    assert "KinderCare" in driver.title

    # Find the username and password elements
    # Fill out username and password then send the return key
    elem_user_login = driver.find_element_by_name("user[login]")
    elem_user_password = driver.find_element_by_name("user[password]")
    elem_user_login.clear()
    elem_user_login.send_keys(USERNAME)
    elem_user_password.clear()
    elem_user_password.send_keys(PASSWORD)
    elem_user_password.send_keys(Keys.RETURN)

    driver.find_element_by_class_name("contacts-close-button").click()

    sleep(20)


if __name__ == "__main__":
    main()
