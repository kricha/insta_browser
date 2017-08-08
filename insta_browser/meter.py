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


class InstaMeter:
    user = {}
    posts = []
    __profile_fp_url = 'https://www.instagram.com/{}/?__a=1'
    __profile_rp_url = 'https://www.instagram.com/graphql/query/?query_id=17888483320059182&variables={}'
    __tmp_req_info = None
    __tmp_data = []
    top_posts_liked = []
    top_posts_commented = []
    top_posts_viewed = []
    __error = None

    def __init__(self, username, callback=None):
        self.username = username
        self.callback = callback

    def analyze_profile(self):
        try:
            self.__get_profile_first_posts()
        except ValueError as exc:
            self.__error = exc.message
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
        self.user['f'] = data['user']['follows']['count']
        self.user['fb'] = data['user']['followed_by']['count']
        self.user['p'] = data['user']['media']['count']
        self.user['iv'] = data['user']['is_verified']
        self.user['ip'] = data['user']['is_private']
        self.user['a'] = {'cc': 0, 'lc': 0, 'vv': 0}

        self.__use_callback(self.user)

        if not self.user['ip']:
            self.__process_posts_first(data['user']['media']['nodes'])
            self.__tmp_req_info = data['user']['media']['page_info']

    def __use_callback(self, data):
        if callable(self.callback):
            self.callback(data)

    def __get_profile_rest_posts(self):
        if not self.user['ip']:
            while self.__request_for_rest_loop()['has_next_page']:
                pass
            self.__process_posts_rest()

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
        self.__tmp_data.extend(data['data']['user']['edge_owner_to_timeline_media']['edges'])
        self.__tmp_req_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']

        return self.__tmp_req_info

    def __process_posts_first(self, posts):
        for post in posts:
            comments = post['comments']['count']
            likes = post['likes']['count']
            self.user['a']['cc'] += comments
            self.user['a']['lc'] += likes
            tmp_post = {
                'id': post['id'],
                'd': post['date'],
                'code': post['code'],
                't': post['caption'],
                'cc': comments,
                'lk': likes,
                'vv': self.__count_viewes(post, 'video_viewes'),
            }

            self.posts.append(tmp_post)

    def __count_viewes(self, post, key):
        video_views = post[key] if post['is_video'] else 0
        self.user['a']['vv'] += video_views
        return video_views

    def __process_posts_rest(self):
        for post in self.__tmp_data:
            post = post.values()[0]
            comments = post['edge_media_to_comment']['count']
            likes = post['edge_media_preview_like']['count']
            self.user['a']['cc'] += comments
            self.user['a']['lc'] += likes
            text = post['edge_media_to_caption']['edges']
            tmp_post = {
                'id': post['id'],
                'd': post['taken_at_timestamp'],
                'code': post['shortcode'],
                't': text[0]['node']['text'][0:100] if text else '',
                'cc': comments,
                'lk': likes,
                'vv': self.__count_viewes(post, 'video_view_count'),
            }
            self.posts.append(tmp_post)
        self.__use_callback(self.posts)

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
        self.top_posts_liked = self.__sort_posts('lk')
        self.__use_callback(self.top_posts_liked)

    def __analyze_top_commented_posts(self):
        self.top_posts_commented = self.__sort_posts('cc')
        self.__use_callback(self.top_posts_commented)

    def __analyze_top_viewed_posts(self):
        self.top_posts_viewed = self.__sort_posts('vv')
        self.__use_callback(self.top_posts_viewed)

    def __sort_posts(self, key):
        tmp_posts = list(self.posts)
        tmp_posts.sort(key=lambda post: post[key], reverse=True)
        return [post for post in tmp_posts if post[key] > 0]

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
            'likes': self.user['a']['lc'],
            'comments': self.user['a']['cc'],
            'video views': self.user['a']['vv'],
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
        self.__print_top(self.top_posts_liked[0:count], 'top liked posts', 'lk', 'likes')

    def print_top_commented(self, count=10):
        self.__print_top(self.top_posts_commented[0:count], 'top commented posts', 'cc', 'comments')

    def print_top_viewed(self, count=10):
        self.__print_top(self.top_posts_viewed[0:count], 'top viewed posts', 'vv', 'viewes')

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
