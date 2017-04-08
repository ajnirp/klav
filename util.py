import asyncio
import datetime
import discord
import json
import os
import pytz
import random
import requests
import server
import sys
import time
import validators

async def set_bias(message, servers, client):
    server = servers[message.server.id]
    content = message.content.strip().lower().split()

    keywords = server.role_map.keys()

    # Figure out which roles to add to the user. Primary is the one mentioned first.
    to_add_ids, secondary = set([]), False
    for word in content:
        for keyword in keywords:
            if keyword in word:
                to_add_ids.add(server.role_map[keyword][secondary])
                secondary = True

    to_add_roles = [discord.utils.find(lambda r: r.id == r_id, message.server.roles) for r_id in to_add_ids]

    if len(to_add_ids) > 0:
        assignable_roles = []
        for pair in server.role_map.values(): assignable_roles.append(pair[0]); assignable_roles.append(pair[1])
        new_roles_ids = [r.id for r in message.author.roles if r.id not in assignable_roles] + list(to_add_ids)
        new_roles = [discord.utils.find(lambda r: r.id == r_id, message.server.roles) for r_id in new_roles_ids]
        await client.replace_roles(message.author, *new_roles)

        bias_chan = client.get_channel(server.bias_chan)
        pluralise = 'biases have' if len(to_add_ids) > 1 else 'bias has'
        report = '{0.mention} Your {1} been set to '.format(message.author, pluralise)
        report += ', '.join('**{}**'.format(role.name) for role in to_add_roles)
        bot_message = await client.send_message(message.channel, report)

        # Sleep and then clean up
        await asyncio.sleep(5)
        await client.delete_message(message)
        await client.delete_message(bot_message)
    else:
        # Irrelevant message, clean it up
        await asyncio.sleep(5)
        await client.delete_message(message)

async def assign_default_role(member, servers, client):
    server = servers[member.server.id]
    if server.default_role is None: return
    default_role = discord.utils.find(lambda r: r.id == server.default_role, member.server.roles)
    await client.add_roles(member, default_role)

def read_configs(servers):
    api_root = 'https://api.myjson.com/bins/'
    with open('servers.txt', 'r') as f:
        id_to_fragment_map = [line.strip().split() for line in f.readlines()]

    for s_id, url_fragment in id_to_fragment_map:
        url = api_root + url_fragment
        r = requests.get(url)
        if r.status_code != 200:
            print('error: read_configs: could not GET {}'.format(url), file=sys.stderr)
            return
        config = json.loads(r.text)
        servers[s_id] = server.Server(s_id, config)

    return id_to_fragment_map

def is_mod(user, s_id, servers):
    server = servers[s_id]
    return any(role.id in server.mod_roles for role in user.roles)

def is_owner(user):
    return user.id == '150919851710480384'

async def delete_messages(message, servers, client):
    if not message.content.startswith(',d'): return
    if not is_mod(message.author, message.server.id, servers): return
    num_messages = message.content[2:]
    try:
        num_messages = 1 + int(num_messages)
        await client.purge_from(message.channel, limit=num_messages)
    except Exception as e:
        print('delete_messages: {}'.format(e), file=sys.stderr)
        return

async def kick_members(message, servers, client):
    if not message.content.startswith(',k'): return
    if not is_mod(message.author, message.server.id, servers): return
    for member in message.mentions:
        await client.kick(member)
        server = servers[message.server.id]
        main_chan = client.get_channel(server.main_chan)
        report = '**{0.name}** was kicked by {1.mention}'
        report = report.format(member, message.author)
        await client.send_message(main_chan, report)

async def command(message, servers, client):
    if message.content[0] not in '.!': return
    server = servers[message.server.id]
    command_str = message.content[1:]
    if command_str in server.command_map:
        response = server.command_map[command_str]
        await client.send_message(message.channel, response)

