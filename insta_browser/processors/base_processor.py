import selenium.common.exceptions as excp
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from insta_browser.db.browser_db import BrowserDB
from ..logger import Logger

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import json


class BaseProcessor:
    post_skipped_excluded = 0
    posts_count_to_like = 0
    feed_scrolled_down = 0
    post_already_liked = 0
    post_excluded = 0
    post_skipped = 0
    like_limit = 416
    progress = None
    post_liked = 0
    heart = None
    count = 0
    hour_like_limit = 150

    def __init__(self, db, br, lg):
        self.db: BrowserDB = db
        self.browser: WebDriver = br
        self.logger: Logger = lg

    def get_summary(self):
        return {'liked': self.post_liked,
                'skipped': self.post_skipped,
                'excluded': self.post_skipped_excluded,
                'already_liked': self.post_already_liked,
                'scrolled': self.feed_scrolled_down}

    @staticmethod
    def _get_feed_post_link(post: WebElement):
        """
        Get link to post from post web-element from feed
        :param post: WebElement
        :return:
        """
        try:
            post_link = post.find_element_by_css_selector('div:nth-child(3) div:nth-child(4) a')
        except excp.NoSuchElementException:
            post_link = post.find_element_by_css_selector('div:nth-child(3) div:nth-child(3) a')
        return post_link.get_attribute('href')

    @staticmethod
    def _get_feed_post_media(post: WebElement):
        """
        Get link to post from post web-element from feed
        :param post: WebElement
        :return: str
        """
        try:
            image = post.find_element_by_css_selector('div:nth-child(2) img')
            return image.get_attribute('src')
        except excp.NoSuchElementException:
            pass

        try:
            video = post.find_element_by_tag_name('video')
            return video.get_attribute('src')
        except excp.NoSuchElementException:
            pass

        return False

    def follow_user(self) -> bool:
        """
        Follow user if need and could
        :return: bool
        """
        if self.__do_i_need_to_follow_this_user() and self.__could_i_follow():
            try:
                follow_button = self.browser.find_element_by_css_selector('._iokts')
                follow_button.click()
                self.logger.log('NEED TO FOLLOW!')
                self.db.follows_increment()
                return True
            except excp.NoSuchElementException:
                self.logger.log('Cant find follow button.')

        return False

    def __could_i_follow(self) -> bool:
        """
        Check if i could to follow more
        :return: bool
        """
        counters = self.db.get_follow_limits_by_account()
        return counters['daily'] < 1001 and counters['hourly'] < 76

    def __do_i_need_to_follow_this_user(self) -> bool:
        """
        Check if i need to follow current user
        :return: bool
        """
        try:
            self.browser.find_element_by_css_selector('._jqf0k')
            return False
        except excp.NoSuchElementException:
            username = self.browser.find_element_by_css_selector('._2g7d5').text
            user_link = 'https://www.instagram.com/{}/?__a=1'.format(username)
            response = urlopen(user_link)
            data = json.loads(response.read().decode('utf-8'))
            followers = data['user']['followed_by']['count']
            following = data['user']['follows']['count']
            posts = data['user']['media']['count']
            return posts > 10 and following < 500 and followers < 1000

    # TODO: refactor this
    def get_like_limits(self, count=None):
        limits = self.db.get_like_limits_by_account()
        today_likes = limits[0]
        hours_left = limits[1]
        hour_likes_by_activity = (self.hour_like_limit * 24 - today_likes) // hours_left
        ll = None
        if self.hour_like_limit <= hour_likes_by_activity < self.hour_like_limit * 2:
            ll = hour_likes_by_activity
        elif hour_likes_by_activity >= self.hour_like_limit * 2:
            ll = self.hour_like_limit * 2
        elif hour_likes_by_activity < self.hour_like_limit:
            ll = hour_likes_by_activity
        self.count = count if 0 < count < ll else ll
        return self.count

    def set_auto_follow(self, flag: bool):
        """
        Enable or disable auto follow mode
        :param flag:
        :return:
        """
        self.auto_follow = flag
        return self
