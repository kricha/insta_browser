# -*- coding: utf-8 -*-
from selenium import webdriver
import time
from .logger import Logger
from .configure import *
from .auth import *
from .insta_not_feed_util import *
from .insta_feed_util import *
import re


class Browser:
    login = ''
    summary = {}

    def __init__(self, debug=False, chrome=False, cookie_path=None, screen_shot_path=None, logger_file=None,
                 exclude=None):
        if chrome:
            self.browser = webdriver.Chrome()
        else:
            self.browser = set_headers(webdriver)
            self.browser.command_executor._commands['executePhantomScript'] = ('POST',
                                                                               '/session/$sessionId/phantom/execute')
            resource_requested_logic(self.browser)
        self.cookie_path = cookie_path
        self.exclude = exclude or []
        self.chrome = chrome
        self.logger = Logger(logger_file, screen_shot_path, debug)

    def auth(self, login, password):
        br = self.browser
        self.get("https://www.instagram.com/accounts/login/")
        time.sleep(1)
        if not auth_with_cookies(br, self.logger, login, self.cookie_path):
            auth_with_credentials(br, self.logger, login, password, self.cookie_path)
        self.login = login

    def get(self, url):
        self.browser.get(url)
        time.sleep(.5)
        self.logger.log(u'Open ' + self.browser.current_url)
        return self

    def close_all(self):
        self.logger.save_screen_shot(self.browser, 'exit.png')
        self.browser.close()
        self.browser.quit()
        self.logger.log(u'Browser process was ended')
        self.logger.log(u'')

    def get_summary(self):
        log = 'Feed scrolled down {scrolled} times, liked {liked} posts, skipped {skipped} posts,' \
              ' skipped excluded {excluded} posts'. \
            format(**self.summary)
        self.logger.log_to_file(log)
        return log

    def process_user(self, username, count=None):
        br = self.browser
        self.get("https://www.instagram.com/{}".format(username))
        self.logger.log("Start liking @{} profile {} posts".format(username, count))
        processor = NotFeedProcessor(br, self.logger)
        processor.like_user_profile(count)
        self.summary = processor.get_summary()

    def process_location(self, location, count=None):
        br = self.browser
        processed_location = re.sub('^(/?explore/locations/|/|/?locations/)', '', location)
        self.get("https://www.instagram.com/explore/locations/{}".format(processed_location))
        self.logger.log("Start liking top posts from {} location".format(processed_location))
        processor = NotFeedProcessor(br, self.logger)
        processor.like_top()
        processor.like_latest(count)
        self.summary = processor.get_summary()

    def process_tag(self, tag, count=None):
        br = self.browser
        self.get("https://www.instagram.com/explore/tags/{}".format(tag))
        self.logger.log("Start liking top posts from {} location".format(tag))
        processor = NotFeedProcessor(br, self.logger)
        processor.like_top()
        processor.like_latest(count)
        self.summary = processor.get_summary()

    def process_feed(self, count=None):
        br = self.browser
        self.get("https://instagram.com/")
        time.sleep(.5)
        processor = FeedProcessor(br, self.logger)
        processor.scroll_feed_to_last_not_liked_posts()
        processor.process(self.exclude, self.login, count)
        self.summary = processor.get_summary()
