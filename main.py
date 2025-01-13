#!/usr/bin/env python3

from monitor import Monitor
from signal import signal, SIGHUP, SIGINT, SIGTERM
from util import *

print("Reading config")
config = read_config()

def handle_sighup(n, f):
    print("Reading config")
    global config
    config = read_config()
signal(SIGHUP , handle_sighup)

context = {}
yes = [ "on", "On", "ON", "true", "True", "TRUE", "yes", "Yes", "YES" ]

def device_added(path, device):
    env = udev_props(device)
    options = device_options(config, env)

    on_add = options.get("on-add")
    if on_add: run(on_add, env)

    auto_mount = options.get("auto-mount")
    if auto_mount in yes:
        cmd = [ "/usr/bin/udisksctl", "mount", "-b", device ]

        mount_options = options.get("mount-options")
        if mount_options: cmd = cmd + ["-o", mount_options]

        mount_as = options.get("mount-as")
        if mount_as: cmd = get_sudo(mount_as) + cmd

        run(cmd)

    context[path] = env

def device_removed(path):
    env = context.get(path)
    if env:
        options = device_options(config, env)
        mounts = env.get("MOUNT_POINTS", [])

        on_unmount = options.get("on-unmount")
        if on_unmount:
            for mount in mounts:
                env["MOUNT_POINT"] = mount
                run(on_unmount, env)
            env.pop("MOUNT_POINT", None)

def mounts_changed(path, new_mounts):
    env = context.get(path)
    if env:
        options = device_options(config, env)
        old_mounts = env.get("MOUNT_POINTS", [])

        on_unmount = options.get("on-unmount")
        if on_unmount:
            for mount in old_mounts:
                if mount not in new_mounts:
                    env["MOUNT_POINT"] = quote(mount)
                    run(on_unmount, env)

        on_mount = options.get("on-mount")
        if on_mount:
            for mount in new_mounts:
                if mount not in old_mounts:
                    env["MOUNT_POINT"] = quote(mount)
                    run(on_mount, env)

        env.pop("MOUNT_POINT", None)
        env["MOUNT_POINTS"] = new_mounts

print("Creating monitor")
monitor = Monitor(device_added, device_removed, mounts_changed)

def handle_sigint(n, f):
    print(f"Received signal {n} - exiting")
    global monitor
    monitor.quit()
signal(SIGINT , handle_sigint)
signal(SIGTERM, handle_sigint)

print("Starting monitor loop")
monitor.run()