#!/usr/bin/env python3

import asyncio
import discord
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

    if message.content[0] not in ',.': return

    await util.delete_messages(message, servers, client)
    await util.kick_members(message, servers, client)
    await util.command(message, servers, client)
    await util.help(message, servers, client)

if __name__ == '__main__':
    util.read_configs(servers)
    client.run(os.environ['F_BOT_TOKEN'])
