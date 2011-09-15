# -*- coding: utf-8 -*-
import oauth, tweepy
import time, sqlite3
import logging

def init_api():
    consumer_key = ""
    consumer_secret = ""
    access_key=""
    access_secret=""
    proxy_h = ""
    proxy_p = ""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return tweepy.API(auth, proxy_host = proxy_h, proxy_port = proxy_p)

def init_db():
    path = "pref.db"
    conn = sqlite3.connect(path)
    try:
        conn.execute('select * from replied')
    except sqlite3.OperationalError, e:
        conn.execute('create table replied (id int)')
        conn.commit()
    return conn

def get_since(conn):
    (mx,) = conn.execute('select max(id) from replied').fetchone()
    return mx

def save_id(conn, id):
    conn.execute('insert into replied values(' + str(id) + ')')
    conn.commit()

def is_replied(conn, id):
    (count,) = conn.execute('select count(id) from replied where id = ' + str(id)).fetchone()
    return count > 0

def format_message(mention):
    user = '@' + mention.author.screen_name
    text = mention.text.strip()
    if text.find('@elephant_trader') == 0:
        text = text[16:].strip()
    maxl = 140 - 45 - len(user)
    if len(text) > (maxl):
        text = text[0:maxl-3] + '...'
    message = user + unicode(" все говорят «", "utf-8") + text + unicode("». А ты возьми, и купи слона!", "utf-8")
    return message

def can_tweet(conn, mention):
    ex = not is_replied(conn, mention.id)
    me = not (mention.author.id == 372156581)
    rt = not mention.retweeted
    return ex and me and rt

def work(api, conn):
    update_time = 60
    while True:
        try:
            since = get_since(conn)
            if since:
                m = api.mentions(since_id = since)
            else:
                m = api.mentions()
            for i in m:
                if can_tweet(conn, i):
                    try:
                        save_id(conn, i.id)
                        api.update_status(status = format_message(i), in_reply_to_status_id = i.id)
                        logging.info('send for @' + i.author.screen_name + ': ' + str(i.id))
                    except tweepy.error.TweepError, e:
                        logging.info('publish error for @' + i.author.screen_name + ' - ' + str(i.id) + ': ' + str(e))
        except Exception, e:
            logging.info('cannot get mentions: ' + str(e))
        time.sleep(update_time)

if __name__ == '__main__':
    logging.basicConfig(filename = 'replier.log',
                        level = logging.INFO,
                        format = '%(asctime)s %(levelname)-8s %(message)s',
                        datefmt = '%d.%m.%Y %H:%M:%S')
    api = init_api()
    conn = init_db()
    try:
        work(api, conn)
    except KeyboardInterrupt, e:
        logging.info('interrupted')
    finally:
        conn.close()
    exit()
