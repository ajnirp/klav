from PIL import Image
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
    if message.server.id == '204294040026480640':
        return

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
        r = requests.get(url, verify=False)
        if r.status_code != 200:
            print('error: read_configs: could not GET {}'.format(url), file=sys.stderr)
            return
        config = json.loads(r.text)
        servers[s_id] = server.Server(s_id, config)

    return id_to_fragment_map

def is_mod(user, s_id, servers, client):
    server = servers[s_id]

    # Server owners are always considered mods
    server_obj = client.get_server(s_id)
    if server_obj is None:
        print("is_mod: couldn't find server with ID:", s_id, file=sys.stderr)
    if server_obj.owner.id == user.id: return True

    return any(role.id in server.mod_roles for role in user.roles)

def is_owner(user):
    return user.id == '150919851710480384'

async def delete_messages(message, servers, client):
    if not message.content.startswith(',d'): return
    if not is_mod(message.author, message.server.id, servers, client): return
    num_messages = message.content[2:]
    try:
        num_messages = 1 + int(num_messages)
        await client.purge_from(message.channel, limit=num_messages)
    except Exception as e:
        print('delete_messages: {}'.format(e), file=sys.stderr)
        return

async def kick_members(message, servers, client):
    if not message.content.startswith(',k'): return
    if not is_mod(message.author, message.server.id, servers, client): return
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
    if message.author.id == '266548590883766284' and message.server.id == '204294040026480640':
        # emoji = discord.utils.find(lambda e: e.name == 'minatired', message.server.emojis)
        # response = 'guar <:{}:{}>'.format(emoji.name, emoji.id)
        response = "Anyway after not being here the past few days i can say i was happier, Cheeksy's targeting of me and every thing i say has negatively impacted me and made me afraid of coming here. I may have negative character traits but i don't think shaming me for every single one of them is helpful in overcoming them. Cheeksy is a Bully and has effectively accomplished his goal of bullying me out forever. To his delight I'll never be a part of aoacord ever again"
        await client.send_message(message.channel, response)
        return
    command_str = message.content[1:]
    if command_str in server.command_map:
        response = server.command_map[command_str]
        await client.send_message(message.channel, response)

async def handle_commands_request(message, servers, client):
    if message.content not in ['.commands', '!commands']: return
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

async def handle_help_request(message, servers, client):
    if message.content not in ['.h', '!h', '.help', '!help']: return
    usage = '''
__**DAI5YBOT HELP**__

Dai5ybot is a kpop server bot. Among other things, it can handle commands.

Commands that start with `-` (hyphen) can only be used by the bot owner.
Commands that start with `.` (period) can be used by anyone on the server.
Any command that starts with `.` (period) can also start with `!` (exclamation mark), there is no difference.
Commands that start with `,` (comma) can only be used by mods.

The exceptions are `,add` `,alias`, `,remove`, `,change` and `,swap`. The bot owner can use these commands as well.

__**Reference**__

>>> Commands that everyone can use:

`.help` The bot direct-messages you with this help message.

`.commands` See all commands for the current server.

`.emojis` List out all custom emojis on a server.

`.u @user` List some information about a user (roles, date of joining, etc.).

`.a @user` Display a user's low-resolution Discord avatar.

>>> Commands that moderators can use:

`,d50` Delete the last 50 messages on the server.
You can replace 50 by any number you like. Note: Discord does __not__ allow you to bulk-delete messages that are older than a certain number of days.

`,add name response` Add a new command.
Example: `,add hello http://i.imgur.com/F5FJw0b.jpg`

`,alias new_name old_name` Add a new command that has the same response as an existing command.
Example: `,alias hi hello`

`,remove name` Remove an existing command.
Example: `,remove hello`

`,change name response` Change the response of an existing command.
Example: `,change hello https://gfycat.com/DismalSimilarDragonfly#?speed=2`

`,swap name1 name2` Swap the responses of two existing commands.
Example: `,swap hello hello2`

`,roles` List out all roles on a server.

For more information, contact the bot owner, <@150919851710480384>.
'''
    await client.send_message(message.author, usage)

