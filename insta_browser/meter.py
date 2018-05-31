# -*- coding: utf-8 -*-
import _md5
import json
import re
from urllib.parse import quote

import requests

from .configure import ua

COUNTERS_KEY = 'acc'
COUNT_KEY_FOLLOWING = 'f'  # Following
COUNT_KEY_FOLLOWED_BY = 'fb'  # Followers
COUNT_KEY_POSTS = 'p'  # Posts
COUNT_KEY_VIDEO_POSTS = 'pvp'  # Video posts
COUNT_KEY_IMAGE_POSTS = 'pip'  # Photo posts
COUNT_KEY_ALBUM_POSTS = 'pap'  # Album posts
COUNT_KEY_LIKES = 'lc'  # Likes count key
COUNT_KEY_COMMENTS = 'cc'  # Comments count key
COUNT_KEY_VIDEO_VIEWS = 'vc'  # Video views count key
COUNT_KEY_LIKES_PER_POST = 'lpp'  # Likes per post
COUNT_KEY_COMMENTS_PER_POST = 'cpp'  # Comments per post
COUNT_KEY_VIEWS_PER_POST = 'vpp'  # Video views per post
TOP_PROGRESS = {'lc': 85, 'cc': 90, 'vc': 95}
POST_TYPES_KEYS = {
    'GraphImage': COUNT_KEY_IMAGE_POSTS,
    'GraphVideo': COUNT_KEY_VIDEO_POSTS,
    'GraphSidecar': COUNT_KEY_ALBUM_POSTS,
}


