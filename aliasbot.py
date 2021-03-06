#!/usr/bin/python3

import requests
import json
import os
import time
import random as rand
import subprocess

#telegram bot stuff
url = "https://api.telegram.org/bot%s/%s"
token = open("token.txt").read().replace('\n', '')
print(url % (token, "getUpdates"))
path = os.path.dirname(__file__)

#globals
locked = []
aliases = {}
commands = {}
chat_id = 0
SCH_CHID = -1001032618176
LOG_CHID = -1001098108881

#requests stuff
ConnectionError = requests.exceptions.ConnectionError

def isCommand(text, command):
    if text[:len(command)] != command:
        return False
    else:
        return True

def stripCommand(text, command):
    return text[len(command) + 1:]

def getUpdates():
    try:
        r = requests.get(
                url % (token, "getUpdates"),
                data={"offset": getUpdates.offset},
                timeout=60
                )
        try:
            r = json.loads(r.text)
        except:
            print("Loading error while getting updates")
            return [], True
        r = r['result']
        if len(r) > 0:
            getUpdates.offset = int(r[-1]['update_id']) + 1
    except ConnectionError:
        print("Connection error while getting updates")
        return [], True
    return r, False
getUpdates.offset = 0

def sendMessage(message, reply_id=False, markdown=True):
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_id:
        payload['reply_to_message_id'] = reply_id
    if not markdown:
        del payload['parse_mode']
    try:
        tresponse = requests.post(
                url % (token, "sendMessage"),
                data=payload,
                timeout=2
                )
        resp = json.loads(tresponse.text)
        if not resp["ok"]:
            return sendMessage(message, reply_id, False)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        print("Connection error while sending message")
        return True
    return False

def loadAliases():
    aliases = {}
    aliasFile = open(path + "/aliases.json").read()
    aliases = json.loads(aliasFile)
    return aliases

def saveAliases():
    aliasFile = open(path + "/aliases.json", "w")
    aliasFile.write(json.dumps(aliases, indent=4))
    aliasFile.close()

def loadLocked():
    locked = []
    lfile = open(path + "/locked.txt").read()
    for line in lfile.split('\n'):
        if line != '':
            locked.append(line)
    return locked

def logMessage(message):
    baseLM = "user: %s ; mesg: %s ; chid: %s\n"
    if 'text' in message.keys():
        filledLM = baseLM % (message['from']['first_name'],
                message['text'],
                message['chat']['id'])
        logfile = open(path + "/logfile.txt", "a")
        logfile.write(filledLM)
        logfile.close()
    if message['chat']['id'] == SCH_CHID:
        payload = {
                'chat_id': LOG_CHID,
                'from_chat_id': SCH_CHID,
                'disable_notification': True,
                'message_id': message['message_id']
                }
#       try:
#           tresponse = requests.post(url % (token, "forwardMessage"),
#                   data=payload, timeout=2)
#       except:
#           return

def alias(content, uid):
    alias = content.split('=')[0]
    while alias[0] == ' ':
        alias = alias[1:]
    while alias[-1] == ' ':
        alias = alias[:-1]
    alias = alias.replace(' ', '_')
    value = '='.join(content.split('=')[1:])
    if len(alias.split()) == 1:
        if alias not in locked or uid == 204403520:
            aliases[alias] = value
            print("alias " + alias + "=" + value + " by " + name)
            saveAliases()
            sendMessage("Aliased " + alias + " to " + value, message_id)
        else:
            print("cannot unlock alias")
            sendMessage("Alias is locked, sorry", message_id)
    else:
        print("alias malformed")
        sendMessage("Alias must be a single term", message_id)


def unalias(content, uid):
    alias = content
    if alias not in locked:
        if len(alias.split()) == 1 and alias in aliases.keys():
            aliases[alias] = ''
            print("del " + alias)
            saveAliases()
            sendMessage("Unaliased " + alias, message_id)
        else:
            print("unalias malformed")
            sendMessage("Invalid alias", message_id)
    else:
        print("cannot unlock alias")
        sendMessage("Alias is locked, sorry", message_id)