async def handle_member_pic_request(message, servers, client):
    if message.content[0] not in '.!': return
    if len(message.content.split()) > 1: return
    if message.server.id == '170293223577747457':
        if message.channel.id != '386268030679646208':
            return
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

async def user_info(message, _, client):
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

async def display_server_info(message, client):
    '''Display the server info in the channel that the message was posted'''
    if message.content not in ['.s', '!s']: return

    embed = discord.Embed(
        title='Server info',
        type='rich',
        description=message.server.name,
        url=discord.Embed.Empty,
        footer=discord.Embed.Empty,
        colour=discord.Color(0xeaa82e))

    roles = ' '.join(r.name for r in message.server.role_hierarchy)

    embed.set_thumbnail(url=message.server.icon_url) \
         .add_field(name='Server created', value=ts(message.server.created_at)) \
         .add_field(name='Members', value=message.server.member_count) \
         .add_field(name='ID', value=message.server.id) \
         .add_field(name='Owner', value=message.server.owner.name) \
         .add_field(name='Roles', value=roles)

    await client.send_message(message.channel, content=None, tts=False, embed=embed)

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

async def list_mods(message, servers, client):
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

async def toggle_leave_message(message, servers, client, id_to_fragment_map):
    if message.content != '-tlm': return
    if not is_owner(message.author): return

    server = servers[message.server.id]
    config = build_config_dict(server)

    key = 'announce_member_leaving'
    if key not in config:
        config[key] = False
    else:
        config[key] = not config[key]

    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        await client.send_message(message.channel, ':skull_crossbones: Error updating config')
        return

    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to toggle leave message. Error code: **{}**'.format(r.status_code)
    else:
        id_to_fragment_map = read_configs(servers)
        report = ':white_check_mark: Member leaving messages are now **{}** on this server'
        report = report.format(['disabled', 'enabled'][config[key]])

    await client.send_message(message.channel, report)

async def handle_show_roles_request(message, client):
    '''Post information about the roles in a server. Info is sent out as a DM to the requester.'''
    if message.content != '-roles': return
    if not is_owner(message.author): return

    MESSAGE_LIMIT = 2000
    chunks = []
    destination = message.author

    for role in sorted(message.server.roles, key=lambda r: r.position, reverse=True):
        if role.name == '@everyone': continue
        c = role.color
        message_chunk = '**{}** {} {} {}\n'.format(role.name, role.id, c.to_tuple(), hex(c.value))
        chunks.append(message_chunk)

    if len(chunks) == 0:
        await client.send_message(destination, ':bangbang: No roles found on this server')
        return

    await client.send_message(destination, '__**Roles on this server**__')
    cumulative_len, start, idx = 0, 0, 0
    for chunk in chunks:
        cumulative_len += len(chunk)
        if cumulative_len > MESSAGE_LIMIT:
            report = ''.join(chunks[start:idx])
            await client.send_message(destination, report)
            start = idx
            cumulative_len = 0
        idx += 1
    report = ''.join(chunks[start:idx])
    await client.send_message(destination, report)


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
    '''Remove a command from the server'''
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers, client) and not is_owner(message.author): return

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

    config = build_config_dict(server)
    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        await client.send_message(message.channel, ':skull_crossbones: Error updating config')
        return

    report = ':white_check_mark: Removed command **{}** (response was: <{}>)'.format(input_, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to remove command: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await client.send_message(message.channel, report)

async def change_command(message, servers, client, id_to_fragment_map):
    '''Change the response of an existing command on the server'''
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers, client) and not is_owner(message.author): return

    split = message.content.split()
    if len(split) < 3: return

    prefix = 'change'
    if message.content[1:1+len(prefix)] != prefix: return

    input_ = split[1]
    output_ = ' '.join(split[2:])
    server = servers[message.server.id]

    if input_ not in server.command_map:
        report = ':bangbang: The command **{}** does not exist. Did you mean to use `add`?'.format(input_)
        await send_wait_and_delete(client, message.channel, report)
        return
    old_response = server.command_map[input_]
    server.command_map[input_] = output_

    config = build_config_dict(server)
    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: Changed command **{}**.\nOld response was <{}>\nNew response is <{}>'.format(input_, old_response, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to add command: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await send_wait_and_delete(client, message.channel, report)

