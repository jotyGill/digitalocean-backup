#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import logging.handlers
import sys
import time

import digitalocean
from dobackup import __basefilepath__, __version__

logging.basicConfig(
    format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.handlers.TimedRotatingFileHandler(__basefilepath__ + 'dobackup.log',
                                                  when='W0', interval=2),
        logging.StreamHandler(sys.stdout)
    ],
    level="INFO")
log = logging.getLogger()


def main():
    parser = argparse.ArgumentParser(
        description='Automated offline snapshots of digitalocean droplets')
    parser.add_argument('-v', '--version', action='version', version="dobackup " + __version__)
    parser.add_argument('--init', dest='init',
                        help='Save token to .token file', action='store_true')
    parser.add_argument('--list-drops', dest='list_drops',
                        help='List all droplets', action='store_true')
    parser.add_argument('--list-backups', dest='list_backups',
                        help='List all snapshots with "dobackup" in their name',
                        action='store_true')
    parser.add_argument('--list-snaps', dest='list_snaps',
                        help='List all snapshots', action='store_true')
    parser.add_argument('--list-tagged', dest='list_tagged',
                        help='List droplets using "--tag-name"',
                        action='store_true')
    parser.add_argument('--list-tags', dest='list_tags',
                        help='List all used tags', action='store_true')
    parser.add_argument('--list-older-than', dest='list_older_than', type=int,
                        help='List snaps older than, in days')
    parser.add_argument('--tag-server', dest='tag_server', type=str,
                        help='Add tag to the provided droplet name or id')
    parser.add_argument('--untag-server', dest='untag_server', type=str,
                        help='Remove tag from the provided droplet name or id')
    parser.add_argument('--tag-name', dest='tag_name', type=str,
                        help='To be used with "--list-tags", "--tag-server" and "--backup-all",\
                         default value is "dobackup"', default='dobackup')
    parser.add_argument('--delete-older-than', dest='delete_older_than',
                        type=int, help='Delete backups older than, in days')
    parser.add_argument('--backup', dest='backup', type=str,
                        help='Shutdown, Backup, Then Restart the droplet with given name or id')
    parser.add_argument('--backup-all', dest='backup_all',
                        help='Shutdown, Backup, Then Restart all droplets with "--tag-name"',
                        action='store_true')
    parser.add_argument('--shutdown', dest='shutdown', type=str,
                        help='Shutdown, the droplet with given name or id')
    parser.add_argument('--powerup', dest='powerup', type=str,
                        help='Powerup, the droplet with given name or id')

    args = parser.parse_args()

    run(args.init, args.list_drops, args.list_backups, args.list_snaps, args.list_tagged,
        args.list_tags, args.list_older_than, args.tag_server, args.untag_server,
        args.tag_name, args.delete_older_than, args.backup, args.backup_all,
        args.shutdown, args.powerup)


def set_token():
    token_str = input("Paste The Digital Ocean's Token to Be Stored In .token File : ")
    if len(token_str) != 64:
        log.error("Is It Really A Token Though? The Length Should Be 64")
        sys.exit()
    tocken_dic = {"token0": token_str}

    try:
        with open(__basefilepath__ + '.token', 'w') as token_file:
            json.dump(tocken_dic, token_file)
        log.info("The Token Has Been Stored In .token File")
    except FileNotFoundError:
        log.error("FileNotFoundError: SOMETHING WRONG WITH THE PATH TO '.token'")
        sys.exit()


def turn_it_off(droplet):
    log.info("Shutting Down : " + str(droplet))
    shut_action = droplet.get_action(droplet.shutdown()["action"]["id"])
    log.debug("shut_action " + str(shut_action) + str(type(shut_action)))
    shut_outcome = shut_action.wait(update_every_seconds=3)
    log.debug("shut_outcome " + str(shut_outcome))
    if shut_outcome:
        for i in range(50):
            time.sleep(3)
            droplet.load()  # refresh droplet data
            log.debug("droplet.status " + droplet.status + " i " + str(i))
            if droplet.status == "off":
                log.info("Shutdown Completed " + str(droplet))
                return
        log.error("SHUTDOWN FAILED, REPORTED 'shut_outcome'=='True' " +
                  str(droplet) + str(shut_action))
    else:
        log.error("SHUTDOWN FAILED " + str(droplet) + str(shut_action))


def start_backup(droplet):
    snap_name = droplet.name + "--dobackup--" + \
        str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # snap_name = droplet.name + "--dobackup--2018-05-02 12:37:52"
    if droplet.status == "active":
        turn_it_off(droplet)
    elif droplet.status == "off":
        log.info("The Droplet Is Already Off : " + str(droplet) + " Taking Snapshot")
    else:
        log.error("'droplet.status' SHOULD BE EITHER 'off' OR 'active'")
    # power_off is hard power off dont want that
    log.info("Taking snapshot of " + droplet.name)
    snap = (droplet.take_snapshot(snap_name, power_off=False))
    snap_action = droplet.get_action(snap["action"]["id"])
    return snap_action


