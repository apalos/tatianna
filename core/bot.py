#!/usr/bin/env python
#
# tatianna v2
#
# Property of #penguins (GRNet).
#
# -*- coding: UTF-8 -*-


import ConfigParser
import re
import traceback
import requests
import json
import random
import time
import sqlite3
import irc.bot
import irc.strings
import sys
import ssl
import types


from BeautifulSoup import BeautifulSoup
from contextlib import closing
from ConfigParser import SafeConfigParser
from datetime import datetime, timedelta
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
from os.path import join as os_path_join
from os.path import isfile as os_path_isfile
from os.path import dirname as os_path_dirname


false = False
true = True
none = None
fkey = none
fapi = none
pver = sys.version_info
db_file = 'tat.sqlite3'


MAX_DL_SIZE = 3145728


class str_ops:

    def __init__(self):
        """
        """


    def uni_dec(self, input):
        if type(input) != unicode:
            input =  input.decode('utf-8')
            return input
        else:
            return input


    def uni_enc(self, input):
        if type(input) != unicode:
            input =  input.encode('utf-8')
            return input
        else:
            return input


class db_api:

    def __init__(self):
        """
        """


    def regexp(self, expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None


    def init_db(self):
        db = sqlite3.connect(db_file)
        dbc = db.cursor()
        dbc.execute('''CREATE TABLE IF NOT EXISTS QUOTES (ID INTEGER PRIMARY KEY,
                                                    QUOTE TEXT collate nocase,
                                                    QUOTE_DT DATETIME,
                                                    ADDED_BY TEXT,
                                                    CHANNEL TEXT
                                                    )''')

        dbc.execute('''CREATE TABLE IF NOT EXISTS URLS (ID INTEGER PRIMARY KEY,
                                                    URL TEXT collate nocase,
                                                    URL_DT DATETIME,
                                                    ADDED_BY TEXT,
                                                    CHANNEL TEXT
                                                    )''')
        db.close()


    def query_db(self, query, pattern = None):
        db = sqlite3.connect(db_file)
        db.create_function("REGEXP", 2, self.regexp)
        dbc = db.cursor()

        if pattern:
            dbc.execute(query, (pattern,))
        else:
            dbc.execute(query,)

        out = dbc.fetchone()
        db.close()
        return out


    def add_dbrow(self, query, quote, user = None, channel = None):
        db = sqlite3.connect(db_file)
        dbc = db.cursor()
        dbc.execute(query, (quote, time.strftime('%H-%M-%S %d-%m-%Y'), user, channel))
        db.commit()
        db.close()


    def query_maxid(self, query):
        db = sqlite3.connect(db_file)
        dbc = db.cursor()
        dbc.execute(query,)
        max_q = dbc.fetchone()
        db.close()
        return max_q[0]


class quote_api:

    def __init__(self):
        """
        """


    def get_quote(self, user, channel, msg):
        toks = msg.split(' ')
        dba = db_api()
        q = None
        qq = None
        out = None
        if len(toks) < 2:
            query = '''SELECT id, quote FROM quotes ORDER BY RANDOM() LIMIT 1'''
            out = dba.query_db(query)
        else:
            idq = re.match('id:', toks[1])
            if idq:
                idx = toks[1].split(':', 1)
                if idx[1].isdigit():
                    query = '''SELECT id, quote, added_by, quote_dt FROM quotes WHERE id == ?'''
                    pattern = idx[1]
                else:
                    query = None
            else:
                query = '''SELECT id, quote FROM quotes WHERE quote like ? ORDER BY RANDOM()'''
                pattern = '%%%s%%' % ' ' . join(toks[1:])
                # not needed, the irc module seems to take care of it
                # pattern = ops.uni_dec(pattern)

            if query:
                out = dba.query_db(query, pattern)


        if out and (len(out) >= 2):
            qn = out[0] # id
            qq = out[1] # quote

        qt = ''
        qu = ''
        if out and (len(out) == 4):
            qu = ' ' + out[2] # user
            qt = ' # ' + out[3] + ' ' # time
            qt = qt.replace('-', ':', 2)

        if qq:
            q = '[' + str(qn) + qu + qt + '] ' + qq

        return q


    def add_quote(self, user, channel, msg):
        ret = None
        dba = db_api()
        quote = ' ' . join(msg.split(' ')[1:])
        #not needed irc module seems to take care of it
        #ops = str_ops()
        #quote = ops.uni_dec(quote)
        #dec_user = ops.uni_dec(user)
        #dec_channel = ops.uni_dec(channel)
        query = '''INSERT INTO quotes (QUOTE, QUOTE_DT, ADDED_BY, CHANNEL) VALUES (?, ?, ?, ?)'''
        dba.add_dbrow(query, quote, user, channel)

        #No intention of deleting, ever...
        query = '''SELECT MAX(id) FROM quotes'''
        max_q = dba.query_maxid(query)
        ret = 'Quote ' + str(max_q) + ' added!'
        return ret


class http_api:

    def __init__(self):
        """
        """


    def get_title(self, url):
        res, resp = open_url(url)
        title = ''

        print(res)
        if res != -1:
            try:
                soup = BeautifulSoup(resp)
            except Exception:
                soup = None
            else:
                try:
                    title = soup.title.string
                    decoded = BeautifulSoup(title, convertEntities = BeautifulSoup.HTML_ENTITIES)
                    title = '' . join(decoded)
                except Exception:
                    title = ' '

        return title


    def add_url(self, url, user, channel):
        ret = None
        dba = db_api()
        #slower
        #query = '''SELECT id, url, added_by, url_dt FROM urls WHERE url REGEXP ? ORDER BY URL_DT LIMIT 1'''
        #pattern = 'http(s)?://%s$' % search_url
        #out = dba.query_db(query, pattern)
        query = '''SELECT id, url, added_by, url_dt FROM urls WHERE url = ? ORDER BY URL_DT'''
        search_url = re.sub('http(s)?://', '', url, 1)
        out = dba.query_db(query, search_url)
        if out == None:
            out = dba.query_db(query, search_url + '/') #old bot did not strip trailing /
        if out == None:
            query = '''INSERT INTO urls (URL, URL_DT, ADDED_BY, CHANNEL) VALUES (?, ?, ?, ?)'''
            #insert urls stripped
            dba.add_dbrow(query, search_url, user, channel)
        else:
            #paranoid
            if (len(out) == 4):
                qu = out[2] #user
                qt = out[3] #time

            fmt = '%H-%M-%S %d-%m-%Y'
            dtm = time.strptime(qt, fmt)
            td =  (time.time() - time.mktime(dtm))
            mins, secs = divmod(td, 60)
            hours, mins = divmod(mins, 60)
            days, hours = divmod(hours, 24)
            years, days = divmod(days, 365)

            pattern = r'%d years %d days %d hours %d mins and %d seconds ago'
            out = pattern % (years, days, hours, mins, secs)
            if years == 0:
                pattern = r'%d days %d hours %d mins and %d seconds ago'
                out = pattern % (days, hours, mins, secs)
            if days == 0:
                pattern = r'%d hours %d mins and %d seconds ago'
                out = pattern % (hours, mins, secs)
            ret = 'OLD! ' + qu + ' mentioned it ' + out
        return ret


def expand_bot_path(filename):
    '''
    '''
    # try "core/"
    first_try = os_path_join(os_path_dirname(__file__), filename)
    if os_path_isfile(first_try):
        return first_try

    # try "core/.."
    second_try = os_path_join(os_path_dirname(__file__), '..', filename)
    if os_path_isfile(second_try):
        return second_try

    raise IOError('File "{0}" not found under "{1}" or "{2}"'.format(
                  filename, first_try, second_try))


class reddit_feed:

    subreddits = None

    def __init__(self):
        """
        """
        subreddits_file = "subreddits.json"
        try:
            with open(expand_bot_path(subreddits_file), 'r') as f:
                self.subreddits = json.loads(f.read())

        except Exception as e:
            print("Caught exception while loading subreddits ({}), using defaults".format(subreddits_file))
            print("%s: %s") % (e.__class__.__name__, e.args)
            self.subreddits = [
                    'AskReddit', 'funny', 'videos', 'WTF', 'movies',
                    'videos', 'gaming'
            ]


    def get_reddit_url(self, what = None):
        subreddits = self.subreddits
        link = ''

        if what:
            nfeed = what
        else:
            try:
                nfeed = random.choice(subreddits)
            except Exception as e:
                print("Subreddits {}".format(subreddits))
                print("%s: %s" % (e.__class__.__name__, e.args))
                return None

        json_data = render_to_json('http://www.reddit.com/r/' + nfeed + '/top.json?limit=50')

        if json_data:
            try:
                children_length = len(json_data['data']['children'])
                if children_length == 1:
                    print("WARNING: children == 1 for {} - This used to throw an exception".format(what))
                    pnum = json_data['data']['children']
                else:
                    pnum = random.randint(1, len(json_data['data']['children']) - 1)
            except (KeyError, ValueError) as e:
                link = 'Overexcitement overflow. Try again'
                None

            try:
                data = json_data['data']['children'][pnum]['data']
            except (KeyError, ValueError) as e:
                link = 'Overexcitement detected. Try again'
            else:
                link = data['url']
        else:
            link = 'Failed to fetch data'

        return nfeed + ': ' + link


class fb_feed:

    def __init__(self):
        """
        """


    def get_fb_post(self, init_url, rchoice, app_id, app_secret, pnum=None):
        follow_url = init_url + rchoice
        ret = None
        #extract post data
        post_url = self.create_post_url(follow_url, app_id, app_secret)
        json_postdata = render_to_json(post_url)
        if json_postdata:
            json_fbposts = json_postdata['data']
            #print post messages and ids
            if pnum == None:
                # XXX this probably throws an exception too
                pnum =  random.randint(1, len(json_fbposts) - 1)

            if len(json_fbposts) >= pnum:
                post = json_fbposts[pnum]
            else:
                return None

            try:
                news = post['message']
            #XXX
            except KeyError as ValueError:
                news = ''
            try:
                link = ' ' + post['link']
            except KeyError as ValueError:
                link = ''

            ret = news + link
        return ret


    def create_post_url(self, graph_url, app_id, app_secret):
        #method to return
        post_args = '/posts/?key=value&access_token=' + app_id + '|' + app_secret
        post_url = graph_url + post_args
        return post_url


class bot_connect(irc.bot.SingleServerIRCBot):
    """Connect on channel"""

    reddit_feed = None

    def __init__(self, channel, nickname, realname, server, port = 6667, ssl_en = False):
        if ssl_en:
            ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname, connect_factory = ssl_factory)
        else:
            irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
        self.channel = '#' + channel
        self.nickname = nickname
        self.realname = realname
        # set 'errors' to replace unicode decode failures with '?'
        self.connection.buffer_class.errors = 'replace'
        try:
            self.start()
        except KeyboardInterrupt:
            self.connection.quit("Exiting.")
            print "Quit IRC."
        except Exception as e:
            # add better exception handling and stacktrace
            print("%s: %s" % (e.__class__.__name__, e.args))
            traceback.print_exc()
            self.connection.quit("%s: %s" % (e.__class__.__name__, e.args))
        raise


    # XXX on_ events check events.py
    def on_nicknameinuse(self, con, evnt):
        print("Nickname in use")


    def on_welcome(self, con, evnt):
        con.join(self.channel)


    def on_pubmsg(self, con, evnt):
        func = self.get_match(evnt.arguments[0])
        if (func):
            method = getattr(self, "do_" + func)
            method(evnt)
        return


    def do_command(self, evnt):
        nick = evnt.source.nick
        con = self.connection
        chan = self.channel
        nick = evnt.source.nick
        msg = evnt.arguments[0]
        cmd = msg.split(' ', 1)

        if cmd[0] == '!quote':
            a = quote_api()
            ret = a.get_quote(nick, chan, msg)
            if ret:
                safe_tell(con, chan, ret)
        elif cmd[0] == '!add':
            a = quote_api()
            ret = a.add_quote(nick, chan, msg)
            if ret:
                safe_tell(con, chan, ret)
        elif cmd[0] == '!news':
            a = fb_feed()
            # newslist = ['news247', 'cnninternational', 'HuffPostGreece',
            #             'HuffingtonPost', 'aljazeera', 'bbcnews']
            newslist = ['lubenmag', 'tokoulouri']
            nfeed = random.choice(newslist)
            if fapi:
                post = a.get_fb_post("https://graph.facebook.com/", nfeed, fapi, fkey, None)
                if post:
                    fpost = nfeed + ': ' + post
                    safe_tell(con, chan, fpost)
            else:
                safe_tell(con, chan, 'Facebook keys missing')
        elif cmd[0] == '!reddit':
            # catch all exceptions in case something goes bad..
            try:
                if self.reddit_feed is None:
                    print("Initialising reddit_feed")
                    self.reddit_feed = reddit_feed()
                if len(cmd) > 1:
                    try:
                        url = self.reddit_feed.get_reddit_url(cmd[1])
                    except:
                        url = self.reddit_feed.get_reddit_url()
                else:
                    url = self.reddit_feed.get_reddit_url()
                if url:
                    # warn that the URLs may be NSFW
                    safe_tell(con, chan, 'NSFW ' + url)
            except Exception as e:
                print("%s: %s" % (e.__class__.__name__, e.args))
                print(traceback.format_exc())
                return None


    def do_try_url(self, evnt):
        nick = evnt.source.nick
        chan = self.channel
        con = self.connection
        url = http_api()
        s = re.search('http(s)?://([^\s]+)', evnt.arguments[0])
        if s:
            s_url = s.group()
        else:
            return
        if re.findall(r'\S/+$', s_url):
            s_url = re.sub('/+$', '', s_url)

        ret = url.get_title(s_url)
        if ret:
            old = url.add_url(s_url, nick, chan)
            if old:
                safe_tell(con, chan, old)

        if ret:
            safe_tell(con, chan, '[' + ret + ']')


    def get_match(self, what):
        chan = self.channel
        con = self.connection
        #first arguement will accept regexp
        cmd_dict = {
            '^!': 'command',
            'http(s)?': 'try_url',
        };

        for key, value in cmd_dict.iteritems():
                m = re.search(key, what)
                if m:
                    return value
        return None


