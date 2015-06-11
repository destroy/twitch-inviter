# -*- coding: utf-8 -*-
import requests
import json
from Queue import Queue
import threading
import time
import eventlet
eventlet.monkey_patch()

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'http://chatdepot.twitch.tv',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
    'Authorization': 'OAuth <!--REPLACE-->',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Referer': 'http://chatdepot.twitch.tv/crossdomain/tmi.html',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6,de;q=0.4,uk;q=0.2',
    'Cookie': '<!--REPLACE-->'
}

num_threads = 15
lock = threading.Lock()


def do_stuff(q, i, f_ok, f_fail):
    while True:
        user = q.get()
        try:
            with eventlet.Timeout(5):
                try:
                    response = requests.post('http://chatdepot.twitch.tv/room_memberships', data='oauth_token=<!--YOUR TOKEN-->&irc_channel=<!--ROOM-->&username=' + user, headers=headers, verify=False, allow_redirects=False)
                except eventlet.Timeout:
                    q.put(user)
                    q.task_done()
                    print 'rekt'
                    continue

            if response.status_code != 200:
                if response.status_code != 401:
                    q.put(user)
                else:
                    with lock:
                        f_fail.write(user + '\n')
            else:
                with lock:
                    f_ok.write(user + '\n')
                    print str(i) + ' ' + user
        except Exception as e:
            q.put(user)
        q.task_done()


#users_js = open('users.txt', 'r').read()
#users = json.loads(users_js)
#users = users['data']['chatters']['viewers']

q = Queue(maxsize=0)

ok_file = open('csgo_ok.txt', 'ab')
fail_file = open('csgo_401.txt', 'ab')

for i in range(num_threads):
    worker = threading.Thread(target=do_stuff, args=(q, i, ok_file, fail_file))
    worker.setDaemon(True)
    worker.start()

while True:
    try:
        response = requests.get('http://tmi.twitch.tv/group/user/faceittv/chatters?_=' + str(time.time()).replace('.', ''))
        users = json.loads(response.text)
        users = users['chatters']['viewers']
        print str(len(users)) + ' current chatters'
    except Exception:
        print 'get users exception'
        continue

    f = open('csgo_ok.txt', 'r')
    users_ok = f.read().splitlines()
    f.close()

    f = open('csgo_401.txt', 'r')
    users_401 = f.read().splitlines()
    f.close()

    users_done = users_ok + users_401
    new_users = set(users) - set(users_done)

    print str(len(new_users)) + ' new users'
    print ''

    for user in new_users:
        q.put(user)

    q.join()

    print '- DONE.'

    time.sleep(10)

