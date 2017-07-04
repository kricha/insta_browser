import selenium.common.exceptions as excp


class BaseProcessor:
    post_skipped_excluded = 0
    posts_count_to_like = 0
    feed_scrolled_down = 0
    post_already_liked = 0
    post_excluded = 0
    post_skipped = 0
    like_limit = 500
    progress = None
    post_liked = 0
    heart = None
    count = 0

    def get_summary(self):
        return {'liked': self.post_liked,
                'skipped': self.post_skipped,
                'excluded': self.post_skipped_excluded,
                'already_liked': self.post_already_liked,
                'scrolled': self.feed_scrolled_down}

    @staticmethod
    def _get_feed_post_link(post):
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
    def _get_feed_post_media(post):  # TODO: refactor searching image
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
