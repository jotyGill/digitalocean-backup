#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import logging.handlers
import sys
import time
from typing import Dict, List

import digitalocean

from .__init__ import __basefilepath__, __version__

logging.basicConfig(
    format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.handlers.TimedRotatingFileHandler(__basefilepath__ + 'dobackup.log',
                                                  when='W0', interval=2),
        logging.StreamHandler(sys.stdout)
    ],
    level="INFO")
log = logging.getLogger()


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Automated offline snapshots of digitalocean droplets')
    parser.add_argument(
        'token_id', nargs='?', help='Specify token number to be used, default=0, supply only if \
    you have multiple DO accounts', default=0)
    parser.add_argument('-v', '-V', '--version', action='version',
                        version="dobackup " + __version__)
    parser.add_argument('--init', dest='init',
                        help='Save token to .token file', action='store_true')
    parser.add_argument('-l', '--list-droplets', dest='list_droplets',
                        help='List all droplets', action='store_true')
    parser.add_argument('--list-backups', dest='list_backups',
                        help='List all snapshots with "dobackup" in their name',
                        action='store_true')
    parser.add_argument('-s', '--list-snaps', dest='list_snaps',
                        help='List all snapshots', action='store_true')
    parser.add_argument('--list-tagged', dest='list_tagged',
                        help='List droplets using "--tag-name"',
                        action='store_true')
    parser.add_argument('--list-tags', dest='list_tags',
                        help='List all used tags', action='store_true')
    parser.add_argument('--list-older-than', dest='list_older_than', type=int,
                        help='List snaps older than, in days')
    parser.add_argument('--tag-droplet', dest='tag_droplet', type=str,
                        help='Add tag to the provided droplet name or id')
    parser.add_argument('--untag-droplet', dest='untag_droplet', type=str,
                        help='Remove tag from the provided droplet name or id')
    parser.add_argument('--tag-name', dest='tag_name', type=str,
                        help='To be used with "--list-tags", "--tag-droplet" and "--backup-all",\
    default value is "dobackup"', default='dobackup')
    parser.add_argument('--delete-older-than', dest='delete_older_than', type=int,
                        help='Delete backups older than, in days')
    parser.add_argument('--delete-snap', dest='delete_snap', type=str,
                        help='Delete the snapshot with given name or id')
    parser.add_argument('--backup', dest='backup', type=str,
                        help='Shutdown, Backup, Then Restart the droplet with given name or id')
    parser.add_argument('--backup-all', dest='backup_all',
                        help='Shutdown, Backup, Then Restart all droplets with "--tag-name"',
                        action='store_true')
    parser.add_argument('--shutdown', dest='shutdown', type=str,
                        help='Shutdown, the droplet with given name or id')
    parser.add_argument('--powerup', dest='powerup', type=str,
                        help='Powerup, the droplet with given name or id')
    parser.add_argument('--restore-droplet', dest='restore_drop', type=str,
                        help='Restore, the droplet with given name or id')
    parser.add_argument('--restore-to', dest='restore_to', type=str,
                        help='Snapshot id or name, to restore the droplet to')
    parser.add_argument('--keep', dest='keep',
                        help='To keep backups for long term. "--delete-older-than" won\'t delete these.\
    To be used with "--backup","--backup-all"', action='store_true')

    return parser.parse_args(argv[1:])


def set_tokens() -> bool:
    tokens = []
    token_dic = {}
    print("Press enter after pasting each token.")
    print("When you have pasted all tokens you have, press another enter (leave field empty)")
    for i in range(5):
        token_str = input("Paste The Digital Ocean's Token to Be Stored In .token File : ")
        if token_str == "":
            break
        elif len(token_str) != 64:
            log.error("Is It Really A Token Though? The Length Should Be 64")
        tokens.append(token_str)
    if not tokens:
        log.error("TOKEN LIST IS EMPTY, EXISTING")
        return False    # to be passed as the exit code

    for i, token in enumerate(tokens):
        token_dic["token" + str(i)] = token
    try:
        with open(__basefilepath__ + '.token', 'w') as token_file:
            json.dump(token_dic, token_file)
        log.info("Token/s Has Been Stored In .token File")
        return True
    except FileNotFoundError:
        log.error("FileNotFoundError: SOMETHING WRONG WITH THE PATH TO '.token'")
        return False    # to be passed as the exit code 1
    return False    # any other exception, or something wrong


