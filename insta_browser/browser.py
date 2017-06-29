# -*- coding: utf-8 -*-
from selenium import webdriver
import selenium.common.exceptions as excp
import time
from .logger import Logger
from .configure import *
from .auth import *
from .insta_not_feed_util import *
import re


class Browser:
    login = ''
    liked = 0
    skipped = 0
    feed_scrolled_down = 0
    skipped_excluded = 0
    feed_posts_per_page = 12
    posts_count_to_like = None
    like_limit = 500

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
        self.logger.log(u'Open ' + self.browser.current_url)
        return self

    def close_all(self):
        self.logger.save_screen_shot(self.browser, 'exit.png')
        self.browser.close()
        self.browser.quit()
        self.logger.log(u'Browser process was ended')
        self.logger.log(u'')

    def is_last_post_in_feed_not_liked(self):
        try:
            self.browser.find_element_by_css_selector('article:last-child .coreSpriteHeartOpen')
            return True
        except excp.NoSuchElementException:
            return False

    def scroll_feed_to_last_not_liked_posts(self):
        while self.is_last_post_in_feed_not_liked():
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.feed_scrolled_down += 1

    def scroll_feed_by_posts_count(self, posts_count):
        self.posts_count_to_like = posts_count
        times_to_scroll = posts_count / 12
        while times_to_scroll > 0:
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.feed_scrolled_down += 1
            times_to_scroll -= 1

    def like_found_posts(self):
        br = self.browser
        articles = br.find_elements_by_tag_name('article')
        posts = self.preprocess_posts_from_feed(articles)
        del articles
        for post in posts:
            webdriver.ActionChains(br).move_to_element(post['heart']).click().perform()
            time.sleep(.5)
            self.liked += 1
            self.logger.log('\t♥️  @{} post {}'.format(post['author'], post['link']))

    def preprocess_posts_from_feed(self, posts):
        posts_to_perform = []
        posts_count = self.posts_count_to_like or len(posts)
        i = 1
        for post in posts:
            if i > posts_count:
                break
            heart = post.find_element_by_css_selector('div:nth-child(3) section a:first-child')
            author = post.find_element_by_css_selector('div:first-child .notranslate').text
            heart_classes = heart.find_element_by_css_selector('span').get_attribute("class")
            if 'coreSpriteHeartOpen' in heart_classes and author != self.login:
                if author in self.exclude:
                    self.skipped_excluded += 1
                else:
                    post_link = self.get_feed_post_link(post)
                    posts_to_perform.append({'heart': heart, 'author': author, 'link': post_link})
            else:
                self.skipped += 1
            i += 1

        return posts_to_perform

    def get_summary(self):
        log = 'Feed scrolled down {} times, liked {} posts, skipped {} posts, skipped excluded {} posts'. \
            format(self.feed_scrolled_down, self.liked, self.skipped, self.skipped_excluded)
        self.logger.log_to_file(log)
        return log

    @staticmethod
    def get_feed_post_link(post):
        """
        Get link to post from post web-element from feed
        :param post:
        :return:
        """
        try:
            post_link = post.find_element_by_css_selector('div:nth-child(3) div:nth-child(4) a')
        except excp.NoSuchElementException:
            post_link = post.find_element_by_css_selector('div:nth-child(3) div:nth-child(3) a')
        return post_link.get_attribute('href')

    def process_user(self, username, count=None):
        br = self.browser
        br.get("https://www.instagram.com/{}".format(username))
        time.sleep(.5)
        if count:
            posts_count = count
        else:
            posts_from_page = br.find_element_by_css_selector("article header ul li span").text
            tmp_count = int(re.match('\d+', posts_from_page).group(0))
            posts_count = self.like_limit if tmp_count > self.like_limit else tmp_count
        self.logger.log("Start liking @{} profile {} posts".format(username, posts_count))
        processor = NotFeedProcessor(br, self.logger)
        result = processor.like_user_profile(posts_count)
        self.liked = result['liked']
        self.skipped = result['skipped']

    def process_location(self, location, count=None):
        br = self.browser
        processed_location = re.sub('^(/?explore/locations/|/|/?locations/)', '', location)
        br.get("https://www.instagram.com/explore/locations/{}".format(processed_location))
        time.sleep(.5)
        posts_count = self.__get_posts_count(count)
        self.logger.log("Start liking top posts from {} location".format(processed_location))
        processor = NotFeedProcessor(br, self.logger)
        processor.like_top()
        result = processor.like_latest(posts_count)
        self.liked = result['liked']
        self.skipped = result['skipped']

    def process_tag(self, tag, count=None):
        br = self.browser
        br.get("https://www.instagram.com/explore/tags/{}".format(tag))
        time.sleep(.5)
        posts_count = self.__get_posts_count(count)
        self.logger.log("Start liking top posts from {} location".format(tag))
        processor = NotFeedProcessor(br, self.logger)
        processor.like_top()
        result = processor.like_latest(posts_count)
        self.liked = result['liked']
        self.skipped = result['skipped']

    def __get_posts_count(self, count):
        if count:
            return self.like_limit - 9 if count > self.like_limit else count
        else:
            return self.like_limit - 9