async def swap_commands(message, servers, client, id_to_fragment_map):
    '''Swap the responses for two existing commands'''
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers, client) and not is_owner(message.author): return

    split = message.content.split()
    if len(split) != 3: return

    prefix = 'swap'
    if message.content[1:1+len(prefix)] != prefix: return

    first = split[1]
    second = split[2]
    server = servers[message.server.id]

    if first not in server.command_map:
        report = ':bangbang: The command **{}** does not exist.'.format(first)
        await send_wait_and_delete(client, message.channel, report)
        return

    if second not in server.command_map:
        report = ':bangbang: The command **{}** does not exist.'.format(second)
        await send_wait_and_delete(client, message.channel, report)
        return

    server.command_map[first], server.command_map[second] = server.command_map[second], server.command_map[first]

    config = build_config_dict(server)
    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: Swapped commands **{0}** and **{1}**.\nResponse for **{0}** is now <{2}>\nResponse for **{1}** is now <{3}>'.format(first, second, server.command_map[first], server.command_map[second])
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to swap commands **{}** and **{}**. Error code: **{}**'.format(first, second, r.status_code)
    await send_wait_and_delete(client, message.channel, report)

async def add_command(message, servers, client, id_to_fragment_map):
    '''Add a command to the server'''
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers, client) and not is_owner(message.author): return

    split = message.content.split()
    if len(split) < 3: return

    prefix = 'add'
    if message.content[1:1+len(prefix)] != prefix: return

    input_ = split[1]
    output_ = ' '.join(split[2:])
    server = servers[message.server.id]

    if input_ in server.command_map:
        report = ':bangbang: The command **{}** already exists. Please remove it before adding a new one.'.format(input_)
        await send_wait_and_delete(client, message.channel, report)
        return
    server.command_map[input_] = output_

    config = build_config_dict(server)
    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: Added command **{}** with response <{}>'.format(input_, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to add command: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await send_wait_and_delete(client, message.channel, report)

async def handle_alias_command_request(message, servers, client, id_to_fragment_map):
    '''Alias one command to another'''
    if message.content[0] != ',': return
    if not is_mod(message.author, message.server.id, servers, client) and not is_owner(message.author): return

    split = message.content.split()
    if len(split) < 3: return

    prefix = 'alias'
    if message.content[1:1+len(prefix)] != prefix: return

    input_, output_ = split[1], split[2]
    server = servers[message.server.id]

    if input_ in server.command_map:
        report = ':bangbang: The command **{}** already exists. Please remove it before adding a new one.'.format(input_)
        await send_wait_and_delete(client, message.channel, report)
        return

    if output_ not in server.command_map:
        report = ':no_entry: The command **{}** does not exist'.format(output_)
        await send_wait_and_delete(client, message.channel, report)
        return

    server.command_map[input_] = server.command_map[output_]

    config = build_config_dict(server)
    r = make_put_request_update_config(server, config, id_to_fragment_map)
    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: The command **{}** has been aliased to **{}**'.format(input_, output_)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to add alias: **{}**. Error code: **{}**'.format(input_, r.status_code)
    await send_wait_and_delete(client, message.channel, report)


def build_config_dict(server):
    role_map = { name: [id1, id2] for (name, (id1, id2)) in server.role_map.items() }
    return {
        'channels': [server.welcome_chan, server.main_chan, server.bias_chan],
        'log_chan': server.log_chan,
        'do_not_log': server.do_not_log,
        'default_role': server.default_role,
        'welcome_msg': server.welcome_msg,
        'mod_roles': server.mod_roles,
        'role_map': role_map,
        'command_map': server.command_map,
        'member_nicknames': server.member_nicknames,
        'member_pics': server.member_pics,
        'periodic_pics': server.periodic_pics,
        'announce_member_leaving': server.announce_member_leaving,
    }

