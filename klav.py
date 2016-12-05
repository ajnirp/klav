#!/usr/bin/env python3

import asyncio
import discord
import notifs
import os
import util

client = discord.Client()
servers = {}

@client.event
async def on_ready():
    print('Logged in as:', client.user.name)
    print('Client ID:', client.user.id)
    print('Version number:', discord.version_info)

@client.event
async def on_member_join(member):
    server = servers[member.server.id]
    main_chan = client.get_channel(server.main_chan)
    welcome_chan = client.get_channel(server.welcome_chan)
    bias_chan = client.get_channel(server.bias_chan)
    greeting = '{0.mention} {1}! Please read {2.mention}, and pick bias roles in {3.mention}.'
    greeting = greeting.format(member, server.welcome_msg, welcome_chan, bias_chan)
    await util.assign_default_role(member, servers, client)
    await client.send_message(main_chan, greeting)

@client.event
async def on_member_remove(member):
    server = servers[member.server.id]
    main_chan = client.get_channel(server.main_chan)
    notification = '**{0.name}** has left the server'
    notification = notification.format(member)
    await client.send_message(main_chan, notification)

@client.event
async def on_message(message):
    if message.server is None: return
    if message.author.id == client.user.id: return
    if len(message.content) == 0: return

    server = servers[message.server.id]
    if message.channel.id == server.bias_chan:
        await util.set_bias(message, servers, client)

    await notifs.check_notifs(message, servers, client)

    if message.content[0] not in ',!.': return

    # Moderators only
    await util.delete_messages(message, servers, client)
    await util.kick_members(message, servers, client)

    # @everyone
    await util.command(message, servers, client)
    await util.help(message, servers, client)
    await notifs.add_notif(message, servers, client)
    await notifs.remove_notif(message, servers, client)
    await notifs.view_notifs(message, servers, client)

async def write_notifs_task(client):
    await client.wait_until_ready()
    while not client.is_closed:
        notifs.write_notifs_all(servers, client)
        print('wrote notifications file')
        await asyncio.sleep(600)

async def daily_post(client):
    await client.wait_until_ready()
    while not client.is_closed:
        for server in servers.values():
            await util.post_daily_pic(server, client)
        await asyncio.sleep(24*3600)

if __name__ == '__main__':
    util.read_configs(servers)
    client.loop.create_task(write_notifs_task(client))
    client.loop.create_task(daily_post(client))
    client.run(os.environ['F_BOT_TOKEN'])
