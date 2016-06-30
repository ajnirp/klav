#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
from datetime import datetime

import asyncio
import discord
import os
import random
import sys
import time
import urllib.error
import urllib.request

'''Flag parse begin'''

SILENT_ENTRY = False
if len(sys.argv) == 2 and sys.argv[1] == '-q':
    SILENT_ENTRY = True

'''Flag parse end'''

LINK_COOLDOWN = 20 # seconds

GSD_SERVER = "Girl's Day"
AOA_SERVER = "Ace of Angels"
BES_SERVER = "BESTie"
KNK_SERVER = "Keunakeun (KNK)"

client = discord.Client()
server = None

CONFIG = {
    GSD_SERVER: 'gsd.txt',
    AOA_SERVER: 'aoa.txt',
    BES_SERVER: 'bestie.txt',
    KNK_SERVER: 'knk.txt',
}

SERVERS = [GSD_SERVER, AOA_SERVER, BES_SERVER, KNK_SERVER]

WELCOME_MSG = {}
IDOLS = {}
ROLES_TO_AVOID_CHANGING = {}
DEFAULT_ROLE = {}
MOD_ROLE = {}
BIAS_CHANNEL = {}
MAIN_CHANNEL = {}
LINK_COMMANDS = {}

last_used = None

HELP_MSG = {s:'' for s in SERVERS}

def time_now():
    now = datetime.now()
    now = datetime.strftime(now, '%s')
    now = int(now)
    return now

