# Description
GNU/Linux administrators often have to deal with a large number of servers. For remote access, the ssh protocol and the Putty program are excellent, which allows you to configure connection settings. However, I don't like Putty's built-in terminal. I also don't like having to enter a password when sending the public key to every new server. I just want to add server parameters to my configuration file, execute a script that will configure my default terminal based on it, send keys and enter a password on its own. And that's it! Minimum action, maximum result! And I wrote such a script!

> **Warning 1**: This software is provided as is. The author is not responsible, you perform any actions at your own peril and risk. And blah blah blah. The software has only been tested in Linux Mint 21.2. Bug reports are welcome.
>
> **Warning 2**: I am using mate terminal. In my opinion, this is the perfect terminal. Therefore, the default script is configured to create profiles in it. Who knows the Python language, theoretically should not experience difficulties in adapting the script for other terminals (pull requests are welcome. I will test and add if the code is working). If you don't know Python and/or are strongly against mate terminal, please leave.

```bash
usage: ok_ssh [-h] [-d] [-s] [-r] [-a] [-y FILE] [-b STR] [-c] [-n] [-t] [--ssh_config_dest STR] [--auto_authorization_method STR]

Script for integrating ssh connections in GNU/Linux OS

options:
  -h, --help            show this help message and exit

Main options:
  -d, --dconf_actions   Run dconf actions to add connection profiles in
                        terminal (default=False)
  -s, --ssh_config_actions
                        Perform actions in the config file
                        (default=False)
  -r, --reset_and_exit  Delete profiles and log out. Has effect only when
                        appropriate options are specified: -d/-s 
                        (default=False)
  -a, --auto_authorization
                        Send keys to servers and log in automatically 
                        (default=True, with -a=False)

Extra options:
  -y FILE, --yml_config FILE
                        Specify main yml config
  -b STR, --base_profile STR
                        Specify a basic terminal profile (takes 
                        precedence over a profile from a file)
  -c, --clear_ssh_config
                        Before adding profiles, first clear ssh config
                        (default=False)
  -n, --not_backup      Don't make backups (default=False)
  -t, --time_postfix    Add postfix for backup files (default=False)
  --ssh_config_dest STR
                        Specify ssh config location 
                        (default - reading from yaml)
  --auto_authorization_method STR
                        Specify the preferred program that will enter the 
                        password when copying the key (sshpass or expect)

Adminka-root 2023. https://github.com/adminka-root
```

## Before running script...

Before running script you should:

1) set up a basic profile in the Mate terminal, on the basis of which new connection profiles will be built;
2) change the configuration of the yml file by defining your list of servers (inventory).

With the first point, I think there will be no problems. Just adjust the font, background color, palette, in general, whatever you think is right. Then run `dconf read /org/mate/terminal/global/profile-list`, this will show the names of existing profiles. Find the one you just created and set the **'base_profile'** key to the appropriate value (by option or in the *~/.local/share/ok_ssh/source/servers.yml* file).

The second point is intuitive. Your task is to populate the **'dict_of_servers'** dictionary with your list of servers in the `~/.local/share/ok_ssh/source/servers.yml` file ([file in the repository](https://github.com/adminka-root/ok_ssh/blob/master/source/servers.yml)). I will only note that the **'i_want_add'** subkey works as if the corresponding server is not in the configuration file. This means that it also affects the reset policy (option `-r`).

## Launch examples

Running with the `-d -s` options will configure the terminal profiles and the config file for ssh. The `-t` option adds a postfix for backup files, which is the recommended behavior for beginners:
```bash
03:36:56 ▶ ok_ssh.py -d -s -t

*** DCONF STATE BEFORE EDITING: ***
Desired added     = ['']
Desired NOT added = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
All profiles      = default, profile0
I don't want to add/edit = ansible, profile0

To restore the original state see - cat '/home/adminka/.local/share/ok_ssh/dconf_restore_08_09_23_(03:37:33).txt'

*** DCONF STATE AFTER EDITING: ***
Desired added     = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
Desired NOT added = ['']
All profiles      = celery, default, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, profile0, template_system, togudb
I don't want to add/edit = ansible, profile0

Ssh config '/home/adminka/.ssh/config' don't exist! Do you want to create?
Answer[Y/n]: 

*** SSH CONFIG STATE BEFORE EDITING: ***
Desired added     = ['']
Desired NOT added = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
All profiles      = ['']

Sending key to pnu3 [__OK__]
Sending key to pnuDB [__OK__]
Sending key to portainer [__OK__]
Sending key to template_system [FAILED]
Sending key to nexus [__OK__]
Sending key to pnu_node2 [__OK__]
Sending key to portal_node3 [__OK__]
Sending key to portal [__OK__]
Sending key to pnu_new [__OK__]
Sending key to portal_node2 [__OK__]
Sending key to togudb [__OK__]
Sending key to celery [__OK__]
Sending key to docker_portal [__OK__]
Sending key to pnu_node3 [__OK__]

Failed to send public key to 1 out of 14 servers!
To view the log, run: cat '/tmp/ssh-copy-id_08_09_23_(03:38:08).log'

*** SSH CONFIG STATE BEFORE EDITING: ***
Desired added     = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
Desired NOT added = ['']
All profiles      = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
```

The same run with the `-r` option implies that the user wants to remove the profiles/servers specified in the yaml settings file:
```bash
03:38:08 ▶ ok_ssh -d -s -r
Reset and exit mode selected. Do you want to continue?
Answer[Y/n]: 

*** DCONF STATE BEFORE EDITING: ***
Desired added     = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
Desired NOT added = ['']
All profiles      = celery, default, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, profile0, template_system, togudb
I don't want to add/edit = ansible, profile0

To restore the original state see - cat '/home/adminka/General/Programming/Ssh/dconf_restore.txt'

*** DCONF STATE AFTER EDITING: ***
Desired added     = ['']
Desired NOT added = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
All profiles      = default, profile0
I don't want to add/edit = ansible, profile0

*** SSH CONFIG STATE BEFORE EDITING: ***
Desired added     = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
Desired NOT added = ['']
All profiles      = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb

*** SSH CONFIG STATE BEFORE EDITING: ***
Desired added     = ['']
Desired NOT added = celery, docker_portal, nexus, pnu3, pnuDB, pnu_new, pnu_node2, pnu_node3, portainer, portal, portal_node2, portal_node3, template_system, togudb
All profiles      = ['']
```


# Dependencies

1) ``openssh-client`` (usually included with GNU/Linux distributions);
2) ``sshpass`` or ``expect`` for authorization in automatic mode (i.e. without manually entering a password) when sending a public key;
3) ``mate-terminal``
4) ``dconf-cli`` to modify terminal profiles;
5) ``python``>= 3.6;
6) ``pip install -r requirements.txt``

# Installation
```bash
cd ~/.local/share/
git clone https://github.com/adminka-root/ok_ssh.git
cd ok_ssh
pip install -r requirements.txt
python3 install.py
source ~/.bashrc
```

# Uninstalling
```bash
ok_ssh_uninstall
```