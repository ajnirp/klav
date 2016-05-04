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
bias_channel, server, token = None, None, None

IMG_FOLDER = {
    GSD_SERVER: 'gsd',
    AOA_SERVER: 'aoa',
}

IDOLS = {
    GSD_SERVER: ['minah', 'sojin', 'hyeri', 'yura', 'dai5y'],
    AOA_SERVER: ['choa', 'jimin', 'seolhyun', 'mina', 'hyejeong', 'chanmi', 'yuna', 'youkyung'],
}

ROLES_TO_AVOID_CHANGING = {
    GSD_SERVER: ['Mod', 'Admin', 'Dai5y'],
    AOA_SERVER: ['Mods', 'Owner', 'Elvis']
}

DEFAULT_ROLE = {
    GSD_SERVER: 'Dai5y',
    AOA_SERVER: 'Elvis',
}

SERVER = ["Girl's Day", "Ace of Angels"]

BIAS_CHANNEL = {
    GSD_SERVER: "whos-your-bias",
    AOA_SERVER: "call_your_roles",
}

MAIN_CHANNEL = {
    GSD_SERVER: "dai5ys",
    AOA_SERVER: "call_your_roles",
}

PIC_COMMANDS = {
    GSD_SERVER: [
        'cheekpoke',
        'consternation',
        'dismay',
        'eat',
        'fightme',
        'happy',
        'hi',
        'hungry',
        'nom',
        'pen',
        'plsno',
        'police',
        'rawr',
        'sad',
        'userious',
        'yoboseyo',
        'yurawr',
    ],
    AOA_SERVER: [
        'angry',
        'banana',
        'bored',
        'cheeky',
        'disapproval',
        'excited',
        'happy',
        'interesting',
        'kms',
        'sad',
    ],
}

HELP_MSG = {}

HELP_MSG[GSD_SERVER] = '**Commands**:'
for pic_cmd in PIC_COMMANDS:
    HELP_MSG[GSD_SERVER] += ' ' + pic_cmd
HELP_MSG[GSD_SERVER] += ' goodnight'

HELP_MSG[GSD_SERVER] += '''
**Biases**: To set your bias, post the name of your bias in **#whos-your-bias**,\
and the bot will set your role to that idol! Alternatively, type *!bias <name>* in any channel.\
 For example, *!bias minah*. If the bot is offline, don't worry, a mod will come along and do it for you!'''

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
    global CHANNEL, SERVER
    global bias_channel, client, server
    print('Logged in as', client.user.name)

@client.event
@asyncio.coroutine
def on_member_join(member):
    server = member.server
    main_channel = find_channel(server, MAIN_CHANNEL)

    fmt = '{0.mention} welcome to the spectacular Girl\'s Day server party!'

    for role in server.roles:
        if role.name == 'Dai5y':
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
def check_pic_upload(client, msg):
    if msg.content[0] == '!':
        server_name = msg.server.name
        for pic_command in PIC_COMMANDS[server_name]:
            if msg.content[1:] == pic_command:
                path = './' + IMG_FOLDER[server_name] + '/' + msg.content[1:] + '.jpg'
                yield from client.send_file(msg.channel, path)

@asyncio.coroutine
def say_goodnight(client, msg):
    if msg.server.name == GSD_SERVER and msg.content == '!goodnight':
        yield from client.send_file(msg.channel, './goodnight.jpg')
        yield from client.send_message(msg.channel, 'Goodnight {0.mention}!'.format(msg.author))

def is_mod(user):
    return any(['Mod' in r.name for r in user.roles])

# Set bias of another user
# Format: !bias @<username_mention> idol
#         !bias idol
# The former only works if mods say it.
# The latter always works.
@asyncio.coroutine
def force_set_bias(client, msg):
    if msg.content[:5] == '!bias':
        split = msg.content.split()
        if len(msg.mentions) > 1: return
        target_user = msg.mentions[0] if len(msg.mentions) == 1 else msg.author
        # Ordinary users should not be able to set others' biases
        if target_user != msg.author and not is_mod(msg.author): return
        content = msg.content.lower()
        for idol in IDOLS[msg.server.name]:
            if idol in content:
                role = find_role(msg.server, idol)
                yield from set_bias(client, msg.channel, target_user, role, msg)
                break

def is_bias_channel(channel):
    return channel.name in BIAS_CHANNEL.values()

@asyncio.coroutine
def normal_set_bias(client, server, msg):
    if not is_bias_channel(msg.channel): return
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
def check_help(client, msg):
    if msg.content[:9] == '!daisybot':
        yield from client.send_message(msg.author, HELP_MSG[msg.server.name])

@asyncio.coroutine
def delete_messages(client, msg):
    if not is_mod(msg.author): return
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
    except ValueError:
        print('could not convert to int')
        return

@asyncio.coroutine
def check_jiltunayobaby(client, msg):
    if msg.server.name != AOA_SERVER: return
    if msg.content != '!jiltunayobaby': return
    yield from client.send_message(msg.channel, 'https://www.youtube.com/watch?v=bhKFSXN2Fr4')

@client.event
@asyncio.coroutine
def on_message(msg):
    global client

    # ignore empty messages
    if len(msg.content) == 0: return

    # ignore own messages
    if msg.author.id == client.user.id: return

    yield from check_help(client, msg)
    yield from check_pic_upload(client, msg)
    yield from say_goodnight(client, msg)
    yield from force_set_bias(client, msg)
    yield from normal_set_bias(client, server, msg)
    yield from delete_messages(client, msg)
    yield from check_jiltunayobaby(client, msg)

client.run(os.environ['DISCORD_TOKEN'])