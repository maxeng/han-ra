#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import re
import yaml
import oauth
from datetime import datetime
from model.ids import IDS
from model.statuses import Statuses
from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db
from hanra import Hanra

#ZENRIZE_COUNT = '10'
#HANRIZE_COUNT = 'hanrize_count'

class TwitBot:
    def __init__(self):
        # config.yamlから設定情報を取得
        #     ---
        #     bot:
        #       consumer_key: ****************
        #       consumer_secret: ********************************
        #       access_token: ****************************************
        #       access_token_secret: ********************************
        #       client = oauth.TwitterClient(consumer_key, consumer_secret, callback_url)
        config_data = yaml.load(open('../config.yaml'))
        self.bot_config = config_data['bot']
        self.client = oauth.TwitterClient(
            self.bot_config['consumer_key'],
            self.bot_config['consumer_secret'],
            None)
#            self.bot_config['callback_url'])

    # 自分のfriendsのデータを更新する
    def friends(self):
        url = 'http://api.twitter.com/1/friends/ids.json'
        result = self.client.make_request(
            url,
            token   = self.bot_config['access_token'],
            secret  = self.bot_config['access_token_secret'],
            additional_params = None,
            protected         = True,
            method            = urlfetch.GET)
        logging.debug(result.status_code)
        logging.debug(result.content)
        if result.status_code == 200:
            ids = IDS.get()
            ids.friends = result.content
            ids.put()

    # 自分のfollowersのデータを更新する
    def followers(self):
        url = 'http://api.twitter.com/1/followers/ids.json'
        result = self.client.make_request(
            url,
            token   = self.bot_config['access_token'],
            secret  = self.bot_config['access_token_secret'],
            additional_params = None,
            protected         = True,
            method            = urlfetch.GET)
        logging.debug(result.status_code)
        logging.debug(result.content)
        if result.status_code == 200:
            ids = IDS.get()
            ids.followers = result.content
            ids.put()

    # friends, followersの情報から、follow返しする
    def refollow(self):
        ids = IDS.get()
        friends   = set(simplejson.loads(ids.friends))
        followers = set(simplejson.loads(ids.followers))
        should_follow   = list(followers - friends)
        random.shuffle(should_follow)
        logging.debug('should follow: %d' % len(should_follow))
        # 繰り返し挑戦するので失敗してもタイムアウトになっても気にしない
        while len(should_follow) > 0:# or len(should_unfollow) > 0:
            url = 'http://api.twitter.com/1/friendships/create.json'
            logging.debug(url)
            result = self.client.make_request(
                url,
                token   = self.bot_config['access_token'],
                secret  = self.bot_config['access_token_secret'],
                additional_params = {"user_id" : should_follow.pop()},
                protected         = True,
                method            = urlfetch.POST)
            if result.status_code != 200:
                logging.warn(result.content)


    # friends, followersの情報から、follow or unfollowする
    def friendship(self):
        ids = IDS.get()
        friends   = set(simplejson.loads(ids.friends))
        followers = set(simplejson.loads(ids.followers))
        should_follow   = list(followers - friends)
        should_unfollow = list(friends - followers)
        random.shuffle(should_follow)
        random.shuffle(should_unfollow)
        logging.debug('should follow: %d' % len(should_follow))
        logging.debug('should unfollow: %d' % len(should_unfollow))
        # 繰り返し挑戦するので失敗してもタイムアウトになっても気にしない
        while len(should_follow) > 0 or len(should_unfollow) > 0:
            if len(should_follow) > 0:
                url = 'http://api.twitter.com/1/friendships/create.json'
                logging.debug(url)
                result = self.client.make_request(
                    url,
                    token   = self.bot_config['access_token'],
                    secret  = self.bot_config['access_token_secret'],
                    additional_params = {"user_id" : should_follow.pop()},
                    protected         = True,
                    method            = urlfetch.POST)
                if result.status_code != 200:
                    logging.warn(result.content)
            if len(should_unfollow) > 0:
                url = 'http://api.twitter.com/1/friendships/destroy.json'
                result = self.client.make_request(
                    url,
                    token   = self.bot_config['access_token'],
                    secret  = self.bot_config['access_token_secret'],
                    additional_params = {"user_id" : should_follow.pop()},
                    protected         = True,
                    method            = urlfetch.POST)
                if result.status_code != 200:
                    logging.warn(result.content)

    # 何かをつぶやく
    def update(self, status = None, in_reply_to = None):
        count = Statuses.all().count()
        if not status:
            status = random.choice(Statuses.all().fetch(1000)).status
        url  = 'http://api.twitter.com/1/statuses/update.json'
        data = {
            'status' : status.encode('utf-8'),
            'in_reply_to_status_id' : in_reply_to,
            }
        result = self.client.make_request(
            url,
            token   = self.bot_config['access_token'],
            secret  = self.bot_config['access_token_secret'],
            additional_params = data,
            protected         = True,
            method            = urlfetch.POST)
        logging.debug(result.status_code)
        logging.debug(result.content)

    # 発言を拾って半裸にする
    def hanrize(self):