def open_url(url, tout = 10, max_download_size=MAX_DL_SIZE):
    sz = 0

    user_agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; PPC Mac OS X 10.9; rv:41.0) Gecko/20100101 Firefox/41.0'}
    # this is still horrible but at least less prone to mistakes
    # due to ordering
    err = {
            'ERR-4': (-4, 'Other exception'),
            'ERR-3': (-3, 'Unknown mime type'),
            'ERR-2': (-2, 'File size exceeded'),
            'ERR-1': (-1, 'Request failed')
          }

    length_so_far = 0
    full_content = ""

    try:
        with closing(requests.get(url, stream=True, headers=user_agent, timeout=tout)) as resp:
            for content in resp.iter_content(chunk_size=256000, decode_unicode=False):
                length_so_far += len(content)
                full_content += content
                if length_so_far > max_download_size:
                    break
            print("Fetched: {} bytes".format(length_so_far))
            try:
                mime = resp.headers['content-type']
            except KeyError:
                mime = ''
            # this can probably optimised by setting the accept http header but leaving
            # it as is, as we are just trying to fix the content length issues
            if mime[:9] != 'text/html' and mime[:16] != 'application/json':
                return err['ERR-3']

    except requests.exceptions.RequestException as e:
        print('Error retrieving {}: {}') . format(url, e)
        return err['ERR-1']
    except Exception:
        # is this ever reached? @apalos
        print(traceback.format_exc())
        return err['ERR-4']

    return (length_so_far, full_content)


