#!/usr/bin/env python3

import os
import sys
import shutil
from datetime import datetime


def backup_file(file):
    if os.path.isfile(file):
        backup_postfix = datetime.now().strftime("%d_%m_%y_(%H:%M:%S)")
        save_to = file + '_' + backup_postfix + '.bak'
        shutil.copyfile(file, save_to)


if __name__ == "__main__":
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))  # '~/.local/share/ok_ssh'
    rc_file = os.path.expanduser('~/.bashrc')

    chmod = int('755', base=8)
    os.chmod(os.path.join(script_dir, 'source', 'ok_ssh.py'), chmod)
    os.chmod(os.path.join(script_dir, 'source', 'expect.exp'), chmod)

    backup_file(rc_file)
    need_add = ("if [ -d '{0}' ]; then alias ok_ssh='{0}/source/ok_ssh.py'; "
                "alias ok_ssh_uninstall='{0}/uninstall.py'; fi").format(script_dir)

    with open(rc_file, 'r+') as file:
        if need_add not in file.read():
            file.write(need_add)