def install_zsh_completion() -> None:
    import os.path
    import shutil
    if os.path.exists(os.path.join(os.path.expanduser("~"), ".oh-my-zsh/custom/plugins/zsh-completions/src/")):
        log.info("Zsh-completions path exists, installing completions file '_dobackup'")
        shutil.copy(__basefilepath__ + "_dobackup",
                    os.path.join(os.path.expanduser("~"), ".oh-my-zsh/custom/plugins/zsh-completions/src/"))
    else:
        log.info("Zsh-completions with oh-my-zsh is not installed, can't use auto completions, but that's ok")


def wait_for_action(an_action: digitalocean.Action, check_freq: int) -> bool:
    for i in range(50):
        try:
            snap_outcome = an_action.wait(update_every_seconds=check_freq)
        except json.decoder.JSONDecodeError:
            log.warning("json.decoder.JSONDecodeError HAPPENED BUT IT'S FINE, TRYING AGAIN")
            time.sleep(5)
            continue
        except digitalocean.baseapi.JSONReadError:
            log.warning("json.decoder.JSONReadError HAPPENED BUT IT'S FINE, TRYING AGAIN")
            time.sleep(5)
            continue
        except digitalocean.baseapi.DataReadError:
            log.warning("json.decoder.DataReadError HAPPENED BUT IT'S FINE, TRYING AGAIN")
            time.sleep(5)
            continue
        except digitalocean.baseapi.Error:
            log.warning("CATCHING digitalocean.baseapi.Error, TRYING AGAIN")
            time.sleep(5)
            continue
        except ValueError:
            log.warning("CATCHING ValueError, TRYING AGAIN")
            time.sleep(5)
            continue
        else:
            break
    if snap_outcome:
        return True
    return False


def turn_it_off(droplet: digitalocean.Droplet) -> bool:
    log.info("Shutting Down : {!s}".format(droplet))
    shut_action = droplet.get_action(droplet.shutdown()["action"]["id"])
    log.debug("shut_action {!s} {!s}".format(shut_action, type(shut_action)))
    shut_outcome = wait_for_action(shut_action, 3)
    log.debug("shut_outcome {}".format(shut_outcome))
    if shut_outcome:
        for i in range(50):
            time.sleep(3)
            droplet.load()  # refresh droplet data
            log.debug("droplet.status {} i== {!s}".format(droplet.status, i))
            if droplet.status == "off":
                log.info("Shutdown Completed " + str(droplet))
                return True
        log.error("SHUTDOWN FAILED, REPORTED 'shut_outcome'=='True' " +
                  str(droplet) + str(shut_action))
        return False
    else:
        log.error("SHUTDOWN FAILED " + str(droplet) + str(shut_action))
        return False


def start_backup(droplet: digitalocean.Droplet, keep: bool) -> digitalocean.Action:
    backup_str = "--dobackup--"
    if keep:
        backup_str = "--dobackup-keep--"
    snap_name = droplet.name + backup_str + \
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


def snap_completed(snap_action: digitalocean.Action) -> bool:
    snap_outcome = wait_for_action(snap_action, 10)
    if snap_outcome:
        log.info(str(snap_action) + " Snapshot Completed")
        return True

    log.error("SNAPSHOT FAILED " + str(snap_action))
    return False


def turn_it_on(droplet: digitalocean.Droplet) -> bool:
    power_up_action = droplet.get_action(droplet.power_on()["action"]["id"])
    log.debug("power_up_action " + str(power_up_action) + str(type(power_up_action)))
    power_up_outcome = wait_for_action(power_up_action, 3)
    log.debug("power_up_outcome " + str(power_up_outcome))
    if power_up_outcome:
        for i in range(5):
            time.sleep(2)
            droplet.load()  # refresh droplet data
            log.debug("droplet.status " + droplet.status)
            if droplet.status == "active":
                log.info("Powered Back Up " + str(droplet))
                return True
        log.critical("DID NOT POWER UP BUT REPORTED 'powered_up'=='True' " + str(droplet))
        return False
    else:
        log.critical("DID NOT POWER UP " + str(droplet))
        return False