def make_put_request_update_config(server, config, id_to_fragment_map):
    headers = { 'Content-Type': 'application/json; charset=utf-8', 'Data-Type': 'json', }

    api_root = 'https://api.myjson.com/bins/'
    for s_id, url_fragment in id_to_fragment_map:
        if s_id == server.id:
            url = api_root + url_fragment
            r = requests.put(url, data=json.dumps(config), headers=headers)
            return r

    return None

async def set_bias_channel(message, servers, client, id_to_fragment_map):
    '''Set the bias channel for a server'''
    if not message.content.startswith('-'): return
    if not is_owner(message.author): return

    prefix = 'sbc'
    if message.content[1:1+len(prefix)] != prefix: return

    if len(message.channel_mentions) != 1:
        report = ':exclamation: Usage: -sbc [#channel_mention]'
        await send_wait_and_delete(client, message.channel, report)
        return

    channel = message.channel_mentions[0]
    server = servers[message.server.id]

    headers = { 'Content-Type': 'application/json; charset=utf-8', 'Data-Type': 'json', }
    config = build_config_dict(server)
    config['channels'][2] = channel.id

    r = make_put_request_update_config(server, config, id_to_fragment_map)

    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: Bias channel is now: {0.mention}.'.format(channel)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to configure bias channel. Error code: **{}**'.format(r.status_code)
    else:
        id_to_fragment_map = read_configs(servers)
    await send_wait_and_delete(client, message.channel, report)

async def set_log_channel(message, servers, client, id_to_fragment_map):
    '''Set the log channel for a server'''
    if not message.content.startswith('-'): return
    if not is_owner(message.author): return

    prefix = 'slc'
    if message.content[1:1+len(prefix)] != prefix: return

    if len(message.channel_mentions) != 1:
        report = ':exclamation: Usage: -slc [#channel_mention] [#user_mention]*'
        await send_wait_and_delete(client, message.channel, report)
        return

    channel = message.channel_mentions[0]
    to_ignore = [member.id for member in message.mentions]
    server = servers[message.server.id]

    headers = { 'Content-Type': 'application/json; charset=utf-8', 'Data-Type': 'json', }
    config = build_config_dict(server)
    config['log_chan'] = channel.id
    config['do_not_log'] = to_ignore

    r = make_put_request_update_config(server, config, id_to_fragment_map)

    if r is None:
        report = ':skull_crossbones: Error updating config'
        await send_wait_and_delete(client, message.channel, report)
        return

    report = ':white_check_mark: Log channel is now: {0.mention}.'.format(channel)
    if len(message.mentions) > 0:
        report += ' Ignored users: ' + ' '.join(m.mention for m in message.mentions)
    if r.status_code != requests.codes.ok:
        report = ':no_entry: Failed to configure log. Error code: **{}**'.format(r.status_code)
    else:
        id_to_fragment_map = read_configs(servers)
    await send_wait_and_delete(client, message.channel, report)

async def list_special_channels(message, servers, client):
    '''List the welcome, bias and log channels'''
    if not is_owner(message.author): return
    if not message.content == '-lsc': return

    server = servers[message.server.id]

    report = [0,0,0,0]

    if server.welcome_chan is None: report[0] = 'No welcome channel'
    else:
        welcome_chan = client.get_channel(server.welcome_chan)
        report[0] = 'Welcome channel: {0.mention}'.format(welcome_chan)

    if server.bias_chan is None: report[1] = 'No bias channel'
    else:
        bias_chan = client.get_channel(server.bias_chan)
        report[1] = 'Bias channel: {0.mention}'.format(bias_chan)

    if server.log_chan is None: report[2] = 'No log channel'
    else:
        log_chan = client.get_channel(server.log_chan)
        report[2] = 'Log channel: {0.mention}.'.format(log_chan)
        ignored_users = map(lambda m: server.get_member(m), server.do_not_log)
        report += 'Ignored users: ' + ' '.join('{0.mention}' for c in ignored_users)

    report = '\n'.join(report)
    await client.send_message(message.channel, report)

