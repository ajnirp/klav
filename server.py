class Server:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            lines = [l.strip() for l in f.readlines()]
            self.id = config_file
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