async def help(message, servers, client):
    if message.content not in ['.h', '!h', '.help', '!help']: return
    server = servers[message.server.id]

    help_str = 'Commands:\n'
    sorted_keys = sorted(server.command_map.keys())

    for key in sorted_keys:
        value = server.command_map[key]
        line = key + ' <' + value + '>' if value.startswith('http') else key + ' ' + value
        if len(help_str) + len(line) >= 2000: # Discord message limit
            await client.send_message(message.author, help_str)
            help_str = ''
        help_str += line + '\n'

    # Send the remainder (or, in case the total message never crossed 2000
    # chars, the entire thing) of the help string.
    await client.send_message(message.author, help_str)

async def handle_member_pic_request(message, servers, client):
    if message.content[0] not in '.!': return
    if len(message.content.split()) > 1: return
    server = servers[message.server.id]
    member_nickname = message.content[1:]
    if member_nickname in server.member_nicknames:
        member_name = server.member_nicknames[member_nickname]
        url_fragment = random.choice(server.member_pics[member_name])
        url = 'https://i.imgur.com/{}.jpg'.format(url_fragment)
        await client.send_message(message.channel, url)

async def handle_avatar_request(message, client):
    '''Post the avatar of a user'''
    if message.content[:3] not in ['.a ', '!a ']: return
    for member in message.mentions:
        report = 'User has no avatar'
        if member.avatar_url != '':
            report = '{}\'s avatar: {}'.format(member.name, member.avatar_url)
        await client.send_message(message.channel, report)

async def post_periodic_pic(server, client):
    if len(server.periodic_pics) > 0:
        url_fragment = random.choice(server.periodic_pics)
        url = 'http://i.imgur.com/{}.jpg'.format(url_fragment)
        main_chan = client.get_channel(server.main_chan)
        await client.send_message(main_chan, url)

async def dialogue(message, _, client):
    condition = 'I love you Klav'
    if message.content.lower()[:len(condition)] != condition.lower(): return
    dest = message.author if message.server is None else message.channel
    reply = 'I love you too {0.mention}'.format(message.author)
    await client.send_message(dest, reply)

def now():
    return time.strftime('[%y%m%d %H:%M]')

def ts(datetime_obj):
    return datetime_obj.strftime('%y%m%d %H:%M')

def time_to_post():
    # post four times a day
    now = datetime.datetime.now()
    return now.hour % 4 == 2 and now.minute == 0

def pin_event(before, after):
    if not before.pinned and after.pinned: return -1
    if before.pinned and not after.pinned: return 1
    return 0

async def handle_user_info_request(message, _, client):
    if message.content[:3] not in ['.u ', '!u ']: return

    for member in message.mentions:
        await display_user_info(member, message.channel, client)

async def display_user_info(member, channel, client):
    '''Send a message to channel 'channel' containing an Embed object
    that has information about the server member 'member'.'''
    account_created = discord.utils.snowflake_time(member.id)

    role_names = 'None'
    if len(member.roles) > 1:
        role_names = ', '.join(r.name for r in member.roles[1:])

    embed = discord.Embed(
        title='User info',
        type='rich',
        description=member.name,
        url=discord.Embed.Empty,
        timestamp=discord.Embed.Empty,
        footer=discord.Embed.Empty,
        colour=member.top_role.colour)

    embed.set_thumbnail(url=member.avatar_url) \
         .add_field(name='Account made', value=ts(account_created)) \
         .add_field(name='Here since', value=ts(member.joined_at)) \
         .add_field(name='ID', value=member.id) \
         .add_field(name='Nickname', value=member.nick) \
         .add_field(name='Status', value=member.status) \
         .add_field(name='Roles', value=role_names)

    await client.send_message(channel, content=None, tts=False, embed=embed)

async def handle_gsd_countdown_request(message, servers, client):
    if message.server.id != '170293223577747457': return
    if message.content not in ['.countdown', '!countdown']: return

    await post_gsd_countdown(message, servers, client)

