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

@client.event
async def on_member_join(member):
    server = servers[member.server.id]
    if server.welcome_msg is not None:
        main_chan = client.get_channel(server.main_chan)
        welcome_chan = client.get_channel(server.welcome_chan)
        bias_chan = client.get_channel(server.bias_chan)
        greeting = '{0.mention} {1} You are the **{2}{3}** member to join! Please read {4.mention}, and pick bias roles in {5.mention}.'

        count = member.server.member_count
        suffix = 'th'
        if count % 10 == 1: suffix = 'st'
        elif count % 10 == 2: suffix = 'nd'
        elif count % 10 == 3: suffix = 'rd'

        greeting = greeting.format(member, server.welcome_msg, count, suffix, welcome_chan, bias_chan)
        await client.send_message(main_chan, greeting)

    await util.assign_default_role(member, servers, client)

    # display member info in the log channel, if there is one
    if server.log_chan is not None:
        log_chan = client.get_channel(server.log_chan)
        report = 'joined: {} {}'.format(member.id, member.name)
        await client.send_message(log_chan, report)
        await util.display_user_info(member, log_chan, client)

@client.event
async def on_member_remove(member):
    if member.server.id == '202834966621585408': return
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

    # await notifs.check_notifs(message, servers, client)

    await util.dialogue(message, servers, client)

    if message.content[0] not in ',!.': return

    # Moderators only
    await util.delete_messages(message, servers, client)
    await util.kick_members(message, servers, client)

    # @everyone
    await util.handle_avatar_request(message, client)
    await util.handle_member_pic_request(message, servers, client)
    await util.command(message, servers, client)
    await util.help(message, servers, client)
    await util.user_info(message, servers, client)
    await util.handle_gsd_countdown_request(message, servers, client)
    # await notifs.add_notif(message, servers, client)
    # await notifs.remove_notif(message, servers, client)
    # await notifs.view_notifs(message, servers, client)

@client.event
async def on_message_delete(message):
    '''Log deleted messages if configured to do so for that server'''
    if message.server is None: return
    if message.author.id == client.user.id: return

    # If the message is a system 'pin added' message, ignore it
    if message.type == discord.MessageType.pins_add: return

    # If the server has no log channel, do nothing
    server = servers[message.server.id]
    if server.log_chan is None: return
    if message.author.id in server.do_not_log: return

    # Do not log messages that have been deleted from the log channel
    if message.channel.id == server.log_chan: return

    log_channel = client.get_channel(server.log_chan)
    timestamp = util.ts(message.timestamp)
    report = 'deleted: [{}] [{}] {}: {}'.format(
            message.channel.name, timestamp,
            message.author.name, message.content)
    await client.send_message(log_channel, report)

@client.event
async def on_message_edit(before, after):
    '''Log edited messages if configured to do so for that server'''
    if after.server is None: return
    if after.author.id == client.user.id: return

    server = servers[after.server.id]
    if server.log_chan is None: return
    if after.author.id in server.do_not_log: return

    if after.channel.id == server.log_chan: return

    log_channel = client.get_channel(server.log_chan)

    timestamp_before = util.ts(before.timestamp)
    timestamp_after = util.ts(after.timestamp)

    # There are multiple cases that trigger this event.
    # We are only interested in messages whose contents
    # have been edited, and messages that have been
    # pinned or unpinned.

    # Message has been pinned or unpinned.
    pin_event = util.pin_event(before, after)
    if pin_event:
        action = ['pinned', 'unpinned'][(pin_event+1)>>1]
        report = '{}: [{}] [{}] {}: {}'.format(
            action, before.channel.name, timestamp_before,
            before.author.name, before.content)
        await client.send_message(log_channel, report)
        return

    # The message has neither been pinned nor unpinned, and
    # the content is the same, meaning it has received an embed.
    # We don't care about this situation.
    if before.content == after.content: return

    # The message has had its contents edited.
    report = 'edited: [{}] [{}] {}: {} -> [{}] {}'.format(
            before.channel.name, timestamp_before,
            before.author.name, before.content,
            timestamp_after, after.content)
    await client.send_message(log_channel, report)

async def write_notifs_task(client):
    await client.wait_until_ready()
    while not client.is_closed:
        notifs.write_notifs_all(servers, client)
        print('wrote notifications file')
        await asyncio.sleep(600)

async def periodic_post_task(client):
    await client.wait_until_ready()
    while not client.is_closed:
        for server in servers.values():
            if util.time_to_post():
                await util.post_periodic_pic(server, client)
        await asyncio.sleep(60)

async def check_musicbot_task(client):
    await client.wait_until_ready()
    while not client.is_closed:
        await util.check_musicbot('202834966621585409', '203320553430450177', '197743740411052032', client)
        await asyncio.sleep(60)

if __name__ == '__main__':
    util.read_configs(servers)
    # client.loop.create_task(write_notifs_task(client))
    client.loop.create_task(periodic_post_task(client))
    # client.loop.create_task(check_musicbot_task(client))
    client.run(os.environ['F_BOT_TOKEN'])