async def send_wait_and_delete(client, destination, content, delete=False, delay=5):
    '''Send a message, wait for a few seconds and then OPTIONALLY delete it'''
    message = await client.send_message(destination, content)
    if delete:
        await asyncio.sleep(delay)
        await client.delete_message(message)

async def list_servers(message, client):
    '''List the names and IDs of all servers the bot is present in'''
    if message.content != '-servers': return
    servers = sorted(client.servers, key=lambda s: s.name)
    report = '\n'.join('{} {}'.format(s.name, s.id) for s in servers)
    await client.send_message(message.channel, report)

async def add_field(message, servers, client, id_to_fragment_map):
    '''Add a field to the remote JSON config for the specific server that the command is run in'''
    if not is_owner(message.author): return

    if message.content[0] != '-': return

    prefix = 'af'
    if message.content[1:1+len(prefix)] != prefix: return

    split = message.content.split()
    if len(split) != 2: return

    field = split[1]
    api_root = 'https://api.myjson.com/bins/'
    for server_id, url_fragment in id_to_fragment_map:
        if server_id == message.server.id:
            server = servers[server_id]
            url = api_root + url_fragment
            config = build_config_dict(server)
            config[field] = None
            r = make_put_request_update_config(server, config, id_to_fragment_map)
            server_name = client.get_server(server_id).name
            if r is None:
                report = ':skull_crossbones: Error updating config for server **{}**'.format(server_name)
                await client.send_message(message.channel, report)
                return
            if r.status_code != requests.codes.ok:
                report = ':no_entry: Failed to update config for server **{}**. Error code: **{}**'.format(server_name, r.status_code)
            else:
                id_to_fragment_map = read_configs(servers)
                report = ':white_check_mark: Added field **{}** to server config'.format(field)
            await client.send_message(message.channel, report)
            break

async def remove_field(message, servers, client, id_to_fragment_map):
    '''Remove a field in the remote JSON config for the specific server that the command is run in'''
    if not is_owner(message.author): return

    if message.content[0] != '-': return

    prefix = 'rf'
    if message.content[1:1+len(prefix)] != prefix: return

    split = message.content.split()
    if len(split) != 2: return

    field = split[1]
    api_root = 'https://api.myjson.com/bins/'
    for server_id, url_fragment in id_to_fragment_map:
        if server_id == message.server.id:
            server = servers[server_id]
            url = api_root + url_fragment
            config = build_config_dict(server)
            if field not in config:
                report = ':no_good: The field **{}** does not exist in the config for this server'.format(field)
                await client.send_message(message.channel, report)
                return
            del config[field]
            r = make_put_request_update_config(server, config, id_to_fragment_map)
            server_name = client.get_server(server_id).name
            if r is None:
                report = ':skull_crossbones: Error updating config for server **{}**'.format(server_name)
                await client.send_message(message.channel, report)
                return
            if r.status_code != requests.codes.ok:
                report = ':no_entry: Failed to update config for server **{}**. Error code: **{}**'.format(server_name, r.status_code)
            else:
                id_to_fragment_map = read_configs(servers)
                report = ':white_check_mark: Removed field **{}** from server config'.format(field)
            await client.send_message(message.channel, report)
            break