def find_old_backups(manager: digitalocean.Manager, older_than: int) -> List[digitalocean.Snapshot]:
    old_snapshots = []
    last_backup_to_keep = datetime.datetime.now() - datetime.timedelta(days=older_than)

    for each_snapshot in manager.get_droplet_snapshots():
        # print(each_snapshot.name, each_snapshot.created_at, each_snapshot.id)
        if "--dobackup--" in each_snapshot.name:
            backed_on = each_snapshot.name[each_snapshot.name.find("--dobackup--") + 12:]
            # print("backed_on", backed_on)
            backed_on_date = datetime.datetime.strptime(backed_on, "%Y-%m-%d %H:%M:%S")
            if backed_on_date < last_backup_to_keep:
                old_snapshots.append(each_snapshot)

    # print("OLD SNAPSHOTS", old_snapshots)
    return old_snapshots


def delete_snapshot(each_snapshot: digitalocean.Snapshot) -> None:
    log.warning("Deleting Snapshot : " + str(each_snapshot))
    destroyed = each_snapshot.destroy()
    if destroyed:
        log.info("Successfully Destroyed The Snapshot")
    else:
        log.error("COULD NOT DESTROY SNAPSHOT " + str(each_snapshot))


def do_tag_droplet(do_token: str, droplet_id: str, tag_name: str) -> None:
    backup_tag = digitalocean.Tag(token=do_token, name=tag_name)
    backup_tag.create()  # create tag if not already created
    backup_tag.add_droplets([droplet_id])


def do_untag_droplet(do_token: str, droplet_id: str, tag_name: str) -> bool:
    backup_tag = digitalocean.Tag(token=do_token, name=tag_name)
    try:
        backup_tag.remove_droplets([droplet_id])
        return True
    except digitalocean.baseapi.NotFoundError:
        log.error("THE GIVEN TAG DOES NOT EXIST")
        return False


def list_all_droplets(manager: digitalocean.Manager) -> None:
    my_droplets = manager.get_all_droplets()
    log.info("Listing All Droplets:  ")
    log.info("<droplet-id>   <droplet-name>   <droplet-status>      <ip-addr>       <memory>\n")
    for droplet in my_droplets:
        log.info(str(droplet).ljust(40) + droplet.status.ljust(12) +
                 droplet.ip_address.ljust(22) + str(droplet.memory))


def get_tagged(manager: digitalocean.Manager, tag_name: str) -> None:
    tagged_droplets = manager.get_all_droplets(tag_name=tag_name)
    return tagged_droplets


def list_snapshots(manager: digitalocean.Manager) -> None:
    log.info("All Available Snapshots Are : <snapshot-name>          <snapshot-id>\n")
    snapshots = [[snap.name, snap.id] for snap in manager.get_all_snapshots()]
    snapshots.sort()
    [log.info(snap[0].ljust(70) + snap[1]) for snap in snapshots]


def set_manager(do_token: str) -> digitalocean.Manager:
    manager = digitalocean.Manager(token=do_token)
    return manager


def get_token(token_id: int) -> str:
    token_key = "token" + str(token_id)
    try:
        with open(__basefilepath__ + '.token') as do_token_file:
            do_token = json.load(do_token_file)
            # print("token", do_token["token0"])
        return do_token[token_key]
    except FileNotFoundError:
        log.error("FileNotFoundError: PLEASE STORE THE DO ACCESS TOKEN USING '--init'")
        return ""
    except KeyError:
        log.error("KeyError: TOKEN KEY '{}' NOT FOUND IN .token FILE".format(token_key))
        return ""


def list_all_tags(manager: digitalocean.Manager) -> None:
    all_tags = manager.get_all_tags()
    log.info("All Available Tags Are : ")
    for tag in all_tags:
        log.info(tag.name)


def find_droplet(droplet_str: str, manager: digitalocean.Manager) -> digitalocean.Droplet:
    all_droplets = manager.get_all_droplets()
    for drop in all_droplets:
        log.debug(str(type(drop)) + str(drop))
        if drop.name == droplet_str:
            log.debug("Found droplet with name == {}".format(droplet_str))
            return drop
        if str(drop.id) == droplet_str:
            log.debug("Found droplet with id == {}".format(droplet_str))
            return drop
    log.error("NO DROPLET FOUND WITH THE GIVEN NAME OR ID")


