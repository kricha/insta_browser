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