def read_config():
    for s_name in SERVERS:
        IDOLS[s_name] = {}
        cfg_file = CONFIG[s_name]
        cfg_path = './config/' + cfg_file
        with open(cfg_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            WELCOME_MSG[s_name] = lines[1]
            for mapping in lines[2].split('\t'):
                split = mapping.split(',')
                val = split[-1]
                for key in split[:-1]:
                    IDOLS[s_name][key] = val
            ROLES_TO_AVOID_CHANGING[s_name] = lines[3].split()
            DEFAULT_ROLE[s_name] = lines[4]
            MOD_ROLE[s_name] = lines[5]
            BIAS_CHANNEL[s_name] = lines[6]
            MAIN_CHANNEL[s_name] = lines[7]
            LINK_COMMANDS[s_name] = {}
            for line in lines[8:]:
                split = line.split('\t')
                cmds = split[0]
                resp = ' '.join(s for s in split[1:])
                for cmd in cmds.split(','):
                    LINK_COMMANDS[s_name][cmd] = resp

    HELP_MSG[GSD_SERVER] = '**Commands**:'
    for pic_cmd in sorted(LINK_COMMANDS[GSD_SERVER].keys()):
        HELP_MSG[GSD_SERVER] += ' ' + pic_cmd
    HELP_MSG[GSD_SERVER] += ' goodnight time'

    HELP_MSG[AOA_SERVER] = '**Commands**:'
    for pic_cmd in sorted(LINK_COMMANDS[AOA_SERVER].keys()):
        HELP_MSG[AOA_SERVER] += ' ' + pic_cmd
    HELP_MSG[AOA_SERVER] += ' time'

    HELP_MSG[BES_SERVER] = '**Commands**:'
    for pic_cmd in sorted(LINK_COMMANDS[BES_SERVER].keys()):
        HELP_MSG[BES_SERVER] += ' ' + pic_cmd
    HELP_MSG[BES_SERVER] += ' time'

    HELP_MSG[GSD_SERVER] += '''
    **Biases**: To set your bias, post the name of your bias in **#whos-your-bias**, \
    and the bot will set your role to that idol. \
    If the bot is offline, don't worry, a mod will come along and do it for you!'''

    HELP_MSG[AOA_SERVER] += '''
    **Biases**: To set your bias, post the name of your bias in **#call_your_roles**, \
    and the bot will set your role to that idol. \
    If the bot is offline, don't worry, a mod will come along and do it for you!'''

    HELP_MSG[BES_SERVER] += '''
    **Biases**: To set your bias, post the name of your bias in **#whos-your-bias**, \
    and the bot will set your role to that idol. \
    If the bot is offline, don't worry, a mod will come along and do it for you!'''

BOT_OWNER_ID = '150919851710480384'
DILATER_ID = '138855295135907840'
LIKROS_ID = '167215724631293953'
DOLOKO_ID = '110106450516271104'
NADEKO_ID = '185826787131916290'
JONAH_ID = '120501261681426432'

def find_role(server, idol):
    for role in server.roles:
        if role.name.lower() == idol.lower():
            return role
    return None

def find_server(client, server_name):
    return next(s for s in client.servers if s.name == server_name)

def find_channel(server, channel_name):
    return next(c for c in server.channels if c.name == channel_name)

# Need to generalise this to arbit events
def countdown(client, msg):
    if msg.author.name != 'kwon': return
    if msg.server.name != AOA_SERVER: return
    if msg.content[:len('!countdown')] != '!countdown': return
    RELEASE = 'May 16 2016 12:00 AM'
    RELEASE = datetime.strptime(RELEASE, '%b %d %Y %I:%M %p')
    # general_chan = find_channel(client, MAIN_CHANNEL[msg.server.name])
    diff = RELEASE - datetime.now()
    secs = diff.seconds
    hrs = secs // 3600
    secs -= hrs * 3600
    mins = secs // 60
    secs -= mins * 60
    secs %= 60
    reply = 'Time until Good Luck: **' + str(hrs) + 'h' + str(mins) + 'm' + str(secs) + 's**!'
    yield from client.send_message(msg.channel, reply)

@client.event
@asyncio.coroutine
def on_ready():
    global CHANNEL
    global last_used, client, server
    print('Logged in as', client.user.name)
    last_used = time_now()
    aoa_server = next(s for s in client.servers if s.name == AOA_SERVER)
    meme_channel = next(c for c in aoa_server.channels if c.name == "meme_and_chill")
    if not SILENT_ENTRY:
        yield from client.send_message(meme_channel, "***HERE COME DAT BOT*** 👌 🔥 💯")

@client.event
@asyncio.coroutine
def on_member_join(member):
    server = member.server
    s_name = server.name

    if s_name == AOA_SERVER: return

    main_channel = find_channel(server, MAIN_CHANNEL[s_name])

    for role in server.roles:
        if role.name == DEFAULT_ROLE[s_name]:
            yield from client.add_roles(member, role)
            break

    welcome_msg = WELCOME_MSG[s_name]
    if welcome_msg == '..':
        return
    fmt = '{0.mention} ' + welcome_msg
    yield from client.send_message(main_channel, fmt.format(member, server))

@client.event
@asyncio.coroutine
def on_member_remove(member):
    server = member.server
    s_name = server.name

    if s_name == AOA_SERVER: return

    main_channel = find_channel(server, MAIN_CHANNEL[s_name])
    fmt = '{0.mention} has left the server'

    yield from client.send_message(main_channel, fmt.format(member, server))

@asyncio.coroutine
def set_bias(client, user, roles, msg):
    if roles is None or len(roles) == 0: return

    # We don't want to overwrite the user's existing roles
    # But we do want to overwrite the roles corresponding to IDOLS
    to_add_back = [r for r in user.roles if r.name in ROLES_TO_AVOID_CHANGING[msg.server.name]]
    to_add = roles + to_add_back
    role_str = ', '.join('**' + r.name.title() + '**' for r in roles)

    try:
        print('adding roles:', [r.name for r in to_add])
        yield from client.replace_roles(user, *to_add)
        response = '{0.mention} Your bias has been set to ' + role_str
        yield from client.send_message(msg.channel, response.format(user))
    except discord.Forbidden:
        print('cannot assign roles to', user.name, file=sys.stderr)
        return

@asyncio.coroutine
def unset_bias(client, user, roles, msg):
    if roles is None or len(roles) == 0: return

    roles_names = [r.name for r in roles]

    new_role_set = [r for r in user.roles \
        if r.name in ROLES_TO_AVOID_CHANGING[msg.server.name] or r.name not in roles_names]

    try:
        yield from client.replace_roles(user, *new_role_set)
        response = '{0.mention} updated your bias list'
        yield from client.send_message(msg.channel, response.format(user))
    except discord.Forbidden:
        print('cannot assign roles to', user.name, file=sys.stderr)
        return

@asyncio.coroutine
def link_request(client, msg):
    global last_used

    # not a command
    if msg.content[0] != '!': return

    # defaults to the AOA server (for PMs)
    s_name = AOA_SERVER if msg.server is None else msg.server.name

    pic_cmd = msg.content[1:]
    if pic_cmd not in LINK_COMMANDS[s_name]: return
    url = LINK_COMMANDS[s_name][pic_cmd]

    now = time_now()
    # diff = now - last_used
    diff = LINK_COOLDOWN + 1
    if diff < LINK_COOLDOWN:
        return
    else:
        last_used = now
        yield from client.send_message(msg.channel, url)

def is_mod(server, user):
    '''Is the user a mod on the specified server?'''
    mod_role = MOD_ROLE[server.name]
    return any([mod_role == r.name for r in user.roles])

def is_bias_channel(server, channel):
    '''Is 'channel' the bias channel for 'server'?'''
    return channel.name == BIAS_CHANNEL[server.name]

@asyncio.coroutine
def normal_remove_bias(client, msg):
    # works only in the bias channel
    if not is_bias_channel(msg.server, msg.channel): return

    if msg.content[:len('!remove')] != '!remove': return

    user = msg.author
    content = msg.content.lower()

    roles_to_remove = []
    for idol_nickname in IDOLS[msg.server.name]:
        if idol_nickname in content.split():
            actual_name = IDOLS[msg.server.name][idol_nickname]
            role = find_role(msg.server, actual_name)
            roles_to_remove.append(role)

    yield from unset_bias(client, user, roles_to_remove, msg)

@asyncio.coroutine
def normal_set_bias(client, msg):
    # works only in the bias channel
    if not is_bias_channel(msg.server, msg.channel): return

    if msg.content[:len('!bias')] == '!bias': return
    if msg.content[:len('!remove')] == '!remove': return

    user = msg.author
    content = msg.content.lower()

    roles_to_add = []
    for idol_nickname in IDOLS[msg.server.name]:
        for word in content.split():
            if idol_nickname in word:
                actual_name = IDOLS[msg.server.name][idol_nickname]
                role = find_role(msg.server, actual_name)
                roles_to_add.append(role)

    roles_to_add = list(set(roles_to_add))

    yield from set_bias(client, user, roles_to_add, msg)

@asyncio.coroutine
def help_request(client, msg):
    if msg.content[:8] != '!bothelp': return
    s_name = AOA_SERVER if msg.server is None else msg.server.name
    yield from client.send_message(msg.author, HELP_MSG[s_name])

@asyncio.coroutine
def delete_messages(client, msg):
    '''Delete a specified number of messages in the channel
    where msg 'msg' was posted. Only works if mods say it.'''
    if not is_mod(msg.server, msg.author): return
    if not msg.content[:7] == '!delete': return
    split = msg.content.split()
    if len(split) != 2: return
    num_msgs = split[1]
    try:
        num_msgs = 1 + int(num_msgs)
        try:
            yield from client.purge_from(msg.channel, limit=num_msgs)
        except discord.Forbidden:
            print('cannot purge')
    except ValueError: # failed to convert split[1] to int
        return

@asyncio.coroutine
def time_check(client, msg):
    if msg.content[:5] != '!time': return
    split = msg.content.split()
    if len(split) < 2: return
    place = '%20'.join(s.title() for s in split[1:])
    url = 'http://time.is/' + place
    req = urllib.request.Request(url, data=None,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
    try:
        resp = urllib.request.urlopen(req)
        page_src = resp.read()
        soup = bs(page_src, 'html.parser')
        time = soup.find(id='twd').string
        msg_hdr = soup.find(id='msgdiv').h1.string
        place = msg_hdr[len('Time in '):]
        place = place[:(len(place) - len(' now'))]
        reply = 'Time in **' + place + '**: ' + time
        yield from client.send_message(msg.channel, reply)
    except urllib.error.HTTPError:
        return

@asyncio.coroutine
def reload(client, msg):
    if msg.content != '!reload': return
    if msg.author.id != BOT_OWNER_ID: return
    yield from client.send_message(msg.channel, 'reading config...')
    read_config()

@client.event
@asyncio.coroutine
def on_member_ban(member):
    log_chan = next(c for c in member.server.channels if c.name == "mod-log")
    resp = '{0.mention} has been banned from the server'
    yield from client.send_message(log_chan, resp.format(member))

@client.event
@asyncio.coroutine
def on_member_unban(member):
    log_chan = next(c for c in member.server.channels if c.name == "mod-log")
    resp = '{0.mention} has been unbanned from the server'
    yield from client.send_message(log_chan, resp.format(member))

@client.event
@asyncio.coroutine
def on_member_update(before, after):
    if before.server.name != AOA_SERVER: return
    r_prev = set([r.name for r in before.roles])
    r_curr = set([r.name for r in after.roles])
    if 'Grounded' in r_curr - r_prev:
        log_chan = next(c for c in after.server.channels if c.name == "mod-log")
        resp = '{0.mention} has been grounded'
        yield from client.send_message(log_chan, resp.format(after))
    elif 'Grounded' in r_prev - r_curr:
        log_chan = next(c for c in after.server.channels if c.name == "mod-log")
        resp = '{0.mention} has been un-grounded'
        yield from client.send_message(log_chan, resp.format(after))

@asyncio.coroutine
def ground_member(client, msg):
    if msg.server.name != AOA_SERVER: return
    if msg.content[:len('!ground')] != '!ground': return
    if len(msg.mentions) != 1: return
    grounded_role = next(r for r in msg.server.roles if r.name == 'Grounded')
    user = msg.mentions[0]
    to_add_back = [r for r in user.roles if r.name in ROLES_TO_AVOID_CHANGING[msg.server.name]]
    to_add = [grounded_role] + to_add_back
    yield from client.replace_roles(user, *to_add)

@asyncio.coroutine
def unground_member(client, msg):
    if msg.server.name != AOA_SERVER: return
    if msg.content[:len('!unground')] != '!unground': return
    if len(msg.mentions) != 1: return
    user = msg.mentions[0]
    to_add = [r for r in user.roles if r.name != 'Grounded']
    yield from client.replace_roles(user, *to_add)

@asyncio.coroutine
def ehh(client, msg):
    if msg.server is not None and msg.server.name != AOA_SERVER: return
    if msg.content[:len('!eh')] != '!eh': return
    msg = yield from client.send_message(msg.channel, 'ehhhhh')
    for i in range(8):
        time.sleep(2)
        msg = yield from client.edit_message(msg, msg.content + 'hhhhhhhh')

@client.event
@asyncio.coroutine
def on_message(msg):
    global client

    # ignore empty messages
    if len(msg.content) == 0: return

    # ignore own messages
    if msg.author.id == client.user.id: return

    yield from help_request(client, msg)
    yield from link_request(client, msg)
    yield from normal_set_bias(client, msg)
    yield from normal_remove_bias(client, msg)
    yield from delete_messages(client, msg)
    yield from time_check(client, msg)
    yield from reload(client, msg)
    yield from ground_member(client, msg)
    yield from unground_member(client, msg)
    yield from ehh(client, msg)

read_config()
client.run(os.environ['DISCORD_TOKEN'])