# Note: Snapshot.resource_id and Snapshot.id are str not int
def find_snapshot(snap_id_or_name: str, manager: digitalocean.Manager,
                  do_token: str, droplet_id=000000) -> digitalocean.Snapshot:
    snap_id_or_name = str(snap_id_or_name)  # for comparisions
    for snap in manager.get_all_snapshots():
        # print(type(snap.resource_id), type(droplet_id))
        if droplet_id == 000000:        # meaning, doesn't matter
            if snap_id_or_name == str(snap.id) or snap_id_or_name == snap.name:
                snap_obj = digitalocean.Snapshot.get_object(do_token, snap.id)
                log.info("snap id and name {!s} {!s}".format(snap.id, snap.name))
                return snap_obj
        # to filter snapshots for a specific droplet
        elif droplet_id == int(snap.resource_id):
            log.info("snap id and name {!s} {!s}".format(snap.id, snap.name))
            if snap_id_or_name == str(snap.id) or snap_id_or_name == snap.name:
                snap_obj = digitalocean.Snapshot.get_object(do_token, snap.id)
                return snap_obj
    if droplet_id == 000000:
        log.error("NO SNAPSHOT FOUND WITH NAME OR ID OF {!s}, EXITING".format(snap_id_or_name))
    else:
        log.error("NO SNAPSHOT FOUND WITH NAME OR ID OF {!s} FOR DROPLET ID {!s}, EXITING".format(
            snap_id_or_name, droplet_id))


def list_taken_backups(manager: digitalocean.Manager) -> None:
    log.info("The Backups Taken With dobackup Are : <snapshot-name>     <snapshot-id>\n")
    backups = []
    for snap in manager.get_all_snapshots():
        if "--dobackup--" in snap.name or "--dobackup-keep--" in snap.name:
            backups.append([snap.name, snap.id])

    backups.sort()
    [log.info(snap[0].ljust(70) + snap[1]) for snap in backups]


def restore_droplet(droplet: digitalocean.Droplet, snapshot: digitalocean.Snapshot,
                    manager: digitalocean.Manager, do_token: str):
    snap = find_snapshot(snapshot, manager, do_token, droplet_id=droplet.id)

    if snap:
        log.info(str(snap) + " Is A Valid Snapshot For " + droplet.name + "\n")
        confirmation = input("Are You Sure You Want To Restore ? (if so, type 'yes') ")
        if confirmation.lower() == "yes":
            log.info("Starting Restore Process")
            restore_act = droplet.get_action(droplet.restore(
                int(snap.id))["action"]["id"])  # return action
            restore_outcome = wait_for_action(restore_act, 10)
            if restore_outcome:
                log.info(str(restore_act) + " Restore Completed")
            else:
                log.error("RESTORE FAILED " + str(restore_act))

    if not snap:
        log.error(str(snapshot) + " IS NOT A VALID SNAPSHOT FOR " + droplet.name)


