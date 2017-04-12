class Server:
    def __init__(self, s_id, config):
        self.id = s_id
        self.welcome_chan = config['channels'][0]
        self.main_chan = config['channels'][1]
        self.bias_chan = config['channels'][2]
        self.log_chan = config['log_chan']
        self.do_not_log = config['do_not_log']
        self.default_role = config['default_role']
        self.role_map = config['role_map']
        self.welcome_msg = config['welcome_msg']
        self.mod_roles = config['mod_roles']
        self.gallery_chan = config['gallery_chan']
        self.do_not_copy_to_gallery = config['do_not_copy_to_gallery']
        self.command_map = config['command_map']
        self.periodic_pics = config['periodic_pics']
        self.member_nicknames = config['member_nicknames']
        self.member_pics = config['member_pics']
        if 'announce_member_leaving' in config:
            self.announce_member_leaving = config['announce_member_leaving']
        else:
            self.announce_member_leaving = False