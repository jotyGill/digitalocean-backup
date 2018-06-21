# dobackup
Simple Automated offline snapshots of digitalocean droplets utilising [python-digitalocean](https://github.com/koalalorenzo/python-digitalocean).
The script safely shutdowns a given droplet or all droplets with a give tag then preforms snapshots of them, Then
it turns them back on. Every step is logged as well as displayed in the console output.
The script is designed to be used as a cron job as well.

## Installation
Install as a user without sudo. This installs it in ~/.local/bin/ make sure this path is in your $PATH.
``` bash
python3 -m pip install --user dobackup --upgrade
```
If not found, add the following to your .bashrc or .zshrc
``` bash
# Add to PATH to Install and run programs with "pip install --user"
export PATH=$PATH:~/.local/bin
```

## Usage

### Initialise
Store the api access token in .token file by running '--init' and providing the token string.
``` bash
dobackup --init
# Provide the token string
```

### Display Information
Display Information about droplets and snapshots using --list commands.
Examples
``` bash
dobackup --list-drops
dobackup --list-snaps
dobackup --list-backups  # snaps created using this tool
dobakcup --list-older_than 7    # lists backup taken by dobackup that are older than 7 days
dobackup --list-tags
dobackup --list-tagged   # list tagged servers with the tag 'dobackup'
```

### Use Tags (optional)
Use tags to backup multiple servers at ones. Use existing tags or create new.
Default tag is 'dobackup' .
To tag a server with a 'dobakup' tag.
``` bash
dobackup --tag-server ubuntu-18-04  # '--tag-name dobackup' is implicit
```
To tag a server with 'web-servers' tag.
``` bash
dobackup --tag-server ubuntu-18-04  --tag-name web-servers
```

### Perform Backups
To backup a server using it's name or id.
``` bash
dobackup --backup ubuntu-18-04
dobackup --backup 1929129
```

To backup all servers that have a given tag.
``` bash
dobackup --backup-all   # --tag-name dobackup    is implicit
dobackup --backup-all --tag-name web-servers
```

### Perform Restore
To restore a server using it's name or id and snapshot's name or id
``` bash
dobackup --restore-drop ubuntu-18-04 --restore-to "ubuntu-18-04--dobackup--2018-06-01 14:36:07"
```

### Delete Old Backups
To delete a specific snapshot.
``` bash
dobackup --delete-snap "ubuntu-1gb-sgp1-01--dobackup--2018-05-31 17:43:11"   # put snap name or id
```

To delete all old backups taken with dobackup.
``` bash
dobackup --delete-older-than 14     # older than 14 days
```

## Options

``` bash
usage: dobackup [-h] [-v] [--init] [--list-drops] [--list-backups]
                [--list-snaps] [--list-tagged] [--list-tags]
                [--list-older-than LIST_OLDER_THAN] [--tag-server TAG_SERVER]
                [--untag-server UNTAG_SERVER] [--tag-name TAG_NAME]
                [--delete-older-than DELETE_OLDER_THAN]
                [--delete-snap DELETE_SNAP] [--backup BACKUP] [--backup-all]
                [--shutdown SHUTDOWN] [--powerup POWERUP]
                [--restore-drop RESTORE_DROP] [--restore-to RESTORE_TO]


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
  --delete-snap DELETE_SNAP
                        Delete the snapshot with given name or id
  --backup BACKUP       Shutdown, Backup, Then Restart the droplet with given
                        name or id
  --backup-all          Shutdown, Backup, Then Restart all droplets with "--
                        tag-name"
  --shutdown SHUTDOWN   Shutdown, the droplet with given name or id
  --powerup POWERUP     Powerup, the droplet with given name or id
  --restore-drop RESTORE_DROP
                        Restore, the droplet with given name or id
  --restore-to RESTORE_TO
                        Snapshot id or name, to restore the droplet to
```
