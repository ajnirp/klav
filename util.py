import asyncio
import discord
import os
import server
import time

async def set_bias(message, servers, client):
    server = servers[message.server.id]
    content = message.content.strip().lower().split()

    # Figure out which roles to add to the user
    to_add_ids = [server.role_map[kw] for kw in server.role_map if kw in content]
    to_add_roles = [discord.utils.find(lambda r: r.id == r_id, message.server.roles) for r_id in to_add_ids]

    if len(to_add_ids) > 0:
        new_roles_ids = [r.id for r in message.author.roles if r.id not in server.role_map.values()] + to_add_ids
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

async def assign_default_role(member, servers, client):
    server = servers[member.server.id]
    default_role = discord.utils.find(lambda r: r.id == server.default_role, member.server.roles)
    await client.add_roles(member, default_role)

def read_configs(servers):
    config_dir = os.path.join('.', 'config')
    config_files = os.listdir(config_dir)
    notifs_dir = os.path.join('.', 'notifs')
    notifs_files = os.listdir(notifs_dir)
    for config_file, notifs_file in zip(config_files, notifs_files):
        config_file_path = os.path.join(config_dir, config_file)
        notifs_file_path = os.path.join(notifs_dir, notifs_file)
        s_id = config_file
        servers[s_id] = server.Server(config_file, config_file_path, notifs_file_path)

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
        mod_chan = client.get_channel(server.mod_chan)
        report = '**{0.name}** was kicked by {1.mention}'
        report = report.format(member, message.author)
        await client.send_message(mod_chan, report)

async def command(message, servers, client):
    if message.content[0] != '.': return
    server = servers[message.server.id]
    command_str = message.content[1:]
    if command_str in server.command_map:
        response = server.command_map[command_str]
        await client.send_message(message.channel, response)

async def help(message, servers, client):
    if message.content != '.h': return
    server = servers[message.server.id]
    help_str = 'Commands: '  + ', '.join(sorted(server.command_map.keys()))
    await client.send_message(message.author, help_str)

def now():
    return time.strftime('[%y%m%d %H:%M]')