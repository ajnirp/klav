#!/usr/bin/env python3

import asyncio
import datetime
import discord
import sys

dt = datetime.datetime

client = discord.Client()
bias_channel, server, token = None, None, None

IDOLS = ['minah', 'sojin', 'hyeri', 'yura', 'dai5y']
ROLES_TO_AVOID_CHANGING = ['Mod', 'Admin', 'Dai5y']

DEFAULT_ROLE = 'Dai5y'
SERVER = "Girl's Day"
BIAS_CHANNEL = "whos-your-bias"
MAIN_CHANNEL = "dai5ys"

PIC_COMMANDS = [
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
]

HELP_MSG = '**Commands**:'
for pic_cmd in PIC_COMMANDS:
    HELP_MSG += ' ' + pic_cmd
HELP_MSG += ' goodnight'

HELP_MSG += '\n**Biases**: To set your bias, post the name of your bias in **#whos-your-bias** and the bot will set your role to that idol! Alternatively, type *!bias <name>* in any channel. For example, *!bias minah*. If the bot is offline, don\'t worry, a mod will come along and do it for you!'

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
    server = find_server(client, SERVER)
    bias_channel = find_channel(server, BIAS_CHANNEL)
    # print(server.id)
    # print([(c.name,c.id) for c in server.channels])
    print('Logged in as', client.user.name)
    print('Listening on channel', bias_channel)

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
    idol_roles = [r for r in user.roles if r.name in IDOLS]
    if role is None: return

    for r in user.roles:
        if r.name.lower() in IDOLS and role == r:
            response = '{0.mention} Your bias is already **' + role.name.title() + '**'
            yield from client.send_message(channel, response.format(user))
            return

    to_add_back = [r for r in user.roles if r.name in ROLES_TO_AVOID_CHANGING]
    to_add = [role] + to_add_back

    yield from client.replace_roles(user, *to_add)
    response = '{0.mention} Your bias has been set to **' + role.name.title() + '**!'
    yield from client.send_message(channel, response.format(user))

@asyncio.coroutine
def check_pic_upload(client, msg):
    if msg.content[0] == '!':
        for pic_command in PIC_COMMANDS:
            if msg.content[1:] == pic_command:
                yield from client.send_file(msg.channel, './' + msg.content[1:] + '.jpg')

@asyncio.coroutine
def say_goodnight(client, msg):
    if msg.content == '!goodnight':
        yield from client.send_file(msg.channel, './goodnight.jpg')
        yield from client.send_message(msg.channel, 'Goodnight {0.mention}!'.format(msg.author))

# Set bias of another user
# Only works if user 'cheeksy' says it
@asyncio.coroutine
def force_set_bias(client, msg):
    author_is_mod = 'Mod' in [r.name for r in msg.author.roles]
    if author_is_mod and msg.content[:5] == '!bias':
        split = msg.content.split()
        if len(split) != 3: return
        if len(msg.mentions) != 1: return
        target_user = msg.mentions[0]
        content = msg.content.lower()
        for idol in IDOLS:
            if idol in content:
                role = find_role(server, idol)
                yield from set_bias(client, msg.channel, target_user, role, msg)
                break

@asyncio.coroutine
def normal_set_bias(client, server, msg):
    if msg.channel != bias_channel: return
    if msg.content[:5] == '!bias': return
    user = msg.author
    content = msg.content.lower()
    for idol in IDOLS:
        if idol in content:
            role = find_role(server, idol)
            yield from set_bias(client, bias_channel, user, role, msg)
            break

@asyncio.coroutine
def check_help(client, msg):
    if msg.content[:9] == '!daisybot':
        yield from client.send_message(msg.author, HELP_MSG)

@client.event
@asyncio.coroutine
def on_message(msg):
    global client, server

    # ignore empty messages
    if len(msg.content) == 0: return

    # ignore own messages
    if msg.author.id == client.user.id: return

    # only work on the Girl's Day server
    if msg.server != server: return

    yield from check_help(client, msg)
    yield from check_pic_upload(client, msg)
    yield from say_goodnight(client, msg)
    yield from force_set_bias(client, msg)
    yield from normal_set_bias(client, server, msg)

client.run('MTM0MjkyMjA5MzkzNTk4NDY0.Cf--Bg.oRMtOYwDS38NgzdsEg-eDixisiA')