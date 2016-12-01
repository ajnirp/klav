import os
import time
import util

async def add_notif(message, servers, client):
    async def report_added_notif(message, notif, client):
        report = '{0.mention} added notification: {1}'
        report = report.format(message.author, notif)
        await client.send_message(message.channel, report)

    async def show_usage(message, client):
        info = '```Usage: .an <notification>.\nExample: .an pink tape\nThis sets a notification for "pink tape".```'
        await client.send_message(message.channel, info)

    prefix = 'an'
    if message.content[0] not in '.!': return
    if not message.content[1:].startswith(prefix): return
    notif = message.content[len(prefix)+2:].strip()
    if notif == '':
        await show_usage(message, client)
        return
    server = servers[message.server.id]
    if notif in server.notifs_map:
        if message.author.id in server.notifs_map[notif]:
            report = '{0.mention} you already have a notification enabled for {1}'
            report = report.format(message.author, notif)
            await client.send_message(message.channel, report)
        else:
            server.notifs_map[notif].add(message.author.id)
            await report_added_notif(message, notif, client)
    else:
        server.notifs_map[notif] = set([message.author.id])
        await report_added_notif(message, notif, client)

async def remove_notif(message, servers, client):
    async def report_not_removed_notif(message, notif, client):
        report = '{0.mention} you do not have a notification enabled for {1}'
        report = report.format(message.author, notif)
        await client.send_message(message.channel, report)

    async def show_usage(message, client):
        info = '```Usage: .rn <notification>.\nExample: .rn pink tape\nThis removes the notification for "pink tape", assuming you had set it previously.```'
        await client.send_message(message.channel, info)

    prefix = 'rn'
    if message.content[0] not in '.!': return
    if not message.content[1:].startswith(prefix): return
    notif = message.content[len(prefix)+2:].strip()
    if notif == '':
        await show_usage(message, client)
        return
    server = servers[message.server.id]
    if notif in server.notifs_map and message.author.id in server.notifs_map[notif]:
        server.notifs_map[notif].remove(message.author.id)
        if len(server.notifs_map[notif]) == 0:
            del server.notifs_map[notif]
        report = '{0.mention} removed {1} from your list of notifications'
        report = report.format(message.author, notif)
        await client.send_message(message.channel, report)
    else:
        await report_not_removed_notif(message, notif, client)

async def check_notifs(message, servers, client):
    server = servers[message.server.id]
    for notif in server.notifs_map:
        if notif in message.content:
            time_now = util.now()
            author_name = message.author.name
            for target_id in server.notifs_map[notif]:
                if target_id == message.author.id: continue
                target = message.server.get_member(target_id)
                report = '{} {}: {}'
                report = report.format(time_now, author_name, message.content)
                await client.send_message(target, report)

async def view_notifs(message, servers, client):
    if message.content not in ['.vn', '!vn']: return
    server = servers[message.server.id]
    notifs = [notif for notif, target_ids in \
              server.notifs_map.items() if message.author.id in target_ids]
    if len(notifs) == 0:
        report = 'No active notifications on {}'
        report = report.format(message.server.name)
        await client.send_message(message.author, report)
    else:
        report = 'Your active notifications on {}: {}'
        report = report.format(message.server.name, ', '.join(notifs))
        await client.send_message(message.author, report)

def write_notifs(server, client):
    notifs_file = os.path.join('.', 'notifs', server.id)
    with open(notifs_file, 'w') as f:
        for notif in server.notifs_map:
            f.write(notif)
            f.write('\t')
            f.write(' '.join(server.notifs_map[notif]))
            f.write('\n')

def read_notifs(server, client):
    notifs_file = os.path.join('.', 'notifs', server.id)
    with open(notifs_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            notif, target_ids = line.split('\t')
            server.notifs_map[notif] = set(target_ids.split())

def write_notifs_all(servers, client):
    for server in servers.values():
        write_notifs(server, client)