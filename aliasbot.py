#!/usr/bin/python3

import requests
import json
import os
import time
import random
#telegram bot stuff
url = "https://api.telegram.org/bot%s/%s"
token = "insert token here"

#parameters
chat_id = ""
max_value = 1024
path = os.path.dirname(__file__)

#requests stuff
ConnectionError = requests.exceptions.ConnectionError

def getUpdates(offset):
    #gets all updates starting with offset
    try:
        r = requests.get(url % (token, "getUpdates"), data={"offset": offset}, timeout=2)
    except:
        print("Error while getting updates")
        return [], offset, True
    try:
        r = json.loads(r.text)
    except:
        return [], offset, True
    r = r["result"]
    if len(r) > 0:
        offset = int(r[-1]['update_id']) + 1
    return r, offset, False

start = time.time()
latestOffset = 1
#update current offset to show the latest messages because telegram is dumb
print("Updating...", end="")
oldLatestOffset = 0
while oldLatestOffset < latestOffset:
    oldLatestOffset = latestOffset
    DRAIN, latestOffset, err = getUpdates(latestOffset)
print("\rUpdated    ")

def sendMessage(message, reply_to_message_id=False, tries=0):
    #send message to current chat with content message
    if tries > 3:
        return True
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if tries > 0:
        #don't parse if we failed the send before
        del payload["parse_mode"]
    if reply_to_message_id:
        #do a reply if specified
        payload['reply_to_message_id'] = reply_to_message_id
        del payload["parse_mode"]
    try:
        tresponse = requests.post(url % (token, "sendMessage"), data=payload, timeout=2)
    except:
        #handle a timeout by trying again with all the same params
        print("Error while sending message (tries: %s)" % str(tries + 1))
        time.sleep(0.5)
        sendMessage(message, reply_to_message_id, tries + 1)
        return True
    try:
        resp = json.loads(tresponse.text)
    except:
        return True
    if not resp["ok"] and tries < 3:
        #something probably went wrong with the parsing, let's try again
        sendMessage(message, reply_to_message_id, tries + 1)
    return False

def loadAliases():
    #puts saved aliases into an aliases dict
    aliases = {}
    keys = []
    aliasFile = open(path + "/aliases.txt").read()
    for term in aliasFile.split("</term>\n"):
        term = term.replace("<term>","")
        alias = term.split("=")[0]
        value = "=".join(term.split("=")[1:])
        if alias != "" and value != "":
            aliases[alias] = value
            keys.append(alias)
    return aliases, keys

def saveAliases(aliases):
    #puts an aliases dict into a savefile
    aliasFile = open(path + "/aliases.txt", "w")
    aliasStr = ""
    for alias in aliases.keys():
        aliasStr += "<term>" + alias + "=" + aliases[alias] + "</term>\n"
    aliasFile.write(aliasStr)
    aliasFile.close()

aliases, aliasList = loadAliases() #load aliases on start
print("Started")

stime = 0
locked = []
users = {}
banned = {}

def logMessage(message):
    baseLM = "user: %s ; mesg: %s ; chid: %s\n"
    filledLM = baseLM % (message['from']['first_name'],
            message['text'],
            message['chat']['id'])
    logfile = open(path + "/logfile.txt", "a")
    logfile.write(filledLM)
    logfile.close()

