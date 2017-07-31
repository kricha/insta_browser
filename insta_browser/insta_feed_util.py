import tqdm
import time
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as excp
from .base.processor import BaseProcessor

NOT_LIKED_CSS_CLASS = '.coreSpriteHeartOpen'


class FeedProcessor(BaseProcessor):

    def scroll_feed_to_last_not_liked_posts(self):
        """
        Scroll down feed to last not liked post

        :return:
        """
        self.logger.log('Start scrolling page.')
        while self.__is_last_post_in_feed_not_liked():
            self.__scroll_down()

    def __scroll_down(self):
        """
        Moving to footer and waiting for querying new posts

        :return:
        """
        footer = self.browser.find_element_by_tag_name('footer')
        ActionChains(self.browser).move_to_element(footer).perform()
        self.logger.log_to_file('---> scrolled down.')
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
        self.get_like_limits(count)
        posts = br.find_elements_by_tag_name('article')
        analyzed_posts = self.pre_process_posts(posts, exclude, login)
        self.logger.log('Start liking posts.')
        progress = tqdm.tqdm(analyzed_posts)
        for post in progress:
            post_element = post.get('post')
            heart = post.get('heart')
            ActionChains(br).move_to_element(post_element).perform()
            time.sleep(.3)
            heart.click()
            time.sleep(.7)
            log = '---> liked @{} post {}'.format(post.get('author'), post.get('link'))
            self.db.likes_increment()
            self.post_liked += 1
            self.logger.log_to_file(log)

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
            heart_classes = heart.find_element_by_css_selector('span').get_attribute('class')

            is_not_liked = 'coreSpriteHeartOpen' in heart_classes
            is_mine = author == login
            need_to_exclude = author in exclude

            if is_mine or not is_not_liked:
                self.post_skipped += 1
            elif need_to_exclude:
                self.post_skipped_excluded += 1
            else:
                post_link = self._get_feed_post_link(post)
                result_posts.append({'post': post,'heart': heart, 'author': author, 'link': post_link})

            pr.update()
        return result_posts