def random(content, uid):
    randomAlias = rand.choice(list(aliases.keys()))
    randomAliasStr = "/%s = %s" % (randomAlias, aliases[randomAlias])
    print(randomAliasStr)
    sendMessage(randomAliasStr)


def uptime(content, uid):
    sendMessage('`' + subprocess.Popen('uptime', stdout=subprocess.PIPE).communicate()[0].decode("utf-8") + '`')


def welp(content, uid):
    sendMessage("gg")


def rip(content, uid):
    response = rand.choice(["me", "rip is right", "rip is me"])
    sendMessage(response)

def amirite(content, uid):
    if rand.randint(1, 10) == 4:
        response = "yep"
    else:
        response = "¬_¬"
    sendMessage(response)

def remind(content, uid):
    global chat_id
    chat_id = SCH_CHID
    sendMessage("heres your periodic schedule reminder!!!\n" + aliases["schedule"])

def newdaypb(content, uid):
    sendMessage(aliases["newdaypb"])

def queue(content, uid):
    print("cue")
    if rand.randint(1, 10) < 3:
        print("Q")
        sendMessage("u wot m8", message_id)

def stan(content, uid):
    sendMessage('no', message_id)

commands = {
        '/alias':       alias,
        '/unalias':     unalias,
        '/random':      random,
        '/time':        uptime,
        'w/elp':        welp,
        '/rip':         rip,
        '/amirite':     amirite,
        '/remindme':    remind,
        '/newdaypb':    newdaypb,
        '/q@IshanBot':  queue,
        'stan':         stan,
        'hi stan':      stan
        }

if __name__ == "__main__":
    aliases = loadAliases()
    locked = loadLocked()
    print("Started")
    loffset = getUpdates.offset - 1
    while getUpdates.offset != loffset:
        loffset = getUpdates.offset
        getUpdates()
    print("Updated to:", getUpdates.offset)

while __name__ == "__main__":
    try:
        r, err = getUpdates()

        if len(r) != 0 and not err:
            print("received updates")
        elif err:
            time.sleep(1)

        for update in r:
            message = update.get('message')
            if message == None:
                continue
            logMessage(message)
            message_id = message['message_id']
            print(message_id)
            chat = message['chat']
            chat_id = chat['id']
            user = message.get('from')
            name = "@" + user.get('username')
            if name == None:
                name = user.get('first_name')
            uid = user['id']
            if chat_id == LOG_CHID:
                try:
                    payload = {
                            'chat_id': LOG_CHID,
                            'user_id': uid
                            }
                    requests.post(
                            url % (token, "kickChatMember"),
                            data=payload,
                            timeout=2
                            )
                    continue
                except ConnectionError:
                    pass
            text = message.get('text', ' ')

            found = False
            for command in commands.keys():
                if isCommand(text, command):
                    content = stripCommand(text, command)
                    found = True
                    commands[command](content, uid)
            if found:
                continue

            if "/" in text:
                terms = text.split()
                response = ''
                for term in terms:
                    if '/' == term[0]:
                        alias = ''
                        if '@' in term and term[1:].split('@')[-1] == "IshanBot":
                            alias = term[1:].split('@')[0]
                        else:
                            alias = term[1:]
                        """
                        for key in aliases.keys():
                            if 'legendary' in aliases[key]:
                                print(key)
                                print([ord(c) for c in key])
                                print([ord(c) for c in alias])
                                print(alias == key)
                                """
                        response += aliases.get(alias, '')
                if response != '':
                    sendMessage(response + ' ' + name)

    except KeyboardInterrupt:
        print("Control menu:\n 0 - Quit\n 1 - Reload locks")
        choice = int(input("> "))
        if choice == 1:
            locked = loadLocked()
        else:
            saveAliases()
            raise SystemExit
    except BaseException as e:
        print(str(e))