def render_to_json(url):
    #render graph url call to JSON
    res, resp = open_url(url)
    json_data = None

    if res > 0:
        try:
            json_data = json.loads(resp)
        except ValueError as e:
            return None

    return json_data


def safe_tell(con, chan, what):
        #get rid of carriage returns
        sayl = []
        chunk = ''
        ret = '' . join(what.splitlines())
        #According to RFC http://tools.ietf.org/html/rfc2812#page-6,
        #clients should not transmit more than 512 bytes
        try:
            sz_f = ret.encode('utf-8') + b'\r\n'
        except UnicodeEncodeError:
            #XXX FIXME
            return
        totsz = 0
        sz = 0
        if len(sz_f) > 512:
            toks = ret.split(' ')
            for w in toks:
                sz = w.encode('utf-8') + b' ' + b'\r\n'
                if totsz + len(sz) <= 512:
                    totsz += len(sz)
                    chunk += ' ' + w
                else:
                    sayl.append(chunk)
                    chunk = ''
                    totsz = 0
            sayl.append(chunk)
        else:
            sayl.append(ret)

        try:
            for i in sayl:
                con.privmsg(chan, i)
        except irc.client.InvalidCharacters as err:
            print(err)
        except irc.client.MessageTooLong as err:
            print(err)


def usage():
    print('usage: bot.py <config file>')