while True:
    try:
        #reload locked aliases on every cycle
        locked = []
        lfile = open(path + "/locked.txt").read()
        for line in lfile.split('\n'):
            if line != '':
                locked.append(line)

        #get updates and the newest offset
        r, latestOffset, err = getUpdates(latestOffset)

        #handle spam detection and unbanning
        if int(time.time()) % 6 == 0:
            users = {}
        toUnban = []
        for name in banned.keys():
            if time.time() > banned[name]:
                print("unbanned " + name)
                toUnban.append(name)
        for name in toUnban:
            del banned[name]

        #do a dumb smart sleep thingo
        if len(r) == 0 and not err:
            if stime < 5:
                stime += 0.25
                print("\rinterval incremented: " + str(stime) + "   ", end="")
        elif err:
            stime = 2.5
        else:
            if stime != 0:
                print("\ninterval reset                 ")
                stime = 0
            print("received updates")

        for update in r:
            #loop through each update
            if "message" in update.keys():
                message = update['message']
                try:
                    logMessage(message)
                except:
                    pass
                message_id = message['message_id']
                chat = message['chat']
                chat_id = chat['id']
                if "from" in message.keys():
                    #find and store name of user
                    user = message['from']
                    if "username" in user.keys():
                        name = "@" + user['username']
                    else:
                        name = user['first_name']
                    if name in banned.keys() and name != "@pieman2201":
                        continue
                if "text" in message.keys():
                    #get the text of the message
                    text = message['text']
                    if "/alias" == text[:6]:
                        #add to the user's count
                        if name in users.keys():
                            users[name] += 1
                        else:
                            users[name] = 1

                        #check if the message is an /alias command and parse
                        content = text[7:]
                        try:
                            alias = content.split("=")[0]
                            alias = alias.replace(" ", "")
                            value = "=".join(content.split("=")[1:])
                            if len(alias.split()) == 1:
                                if alias not in locked or name == "@pieman2201":
                                    if len(value) < max_value:
                                        aliases[alias] = value
                                        if "term>" not in alias and "term>" not in value:
                                            print("alias " + alias + "=" + value + " by " + name)
                                            saveAliases(aliases)
                                            sendMessage("Aliased " + alias + " to " + value, message_id)
                                        else:
                                            banned[name] = time.time() + 300
                                            sendMessage("Banned " + name + " for 5m (reason: hacks)")
                                            print("banned " + name)
                                    else:
                                        print("value too big")
                                        sendMessage("Value is too big (" + str(max_value) + " chars)",
                                                message_id)
                                else:
                                    print("cannot unlock alias")
                                    sendMessage("Alias is locked, sorry", message_id)
                            else:
                                print("alias malformed")
                                sendMessage("Alias must be a single term", message_id)
                        except:
                            pass

                    elif "/unalias" == text[:8]:
                        #add to the user's count
                        if name in users.keys():
                            users[name] += 1
                        else:
                            users[name] = 1

                        #check if the message is an /unalias command and parse
                        content = text[9:]
                        try:
                            alias = content
                            if alias not in locked:
                                if len(alias.split()) == 1:
                                    if alias in aliases.keys():
                                        del aliases[alias]
                                    print("del " + alias)
                                    saveAliases(aliases)
                                    sendMessage("Unaliased " + alias, message_id)
                                else:
                                    print("unalias malformed")
                                    sendMessage("Alias must be a single term", message_id)
                            else:
                                print("cannot unlock alias")
                                sendMessage("Alias is locked, sorry", message_id)
                        except:
                            pass
                    elif "w/elp" == text[:5]:
                        sendMessage("gg")
                    elif "/random" == text[:7]:
                        #add to the user's count
                        if name in users.keys():
                            users[name] += 1
                        else:
                            users[name] = 1

                        #send a random one
                        randomAlias = random.choice(aliasList)
                        randomAliasStr = "/%s = %s" % (randomAlias, aliases[randomAlias])
                        sendMessage(randomAliasStr)

                    elif "/ban" == text[:4] and name == "@pieman2201":
                        try:
                            nameToBan, length = text[5:].split()
                            banned[nameToBan] = time.time() + int(length)
                            sendMessage("Banned user (reason: mod request)")
                        except:
                            continue

                    elif "/time" == text[:5]:
                        #add to the user's count (there should really be a func for this)
                        if name in users.keys():
                            users[name] += 1
                        else:
                            users[name] = 1

                        #send the current time in seconds since the bot started
                        sendMessage("up for " + str(time.time() - start) + "s")

                    elif "/" in text:
                        #if there is a different command in the message
                        terms = text.split()
                        commands = []
                        for term in terms:
                            #find the command in the message
                            if "/" == term[0]:
                                if "@" in term:
                                    alias = term[1:].split("@")[0]
                                else:
                                    alias = term[1:]
                                commands.append(alias)
                        response = ""
                        aliasesUsed = 0
                        for command in commands:
                            #for each command in the message...
                            for alias in aliases.keys():
                                #check to see if the command is an alias...
                                if alias == command:
                                    #if it is, add the value to the response
                                    value = aliases[alias]
                                    aliasesUsed += 1
                                    response += value + " "
                                    print(alias + " -> " + value)

                        if response != "" and len(response) < max_value:
                            #add to the user's count based on length of message
                            if aliasesUsed > 1:
                                if name in users.keys():
                                    users[name] += int(len(response) / 10)
                                else:
                                    users[name] = int(len(response) / 10)
                            else:
                                if name in users.keys():
                                    users[name] += 1
                                else:
                                    users[name] = 1
                            #check if the message is blank. if not...
                            response += name
                            sendMessage(response) #send the values
                    else:
                        #unrelated message handling because telegram is dumb
                        pass

                    #handle banning users
                    for name in users.keys():
                        if users[name] >= 5:
                            users[name] = 0
                            banned[name] = time.time() + 300
                            sendMessage("Banned " + name + " for 5m (reason: spam)")
                            print("banned " + name)

        #sleep for the determined amount of time
        time.sleep(stime)

    except ConnectionError:
        print("ConnectionError") #should put stuff here but whatever
