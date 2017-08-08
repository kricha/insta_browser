# -*- coding: utf-8 -*-
import json

try:
    import urllib.request as simple_browser
except ImportError:
    import urllib2 as simple_browser
from .configure import ua

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

COUNTERS_KEY = 'acc'
LIKES_COUNT_KEY = 'lc'
COMMENTS_COUNT_KEY = 'cc'
VIDEO_VIEWS_COUNT_KEY = 'vc'


class InstaMeter:
    __profile_fp_url = 'https://www.instagram.com/{}/?__a=1'
    __profile_rp_url = 'https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={}'

    def __init__(self, username, callback=None):
        self.username = username
        self.callback = callback
        self.user = {}
        self.posts = []
        self.__tmp_req_info = None
        self.__tmp_data = []
        self.top_posts_liked = []
        self.top_posts_commented = []
        self.top_posts_viewed = []
        self.__error = None

    def analyze_profile(self):
        try:
            self.__get_profile_first_posts()
        except ValueError as exc:
            self.__error = "{}".format(exc)
            return self.__error
        self.__get_profile_rest_posts()
        self.__analyze_top_liked_posts()
        self.__analyze_top_commented_posts()
        self.__analyze_top_viewed_posts()

        return json.dumps({
            'account': self.user,
            'posts': self.posts,
            'top_posts_liked': self.top_posts_liked[0:10],
            'top_posts_commented': self.top_posts_commented[0:10],
        }, ensure_ascii=False)

    def __get_profile_first_posts(self):
        url = self.__profile_fp_url.format(self.username)
        try:
            data = json.loads(self.__process_url(url))
        except simple_browser.HTTPError:
            raise ValueError('User not found.')

        self.user['un'] = self.username
        self.user['id'] = data['user']['id']
        self.user['fn'] = data['user']['full_name']
        self.user['pic'] = data['user']['profile_pic_url_hd']
        self.user['f'] = data['user']['follows']['count']
        self.user['fb'] = data['user']['followed_by']['count']
        self.user['p'] = data['user']['media']['count']
        self.user['iv'] = data['user']['is_verified']
        self.user['ip'] = data['user']['is_private']
        self.user[COUNTERS_KEY] = {LIKES_COUNT_KEY: 0, COMMENTS_COUNT_KEY: 0, VIDEO_VIEWS_COUNT_KEY: 0}

        self.__use_callback({'account': self.user})

        if not self.user['ip']:
            self.__process_posts_first(data['user']['media']['nodes'])
            self.__tmp_req_info = data['user']['media']['page_info']

    def __use_callback(self, data):
        if callable(self.callback):
            self.callback(data)

    def __get_profile_rest_posts(self):
        if not self.user['ip']:
            while self.posts.__len__() < self.user['p']:
                self.__request_for_rest_loop()
                posts_for_update = []
                for post in self.__tmp_data:
                    post = post['node']
                    comments = post['edge_media_to_comment']['count']
                    likes = post['edge_media_preview_like']['count']
                    self.user[COUNTERS_KEY][LIKES_COUNT_KEY] += likes
                    self.user[COUNTERS_KEY][COMMENTS_COUNT_KEY] += comments
                    text = post['edge_media_to_caption']['edges']
                    tmp_post = {
                        'id': post['id'],
                        'd': post['taken_at_timestamp'],
                        'code': post['shortcode'],
                        't': text[0]['node']['text'][0:99] if text else '',
                        LIKES_COUNT_KEY: likes,
                        COMMENTS_COUNT_KEY: comments,
                        VIDEO_VIEWS_COUNT_KEY: self.__count_views(post, 'video_view_count'),
                    }
                    posts_for_update.append(tmp_post)
                self.posts.extend(posts_for_update)
                self.__use_callback({'account': self.user})
                self.__use_callback({'posts': posts_for_update})

    def __request_for_rest_loop(self):
        var_json = {
            'id': self.user['id'],
            'first': 500 if self.user['p'] > 500 else self.user['p'] - 12,
        }
        if self.__tmp_req_info['has_next_page']:
            var_json.update({'after': self.__tmp_req_info['end_cursor']})
        variable = json.dumps(var_json).replace(' ', '')
        url = self.__profile_rp_url.format(quote(variable))
        data = json.loads(self.__process_url(url))
        self.__tmp_data = data['data']['user']['edge_owner_to_timeline_media']['edges']
        self.__tmp_req_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']

        return self.__tmp_req_info

    def __process_posts_first(self, posts):
        posts_for_update = []
        for post in posts:
            comments = post['comments']['count']
            likes = post['likes']['count']
            self.user[COUNTERS_KEY][LIKES_COUNT_KEY] += likes
            self.user[COUNTERS_KEY][COMMENTS_COUNT_KEY] += comments
            tmp_post = {
                'id': post['id'],
                'd': post['date'],
                'code': post['code'],
                't': post['caption'][0:99] if 'caption' in post else '',
                LIKES_COUNT_KEY: likes,
                COMMENTS_COUNT_KEY: comments,
                VIDEO_VIEWS_COUNT_KEY: self.__count_views(post, 'video_views'),
            }
            posts_for_update.append(tmp_post)
        self.posts.extend(posts_for_update)
        self.__use_callback({'account': self.user})
        self.__use_callback({'posts': posts_for_update})

    def __count_views(self, post, key):
        video_views = post[key] if post['is_video'] else 0
        self.user[COUNTERS_KEY][VIDEO_VIEWS_COUNT_KEY] += video_views
        return video_views

    @staticmethod
    def __process_url(url):
        headers = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Accept-Language': 'en-US',
            'Connection': 'close',
        }
        request = simple_browser.Request(url, headers=headers)
        response = simple_browser.urlopen(request)
        return response.read()

    def __analyze_top_liked_posts(self):
        self.top_posts_liked = self.__sort_posts(LIKES_COUNT_KEY)

    def __analyze_top_commented_posts(self):
        self.top_posts_commented = self.__sort_posts(COMMENTS_COUNT_KEY)

    def __analyze_top_viewed_posts(self):
        self.top_posts_viewed = self.__sort_posts(VIDEO_VIEWS_COUNT_KEY)

    def __sort_posts(self, key):
        tmp_posts = list(self.posts)
        tmp_posts.sort(key=lambda post: post[key], reverse=True)
        posts = [post for post in tmp_posts if post[key] > 0][0:12]
        self.__use_callback({'posts_top_{}'.format(key): posts})
        return posts

    def __check_user_before_print(self):
        if not self.user:
            print('User was not analyzed because of: "{}"'.format(self.__error))
            exit()

    def print_account_statistic(self):
        self.__check_user_before_print()
        stats = {
            'following': self.user['f'],
            'followed': self.user['fb'],
            'posts': self.user['p'],
            'likes': self.user[COUNTERS_KEY][LIKES_COUNT_KEY],
            'comments': self.user[COUNTERS_KEY][COMMENTS_COUNT_KEY],
            'video views': self.user[COUNTERS_KEY][VIDEO_VIEWS_COUNT_KEY],
        }
        print('+-- https://instagram.com/{:-<37}+'.format(self.user['un'] + '/ '))
        print('|   {:<27}|{:^31}|'.format('counter', 'value'))
        print('+{:-^30}+{:-^31}+'.format('', ''))
        for key, value in stats.items():
            print('|   {:<27}|{:^31}|'.format(key, value))
        print('|{: ^62}|'.format(''))
        print('+{:-^62}+'.format(' https://github.com/aLkRicha/insta_browser '))

    def __print_top(self, posts, header_text, key, counter_text):
        self.__check_user_before_print()
        if not self.user['ip']:
            self.__print_top_header(header_text)
            self.__print_top_rest(posts, counter_text, key)

    def print_top_liked(self, count=10):
        self.__print_top(self.top_posts_liked[0:count], 'top liked posts', LIKES_COUNT_KEY, 'likes')

    def print_top_commented(self, count=10):
        self.__print_top(self.top_posts_commented[0:count], 'top commented posts', COMMENTS_COUNT_KEY, 'comments')

    def print_top_viewed(self, count=10):
        self.__print_top(self.top_posts_viewed[0:count], 'top viewed posts', VIDEO_VIEWS_COUNT_KEY, 'views')

    @staticmethod
    def __print_top_header(text):
        print('+{:-^62}+'.format('', ''))
        print('|{:^62}|'.format(text))
        print('+{:-^62}+'.format('', ''))

    @staticmethod
    def __print_top_rest(posts, text, key):
        for post in posts:
            print_text = 'https://instagram.com/p/{}/ - {} {}'.format(post['code'], post[key], text)
            print('|{:^62}|'.format(print_text))
        print('+{:-^62}+'.format('', ''))
