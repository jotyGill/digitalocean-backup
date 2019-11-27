# dobackup
<p align="center">
<a href="https://pepy.tech/project/dobackup"><img alt="Downloads" src="https://pepy.tech/badge/dobackup"></a> </p>
Simple Automated offline snapshots of digitalocean droplets utilising [python-digitalocean](https://github.com/koalalorenzo/python-digitalocean).
The script safely shutdowns a given droplet or all droplets with a give tag then performs snapshots of them, Then
it turns them back on. Every step is logged as well as displayed in the console output.
The script is designed to be used as a cron job as well. If any error occurs the script logs it then exits with
exit code of 1. Very useful feature to ensure that the backups are successfully completed. I use it to delete older
backups only if new one is successful and to use a 'healthchecks' service to get notified if a backup failed.
(see cron examples)

**NOTE: The currently published pypi version of API wrapper [python-digitalocean] has a bug, which recently started breaking functionality.**
**Please update dobackup to the latest version (2.1.1) which is temporarily using a fork I published as [python-digitalocean-latest]**

**RUN: `python3 -m pip uninstall python-digitalocean`  then  `python3 -m pip install --user -U dobackup`**

![dobackup](https://user-images.githubusercontent.com/8462091/67843798-96c57d00-faf4-11e9-8ce1-5596bf422a44.gif)

## Installation
Install as a user without sudo. This installs it in ~/.local/bin/ make sure this path is in your $PATH.
``` bash
python3 -m pip install --user -U dobackup
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
# Paste the digitalocean token string, press enter
# If you have multiple accounts, paste each- press enter, so on
# When done, just press enter to submit an empty string
# The sequence of these tokens (0,1,2) will be later used to "use" the tokens
```
To use one of the stored tokens, specify it's index after "dobackup ",
``` bash
dobackup 0      # 0 is implicit
dobackup 1      # will use token 1
dobackup 2      # will use token 2
```

### Display Information
Display Information about droplets and snapshots using --list commands.
Examples
``` bash
dobackup --list-droplets
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
NOTE: In 2.0, --'tag-name'-- is appended to the backup name, instead of hardcoded str '--dobackup--'.
The default value of tag_name is still 'dobackup'. Now we can use --tag-name along with --list-backups, --list-older-than,
--delete-older-than. Now we can keep the backups of droplets with lets say 'tag1' for 5 days and 'tag2' for 10 days.
example command. "--delete-older-than 5 --tag-name 'tag1'" ,   "--delete-older-than 10 --tag-name 'tag2'"


### Perform Backups
To backup a server using it's name or id.
``` bash
dobackup --backup ubuntu-18-04
dobackup --backup 1929129
dobackup --live-backup ubuntu-18-04       # live backup, backup without shutting down the vm
dobackup --backup ubuntu-18-04 --keep     # this won't be deleted with '--delete-older-than'
```

To backup all servers that have a given tag.
``` bash
dobackup --backup-all   # --tag-name dobackup    is implicit
dobackup --backup-all --tag-name web-servers
```
To set a cron job, to backup all 'tagged' servers and auto delete old backups, if backups were successful
``` bash
0 1 * * * ~/.local/bin/dobackup --backup-all && ~/.local/bin/dobackup --delete-older-than 7
```

Using amazing utility [healthchecks](https://github.com/healthchecks/healthchecks). to get notified if an error occurred during the process.
``` bash
0 1 * * * ~/.local/bin/dobackup --backup-all && ~/.local/bin/dobackup --delete-older-than 7 && wget -O/dev/null https://hc-ping.com/your-string
```

### Perform Restore
To restore a server using it's name or id and snapshot's name or id
``` bash
dobackup --restore-droplet ubuntu-18-04 --restore-to "ubuntu-18-04--dobackup--2018-06-01 14:36:07"
```

### Delete Old Backups
To delete a specific snapshot.
``` bash
dobackup --delete-snap "ubuntu-1gb-sgp1-01--dobackup--2018-05-31 17:43:11"   # put snap name or id
```

To delete all old backups taken with dobackup.
``` bash
# delete snapshots older than 14 days with '--dobackup--' in their names
# WILL NOT delete snapshots with '--dobackup-keep--' in their names
dobackup --delete-older-than 14
```

## Options

``` bash
usage: dobackup [-h] [-v] [--init] [-l] [--list-backups] [-s] [--list-tagged]
                [--list-tags] [--list-older-than LIST_OLDER_THAN]
                [--backup BACKUP] [--backup-all] [--live-backup LIVE_BACKUP]
                [--live-backup-all] [--tag-droplet TAG_DROPLET]
                [--untag-droplet UNTAG_DROPLET] [--tag-name TAG_NAME]
                [--delete-older-than DELETE_OLDER_THAN]
                [--delete-snap DELETE_SNAP] [--shutdown SHUTDOWN]
                [--powerup POWERUP] [--restore-droplet RESTORE_DROP]
                [--restore-to RESTORE_TO] [--keep]
                [token_id]

Automated Offline Or Live Snapshots Of Digitalocean Droplets

positional arguments:
  token_id              Specify token number to be used, default=0, supply
                        only if you have multiple Digitalocean accounts

optional arguments:
  -h, --help            show this help message and exit
  -v, -V, --version     show programs version number and exit
  --init                Save token to .token file
  --tag-name TAG_NAME   To be used with "--list-tags", "--tag-droplet" and "--
                        backup-all", default value is "dobackup"
  --keep                To keep backups for long term. "--delete-older-than"
                        wont delete these. To be used with "--backup","--
                        backup-all"

Informational Args:
  Arguments That Display Information

  -l, --list-droplets   List all droplets
  --list-backups        List all snapshots with "dobackup" in their name
  -s, --list-snaps      List all snapshots
  --list-tagged         List droplets using "--tag-name"
  --list-tags           List all used tags
  --list-older-than LIST_OLDER_THAN
                        List snaps older than, in days

Backup Args:
  Arguments That Backup Or Restore Droplets

  --backup BACKUP       Shutdown, Backup (snapshot), Then Restart the droplet
                        with given name or id
  --backup-all          Shutdown, Backup (snapshot), Then Restart all droplets
                        with the given "--tag-name"
  --live-backup LIVE_BACKUP
                        Backup (snapshot), the droplet with given name or id,
                        without shutting it down
  --live-backup-all     Backup (snapshot), all droplets with the given "--tag-
                        name", without shutting them down
  --restore-droplet RESTORE_DROP
                        Restore, the droplet with given name or id
  --restore-to RESTORE_TO
                        Snapshot id or name, to restore the droplet to

Action Args:
  Arguments That Perform Actions

  --tag-droplet TAG_DROPLET
                        Add tag to the provided droplet name or id
  --untag-droplet UNTAG_DROPLET
                        Remove tag from the provided droplet name or id
  --delete-older-than DELETE_OLDER_THAN
                        Delete backups older than, in days
  --delete-snap DELETE_SNAP
                        Delete the snapshot with given name or id
  --shutdown SHUTDOWN   Shutdown, the droplet with given name or id
  --powerup POWERUP     Powerup, the droplet with given name or id

```
