import sys
import os
from transifex_browser import get_driver_with_login, save_cookies, kill_browser
from visualizer import visualize_string_counts, visualize_user_contributions


def main():
    # Check for environment variables first (for CI/CD)
    username = os.environ.get("TRANSIFEX_USERNAME")
    password = os.environ.get("TRANSIFEX_PASSWORD")
    
    # Fall back to command line args if env vars not found
    if not username or not password:
        if len(sys.argv) != 3:
            print("Usage: python main.py <username> <password>")
            print("Or set TRANSIFEX_USERNAME and TRANSIFEX_PASSWORD environment variables")
            sys.exit(1)
        username = sys.argv[1]
        password = sys.argv[2]
    
    driver = get_driver_with_login(username, password)
    # Navigate to a specific URL if needed.
    driver.get("https://app.transifex.com/python-doc/python-newest/translate/#fa/$")
    # Allow time for the page to load.
    driver.implicitly_wait(10)
    # Update cookies after visiting the page.
    save_cookies(driver)
    visualize_user_contributions()
    visualize_string_counts()
    kill_browser()


if __name__ == "__main__":
    main()