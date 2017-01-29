import asyncio
import datetime
import discord
import os
import random
import server
import time

async def set_bias(message, servers, client):
    server = servers[message.server.id]
    content = message.content.strip().lower().split()

    keywords = server.role_map.keys()

    # Figure out which roles to add to the user. Primary is the one mentioned first.
    to_add_ids, secondary = set([]), False
    for word in content:
        if word in keywords:
            to_add_ids.add(server.role_map[word][secondary])
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
    config_dir = os.path.join('.', 'config')
    config_files = os.listdir(config_dir)
    notifs_dir = os.path.join('.', 'notifs')
    notifs_files = os.listdir(notifs_dir)
    daily_dir = os.path.join('.', 'daily')
    daily_files = os.listdir(daily_dir)
    for config_file, notifs_file, daily_file in zip(config_files, notifs_files, daily_files):
        config_file_path = os.path.join(config_dir, config_file)
        notifs_file_path = os.path.join(notifs_dir, notifs_file)
        daily_file_path = os.path.join(daily_dir, daily_file)
        s_id = config_file
        servers[s_id] = server.Server(config_file, config_file_path, notifs_file_path, daily_file_path)

def is_mod(user, s_id, servers):
    server = servers[s_id]
    return any(role.id in server.mod_roles for role in user.roles)

async def delete_messages(message, servers, client):
    if not message.content.startswith(',d'): return
    if not is_mod(message.author, message.server.id, servers): return
    num_messages = message.content[2:]
    try:
        num_messages = 1 + int(num_messages)
        await client.purge_from(message.channel, limit=num_messages)
    except:
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
    if message.content not in ['.h', '!h']: return
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

async def search(message, servers, client):
    if message.content[0] not in '.!': return
    prefix = 's '
    if not message.content[1:].startswith(prefix): return
    query = message.content[1+len(prefix):].lower()
    if 'luber' in query:
        await client.send_message(message.author, 'Did you mean: *lunber*?')
        return
    skip = True
    channel_name = message.channel.name
    async for entry in client.logs_from(message.channel, limit=5000):
        if skip: skip = False; continue # skip the first element
        if query in entry.content.lower():
            timestamp = util.ts(entry.timestamp)
            report = '[{}] [{}] {}: {}'.format(channel_name, timestamp, entry.author.name, entry.content)
            await client.send_message(message.author, report)

async def post_periodic_pic(server, client):
    if len(server.daily_pics) > 0:
        url_fragment = random.choice(server.daily_pics)
        url = 'http://i.imgur.com/{}.jpg'.format(url_fragment)
        main_chan = client.get_channel(server.main_chan)
        await client.send_message(main_chan, url)

async def dialogue(message, _, client):
    condition = 'I love you Klav'
    if message.content.lower()[:len(condition)] != condition.lower(): return
    dest = message.author if message.server is None else message.channel
    reply = 'I love you too {0.mention}'.format(message.author)
    await client.send_message(dest, reply)

async def check_musicbot(music_voice_chan, music_text_chan, bot_id, client):
    voice_chan = client.get_channel(music_voice_chan)
    bot_connected = any(member.id == bot_id for member in voice_chan.voice_members)
    if not bot_connected:
        print('Detected disconnected bot, restarting...')
        text_chan = client.get_channel(music_text_chan)
        await client.send_message(text_chan, '+restart')

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