async def set_field_string(message, servers, client, id_to_fragment_map):
    '''Set a field to a string in the remote JSON config for the specific server that the command is run in'''
    if not is_owner(message.author): return
    if message.content[0] != '-': return

    prefix = 'sf'
    if message.content[1:1+len(prefix)] != prefix: return

    split = message.content.split()
    if len(split) < 3: return

    field = split[1]
    value = message.content[1+len(prefix)+1+len(field)+1:]
    api_root = 'https://api.myjson.com/bins/'
    for server_id, url_fragment in id_to_fragment_map:
        if server_id == message.server.id:
            server = servers[server_id]
            url = api_root + url_fragment
            config = build_config_dict(server)
            if field not in config:
                report = ':no_good: The field **{}** does not exist in the config for this server'.format(field)
                await client.send_message(message.channel, report)
                return
            config[field] = value
            r = make_put_request_update_config(server, config, id_to_fragment_map)
            server_name = client.get_server(server_id).name
            if r is None:
                report = ':skull_crossbones: Error updating config for server **{}**'.format(server_name)
                await client.send_message(message.channel, report)
                return
            if r.status_code != requests.codes.ok:
                report = ':no_entry: Failed to update config for server **{}**. Error code: **{}**'.format(server_name, r.status_code)
            else:
                id_to_fragment_map = read_configs(servers)
                report = ':white_check_mark: Set field **{}** to value **{}**'.format(field, value)
            await client.send_message(message.channel, report)
            break

async def list_urls(message, client, id_to_fragment_map):
    if not is_owner(message.author): return
    if message.content != '-lu': return
    api_root = 'https://api.myjson.com/{}'
    report = []
    for server_id, url_frag in id_to_fragment_map:
        server = client.get_server(server_id)
        url = api_root.format(url_frag)
        line = '{} {}'.format(server.name, url)
        report.append(line)
    report = '\n'.join(report)
    await client.send_message(message.author, report)

async def display_color(message, client):

    async def show_usage(message, client):
        report = 'Usage: `.color <RGB hex code>` e.g.\n`.color #abc123`\n`.color 142 79 105`'
        await client.send_message(message.channel, report)

    def hex_code_to_rgb(h):
        return tuple(int(channel, 16) for channel in [h[:2], h[2:4], h[4:]])

    def rgb_to_hex_code(r, g, b):
        def two_digit_hex(n):
            return hex(int(n))[2:].rjust(2, '0')
        return ''.join(map(two_digit_hex, [r, g, b]))

    async def send_color_patch_pic(client, color):
        data = [color for i in range(64 * 64)]
        img = Image.new('RGB', (64, 64))
        img.putdata(data)
        filename = form_filename(color)
        img.save(filename)
        await client.send_file(message.channel, filename)
        os.remove(filename)

    def form_filename(color):
        hex_code = rgb_to_hex_code(*color)
        filename = '{}.png'.format(hex_code)
        return filename

    if message.content[0] not in '.!': return

    prefixes = ['color', 'colour']
    if not any(message.content[1:1+len(prefix)] == prefix for prefix in prefixes):
        return

    split = message.content.split()

    if len(split) == 2:
        color = split[1]
        if color.startswith('#'): color = color[1:]
        elif color.startswith('0x'): color = color[2:]
        color = hex_code_to_rgb(color)
        await send_color_patch_pic(client, color)

    elif len(split) == 4:
        color = tuple(int(s) for s in split[1:])
        await send_color_patch_pic(client, color)

    else:
        await show_usage(message, client)
        return

async def handle_choose_request(message, client):

    async def show_usage(message, client):
        report = 'Usage: `.choose <choice1> | <choice2> | <choice3> | ...`' + \
                 '\ne.g. `.choose go to sleep | post on discord`'
        await client.send_message(message.channel, report)

    if message.content[0] not in '.!': return

    prefix = 'choose'
    if message.content[1:1+len(prefix)] != prefix: return

    split = message.content.split()
    if len(split) < 2:
        await show_usage(message, client)
        return

    choices = message.content.strip()[2+len(prefix):].strip()
    choices = choices.split('|')
    chosen = random.choice(choices)
    report = '{0.mention} I choose: **{1}**!'.format(message.author, chosen.strip())
    await client.send_message(message.channel, report)