def random_petname():
    petnames = none
    petnames_file = 'petnames.json'

    try:
        with open(expand_bot_path(petnames_file), 'r') as f:
            petnames = json.loads(f.read())
    
    except Exception as e:
        print('[!] couldn\'t load petnames, using default list')
        petnames = ['tatianna', 'svetlana', 'delas', 'teslas']

    return random.choice(petnames)


def get_cfg_value(configfile, category, what, strict = 'yes'):
    ret = None
    parser = SafeConfigParser()
    # FIXME make the path configurable
    parser.read(configfile)

    try:
        ret = parser.get(category, what)
    except ConfigParser.NoSectionError:
        print('No section [%s] found in config file. Fix your config file' % category)
        if strict == 'yes':
            exit(1);
    except ConfigParser.NoOptionError:
        print('No option %s= found in config file. Fix your config file' % what)
        if strict == 'yes':
            exit(1);

    return ret


def main():

    try:
        configfile = sys.argv[1]
    except IndexError:
        usage()
        exit(1)

    # XXX FIXME better error checking on config file
    try:
        port = get_cfg_value(configfile, 'irc', 'port')
        server = get_cfg_value(configfile, 'irc', 'server')
        ssl_en =  get_cfg_value(configfile, 'irc', 'ssl')
        channel =  get_cfg_value(configfile, 'irc', 'channel')
        port =  int(get_cfg_value(configfile, 'irc', 'port'))
        fkey =  get_cfg_value(configfile, 'irc', 'facebook_key', 'no')
        fapi =  get_cfg_value(configfile, 'irc', 'facebook_api', 'no')
    except ValueError as e:
        print('Options missing %s') % e
        exit(1);

    if ssl_en == 'yes':
        ssl_en = true
    else:
        ssl_en = false

    nickname = random_petname()
    realname = random_petname()

    a = db_api()
    a.init_db()

    try:
        b = bot_connect(channel, nickname, realname, server, port, ssl_en)
    except Exception as e:
        print('%s' % (e))


if __name__ == '__main__':
    main()

# EOF