class InstaMeter:
    __profile_fp_url = 'https://instagram.com/{}/?__a=1'
    __profile_rp_url = 'https://instagram.com/graphql/query/?query_hash=42323d64886122307be10013ad2dcc44&variables={}'

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
        self.client = requests.session()
        self.headers = {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
            'Cookie': 'ig_pr=2;',
        }
        self.client.headers.update(self.headers)
        m = re.search(r'"rhx_gis":"([A-z0-9]+)"', self.client.get('https://instagram.com/').text)
        if m is None:
            raise Exception("STOP!")
        self.rhx_gis = m.group(1)

    def analyze_profile(self):
        try:
            self.__get_profile_first_posts()
        except ValueError as exc:
            self.__error = "{}".format(exc)
            self.__use_callback({'success': False, 'error': self.__error})
            return self.__error
        if not self.user['ip'] and self.user[COUNTERS_KEY][COUNT_KEY_POSTS]:
            self.__get_profile_rest_posts()
            self.__send_success_callback('posts_result', self.posts, 60)
            self.__analyze_top_liked_posts()
            self.__analyze_top_commented_posts()
            self.__analyze_top_viewed_posts()
        if not self.user['ip']:
            self.__send_success_callback('account_result', self.user, 100)

        return json.dumps({
            'account': self.user,
            'posts': self.posts,
            'top_posts_liked': self.top_posts_liked,
            'top_posts_commented': self.top_posts_commented,
            'top_posts_viewed': self.top_posts_viewed,
        }, ensure_ascii=False)

    def __update_instagram_gis(self, params):
        instagram_gis = _md5.md5('{}:{}'.format(self.rhx_gis, params).encode("utf-8")).hexdigest()
        self.client.headers.update({'x-instagram-gis': instagram_gis})

    def __get_profile_first_posts(self):
        url = self.__profile_fp_url.format(self.username)
        self.__update_instagram_gis('/{}/'.format(self.username))
        data = self.client.request('get', url).json()
        user_data = data['graphql']
        self.user['un'] = self.username
        self.user['id'] = user_data['user']['id']
        self.user['fn'] = user_data['user']['full_name']
        self.user['b'] = user_data['user']['biography']
        self.user['pic'] = user_data['user']['profile_pic_url_hd']
        self.user['iv'] = user_data['user']['is_verified']
        self.user['ip'] = user_data['user']['is_private']
        self.user[COUNTERS_KEY] = {
            COUNT_KEY_FOLLOWING: user_data['user']['edge_follow']['count'],
            COUNT_KEY_FOLLOWED_BY: user_data['user']['edge_followed_by']['count'],
            COUNT_KEY_POSTS: user_data['user']['edge_owner_to_timeline_media']['count'],
            COUNT_KEY_IMAGE_POSTS: 0,
            COUNT_KEY_VIDEO_POSTS: 0,
            COUNT_KEY_ALBUM_POSTS: 0,
            COUNT_KEY_LIKES: 0,
            COUNT_KEY_COMMENTS: 0,
            COUNT_KEY_VIDEO_VIEWS: 0,
            COUNT_KEY_LIKES_PER_POST: 0,
            COUNT_KEY_COMMENTS_PER_POST: 0,
            COUNT_KEY_VIEWS_PER_POST: 0,
        }

        self.__send_success_callback('account', self.user)

        if not self.user['ip'] and self.user[COUNTERS_KEY][COUNT_KEY_POSTS]:
            self.__process_posts_first(user_data['user']['edge_owner_to_timeline_media']['edges'])
            self.__tmp_req_info = user_data['user']['edge_owner_to_timeline_media']['page_info']

    def __send_success_callback(self, key, data, progress=None):
        self.__use_callback({'data': {key: data}, '_id': self.user['id'],
                             'progress': progress if progress else self.__calculate_progress(), 'success': True})

    def __use_callback(self, data):
        if callable(self.callback):
            self.callback(data)

    def __process_posts_first(self, posts):
        posts_for_update = []
        for post in posts:
            post = post['node']
            tmp_post = {
                'id': post['id'],
                'd': post['taken_at_timestamp'],
                'code': post['shortcode'],
                'iv': post['is_video'],
            }
            tmp_post.update(self.__update_user_and_post_counters(post))
            posts_for_update.append(tmp_post)
        self.posts.extend(posts_for_update)
        self.__calculate_per_post_counters()
        self.__send_callback_for_post_processing(posts_for_update)

    def __get_profile_rest_posts(self):
        while self.__tmp_req_info['has_next_page']:
            self.__request_for_rest_loop()
            posts_for_update = []
            for post in self.__tmp_data:
                post = post['node']
                tmp_post = {
                    'id': post['id'],
                    'd': post['taken_at_timestamp'],
                    'code': post['shortcode'],
                }
                tmp_post.update(self.__update_user_and_post_counters(post))
                posts_for_update.append(tmp_post)
            self.posts.extend(posts_for_update)
            self.__calculate_per_post_counters()
            self.__send_callback_for_post_processing(posts_for_update)

    def __update_user_and_post_counters(self, post):
        typename = post['__typename']
        comments = post['comments']['count'] if 'comments' in post else post['edge_media_to_comment']['count']
        likes = post['likes']['count'] if 'likes' in post else post['edge_media_preview_like']['count']
        if 'edge_media_to_caption' in post:
            text = post['edge_media_to_caption']['edges'][0]['node']['text'] \
                if post['edge_media_to_caption']['edges'] \
                else ''
        else:
            text = post['caption'] if 'caption' in post else ''
        self.user[COUNTERS_KEY][COUNT_KEY_LIKES] += likes
        self.user[COUNTERS_KEY][COUNT_KEY_COMMENTS] += comments
        self.user[COUNTERS_KEY][POST_TYPES_KEYS[typename]] += 1
        vv_tmp = self.__count_views(post) if post['is_video'] else 0
        return {
            'txt': text,
            COUNT_KEY_LIKES: likes,
            COUNT_KEY_COMMENTS: comments,
            COUNT_KEY_VIDEO_VIEWS: vv_tmp,
            't': POST_TYPES_KEYS[typename],
        }

    @staticmethod
    def __prepare_post_text(text):
        prepared = ' '.join(re.sub(r"(#[\w]+ ?)", '', str(text), flags=re.U).split())[0:99]
        return prepared

    def __calculate_per_post_counters(self):
        posts = float(self.user[COUNTERS_KEY][COUNT_KEY_POSTS])
        ck = COUNTERS_KEY
        if posts:
            self.user[ck][COUNT_KEY_LIKES_PER_POST] = self.user[ck][COUNT_KEY_LIKES] / posts
            self.user[ck][COUNT_KEY_COMMENTS_PER_POST] = self.user[ck][COUNT_KEY_COMMENTS] / posts
            vpc = sum(1 for p in self.posts if p.get('t') == 'pvp')
            self.user[ck][COUNT_KEY_VIEWS_PER_POST] = self.user[ck][COUNT_KEY_VIDEO_VIEWS] / vpc if vpc else 0

    def __request_for_rest_loop(self):
        var_json = {
            'id': self.user['id'],
            'first': 50 if self.user[COUNTERS_KEY][COUNT_KEY_POSTS] > 50 else self.user[COUNTERS_KEY][
                                                                                  COUNT_KEY_POSTS] - 12,
        }
        if self.__tmp_req_info['has_next_page']:
            var_json.update({'after': self.__tmp_req_info['end_cursor']})
        variables = json.dumps(var_json, separators=(',', ':'))
        url = self.__profile_rp_url.format(quote(variables))
        self.__update_instagram_gis(variables)
        data = self.client.request('get', url).json()
        self.__tmp_data = data['data']['user']['edge_owner_to_timeline_media']['edges']
        self.__tmp_req_info = data['data']['user']['edge_owner_to_timeline_media']['page_info']

        return self.__tmp_req_info

    def __send_callback_for_post_processing(self, posts):
        self.__send_success_callback('account', self.user)
        self.__send_success_callback('posts', posts)

    def __count_views(self, post):
        video_views = post.get('video_views', post.get('video_view_count'))
        self.user[COUNTERS_KEY][COUNT_KEY_VIDEO_VIEWS] += video_views
        return video_views

    # @staticmethod
    # def __process_url(url):
    #     headers = {
    #         'User-Agent': ua,
    #         'Accept': '*/*',
    #         'Accept-Language': 'en-US',
    #         'Connection': 'close',
    #     }
    #     request = simple_browser.Request(url, headers=headers)
    #     response = simple_browser.urlopen(request)
    #     return response.read().decode('utf-8')

    def __analyze_top_liked_posts(self):
        self.top_posts_liked = self.__sort_posts(COUNT_KEY_LIKES)

    def __analyze_top_commented_posts(self):
        self.top_posts_commented = self.__sort_posts(COUNT_KEY_COMMENTS)

    def __analyze_top_viewed_posts(self):
        self.top_posts_viewed = self.__sort_posts(COUNT_KEY_VIDEO_VIEWS)

    def __sort_posts(self, key):
        if key == COUNT_KEY_VIDEO_VIEWS:
            tmp_posts = [el for el in self.posts if el['t'] == 'pvp']
        else:
            tmp_posts = list(self.posts)
        tmp_posts.sort(key=lambda post: post[key], reverse=True)
        posts = [post for post in tmp_posts if post[key] > 0][0:12]
        self.__send_success_callback('posts_top_{}'.format(key), posts, TOP_PROGRESS[key])
        return posts

    def __check_user_before_print(self):
        if not self.user:
            print('User was not analyzed because of: "{}"'.format(self.__error))
            exit()

    def print_account_statistic(self):
        self.__check_user_before_print()
        stats = {
            'following': self.user['acc']['f'],
            'followed': self.user['acc']['fb'],
            'posts': self.user[COUNTERS_KEY][COUNT_KEY_POSTS],
            'likes': self.user[COUNTERS_KEY][COUNT_KEY_LIKES],
            'comments': self.user[COUNTERS_KEY][COUNT_KEY_COMMENTS],
            'video views': self.user[COUNTERS_KEY][COUNT_KEY_VIDEO_VIEWS],
            'likes/post': self.user[COUNTERS_KEY][COUNT_KEY_LIKES_PER_POST],
            'comments/post': self.user[COUNTERS_KEY][COUNT_KEY_COMMENTS_PER_POST],
            'views/post': self.user[COUNTERS_KEY][COUNT_KEY_VIEWS_PER_POST],
        }
        print('+-- https://instagram.com/{:-<37}+'.format(self.user['un'] + '/ '))
        print('|   {:<27}|{:^31}|'.format('counter', 'value'))
        print('+{:-^30}+{:-^31}+'.format('', ''))
        for key, value in stats.items():
            print('|   {:<27}|{:^31}|'.format(key, value))
        print('|{: ^62}|'.format(''))
        print('+{:-^62}+'.format(' https://github.com/kricha/insta_browser '))

    def __print_top(self, posts, header_text, key, counter_text):
        self.__check_user_before_print()
        if not self.user['ip']:
            self.__print_top_header(header_text)
            self.__print_top_rest(posts, counter_text, key)

    def print_top_liked(self, count=10):
        self.__print_top(self.top_posts_liked[0:count], 'top liked posts', COUNT_KEY_LIKES, 'likes')

    def print_top_commented(self, count=10):
        self.__print_top(self.top_posts_commented[0:count], 'top commented posts', COUNT_KEY_COMMENTS, 'comments')

    def print_top_viewed(self, count=10):
        self.__print_top(self.top_posts_viewed[0:count], 'top viewed posts', COUNT_KEY_VIDEO_VIEWS, 'views')

    def __calculate_progress(self):
        has_posts = self.user[COUNTERS_KEY][COUNT_KEY_POSTS]
        if self.user['ip']:
            return 100
        elif has_posts:
            percent = self.posts.__len__() * 100 / float(self.user[COUNTERS_KEY][COUNT_KEY_POSTS])
            return percent if percent < 81 else 80
        else:
            return 100

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