def run(token_id: int, init: bool, list_droplets: bool, list_backups: bool, list_snaps: bool,
        list_tagged: bool, list_tags: bool, list_older_than: int, tag_droplet: str, untag_droplet: str,
        tag_name: str, delete_older_than: int, delete_snap: str, backup: str, backup_all: bool,
        shutdown: str, powerup: str, restore_drop: str, restore_to: str, keep: bool) -> int:
    try:
        log.info("-------------------------START-------------------------\n\n")
        if init:
            if set_tokens() is False:
                return 1
            install_zsh_completion()

        do_token = get_token(token_id)
        if do_token == "":
            return 1
        manager = set_manager(do_token)

        if list_droplets:
            list_all_droplets(manager)
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
        if tag_droplet:
            droplet = find_droplet(tag_droplet, manager)
            if droplet is None:
                return 1
            do_tag_droplet(do_token, str(droplet.id), tag_name)
            tagged_droplets = get_tagged(manager, tag_name=tag_name)
            log.info("Now, Droplets Tagged With : {} Are :".format(tag_name))
            log.info(tagged_droplets)
        if untag_droplet:
            droplet = find_droplet(untag_droplet, manager)
            if droplet is None:
                return 1
            if do_untag_droplet(do_token, str(droplet.id), tag_name) is False:
                return 1
            tagged_droplets = get_tagged(manager, tag_name=tag_name)
            log.info("Now, droplets tagged with : " + tag_name + " are :")
            log.info(tagged_droplets)
        if delete_older_than or delete_older_than == 0:     # even accept value 0
            old_backups = find_old_backups(manager, delete_older_than)
            log.info(
                "Snapshots Older Than {} Days, With '--dobackup--' In Their Name Are :"
                " \n".format(delete_older_than))
            [log.info(str(x)) for x in old_backups]
            if old_backups:     # not an empty list
                [delete_snapshot(snap_x) for snap_x in old_backups]
            else:
                log.info("No Snapshot Is Old Enough To be Deleted")
        if delete_snap:
            snap = find_snapshot(delete_snap, manager, do_token)
            delete_snapshot(snap)
        if list_older_than or list_older_than == 0:
            old_backups = find_old_backups(manager, list_older_than)
            log.info(
                "Snapshots Older Than {!s} Days, With '--dobackup--' or '--dobackup-keep--'"
                "In Their Name Are : \n".format(list_older_than))
            [log.info(str(x)) for x in old_backups]
        if backup:
            droplet = find_droplet(backup, manager)
            if droplet is None:
                return 1
            original_status = droplet.status    # active or off
            snap_action = start_backup(droplet, keep)
            snap_done = snap_completed(snap_action)
            if original_status != "off":
                turn_it_on(droplet)
            if not snap_done:
                log.error("SNAPSHOT FAILED {!s} {!s}".format(snap_action, droplet))
        if backup_all:
            # stores all {"snap_action": snap_action, "droplet_id": droplet}
            snap_and_drop_ids = []
            tagged_droplets = get_tagged(manager, tag_name=tag_name)

            if tagged_droplets:  # doplets found with the --tag-name
                for drop in tagged_droplets:
                    droplet = manager.get_droplet(drop.id)
                    snap_action = start_backup(droplet, keep)
                    snap_and_drop_ids.append({"snap_action": snap_action, "droplet_id": droplet.id})
                log.info("Backups Started, snap_and_drop_ids: {!s}".format(snap_and_drop_ids))
                for snap_id_pair in snap_and_drop_ids:
                    snap_done = snap_completed(snap_id_pair["snap_action"])
                    # print("snap_action and droplet_id", snap_id_pair)
                    turn_it_on(manager.get_droplet(snap_id_pair["droplet_id"]))
                    if not snap_done:
                        log.error("SNAPSHOT FAILED {!s} {!s}".format(snap_action, droplet))
            else:  # no doplets with the --tag-name
                log.warning("NO DROPLET FOUND WITH THE TAG NAME " + tag_name)
        if shutdown:
            droplet = find_droplet(shutdown, manager)
            if droplet is None:
                return 1
            turn_it_off(droplet)
        if powerup:
            droplet = find_droplet(powerup, manager)
            if droplet is None:
                return 1
            turn_it_on(droplet)
        if restore_drop:
            if restore_to:
                droplet = find_droplet(restore_drop, manager)
                if droplet is None:
                    return 1
                restore_droplet(droplet, restore_to, manager, do_token)
            else:
                log.warning("Please Use '--restore-to' To Provide The id Of "
                            "Snapshot To Restore This Droplet To")

        log.info("---------------------------END----------------------------")
        log.info("\n\n")
        return 0        # if all good, return 0
    except Exception as e:
        log.critical(e, exc_info=True)     # if errored at any time, mark CRITICAL and log traceback
        return 1


def main() -> int:
    args = parse_args(sys.argv)
    return_code = run(args.token_id, args.init, args.list_droplets, args.list_backups, args.list_snaps,
                      args.list_tagged, args.list_tags, args.list_older_than, args.tag_droplet,
                      args.untag_droplet, args.tag_name, args.delete_older_than, args.delete_snap, args.backup,
                      args.backup_all, args.shutdown, args.powerup, args.restore_drop, args.restore_to, args.keep)
    return return_code


if __name__ == '__main__':
    sys.exit(main())
