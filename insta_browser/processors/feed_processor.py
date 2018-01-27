import selenium.common.exceptions as excp
import time
import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_processor import BaseProcessor

NOT_LIKED_CSS_CLASS = '.coreSpriteHeartOpen'


class FeedProcessor(BaseProcessor):
    posts_list = []
    posts_hash_list = []

    def scroll_feed_to_last_not_liked_posts(self, count):
        """
        Scroll down feed to last not liked post

        :return:
        """
        self.get_like_limits(count)
        self.logger.log('Start scrolling page.')
        while self.__is_last_post_in_feed_not_liked():
            self.__scroll_down()

    def __scroll_down(self):
        """
        Moving to footer and waiting for querying new posts

        :return:
        """
        last_post = WebDriverWait(self.browser, 10). \
            until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'article:last-child')))
        self.browser.execute_script("return arguments[0].scrollIntoView();", last_post)
        self.logger.log_to_file('---> scrolled down.')
        self.feed_scrolled_down += 1
        time.sleep(1)

    def __is_last_post_in_feed_not_liked(self):
        """
        Check last five posts if they are not liked

        :return: False if one of five posts wasn't liked, True if all five were liked
        """
        posts = self.browser.find_elements_by_tag_name('article')
        for post in posts:
            post_link = self._get_feed_post_link(post)
            if post_link not in self.posts_hash_list:
                self.posts_hash_list.append(post_link)
                self.posts_list.append({'pl': post_link, 'p': post})

        if 0 < len(self.posts_list) >= self.count:
            return False

        try:
            for i in range(5):
                post = posts.pop()
                post.find_element_by_css_selector(NOT_LIKED_CSS_CLASS)
            del posts
            return True
        except excp.NoSuchElementException:
            return False
        except IndexError:
            return True

    def process(self, exclude, login):
        """
        liking pre-processed posts. Moving to each post with ActionChains

        :param exclude:
        :param login:
        :param count:
        :return:
        """
        br = self.browser

        self.posts_list.reverse()

        progress = tqdm.tqdm(self.posts_list)
        for post in progress:
            real_time_posts = br.find_elements_by_tag_name('article')
            post_link = post.get('pl')
            filtered_posts = [p for p in real_time_posts if self._get_feed_post_link(p) == post_link]
            if filtered_posts.__len__():
                real_post = filtered_posts.pop()
                # scroll to real post in markup
                heart = real_post.find_element_by_css_selector('div:nth-child(3) section a:first-child')
                self.browser.execute_script("return arguments[0].scrollIntoView(false);", heart)
                # getting need to process elements
                author = real_post.find_element_by_css_selector('div:first-child .notranslate').text
                heart_classes = heart.find_element_by_css_selector('span').get_attribute('class')
                # check restrictions
                is_not_liked = 'coreSpriteHeartOpen' in heart_classes
                is_mine = author == login
                need_to_exclude = author in exclude

                if is_mine or not is_not_liked:
                    self.post_skipped += 1
                    pass
                elif need_to_exclude:
                    self.post_skipped_excluded += 1
                    pass
                else:
                    # like this post
                    time.sleep(.3)
                    heart.click()
                    time.sleep(.7)
                    self.db.likes_increment()
                    self.post_liked += 1
                    log = '---> liked @{} post {}'.format(author, post_link)
                    self.logger.log_to_file(log)

                progress.update()
