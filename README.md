### About

Klav is a Discord bot for K-pop servers.

### Features

* Welcome new members and auto-assign them a default role
* Assign members (possibly multiple) bias roles
* User commands
* Moderator commands: kick members, purge message history
* Post a daily picture

### Adding Klav to a server

1. Create a new file (name = server ID) in each of the directories `config`, `daily` and `notifs`.
2. For the format of the `config/` file, see the `__init__()` method in `server.py`. The files in `daily/` and `notifs/` can be left empty.