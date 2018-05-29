# dobackup
Simple Automated offline snapshots of digitalocean droplets utilising [python-digitalocean](https://github.com/koalalorenzo/python-digitalocean)


## Installation
Install as a user without sudo. This installs it in ~/.local/bin/ make sure this path is in your $PATH.
``` bash
python3 -m pip install --user dobackup
```
If not found, add the following to your .bashrc or .zshrc
``` bash
# Add to PATH to Install and run programs with "pip install --user"
export PATH=$PATH:~/.local/bin
```

## Usage
``` bash
usage: dobackup [-h] [-v] [--init] [--list-drops] [--list-snaps]
                [--list-tagged] [--list-tags]
                [--list-older-than LIST_OLDER_THAN] [--tag-server TAG_SERVER]
                [--untag UNTAG] [--tag-name TAG_NAME]
                [--delete-older-than DELETE_OLDER_THAN] [--backup BACKUP]
                [--backup-all]


optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show programs version number and exit
  --init                Save token to .token file
  --list-drops          List all droplets
  --list-backups        List all snapshots with "dobackup" in their name
  --list-snaps          List all snapshots
  --list-tagged         List droplets using "--tag-name"
  --list-tags           List all used tags
  --list-older-than LIST_OLDER_THAN
                        List snaps older than, in days
  --tag-server TAG_SERVER
                        Add tag to the provided droplet name or id
  --untag-server UNTAG_SERVER
                        Remove tag from the provided droplet name or id
  --tag-name TAG_NAME   To be used with "--list-tags", "--tag-server" and "--
                        backup-all", default value is "dobackup"
  --delete-older-than DELETE_OLDER_THAN
                        Delete backups older than, in days
  --backup BACKUP       Shutdown, Backup, Then Restart the droplet with given
                        name or id
  --backup-all          Shutdown, Backup, Then Restart all droplets with "--
                        tag-name"
  --shutdown SHUTDOWN   Shutdown, the droplet with given name or id
  --powerup POWERUP     Powerup, the droplet with given name or id
```
