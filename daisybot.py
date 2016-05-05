#!/usr/bin/env python3

import asyncio
import datetime
import discord
import os
import sys

GSD_SERVER = "Girl's Day"
AOA_SERVER = "Ace of Angels"

dt = datetime.datetime

client = discord.Client()
server = None

CONFIG = {
    GSD_SERVER: 'gsd.txt',
    AOA_SERVER: 'aoa.txt',
}

SERVERS = [GSD_SERVER, AOA_SERVER]

WELCOME_MSG = {}
IDOLS = {}
ROLES_TO_AVOID_CHANGING = {}
DEFAULT_ROLE = {}
MOD_ROLE = {}
BIAS_CHANNEL = {}
MAIN_CHANNEL = {}
LINK_COMMANDS = {}

for s_name in SERVERS:
    cfg_file = CONFIG[s_name]
    with open(cfg_file, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
        WELCOME_MSG[s_name] = lines[1]
        IDOLS[s_name] = lines[2].split()
        ROLES_TO_AVOID_CHANGING[s_name] = lines[3].split()
        DEFAULT_ROLE[s_name] = lines[4]
        MOD_ROLE[s_name] = lines[5]
        BIAS_CHANNEL[s_name] = lines[6]
        MAIN_CHANNEL[s_name] = lines[7]
        LINK_COMMANDS[s_name] = {}
        for line in lines[8:]:
            cmd, url = line.split()
            LINK_COMMANDS[s_name][cmd] = url

HELP_MSG = {GSD_SERVER:'', AOA_SERVER:''}

HELP_MSG[GSD_SERVER] = '**Commands**:'
for pic_cmd in LINK_COMMANDS[GSD_SERVER].keys():
    HELP_MSG[GSD_SERVER] += ' ' + pic_cmd
HELP_MSG[GSD_SERVER] += ' goodnight'

HELP_MSG[AOA_SERVER] = '**Commands**:'
for pic_cmd in LINK_COMMANDS[AOA_SERVER].keys():
    HELP_MSG[AOA_SERVER] += ' ' + pic_cmd

HELP_MSG[GSD_SERVER] += '''
**Biases**: To set your bias, post the name of your bias in **#whos-your-bias**,\
and the bot will set your role to that idol! Alternatively, type *!bias <name>* in any channel.\
 For example, *!bias minah*. If the bot is offline, don't worry, a mod will come along and do it for you!'''

HELP_MSG[AOA_SERVER] += '''
**Biases**: To set your bias, post the name of your bias in **#whos-your-bias**,\
and the bot will set your role to that idol! Alternatively, type *!bias <name>* in any channel.\
 For example, *!bias jimin*. If the bot is offline, don't worry, a mod will come along and do it for you!'''

def find_role(server, idol):
    for role in server.roles:
        if role.name.lower() == idol.lower():
            return role
    return None

def find_server(client, server_name):
    return next(s for s in client.servers if s.name == server_name)

def find_channel(server, channel_name):
    return next(c for c in server.channels if c.name == channel_name)

@client.event
@asyncio.coroutine
def on_ready():
    global CHANNEL
    global bias_channel, client, server
    print('Logged in as', client.user.name)

@client.event
@asyncio.coroutine
def on_member_join(member):
    server = member.server
    s_name = server.name
    if s_name != GSD_SERVER: return
    main_channel = find_channel(server, MAIN_CHANNEL[s_name])
    fmt = '{0.mention} ' + WELCOME_MSG[s_name]

    for role in server.roles:
        if role.name == DEFAULT_ROLE[s_name]:
            yield from client.add_roles(member, role)
            break

    yield from client.send_message(main_channel, fmt.format(member, server))

@asyncio.coroutine
def set_bias(client, channel, user, role, msg):
    idol_roles = [r for r in user.roles if r.name in IDOLS[msg.server.name]]
    if role is None: return

    for r in user.roles:
        if r.name.lower() in IDOLS[msg.server.name] and role == r:
            response = '{0.mention} Your bias is already **' + role.name.title() + '**'
            yield from client.send_message(msg.channel, response.format(user))
            return

    to_add_back = [r for r in user.roles if r.name in ROLES_TO_AVOID_CHANGING[msg.server.name]]
    to_add = [role] + to_add_back

    yield from client.replace_roles(user, *to_add)
    response = '{0.mention} Your bias has been set to **' + role.name.title() + '**!'
    yield from client.send_message(msg.channel, response.format(user))

@asyncio.coroutine
def link_request(client, msg):
    if msg.content[0] != '!': return
    s_name = msg.server.name
    pic_cmd = msg.content[1:]
    if pic_cmd not in LINK_COMMANDS[s_name].keys(): return
    url = LINK_COMMANDS[s_name][pic_cmd]
    yield from client.send_message(msg.channel, url)

def is_mod(server, user):
    '''Is the user a mod on the specified server?'''
    mod_role = MOD_ROLE[server.name]
    return any([mod_role == r.name for r in user.roles])

@asyncio.coroutine
def force_set_bias(client, msg):
    '''Set bias of another user
    Format: !bias @<username_mention> idol
            !bias idol
    The former only works if mods say it.
    The latter always works.'''
    if msg.content[:5] == '!bias':
        split = msg.content.split()
        if len(msg.mentions) > 1: return
        target_user = msg.mentions[0] if len(msg.mentions) == 1 else msg.author
        # Ordinary users should not be able to set others' biases
        if target_user != msg.author and not is_mod(msg.server, msg.author): return
        content = msg.content.lower()
        for idol in IDOLS[msg.server.name]:
            if idol in content:
                role = find_role(msg.server, idol)
                yield from set_bias(client, msg.channel, target_user, role, msg)
                break

def is_bias_channel(server, channel):
    '''Is 'channel' the bias channel for 'server'?'''
    return channel.name == BIAS_CHANNEL[server.name]

@asyncio.coroutine
def normal_set_bias(client, server, msg):
    if not is_bias_channel(msg.server, msg.channel): return
    if msg.content[:5] == '!bias': return
    user = msg.author
    content = msg.content.lower()
    for idol in IDOLS[msg.server.name]:
        if idol in content:
            role = find_role(msg.server, idol)
            bias_channel = BIAS_CHANNEL[msg.server.name]
            yield from set_bias(client, bias_channel, user, role, msg)
            break

@asyncio.coroutine
def help_request(client, msg):
    if msg.content[:8] != '!bothelp': return
    yield from client.send_message(msg.author, HELP_MSG[msg.server.name])

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
        logs = yield from client.logs_from(msg.channel, limit=num_msgs)
        for log_entry in logs:
            try:
                yield from client.delete_message(log_entry)
            except discord.Forbidden:
                print('cannot delete: ' + log_entry.content)
                continue
    except ValueError: # failed to convert split[1] to int
        return

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
    yield from force_set_bias(client, msg)
    yield from normal_set_bias(client, server, msg)
    yield from delete_messages(client, msg)

client.run(os.environ['DISCORD_TOKEN'])