# async def post_gsd_countdown(message, _, client):
#     target_time_string = '27 March 2017 12:00:00 PM +0900'
#     target_time = datetime.datetime.strptime(target_time_string, '%d %B %Y %H:%M:%S %p %z')
#     td = target_time - datetime.datetime.now(pytz.utc)

#     seconds = td.seconds
#     hours = seconds // 3600
#     hours_overflow = seconds - (hours * 3600)
#     minutes = hours_overflow // 60
#     seconds = hours_overflow - (minutes * 60)

#     days_string = '{} day'.format(td.days) + ['', 's'][td.days != 1]
#     hours_string = '{} hour'.format(hours) + ['', 's'][hours != 1]
#     minutes_string = '{} minute'.format(minutes) + ['', 's'][minutes != 1]
#     seconds_string = '{} second'.format(seconds) + ['', 's'][seconds != 1]

#     report = '{} {} {} {} to go!'.format(days_string, hours_string, minutes_string, seconds_string)

#     await client.send_message(message.channel, report)

async def handle_list_mods_request(message, servers, client):
    if message.content not in ['.m', '!m']: return
    server = servers[message.server.id]
    mods = []
    mod_ids = set()
    for member in message.server.members:
        for role in member.roles:
            if role.id in server.mod_roles and member.id not in mod_ids:
                mod_ids.add(member.id)
                mods.append(member)
    report = 'Mods: {}'.format(', '.join(mod.name for mod in mods))
    await client.send_message(message.channel, report)

async def gallery_update(message, servers, client):
    server = servers[message.server.id]

    if server.gallery_chan is None: return
    if message.channel.id in [server.gallery_chan, server.welcome_chan, server.log_chan, server.bias_chan]: return
    if message.channel.id in server.do_not_copy_to_gallery: return

    found_urls = ' '.join(word for word in message.content.split() if validators.url(word))
    found_urls += ' '.join(attachment['url'] for attachment in message.attachments)

    if len(found_urls) > 0:
        report = '**{0}** in {1.mention}: {2}'.format(message.author.name, message.channel, found_urls)
        gallery_chan = client.get_channel(server.gallery_chan)

        await client.send_message(gallery_chan, report)

async def handle_list_roles_request(message, servers, client):
    '''Post information about the roles in a server'''
    if message.content != ',roles': return
    if not is_mod(message.author, message.server.id, servers): return

    MESSAGE_LIMIT = 2000
    chunks = []

    for role in sorted(message.server.roles, key=lambda r: r.position, reverse=True):
        if role.name == '@everyone': continue
        c = role.color
        message_chunk = '**{}** {} {}\n'.format(role.name, c.to_tuple(), hex(c.value))
        chunks.append(message_chunk)
    if len(chunks) == 0:
        await client.send_message(message.channel, ':bangbang: No roles found on this server')
        return
    cumulative_len, start, idx = 0, 0, 0
    for chunk in chunks:
        cumulative_len += len(chunk)
        if cumulative_len > MESSAGE_LIMIT:
            report = ''.join(chunks[start:idx])
            await client.send_message(message.channel, report)
            start = idx
            cumulative_len = 0
        idx += 1
    report = ''.join(chunks[start:idx])
    await client.send_message(message.channel, report)

async def handle_list_emojis_request(message, client):
    '''Post all the emojis in a server'''
    if message.content not in ['.emojis', '!emojis']: return

    MESSAGE_LIMIT = 2000
    chunks = []

    # the [:-1] is so that we ignore @everyone
    for emoji in sorted(message.server.emojis, key=lambda e: e.name):
        message_chunk = '{} <:{}:{}>  '.format(emoji.name, emoji.name, emoji.id)
        chunks.append(message_chunk)
    if len(chunks) == 0:
        await client.send_message(message.channel, ':bangbang: No emojis found on this server')
        return
    cumulative_len, start, idx = 0, 0, 0
    for chunk in chunks:
        cumulative_len += len(chunk)
        if cumulative_len > MESSAGE_LIMIT:
            report = ''.join(chunks[start:idx])
            await client.send_message(message.channel, report)
            start = idx
            cumulative_len = 0
        idx += 1
    report = ''.join(chunks[start:idx])
    await client.send_message(message.channel, report)

