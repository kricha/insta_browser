import tqdm
import time
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as excp

TOP_POSTS_XPATH = '//*[@id="react-root"]/section/main/article/div[1]/div'
LATEST_POSTS_XPATH = '//*[@id="react-root"]/section/main/article/div[2]'


class NotFeedProcessor:
    liked = 0
    skipped = 0
    progress = None
    heart = None
    already_liked = 0
    count = 0

    def __init__(self, browser, logger):
        self.browser = browser
        self.logger = logger

    def like_user_profile(self, count):
        self.browser.find_element_by_css_selector("article > div a").click()
        self.go_through_posts(count)
        return self.__return_liking_summary()

    def like_top(self):
        self.logger.log('Start processing top posts')
        self.__get_posts_block(TOP_POSTS_XPATH)
        self.go_through_posts(9)
        return self.__return_liking_summary()

    def like_latest(self, count):
        self.logger.log('Start processing lastest posts')
        self.__get_posts_block(LATEST_POSTS_XPATH)
        self.go_through_posts(count)
        return self.__return_liking_summary()

    def go_through_posts(self, count):
        self.count = count
        time.sleep(.5)
        self.already_liked = 0
        progress = tqdm.tqdm(range(self.count))
        for i in progress:
            time.sleep(1)
            self.__like_post()
            if not self.__go_to_next_post():
                progress.close()
                break
            progress.update()

    def __like_post(self):
        if self.__is_not_liked_acc_post():
            self.heart.click()
            self.logger.log_to_file("--> like post")
            self.liked += 1
            self.already_liked = 0
            time.sleep(0.5)
        elif not self.heart and self.count > 9:
            self.already_liked += 1
            self.skipped +=1
        else:
            self.skipped += 1

    def __go_to_next_post(self):
        """
        Go to next post on non-feed page
        :return:
        """
        link = self.__has_next()
        if not link or self.already_liked > 5:
            return False
        else:
            link.click()
            return True

    def __return_liking_summary(self):
        return {'liked': self.liked, 'skipped': self.skipped}

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
