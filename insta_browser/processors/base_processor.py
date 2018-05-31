import datetime
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
    auto_follow = False
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
        if self.__could_i_follow():
            # Second if, because we don't need to make http requests if user reaches follow limits
            if self.__do_i_need_to_follow_this_user():
                try:
                    follow_button = self.browser.find_element_by_css_selector('._5f5mN')
                    follow_button.click()
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
        self.browser.implicitly_wait(1)

        try:
            self.browser.find_element_by_css_selector('.qPANj')
            return False
        except excp.NoSuchElementException:
            username = self.browser.find_element_by_css_selector('.notranslate').text
            counters = self.__get_counters(username)
            if not counters:
                user_link = 'https://www.instagram.com/{}/?__a=1'.format(username)
                response = urlopen(user_link)
                data = json.loads(response.read().decode('utf-8'))
                counters['followers'] = data['user']['followed_by']['count']
                counters['following'] = data['user']['follows']['count']
                counters['posts'] = data['user']['media']['count']
                need_to_be_followed = counters['posts'] > 10 and counters['following'] < 500 and counters[
                    'followers'] < 1000
                if not need_to_be_followed:
                    self.db.store_user_counters(username, counters)
                return need_to_be_followed
            else:
                return False

    def __get_counters(self, login):
        counters = self.db.get_user_counters(login)
        today = datetime.date.today()
        updated_at = datetime.datetime.strptime(counters['updated_at'], '%Y-%m-%d')
        updated_at_date = datetime.date(year=updated_at.year, month=updated_at.month, day=updated_at.day)
        if (today - updated_at_date).days > 31:
            return {}
        return counters['counters']

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