async def handle_remove_command_request(message, servers, client, id_to_fragment_map):
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers): return

    split = message.content.split()
    if len(split) != 2: return

    prefix = 'remove'
    if message.content[1:1+len(prefix)] != prefix: return

    server = servers[message.server.id]

    input_ = split[1]
    if input_ not in server.command_map:
        report = ':no_entry: The command **{}** does not exist'.format(input_)
        await client.send_message(message.channel, report)
        return

    output_ = server.command_map[input_]
    del server.command_map[input_]

    r = make_put_request_update_config(message, server, id_to_fragment_map)
    if r is None:
        await client.send_message(message.channel, ':skull_crossbones: Error updating config')
        return

    report = ':white_check_mark: Removed command **{}** (response was: {})'.format(input_, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to remove command: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await client.send_message(message.channel, report)

async def handle_add_command_request(message, servers, client, id_to_fragment_map):
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers): return

    split = message.content.split()
    if len(split) < 3: return

    prefix = 'add'
    if message.content[1:1+len(prefix)] != prefix: return

    input_ = split[1]
    output_ = ' '.join(split[2:])
    server = servers[message.server.id]

    if input_ in server.command_map:
        report = ':bangbang: The command **{}** already exists. Please remove it before adding a new one.'.format(input_)
        await client.send_message(message.channel, report)
        return
    server.command_map[input_] = output_

    r = make_put_request_update_config(message, server, id_to_fragment_map)
    if r is None:
        await client.send_message(message.channel, ':skull_crossbones: Error updating config')
        return
    
    report = ':white_check_mark: Added command **{}** with response {}'.format(input_, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to add command: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await client.send_message(message.channel, report)

def build_config_dict(server):
    role_map = { name: [id1, id2] for (name, (id1, id2)) in server.role_map.items() }
    return {
        'channels': [server.welcome_chan, server.main_chan, server.bias_chan],
        'log_chan': server.log_chan,
        'do_not_log': server.do_not_log,
        'default_role': server.default_role,
        'welcome_msg': server.welcome_msg,
        'mod_roles': server.mod_roles,
        'gallery_chan': server.gallery_chan,
        'do_not_copy_to_gallery': server.do_not_copy_to_gallery,
        'role_map': role_map,
        'command_map': server.command_map,
        'member_nicknames': server.member_nicknames,
        'member_pics': server.member_pics,
        'periodic_pics': server.periodic_pics,
    }

def make_put_request_update_config(message, server, id_to_fragment_map):
    headers = { 'Content-Type': 'application/json; charset=utf-8', 'Data-Type': 'json', }
    config = build_config_dict(server)

    api_root = 'https://api.myjson.com/bins/'
    for s_id, url_fragment in id_to_fragment_map:
        if s_id == message.server.id:
            url = api_root + url_fragment
            r = requests.put(url, data=json.dumps(config), headers=headers)
            return r

    return None

async def set_gallery_channel(message, servers, client):
    if not message.content.startswith('-'): return
    if not is_owner(message.author): return

    prefix = 'sgc'
    if message.content[1:1+len(prefix)] != prefix: return

    if len(message.channel_mentions) != 1:
        report = ':exclamation: Usage: -sgc #channel'
        await client.send_message(message.channel, report)
        return

    channel = message.channel_mentions[0]

    headers = { 'Content-Type': 'application/json; charset=utf-8', 'Data-Type': 'json', }
    config = build_config_dict(server)
    config['gallery_chan'] = channel.id

    api_root = 'https://api.myjson.com/bins/'
    for s_id, url_fragment in id_to_fragment_map:
        if s_id == message.server.id:
            url = api_root + url_fragment
            r = requests.put(url, data=json.dumps(config), headers=headers)
            return r

    return None