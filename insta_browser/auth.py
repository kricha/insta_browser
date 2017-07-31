import pickle
import time
import tempfile
import os
import selenium.common.exceptions as excp


def auth_with_cookies(browser, logger, login, cookie_path=tempfile.gettempdir()):
    """
    Authenticate to instagram.com with cookies
    :param browser: WebDriver
    :param logger:
    :param login:
    :param cookie_path:
    :return:
    """
    logger.save_screen_shot(browser, 'login.png')
    try:
        logger.log('Trying to auth with cookies.')
        cookies = pickle.load(open(os.path.join(cookie_path, login+'.pkl'), "rb"))
        for cookie in cookies:
            browser.add_cookie(cookie)
        browser.refresh()
        if check_if_user_authenticated(browser):
            logger.log("Successful authorization with cookies.")
            return True
    except:
        pass

    logger.log("Unsuccessful authorization with cookies.")
    return False


def auth_with_credentials(browser, logger, login, password, cookie_path=tempfile.gettempdir()):
    logger.log('Trying to auth with credentials.')
    login_field = browser.find_element_by_name("username")
    login_field.clear()
    logger.log("--->AuthWithCreds: filling username.")
    login_field.send_keys(login)
    password_field = browser.find_element_by_name("password")
    password_field.clear()
    logger.log("--->AuthWithCreds: filling password.")
    password_field.send_keys(password)
    submit = browser.find_element_by_css_selector("form button")
    logger.log("--->AuthWithCreds: submitting login form.")
    submit.submit()
    time.sleep(3)
    logger.log("--->AuthWithCreds: saving cookies.")
    pickle.dump([browser.get_cookie('sessionid')], open(os.path.join(cookie_path, login + '.pkl'), "wb"))
    if check_if_user_authenticated(browser):
        logger.log("Successful authorization with credentials.")
        return True
    logger.log("Unsuccessful authorization with credentials.")
    return False


def check_if_user_authenticated(browser):
    try:
        browser.find_element_by_css_selector(".coreSpriteDesktopNavProfile")
        return True
    except excp.NoSuchElementException:
        return False
