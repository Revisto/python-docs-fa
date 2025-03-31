import json
from helium import start_chrome, click, write, kill_browser
from selenium.webdriver.common.by import By
from time import sleep

COOKIE_FILE = "transifex_cookies.json"
TRANSIFEX_URL = "https://www.transifex.com/dashboard/"


def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    return cookies


def is_logged_in(driver):
    # Check for an element that only exists when logged in.
    try:
        driver.find_element(By.CSS_SELECTOR, ".user-profile")
        return True
    except Exception:
        return False


def login_transifex(driver, username, password):
    driver.get("https://app.transifex.com/signin/")
    sleep(5)
    write(username, into="Email")
    write(password, into="Password")
    click("Log in")  # Adjust selector if needed.
    # Allow time for login and cookie propagation.
    driver.implicitly_wait(10)
    save_cookies(driver)
    return driver


def get_driver_with_login(username, password):
    driver = start_chrome(headless=False)  # FIXME
    driver.get(TRANSIFEX_URL)
    sleep(5)
    login_transifex(driver, username, password)
    return driver
