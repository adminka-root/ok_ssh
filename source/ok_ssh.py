#!/usr/bin/env python3

import sys
import os
from datetime import datetime
import subprocess
import argparse
import shutil
import re

import yaml  # pyyaml
from jinja2 import FileSystemLoader, Environment
from ast import literal_eval  # dict/list as str to dict/list
from sshconf import read_ssh_config, empty_ssh_config_file  # https://github.com/sorend/sshconf

SCRIPT_DIR: str = os.path.abspath(os.path.dirname(sys.argv[0]))
TIME_POSTFIX = False
# CHECK_VARS = lambda x: x in vars().keys() or x in globals().keys()

# del trash: ssh-copy, backups
# 


class StaticMethods:
    """ Typical functions of program's"""
    SAVE_DIR: str = SCRIPT_DIR
    TIME_POSTFIX: bool = TIME_POSTFIX

    @staticmethod
    def select_yes_or_no(question: str, yes_by_default: bool = True):
        """ User Dialogue, using input() """
        inscription = '\nAnswer[Y/n]: ' if yes_by_default else '\nAnswer[y/N]: '
        answer = input(question + inscription).lower()
        if yes_by_default and answer == '':
            return True

        if answer in ['yes', 'y', 'true']:
            return True
        else:
            return False

    @staticmethod
    def dconf_backup_command(schema: str, create_backup_file: bool = True):
        """
        Backup dconf schema properties
        :param schema: Schema for backup. Only path! (without schema+value)
        :param create_backup_file: Whether to create a file with which you can restore the previous state
        :return: Bash command for restore from dconf
        :rtype: str
        """
        backup_file = os.path.join(StaticMethods.SAVE_DIR, schema[1:].replace('/', '.') + 'ini')
        proc = subprocess.Popen(
            ['dconf', 'dump', schema],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.wait()

        (stdout, stderr) = proc.communicate()
        if proc.returncode != 0:  # if err
            print("stderr: ", stderr)
            if not StaticMethods.select_yes_or_no(
                    "Command 'dconf dump %s > %s' failed! Do you want to continue anyway?" % (schema, backup_file),
                    yes_by_default=False
            ):
                print('Aborted!')
                sys.exit(0)
        else:

            if create_backup_file:
                backup_file = StaticMethods.save_file(backup_file, stdout, mode='wb')
                # print("\nSuccessful backup for сommand 'dconf dump %s > %s' !" % (schema, backup_file))
                command = "dconf reset -f %s\ndconf load %s < '%s'" % (schema, schema, backup_file)
                # print("To restore use command:\n%s" % command)
                return command
            else:
                print(stdout)

    @staticmethod
    def save_file(save_to: str, data, time_postfix=None, mode='w', chmod: str = None):
        """
        Save data to file
        :return: the path where the file was saved
        :rtype: str
        """
        time_postfix = StaticMethods.TIME_POSTFIX if time_postfix is None else time_postfix
        save_to_dir = os.path.dirname(save_to)
        os.makedirs(save_to_dir, exist_ok=True)
        if time_postfix:
            save_to = StaticMethods.get_name_with_time_postfix(save_to)

        with open(save_to, mode) as file:
            if type(data) == list:
                data = '\n'.join(data)
            file.write(data)

        if chmod is not None:
            chmod = int(chmod, base=8)
            os.chmod(save_to, chmod)

        return save_to

    @staticmethod
    def get_name_with_time_postfix(path: str):
        """
        Get filename with time postfix (123.tar.gz -> 123.tar._%d_%m_%y_(%H:%M:%S).gz)
        :return: filename
        :rtype: str
        """
        dir_ = os.path.dirname(path)
        backup_postfix = '_' + datetime.now().strftime("%d_%m_%y_(%H:%M:%S)")
        file_ = os.path.basename(path)
        index = file_.rfind('.')
        if index == -1:
            file_ += backup_postfix
        else:
            file_ = file_[:index] + backup_postfix + file_[index:]
        path = os.path.join(dir_, file_)
        return path

    @staticmethod
    def dconf_read_command(schema: str, list_: bool = False):
        """
        Get data from dconf
        :param schema:
        :param list_: 'dconf read' if list_ else 'dconf list'
        :return: output: str if successful else False
        """
        try:
            return subprocess.check_output(
                ['dconf', 'read' if not list_ else 'list', schema], universal_newlines=True
            ).replace('\n', '')
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def dconf_reset_command(schema: str):
        """
        Reset data from dconf
        :param schema:
        :return: output: str if successful else False
        """
        try:
            return subprocess.check_output(
                ['dconf', 'reset', '-f', schema], universal_newlines=True
            ).replace('\n', '')
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def dconf_write_command(schema: str, value: str):
        """
        Dconf write command
        Prints to output the command that resulted in the error
        :param schema: working full schema
        :param value: value for write
        :return: executed command: str if successful else 1
        """
        proc = subprocess.Popen(
            ['dconf', 'write', schema, value],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            proc.wait(3)
            return_cmd = 'dconf write {0} "{1}"'.format(schema, value)
            if proc.returncode != 0:
                print("Err:", return_cmd)
                return False
            return return_cmd
        except:
            return 1

    @staticmethod
    def backup_file(file: str, time_postfix: bool = None):
        """
        Backup file with permissions (near)
        :param file: full path to the file
        :param time_postfix: whether to add time postfix
        :return: the path where the file was saved
        :rtype: str
        """
        time_postfix = StaticMethods.TIME_POSTFIX if time_postfix is None else time_postfix
        if os.path.isfile(file):
            if time_postfix:
                save_to = StaticMethods.get_name_with_time_postfix(file) + '.bak'
            else:
                save_to = file + '.bak'
            shutil.copy2(file, save_to)
            st = os.stat(file)
            os.chown(save_to, st.st_uid, st.st_gid)
            return save_to

    @staticmethod
    def read_file(input_file: str, mode='r'):
        """
        Method for reading data from a file. Throws an exception on failure
        :rtype: str
        """
        try:
            with open(input_file, mode) as file:
                return file.read()
        except:
            raise Exception('Failed to load %s!' % input_file)

    @staticmethod
    def delete_newlines(data: str):
        """ Replace 2 or more consecutive newlines with 2 newlines """
        data = re.sub(r'\n{2,}', r'\n\n', data)
        return data

    @staticmethod
    def run_popen(command_list, timeout: float = 60):
        """
        Execute a child program in a new process
        :return: returncode or 1 if failed, stdout: str, stderr: str
        """
        proc = subprocess.Popen(command_list,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, universal_newlines=True)
        try:
            proc.wait(timeout)
            stdout, stderr = proc.communicate()
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired as Err:
            return 1, '', str(Err) + '\n'


class SpecificMethods:
    """ Specific program functions """

    @staticmethod
    def read_yml(yml_file: str):
        """
        Specific reading of the main yaml config for it program
        :rtype: dict
        """
        with open(yml_file, "r") as file:
            try:
                yaml_data = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                raise Exception("\n\nError! %s" % exc)

        env = Environment(loader=FileSystemLoader(searchpath=os.path.dirname(yml_file)))
        env.filters['path_join'] = lambda x: os.path.join(*x)
        template = env.get_template(os.path.basename(yml_file))
        yaml_data = yaml.safe_load(template.render(yaml_data))

        for server in yaml_data['dict_of_servers'].keys():
            # binding for proper references to other dictionaries
            for server_key in yaml_data['dict_of_servers'][server].keys():
                value = yaml_data['dict_of_servers'][server][server_key]
                if isinstance(value, str) and (value[0] + value[-1] == '{}'):
                    yaml_data['dict_of_servers'][server][server_key] = literal_eval(value)
        for key_ in yaml_data.keys():
            value = yaml_data[key_]
            if isinstance(value, str) and (value[0] + value[-1] in ['{}', '[]']):
                yaml_data[key_] = literal_eval(value)
        return yaml_data

    @staticmethod
    def i_want_add(yml_dict: dict):
        """ I want to add what is defined in yml as i_want_add """
        i_want_add = []
        for server in yml_dict['dict_of_servers'].keys():
            if yml_dict['dict_of_servers'][server]['i_want_add']:
                i_want_add.append(server)
        return i_want_add

    @staticmethod
    def i_want_skeep(yml_dict: dict, base_profile: str = None):
        """
        I want to skip, anything I don't want to add (i_want_add) and possibly base_profile
        :param base_profile: if given, will include in the resulting returned list
        :rtype: list
        """
        i_want_skeep = [base_profile if base_profile is not None else '']
        for server in yml_dict['dict_of_servers'].keys():
            if not yml_dict['dict_of_servers'][server]['i_want_add']:
                i_want_skeep.append(server)
        return i_want_skeep

    @staticmethod
    def server_info(yml_dict: dict, server: str):
        """
        For comfort func
        :return: dict(User, Password, IP, Port, AuthorizationFile, IdentityFile)"""
        server_dict = yml_dict['dict_of_servers'][server]
        user = server_dict['authorization']['username']
        password = server_dict['authorization']['password']
        ip = server_dict['ip']
        port = server_dict['port'] if "port" in server_dict else '22'
        public_key = os.path.expanduser(server_dict['keys']['public_key'])
        private_key = os.path.expanduser(server_dict['keys']['private_key'])
        return dict(
            User=user, Password=password, IP=ip, Port=port,
            AuthorizationFile=public_key, IdentityFile=private_key
        )


class AnalyzeCliParameters:
    """ Handling command line options """
    DEFAULT_YML_CONFIG = os.path.join(SCRIPT_DIR, 'servers.yml')

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog=sys.argv[0],
            description='Script for integrating ssh connections in GNU/Linux OS',
            epilog='Adminka-root 2023. https://github.com/adminka-root'
        )

        self.main_group = self.parser.add_argument_group(title='Main options')
        self.extra_group = self.parser.add_argument_group(title='Extra options')

        self.main_group.add_argument(
            '-d', '--dconf_actions', action='store_true', default=False, required=False,
            help='Run dconf actions to add connection profiles in terminal (default=False)',
        )

        self.main_group.add_argument(
            '-s', '--ssh_config_actions', action='store_true', default=False, required=False,
            help='Perform actions in the config file (default=False)',
        )

        self.main_group.add_argument(
            '-r', '--reset_and_exit', action='store_true', default=False, required=False,
            help='Delete profiles and log out. Has effect only when appropriate options are '
                 'specified: -d/-s (default=False)',
        )

        self.main_group.add_argument(
            '-a', '--auto_authorization', action='store_false', default=True, required=False,
            help='Send keys to servers and log in automatically (default=True, with -a=False)',
        )

        self.extra_group.add_argument(
            '-y', '--yml_config', nargs=1, type=os.path.expanduser,
            default=self.DEFAULT_YML_CONFIG, metavar='FILE',
            help='Specify main yml config (default=' + self.DEFAULT_YML_CONFIG + ')',
        )

        self.extra_group.add_argument(
            '-b', '--base_profile', nargs=1, type=str, required=False, default=None,
            help='Specify a basic terminal profile (takes precedence over a profile from a file)',
            metavar='STR',
        )

        self.extra_group.add_argument(
            '-c', '--clear_ssh_config', action='store_true', default=False, required=False,
            help='Before adding profiles, first clear ssh config (default=False)',
        )

        self.extra_group.add_argument(
            '-n', '--not_backup', action='store_true', default=False, required=False,
            help='Don\'t make backups (default=False)',
        )

        self.extra_group.add_argument(
            '-t', '--time_postfix', action='store_true', default=False, required=False,
            help='Add postfix for backup files (default=False)',
        )

        self.extra_group.add_argument(
            '--ssh_config_dest', nargs=1, type=str, required=False, default=None,
            help='Specify ssh config location (default - reading from yaml)',
            metavar='STR',
        )

        self.extra_group.add_argument(
            '--auto_authorization_method', nargs=1, type=str, required=False, default=None,
            help='Specify the preferred program that will enter the password when copying the key (sshpass or expect)',
            metavar='STR',
        )

        self.options = self.parser.parse_args(sys.argv[1:])  # parsing options

        if not self.options.dconf_actions and not self.options.ssh_config_actions:
            self.get_error('Please use at least one of the options -s/-d')

        if not os.path.isfile(self.options.yml_config):
            raise Exception("The file {0} does not exist!".format(self.options.yml_config))
        if self.options.reset_and_exit and not StaticMethods.select_yes_or_no(
                'Reset and exit mode selected. Do you want to continue?',
        ):
            print('Aborted!')
            sys.exit(0)

        if self.options.base_profile is not None:
            self.options.base_profile = self.options.base_profile[0]

        if self.options.ssh_config_dest is not None:
            self.options.ssh_config_dest = os.path.expanduser(
                self.options.ssh_config_dest[0])

        if self.options.auto_authorization:
            sshpass_exists = os.path.isfile('/usr/bin/sshpass')
            expect_exists = os.path.isfile('/usr/bin/expect')
            if not sshpass_exists and not expect_exists:
                self.get_error(
                    'Please install sshpass or expect for automatic authorization while copying the public key!')
            if self.options.auto_authorization_method is None:
                self.options.auto_authorization_method = 'sshpass' if sshpass_exists else 'expect'
            else:
                self.options.auto_authorization_method = self.options.auto_authorization_method[0].lower()
                if self.options.auto_authorization_method not in ['sshpass', 'expect']:
                    self.get_error('-a "' + self.options.auto_authorization_method + '" is not correct!')
                elif (self.options.auto_authorization_method == 'sshpass' and not sshpass_exists) or \
                        (self.options.auto_authorization_method == 'expect' and not expect_exists):
                    self.get_error('Please install ' + self.options.auto_authorization_method + ' !')

    def get_error(self, message: str):
        self.parser.print_help()
        print('\n', message)
        sys.exit(1)


class ConfigureDconfTerminal:
    """ Setting up terminal profiles for convenient connection via ssh """
    schema_of_terminal: str = '/org/mate/terminal/profiles/'
    schema_global_list: str = '/org/mate/terminal/global/profile-list'
    save_dir: str = SCRIPT_DIR

    @property
    def added_in_dconf_yml_servers(self):
        """
        Added what I want to add (i_want_add) and what is in the dconf branch (all_profiles_in_dconf)
        :rtype: list of str
        """
        return list(set(SpecificMethods.i_want_add(self.yml_dict)) & set(self.all_profiles_in_dconf))

    @property
    def all_profiles_in_dconf(self):
        """
        Clean scan of dconf branch
        :rtype: list of str
        """
        all_profiles_in_dconf: "list of str" = []
        for profile_title in self.dconf_profile_title_dict.items():
            all_profiles_in_dconf.append(profile_title[0])
        return all_profiles_in_dconf

    @property
    def dconf_profile_title_dict(self):
        """
        :return: dict(
                    profile_N (pathname in dconf) =
                        title_name_N (corresponding),
                    ...)
        :rtype: dict
        """
        dconf_profile_title_dict = {}
        for profile in ConfigureDconfTerminal.get_relative_list_of_dirnames(self.schema_of_terminal):
            # get it as is
            title_name: str = StaticMethods.dconf_read_command(
                self.schema_of_terminal + profile + '/title'
            )
            if title_name:
                if title_name[0] + title_name[-1] == "''":
                    title_name = title_name[1:-1]
                title_name = title_name.split(' ')[0]
            dconf_profile_title_dict[profile]: str = title_name
        return dconf_profile_title_dict

    @staticmethod
    def get_relative_list_of_dirnames(schema: str = None):
        """
        Get a relative list of directory names in dconf
        :rtype: list
        """
        schema = ConfigureDconfTerminal.schema_of_terminal if schema is None else schema
        return StaticMethods.dconf_read_command(
            schema=schema, list_=True
        ).split('/')[:-1]

    @staticmethod
    def check_exists_profile(profile: str, schema: str = None):
        """ Make sure the profile exists """
        schema = ConfigureDconfTerminal.schema_of_terminal if schema is None else schema
        if profile not in ConfigureDconfTerminal.get_relative_list_of_dirnames(schema):
            return False
        return True

    @property
    def not_added_in_dconf_yml_servers(self):
        """
        Not added what I want to add (i_want_add) but what is not in dconf branch (all_profiles_in_dconf)
        """
        return list(set(SpecificMethods.i_want_add(self.yml_dict)) - set(self.all_profiles_in_dconf))

    @staticmethod
    def update_global_profile_list(schema_global_list: str = None, schema_of_terminal: str = None):
        """ Rewriting """
        schema_global_list = \
            ConfigureDconfTerminal.schema_global_list if schema_global_list is None else schema_global_list
        schema_of_terminal = \
            ConfigureDconfTerminal.schema_of_terminal if schema_of_terminal is None else schema_of_terminal

        StaticMethods.dconf_write_command(
            schema_global_list, str(ConfigureDconfTerminal.get_relative_list_of_dirnames(schema_of_terminal)))

    def __init__(self, yml_dict: dict, options: argparse.Namespace,
                 schema_of_terminal: str = None, schema_global_list: str = None,
                 save_dir: bool = None, type_f: str = 'Mate'):
        self.yml_dict = yml_dict
        self.options = options

        self.schema_of_terminal = self.schema_of_terminal if not schema_of_terminal else schema_of_terminal
        self.schema_global_list = self.schema_global_list if not schema_global_list else schema_global_list
        self.save_dir = self.save_dir if not save_dir else save_dir
        self.type_f = type_f  # add_new_terminal_profiles_in_dconf

        # overriding methods for convenience ----------------------
        self.update_global_profile_list = lambda: ConfigureDconfTerminal.update_global_profile_list(
            self.schema_global_list, self.schema_of_terminal)

        self.check_exists_profile = lambda profile: ConfigureDconfTerminal.check_exists_profile(
            profile, self.schema_of_terminal)
        # ---------------------------------------------------------

        self.options.base_profile = self.get_base_profile_canonical_name()
        self.show_dconf_property(start_message='*** DCONF STATE BEFORE EDITING: ***', show=True)

        if not self.options.not_backup:
            self.dconf_backup()

        if self.options.reset_and_exit:
            self.delete_existing_profiles()
        else:
            self.values_of_base_profile = self.get_values_of_base_profile()
            self.add_new_terminal_profiles_in_dconf()
        self.show_dconf_property(start_message='*** DCONF STATE AFTER EDITING: ***', show=True)

    def dconf_backup(self):
        """
        Backup branches self.schema_of_terminal and self.schema_global_list
        in file os.path.join(self.save_dir, 'dconf_restore.txt')
        :return: raise Exception if Failed else None
        """
        command = StaticMethods.dconf_backup_command(schema=self.schema_of_terminal)

        backup_file = os.path.join(self.save_dir, 'dconf_restore.txt')
        data = StaticMethods.dconf_read_command(schema=self.schema_global_list)
        if data:
            data = 'To restore the original state, enter the following commands in the terminal:\n\n' \
                   'dconf write %s \"%s\"\n' % (self.schema_global_list, data)
            data += command + '\n\n' + 'Adminka-root 2023. Welcome with questions ' \
                                       'to https://github.com/adminka-root ^_^\n'
            print("\nTo restore the original state see - cat '%s'" % StaticMethods.save_file(backup_file, data))
        else:
            raise Exception("Can't save the file %s! Aborted!" % backup_file)

    def show_dconf_property(self, start_message: str = 'Dconf:', show: bool = True):
        """ Output the main properties of a class instance is show == True """
        if show:
            formatting = lambda x: ', '.join(sorted(x)) if x else "['']"
            print()
            print(start_message)
            print("Desired added     = %s" % formatting(self.added_in_dconf_yml_servers))
            print("Desired NOT added = %s" % formatting(self.not_added_in_dconf_yml_servers))
            print("All profiles      = %s" % formatting(self.all_profiles_in_dconf))
            print("I don't want to add/edit = %s" % formatting(
                SpecificMethods.i_want_skeep(self.yml_dict, self.options.base_profile)
            ))

    def get_base_profile_canonical_name(self):
        """ Obtaining a canonical base profile else raise Exception"""
        alt_base_profile = self.yml_dict['base_profile']
        if self.options.base_profile is not None:
            if self.check_exists_profile(self.options.base_profile):
                return self.options.base_profile
            elif not self.check_exists_profile(alt_base_profile):
                raise Exception("Profiles of terminal '%s' and '%s' don't exist! Existing Profiles: %s" % (
                    self.options.base_profile, alt_base_profile, self.all_profiles_in_dconf))
            elif not StaticMethods.select_yes_or_no(
                    "Profile of terminal '%s' don't exist! "
                    "Do you wan't continue with '%s'?" % (
                            self.options.base_profile, alt_base_profile),
                    yes_by_default=False
            ):
                print('Aborted!')
                sys.exit(1)
        elif not self.check_exists_profile(alt_base_profile):
            raise Exception("Profile of terminal '%s' don't exist!" % (
                alt_base_profile))

        return alt_base_profile

    def delete_existing_profiles(self):
        """ Delete existing profiles that I want to add """
        for profile in self.added_in_dconf_yml_servers:
            if profile != self.options.base_profile:
                StaticMethods.dconf_reset_command(
                    self.schema_of_terminal + profile + '/')
            else:
                server = self.dconf_profile_title_dict[profile]
                print("Skipping profile reset %s for server %s!" % (profile, server))

        # if SpecificMethods.i_want_skeep(self.yml_dict, self.options.base_profile):
        #     print("\nServers", SpecificMethods.i_want_skeep(self.yml_dict, self.options.base_profile),
        #           "were skipped for reset!")
        self.update_global_profile_list()

    def get_values_of_base_profile(self):
        """ Get the base profile properties specified in the self.yml_dict['opts_key_from_base_profile'] dictionary """
        values_of_base_profile = {}
        for basename in self.yml_dict['opts_key_from_base_profile']:
            full_schema = self.schema_of_terminal + self.options.base_profile + '/' + basename
            returned_value = StaticMethods.dconf_read_command(full_schema)
            # cast to correct format
            # strings in '' quotes, the rest without
            # note: but if run via terminal (not subprocess of pytho), everything is in ""
            if returned_value:
                if returned_value[0] + returned_value[-1] in ("''", '""'):
                    returned_value = returned_value[1:-1]
                if returned_value[0] != '[' and not returned_value.isdigit() \
                        and not returned_value.lower() in ('true', 'false'):
                    returned_value = "'" + returned_value + "'"
            values_of_base_profile[basename] = returned_value
        return values_of_base_profile

    def add_new_terminal_profiles_in_dconf(self):
        """ Adding new terminal profiles to dconf """
        dconf_py_applied_commands = []

        if self.type_f == 'Mate':
            custom_schema_value_dict = \
                lambda f, s: self._return_Mate_custom_scheme(f, s)
        else:
            raise Exception('Method for type_f=%s does not exist in ConfigureDconfTerminal' % self.type_f)

        for server in self.not_added_in_dconf_yml_servers:
            full_schema_p1 = self.schema_of_terminal + server + '/'
            for basename in self.values_of_base_profile.items():
                full_schema = full_schema_p1 + basename[0]
                value_in_schema = basename[1]
                result = StaticMethods.dconf_write_command(full_schema, value_in_schema)
                if result:
                    dconf_py_applied_commands.append(result)

            for schema_dict in custom_schema_value_dict(full_schema_p1, server):
                result = StaticMethods.dconf_write_command(
                    schema_dict['full_schema'], schema_dict["value_in_schema"]
                )
                if result:
                    dconf_py_applied_commands.append(result)

            dconf_py_applied_commands.append('')
        self.update_global_profile_list()

        if not self.options.not_backup and dconf_py_applied_commands:
            StaticMethods.save_file(
                os.path.join(self.save_dir, 'dconf_applied_commands.txt'),
                dconf_py_applied_commands)

    def _return_Mate_custom_scheme(self, full_schema_p1, server):
        """
        Returns a custom schema for Mate Terminal
        :return: list of dict(full_schema: str, value_in_schema: str)
        """
        si = SpecificMethods.server_info(self.yml_dict, server)
        custom_scheme = [
            dict(  # ssh connection command
                full_schema=full_schema_p1 + 'custom-command',
                value_in_schema="'ssh -p {0} {1}@{2}'".format(si['Port'], si['User'], si['IP'])
            ),
            dict(  # terminal profile name
                full_schema=full_schema_p1 + 'visible-name',
                value_in_schema="'{0} ({1})'".format(server, si['IP'])
            ),
            dict(  # display title in terminal
                full_schema=full_schema_p1 + 'title',
                value_in_schema="'{0}'".format(server)
            ),
        ]
        return custom_scheme


class ConfigureSSH:
    """ Changing the ssh config file and sending key + auto authorization on a remote server """
    config_file: str = os.path.expanduser('~/.ssh/config')

    @property
    def added_in_config_hosts(self):
        """
        Added what I want to add (i_want_add) and what is in config file
        :rtype: list of str
        """
        return list(set(SpecificMethods.i_want_add(self.yml_dict)) & set(self.ssh_config.hosts()))

    @property
    def not_added_in_config_hosts(self):
        """
        Not added what I want to add (i_want_add) but what is not in config file
        :rtype: list of str
        """
        return list(set(SpecificMethods.i_want_add(self.yml_dict)) - set(self.ssh_config.hosts()))

    @staticmethod
    def delete_newlines_in_config_file(config_file: str = None):
        """ Replace 2 or more consecutive newlines with 2 newlines """
        config_file = ConfigureSSH.config_file if config_file is None else config_file
        data = StaticMethods.read_file(config_file)
        data = StaticMethods.delete_newlines(data)
        StaticMethods.save_file(config_file, data, False)

    def __init__(self, yml_dict: dict, options: argparse.Namespace, send_key_timeout: float = 60):
        self.yml_dict = yml_dict
        self.options = options
        self.send_key_timeout = send_key_timeout

        self.config_file = self.get_ssh_config_canonical_path()
        os.chmod(os.path.dirname(self.config_file), int('700', base=8))

        # overriding methods for convenience ----------------------
        self.delete_newlines_in_config_file = \
            lambda: ConfigureSSH.delete_newlines_in_config_file(self.config_file)
        # ---------------------------------------------------------

        self.ssh_config = read_ssh_config(self.config_file)
        self.show_config_property(start_message='*** SSH CONFIG STATE BEFORE EDITING: ***', show=True)

        if not self.options.not_backup:
            StaticMethods.backup_file(self.config_file)

        if self.options.clear_ssh_config:
            # ??? if not added and not not_added -> only remove all data
            # strange desire of the user, but so be it. I'm tired and lazy
            self.ssh_config = empty_ssh_config_file()
            self.ssh_config.write(self.config_file)
            self.ssh_config = read_ssh_config(self.config_file)
        elif self.options.reset_and_exit:
            self.delete_existing_profiles()

        if not self.options.reset_and_exit:
            self.modify_params_of_existed_profiles()
            self.create_profiles()
            if self.options.auto_authorization:
                self.send_keys_to_hosts()
        self.delete_newlines_in_config_file()
        self.show_config_property(start_message='*** SSH CONFIG STATE BEFORE EDITING: ***', show=True)

    def show_config_property(self, start_message: str = 'Ssh config:', show: bool = True):
        """ Output the main properties of a class instance is show == True """
        if show:
            formatting = lambda x: ', '.join(sorted(x)) if x else "['']"
            print()
            print(start_message)
            print("Desired added     = %s" % formatting(self.added_in_config_hosts))
            print("Desired NOT added = %s" % formatting(self.not_added_in_config_hosts))
            print("All profiles      = %s" % formatting(self.ssh_config.hosts()))

    def delete_existing_profiles(self):
        """ Delete existing profiles from ssh config that I want to add """
        for host in self.added_in_config_hosts:
            self.ssh_config.remove(host)
        self.ssh_config.save()

    def modify_params_of_existed_profiles(self):
        """ Update according to yaml dictionary existing profiles from ssh config that I want to add """
        for host in self.added_in_config_hosts:
            si = SpecificMethods.server_info(self.yml_dict, host)
            self.ssh_config.set(
                host, Hostname=si['IP'], Port=si['Port'],
                User=si['User'], IdentityFile=si['IdentityFile'],
            )
        self.ssh_config.save()

    def create_profiles(self):
        """ Create entries for missing hosts in the ssh config """
        for host in self.not_added_in_config_hosts:
            si = SpecificMethods.server_info(self.yml_dict, host)
            self.ssh_config.add(
                host, Hostname=si['IP'], Port=si['Port'],
                User=si['User'], IdentityFile=si['IdentityFile'],
            )
        self.ssh_config.save()

    def get_ssh_config_canonical_path(self):
        """ Obtaining a canonical path of ssh config """
        def create_config(file: str):
            if StaticMethods.select_yes_or_no(
                    "\nSsh config '{0}' don't exist! Do you want to create?".format(file)):
                StaticMethods.save_file(file, '', time_postfix=False, chmod='600')
                return True
            return False

        alt_ssh_config = os.path.expanduser(self.yml_dict['ssh_config_dest'])
        if self.options.ssh_config_dest is not None:
            self.options.ssh_config_dest = os.path.expanduser(self.options.ssh_config_dest)
            if os.path.isfile(self.options.ssh_config_dest):
                return self.options.ssh_config_dest
            elif create_config(self.options.ssh_config_dest):
                return self.options.ssh_config_dest

        if os.path.isfile(alt_ssh_config):
            return alt_ssh_config
        elif create_config(alt_ssh_config):
            return alt_ssh_config
        print('Aborted!')
        sys.exit(1)

    def send_keys_to_hosts(self):
        """ Send public keys to remote hosts. Note: need execute AFTER saving the updated configuration! """
        if self.options.auto_authorization_method == 'sshpass':
            re_send_key_to_host = lambda si: self._send_key_to_host_sshpass(si)
        else:  # elif self.options.auto_authorization_method == 'expect':
            self.expect = os.path.join(SCRIPT_DIR, 'expect.exp')
            re_send_key_to_host = lambda si: self._send_key_to_host_expect(si)

        error_data = []
        success_data = []
        log_file = os.path.join('/tmp', 'ssh-copy-id.log')
        print()
        for host in self.added_in_config_hosts:
            si = SpecificMethods.server_info(self.yml_dict, host)
            host_info = "Host: '{0}', User: '{1}', IP: '{2}'".format(host, si['User'], si['IP'])
            print('Sending key to %s ...' % host, end="\r")
            result = re_send_key_to_host(si)
            if result[0]:  # got error
                print('Sending key to %s [FAILED]' % host)
                error_data.append("---- %s:\nStdout:\n%s\nStderr:\n%s----\n" %
                                  (host_info, result[1], result[2]))
            else:
                print('Sending key to %s [__OK__]' % host)
                success_data.append(host_info)
        if error_data:
            print("\nFailed to send public key to {0} out of {1} servers!".format(
                len(error_data), len(self.added_in_config_hosts)))
            success_and_error_data = \
                "******************** SUCCESSFUL TRANSMISSION OF THE PUBLIC KEY: ********************\n\n" + \
                '\n\n'.join(success_data) + "\n*********************************** END SUCCESS *****************" + \
                "*******************" if success_data else "Don't worry, someday it will work ^_^"
            success_and_error_data += \
                "\n\n\n************************ FAILED TRANSMISSION OF PUBLIC KEY: ************************\n\n" + \
                '\n\n'.join(error_data) + \
                "\n************************************ END FAILED ************************************\n"
            log_file = StaticMethods.save_file(log_file, success_and_error_data)
            print("To view the log, run: cat '%s'" % log_file)
        elif success_data:
            print("\nSuccessful sending of keys to all servers!")
        self.ssh_config.save()

    def _send_key_to_host_sshpass(self, si: dict):
        """ Automatic password entry is performed by the program 'sshpass' """
        return StaticMethods.run_popen(command_list=[
            'sshpass', '-p', si['Password'],
            'ssh-copy-id', '-o', 'StrictHostKeyChecking no',
            '-i', si['AuthorizationFile'],
            si['User'] + '@' + si['IP'],
        ], timeout=self.send_key_timeout)

    def _send_key_to_host_expect(self, si: dict):
        """ Automatic password entry is performed by the program 'expect' """
        return StaticMethods.run_popen(command_list=[
            self.expect, si['Password'],
            'ssh-copy-id', '-o', 'StrictHostKeyChecking no',
            '-i', si['AuthorizationFile'], '-f',
            si['User'] + '@' + si['IP'],
        ], timeout=self.send_key_timeout)


if __name__ == "__main__":

    cli_parameters = AnalyzeCliParameters()
    TIME_POSTFIX = cli_parameters.options.time_postfix
    StaticMethods.TIME_POSTFIX = TIME_POSTFIX

    yml_data = SpecificMethods.read_yml(yml_file=cli_parameters.options.yml_config)
    if cli_parameters.options.dconf_actions:
        ConfigureDconfTerminal(yml_dict=yml_data, options=cli_parameters.options)
    if cli_parameters.options.ssh_config_actions:
        ConfigureSSH(yml_dict=yml_data, options=cli_parameters.options, send_key_timeout=10)

