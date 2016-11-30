import os
import time
import util

async def add_notif(message, servers, client):
    prefix = '.an '
    if not message.content.startswith(prefix): return
    notif = message.content[len(prefix):]
    server = servers[message.server.id]
    server.notifs_map[notif] = message.author.id
    report = '{0.mention} added notification: {1}'
    report = report.format(message.author, notif)
    await client.send_message(message.channel, report)

async def check_notifs(message, servers, client):
    server = servers[message.server.id]
    for notif in server.notifs_map:
        if notif in message.content:
            time_now = util.now()
            target_id = server.notifs_map[notif]
            if target_id == message.author.id: continue
            target = message.server.get_member(target_id)
            author_name = message.author.name
            report = '{} {}: {}'
            report = report.format(time_now, author_name, message.content)
            await client.send_message(target, report)

async def view_notifs(message, servers, client):
    if not message.content.startswith('.vn'): return
    server = servers[message.server.id]
    notifs = [notif for notif, target_id in \
              server.notifs_map.items() if target_id == message.author.id]
    report = 'Your active notifs on {}: {}'
    report = report.format(message.server.name, ', '.join(notifs))
    await client.send_message(message.author, report)

def write_notifs(server, client):
    notifs_map = server.notifs_map
    notifs_file = os.path.join('.', 'notifs', server.id)
    with open(notifs_file, 'w') as f:
        for notif in notifs_map:
            f.write(notif)
            f.write('\t')
            f.write(notifs_map[notif])
            f.write('\n')

def read_notifs(server, client):
    notifs_file = os.path.join('.', 'notifs', server.id)
    with open(notifs_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            notif, user_id = line.split('\t')
            server.notifs_map[notif] = user_id

def write_notifs_all(servers, client):
    for server in servers.values():
        write_notifs(server, client)