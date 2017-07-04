import tqdm
import time
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as excp
from .base.processor import BaseProcessor

NOT_LIKED_CSS_CLASS = '.coreSpriteHeartOpen'


class FeedProcessor(BaseProcessor):
    def __init__(self, browser, logger):
        self.browser = browser
        self.logger = logger

    def scroll_feed_to_last_not_liked_posts(self):
        """
        Scroll down feed to last not liked post

        :return:
        """
        while self.__is_last_post_in_feed_not_liked():
            self.__scroll_down()

    def __scroll_down(self):
        """
        Moving to footer and waiting for querying new posts

        :return:
        """
        footer = self.browser.find_element_by_tag_name('footer')
        ActionChains(self.browser).move_to_element(footer).perform()
        self.logger.log_to_file('Scrolled down.')
        self.feed_scrolled_down += 1
        time.sleep(1)

    def __is_last_post_in_feed_not_liked(self):
        """
        Check last five posts if they are not liked

        :return: False if one of five posts wasn't liked, True if all five were liked
        """
        posts = self.browser.find_elements_by_tag_name('article')
        try:
            for i in range(5):
                post = posts.pop()
                post.find_element_by_css_selector(NOT_LIKED_CSS_CLASS)
            del posts
            return True
        except excp.NoSuchElementException:
            return False

    def process(self, exclude, login, count):
        """
        liking pre-processed posts. Moving to each post with ActionChains

        :param exclude:
        :param login:
        :param count:
        :return:
        """
        br = self.browser
        self.count = count
        posts = br.find_elements_by_tag_name('article')
        analyzed_posts = self.pre_process_posts(posts, exclude, login)
        self.logger.log('Start liking posts.')
        print(analyzed_posts)
        progress = tqdm.tqdm(analyzed_posts)
        for post in progress:
            ActionChains(br).move_to_element(post.get("heart"))
            log = "---> liked @{} post {}".format(post.get('author'), post.get('link'))
            self.post_liked += 1
            self.logger.log_to_file(log)
            time.sleep(.5)

    def pre_process_posts(self, posts, exclude, login):
        """
        Preparing posts from feed for liking (remove from list excluded, already liked and own posts)
        Getting from DOM heart link, author name and post link

        :param posts:
        :param exclude:
        :param login:
        :return: Reversed post list for starting process from the bottom
        :rtype: list
        """
        self.logger.log('Pre-processing posts.')
        result_posts = list()
        pr = tqdm.tqdm(posts)
        while posts:
            if 0 < len(result_posts) == self.count:
                pr.update(len(posts))
                break
            post = posts.pop()
            heart = post.find_element_by_css_selector('div:nth-child(3) section a:first-child')
            author = post.find_element_by_css_selector('div:first-child .notranslate').text
            heart_classes = heart.find_element_by_css_selector('span').get_attribute("class")

            is_not_liked = 'coreSpriteHeartOpen' in heart_classes
            is_mine = author == login
            need_to_exclude = author in exclude

            if is_not_liked and is_mine:
                self.post_skipped += 1
            elif is_not_liked and need_to_exclude:
                self.post_skipped_excluded += 1
            else:
                post_link = self.__get_feed_post_link(post)
                tmp_post = {"heart": heart, "author": author, "link": post_link}
                result_posts.append(tmp_post)

            pr.update()
        return result_posts

    @staticmethod
    def __get_feed_post_link(post):
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

    @staticmethod
    def __get_feed_post_media(post):  # TODO: refactor searching image
        """
        Get link to post from post web-element from feed

        :param post:
        :return:
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
