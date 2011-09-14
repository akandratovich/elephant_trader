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
        conn.execute('select * from called')
    except sqlite3.OperationalError, e:
        conn.execute('create table called (id int)')
        conn.commit()
    return conn

def init_facts():
    facts = set()
    path = "facts.txt"
    with open(path) as f:
        for line in f:
            facts.add(line.strip())
    f.close()
    return facts

def save_id(conn, id):
    conn.execute('insert into called values(' + str(id) + ')')
    conn.commit()

def is_called(conn, id):
    (count,) = conn.execute('select count(id) from called where id = ' + str(id)).fetchone()
    return count > 0

def get_random_fact(facts):
    f = facts.pop()
    facts.add(f)
    return f

def format_message(mention, facts):
    user = '@' + mention.from_user
    fact = get_random_fact(facts)
    message = user + unicode(" а Вы знали, что " + fact, "utf-8") + " ?"
    return message

def work(api, conn, facts):
    update_time = 120
    while True:
        try:
            m = api.search(unicode("слон", "utf-8"))
            for i in m:
                if not is_called(conn, i.from_user_id):
                    try:
                        save_id(conn, i.from_user_id)
                        api.update_status(status = format_message(i, facts), in_reply_to_status_id = i.id)
                        logging.info('send for @' + i.from_user + ': ' + str(i.id))
                    except tweepy.error.TweepError, e:
                        logging.info('publish error for @' + i.from_user + ' - ' + str(i.id) + ': ' + str(e))
        except tweepy.error.TweepError, e:
            logging.info('cannot get mentions: ' + str(e))
        time.sleep(update_time)

if __name__ == '__main__':
    logging.basicConfig(filename = 'caller.log',
                        level = logging.INFO,
                        format = '%(asctime)s %(levelname)-8s %(message)s',
                        datefmt = '%d.%m.%Y %H:%M:%S')
    api = init_api()
    conn = init_db()
    facts = init_facts()
    try:
        work(api, conn, facts)
    except KeyboardInterrupt, e:
        logging.info('interrupted')
    finally:
        conn.close()
    exit()