#        cache = memcache.decr(HANRIZE_COUNT)
#        if cache:
#            logging.debug('count: %d' % cache)
#            return

        url = 'http://api.twitter.com/1/statuses/home_timeline.json'
        result = self.client.make_request(
            url,
            token   = self.bot_config['access_token'],
            secret  = self.bot_config['access_token_secret'],
            additional_params = { 'count': 100 },
            protected         = True,
            method            = urlfetch.GET)
        logging.debug(result.status_code)
        if result.status_code == 200:
            statuses = simplejson.loads(result.content)

            # 次の実行時間を決定する
#            format = '%a %b %d %H:%M:%S +0000 %Y'
#            first = datetime.strptime(statuses[ 0]['created_at'], format)
#            last  = datetime.strptime(statuses[-1]['created_at'], format)
#            logging.debug('first : %s' % first)
#            logging.debug('last  : %s' % last)
#            logging.debug(first - last)
#            memcache.set(HANRIZE_COUNT, (first - last).seconds * 2 / 60)

            def judge(status):
                # 過去発言は繰り返さない
#                reply_ids = Statuses.all()
#                if status['id']:
#                    return False

                # 非公開の発言も除く
                if status['user']['protected']:
                    return False
                # 120文字以上の発言は除く
                if len(status['text']) > 120:
                    return False
                # RTっぽい発言も除く
                if re.search('RT[ :].*@\w+', status['text']):
                    return False
                # ハッシュタグっぽいものを含んでいる発言も除く
                if re.search(u'[#＃]\w+', status['text']):
                    return False
                # 既に「裸」が含まれている発言も除く
                if re.search(u'裸', status['text']):
                    return False
                # それ以外のものはOK
                return True

            # 残ったものからランダムに選択して半裸にする
            candidate = filter(judge, statuses)
            random.shuffle(candidate)
            hanra = Hanra()
            
            for status in candidate:
                text = hanra.hanrize(status['text']).decode('utf-8')
                
                # BadValueError: Property status is not multi-line 対策
                text = text.strip('\t\n\x0b\x0c\r')
                
                # うまく半裸にできたもの かつ 120文字まで
                if re.search(u'半裸で', text):    # and len(text) < 120:
                    logging.debug(text)

                    rep_id = status['id']
#                    query = Statuses.all().filter('in_reply_to =', rep_id)

#                    query = GqlQuery('SELECT * FROM Statuses WHERE in_reply_to = rep_id')
#                    exist = db.get(db.Key.from_path('Statuses', rep_id))
#                    if query == None:
#                    if not query:

                    logging.debug(rep_id)

                    tweeted = Statuses()
                    tweeted.status = text
                    tweeted.in_reply_to = status['id']
                    tweeted.put()
                
                    self.update(status = u'半裸RT @%s: %s' % (
                        status['user']['screen_name'],
                        text,
                        ), in_reply_to = status['id'])


                    break
