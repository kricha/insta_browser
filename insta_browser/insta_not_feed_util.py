import tqdm
import time
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as excp
from .base.processor import BaseProcessor
import re

TOP_POSTS_XPATH = '//*[@id="react-root"]/section/main/article/div[1]/div'
LATEST_POSTS_XPATH = '//*[@id="react-root"]/section/main/article/div[2]'
POST_CSS_SELECTOR = '#fb-root + div article'


class NotFeedProcessor(BaseProcessor):

    def like_user_profile(self, count):
        if count:
            posts_count = count
        else:
            posts_from_page = self.browser.find_element_by_css_selector("article header ul li span").text
            tmp_count = int(re.match('\d+', posts_from_page).group(0))
            posts_count = self.like_limit if tmp_count > self.like_limit else tmp_count
        self.browser.find_element_by_css_selector("article > div a").click()
        self.go_through_posts(posts_count)

    def like_top(self):
        self.get_like_limits(9)
        self.logger.log('Start processing top posts.')
        self.__get_posts_block(TOP_POSTS_XPATH)
        self.go_through_posts(self.count)

    def like_latest(self, count):
        self.get_like_limits(count)
        self.logger.log('Start processing latest posts.')
        self.__get_posts_block(LATEST_POSTS_XPATH)
        self.go_through_posts(self.count-9)

    def go_through_posts(self, count):
        self.count = count
        time.sleep(.5)
        self.post_already_liked = 0
        progress = tqdm.tqdm(range(self.count))
        for i in progress:
            time.sleep(1)
            self.__like_post()
            if not self.__go_to_next_post():
                progress.close()
                break
            progress.update()

    def __like_post(self):
        """
        Like posts or skip

        :return:
        """
        if self.__is_not_liked_acc_post():
            self.heart.click()
            self.logger.log_to_file('--> like post {}'.format(self.browser.current_url))
            self.db.likes_increment()
            self.post_liked += 1
            self.post_already_liked = 0
            time.sleep(0.5)
        elif not self.heart and self.count > 9:
            self.post_already_liked += 1
            self.post_skipped +=1
        else:
            self.post_skipped += 1

    def __go_to_next_post(self):
        """
        Go to next post on non-feed page

        :return:
        """
        link = self.__has_next()
        if not link or self.post_already_liked > 4:
            return False
        else:
            link.click()
            return True

    def __get_posts_block(self, block_xpath):
        top_block = self.browser.find_element_by_xpath(block_xpath)
        post_link = top_block.find_element_by_css_selector("a")
        ActionChains(self.browser).move_to_element(post_link).click().perform()

    def __is_not_liked_acc_post(self):
        """
        Check if not feed post is liked

        :return: like WebElement if exist or False if not
        """
        self.heart = None
        try:
            is_not_liked_span = self.browser.find_element_by_css_selector(".coreSpriteHeartOpen")
            self.heart = is_not_liked_span.find_element_by_xpath('..')
            return True
        except excp.NoSuchElementException:
            return False

    def __has_next(self):
        """
        Check if page has nex link

        :return: next link WebElement if exist and False if not
        """
        try:
            next_link = self.browser.find_element_by_css_selector(".coreSpriteRightPaginationArrow")
            return next_link
        except excp.NoSuchElementException:
            return False
