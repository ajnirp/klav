class Server:
    def __init__(self, s_id, config_file_path, notifs_file_path):
            self.id = s_id
            self.read_config(config_file_path)
            self.read_notifs(notifs_file_path)

    def read_config(self, config_file_path):
        with open(config_file_path, 'r') as f:
            lines = [l.strip() for l in f.readlines()]
            self.welcome_chan = lines[0]
            self.main_chan = lines[1]
            self.mod_chan = lines[2]
            self.bias_chan = lines[3]
            self.default_role = lines[4]
            self.welcome_msg = lines[5]
            self.mod_roles = lines[6].split()
            self.role_map = {}
            for keyword_list in lines[7].split(':'):
                split = keyword_list.split(',')
                role = split[-1]
                for keyword in split[:-1]:
                    self.role_map[keyword] = role
            self.command_map = {}
            for command_line in lines[8:]:
                commands, response = command_line.split('\t')
                for command in commands.split(','):
                    self.command_map[command] = response

    def read_notifs(self, notifs_file_path):
        with open(notifs_file_path, 'r') as f:
            lines = [l.strip() for l in f.readlines()]
            self.notifs_map = {}
            for line in lines:
                split = line.split('\t')
                notif, targets = split[0], split[1:]
                self.notifs_map[notif] = set()
                for target in targets.split(' '):
                    self.notifs_map[notif].add(target)