def snap_completed(snap_action):
    snap_outcome = snap_action.wait(update_every_seconds=3)
    if snap_outcome:
        log.info(str(snap_action) + " Snapshot Completed")
        return True
    else:
        log.error("SNAPSHOT FAILED " + str(snap_action))
        return False


def turn_it_on(droplet):
    power_up_action = droplet.get_action(droplet.power_on()["action"]["id"])
    log.debug("power_up_action " + str(power_up_action) + str(type(power_up_action)))
    power_up_outcome = power_up_action.wait(update_every_seconds=3)
    log.debug("power_up_outcome " + str(power_up_outcome))
    if power_up_outcome:
        for i in range(5):
            time.sleep(2)
            droplet.load()  # refresh droplet data
            log.debug("droplet.status " + droplet.status)
            if droplet.status == "active":
                log.info("Powered Back Up " + str(droplet))
                return
        log.critical("DID NOT POWER UP BUT REPORTED 'powered_up'=='True' " + str(droplet))
    else:
        log.critical("DID NOT POWER UP " + str(droplet))


def find_old_backups(manager, older_than):
    old_snapshots = []
    last_backup_to_keep = datetime.datetime.now() - datetime.timedelta(days=older_than)

    for each_snapshot in manager.get_droplet_snapshots():
        # print(each_snapshot.name, each_snapshot.created_at, each_snapshot.id)
        if "--dobackup--" in each_snapshot.name:
            backed_on = each_snapshot.name[each_snapshot.name.find("--dobackup--") + 15:]
            # print("backed_on", backed_on)
            backed_on_date = datetime.datetime.strptime(backed_on, "%Y-%m-%d %H:%M:%S")
            if backed_on_date < last_backup_to_keep:
                old_snapshots.append(each_snapshot)
                print(each_snapshot)

    # print("OLD SNAPSHOTS", old_snapshots)
    return old_snapshots


def purge_backups(old_snapshots):
    if old_snapshots:   # list not empty
        for each_snapshot in old_snapshots:
            log.warning("Deleting Old Snapshot: " + str(each_snapshot))
            destroyed = each_snapshot.destroy()
            if destroyed:
                log.info("Successfully Destroyed The Snapshot")
            else:
                log.error("COULD NOT DESTROY SNAPSHOT " + str(each_snapshot))
    else:
        log.info("No Snapshot Is Old Enough To be Deleted")


def tag_droplet(do_token, droplet_id, tag_name):
    backup_tag = digitalocean.Tag(token=do_token, name=tag_name)
    backup_tag.create()  # create tag if not already created
    backup_tag.add_droplets([droplet_id])


def untag_droplet(do_token, droplet_id, tag_name):      # Currely broken
    backup_tag = digitalocean.Tag(token=do_token, name=tag_name)
    backup_tag.remove_droplets([droplet_id])


def list_droplets(manager):
    my_droplets = manager.get_all_droplets()
    log.info("Listing All Droplets:  ")
    log.info("<droplet-id>   <droplet-name>   <droplet-status>      <ip-addr>       <memory>\n")
    for droplet in my_droplets:
        log.info(str(droplet).ljust(40) + droplet.status.ljust(12) +
                 droplet.ip_address.ljust(22) + str(droplet.memory))


def get_tagged(manager, tag_name):
    tagged_droplets = manager.get_all_droplets(tag_name=tag_name)
    return tagged_droplets


def list_snapshots(manager):
    log.info("All Available Snapshots Are : <snapshot-name>   <snapshot-id>\n")
    snapshots = []
    for snap in manager.get_all_snapshots():
        snapshots.append([snap.name, snap.id])

    snapshots.sort()
    for snap in snapshots:
        log.info(snap[0].ljust(70) + snap[1])


def set_manager(do_token):
    manager = digitalocean.Manager(token=do_token)
    return manager


def get_token():
    try:
        with open(__basefilepath__ + '.token') as do_token_file:
            do_token = json.load(do_token_file)
            # print("token", do_token["token0"])
        return do_token["token0"]
    except FileNotFoundError:
        log.error("FileNotFoundError: PLEASE STORE THE DO ACCESS TOKEN USING '--init'")
        sys.exit()


def list_all_tags(manager):
    all_tags = manager.get_all_tags()
    log.info("All Available Tags Are : ")
    for tag in all_tags:
        log.info(tag.name)


