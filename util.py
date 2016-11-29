import discord
import os
import server

async def report_bias(message, roles, client):
    report = '{0.mention} Your bias has been set to '.format(message.author)
    report += ', '.join('**{}**'.format(role.name) for role in roles)
    await client.send_message(message.channel, report)

async def set_bias(message, servers, client):
    content = message.content.lower()
    server = servers[message.server.id]
    role_ids = [server.role_map[kw] for kw in server.role_map if kw in content]
    roles = [discord.utils.find(lambda r: r.id == role_id, message.server.roles) for role_id in role_ids]
    if len(roles) > 0:
        bias_chan = client.get_channel(server.bias_chan)
        await client.add_roles(message.author, *roles)
        await report_bias(message, roles, client)

async def assign_default_role(member, servers, client):
    server = servers[member.server.id]
    default_role = discord.utils.find(lambda r: r.id == server.default_role, member.server.roles)
    await client.add_roles(member, default_role)

def read_configs(servers):
    config_dir = os.path.join('.', 'config')
    config_files = os.listdir(config_dir)
    for s_id in config_files:
        file_path = os.path.join(config_dir, s_id)
        servers[s_id] = server.Server(file_path)

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