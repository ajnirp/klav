class Server:
    def __init__(self, s_id, config_file_path, notifs_file_path, daily_file_path):
            self.id = s_id
            self.read_config(config_file_path)
            self.read_notifs(notifs_file_path)
            self.read_daily(daily_file_path)

    def read_config(self, config_file_path):
        with open(config_file_path, 'r') as f:
            lines = [l.strip() for l in f.readlines()]

            self.welcome_chan = lines[0]
            self.main_chan = lines[1]
            self.bias_chan = lines[2]

            log_config = lines[3]
            if log_config is '':
                self.log_chan = None
                self.do_not_log = []
            else:
                log_config = log_config.split()
                self.log_chan = log_config[0]
                self.do_not_log = log_config[1:]

            self.default_role = lines[4]
            if self.default_role is '':
                self.default_role = None

            self.welcome_msg = lines[5]
            if self.welcome_msg is '':
                self.welcome_msg = None

            self.mod_roles = lines[6].split()

            self.user_info_allowed = lines[7].split()

            self.role_map = {}
            for role_config in lines[8].split(':'):
                split = role_config.split(',')
                self.role_map[split[0]] = (split[1], split[2])

            self.command_map = {}
            for command_line in lines[9:]:
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

    def read_daily(self, daily_file_path):
        with open(daily_file_path, 'r') as f:
            self.daily_pics = f.read().strip().split()