def find_droplet(droplet_str, manager):
    all_droplets = manager.get_all_droplets()
    for drop in all_droplets:
        log.debug(str(type(drop)) + str(drop))
        if drop.name == droplet_str:
            log.debug("Found droplet with name == " + droplet_str)
            return drop
        if str(drop.id) == droplet_str:
            log.debug("Found droplet with id == " + droplet_str)
            return drop
    log.error("NO DROPLET FOUND WITH THE GIVEN NAME OR ID")
    sys.exit()


def list_taken_backups(manager):
    log.info("The Backups Taken With dobackup Are : <snapshot-name>     <snapshot-id>\n")
    backups = []
    for snap in manager.get_all_snapshots():
        if "--auto-backup--" in snap.name:
            backups.append([snap.name, snap.id])

    backups.sort()
    for snap in backups:
        log.info(snap[0].ljust(70) + snap[1])


def run(init, list_drops, list_backups, list_snaps, list_tagged, list_tags,
        list_older_than, tag_server, untag_server, tag_name, delete_older_than,
        backup, backup_all, shutdown, powerup):
    try:
        log.info("-------------------------START-------------------------\n\n")
        if init:
            set_token()

        do_token = get_token()
        manager = set_manager(do_token)

        if list_drops:
            list_droplets(manager)
        if list_backups:
            list_taken_backups(manager)
        if list_snaps:
            list_snapshots(manager)
        if list_tagged:
            tagged_droplets = get_tagged(manager, tag_name=tag_name)
            log.info("Listing All The Tagged Droplets, with the tag of : " + tag_name)
            log.info(tagged_droplets)
        if list_tags:
            list_all_tags(manager)
        if tag_server:
            droplet = find_droplet(tag_server, manager)
            tag_droplet(do_token, str(droplet.id), tag_name)
            tagged_droplets = get_tagged(manager, tag_name=tag_name)
            log.info("Now, Droplets Tagged With : " + tag_name + " Are :")
            log.info(tagged_droplets)
        if untag_server:   # broken
            droplet = find_droplet(untag_server, manager)
            untag_droplet(do_token, str(droplet.id), tag_name)
            tagged_droplets = get_tagged(manager, tag_name=tag_name)
            log.info("Now, droplets tagged with : " + tag_name + " are :")
            log.info(tagged_droplets)
        if delete_older_than or delete_older_than == 0:     # even accept value 0
            log.info("Snapshots Older Than " + str(delete_older_than) +
                     " Days, With '--dobackup--' In Their Name Are :")
            old_backups = find_old_backups(manager, delete_older_than)
            purge_backups(old_backups)
        if list_older_than or list_older_than == 0:
            log.info("Snapshots Older Than " + str(list_older_than) +
                     " Days, With '--dobackup--' In Their Name Are :")
            find_old_backups(manager, list_older_than)
        if backup:
            droplet = find_droplet(backup, manager)
            original_status = droplet.status    # active or off
            snap_action = start_backup(droplet)
            snap_done = snap_completed(snap_action)
            if original_status != "off":
                turn_it_on(droplet)
            if not snap_done:
                log.error("SNAPSHOT FAILED " + str(snap_action) + str(droplet))
        if backup_all:
            # stores all {"snap_action": snap_action, "droplet_id": droplet}
            snap_and_drop_ids = []
            tagged_droplets = get_tagged(manager, tag_name=tag_name)

            if tagged_droplets:  # doplets found with the --tag-name
                for drop in tagged_droplets:
                    droplet = manager.get_droplet(drop.id)
                    snap_action = start_backup(droplet)
                    snap_and_drop_ids.append({"snap_action": snap_action, "droplet_id": droplet.id})
                log.info("Backups Started, snap_and_drop_ids:" + str(snap_and_drop_ids))
                for snap_id_pair in snap_and_drop_ids:
                    snap_done = snap_completed(snap_id_pair["snap_action"])
                    # print("snap_action and droplet_id", snap_id_pair)
                    turn_it_on(manager.get_droplet(snap_id_pair["droplet_id"]))
                    if not snap_done:
                        log.error("SNAPSHOT FAILED " + str(snap_action) + str(droplet))
            else:  # no doplets with the --tag-name
                log.warning("NO DROPLET FOUND WITH THE TAG NAME " + tag_name)
        if shutdown:
            droplet = find_droplet(shutdown, manager)
            turn_it_off(droplet)
        if powerup:
            droplet = find_droplet(powerup, manager)
            turn_it_on(droplet)
        log.info("---------------------------END----------------------------")
        log.info("\n\n")
    except Exception as e:
        log.critical(e, exc_info=1)     # if errored at any time, mark CRITICAL and log traceback


if __name__ == '__main__':
    main()
