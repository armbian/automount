# Auto-mount Service for Systems with No Desktop

**Auto-mount** uses
[`udisks`](https://www.freedesktop.org/wiki/Software/udisks/) to monitor and
respond to block-device related events, such as USB or optical drive
insertion/removal, partition mounting/unmounting, and more.

Out of the box, **auto-mount** will automatically mount any block device
containing a filesystem, when it appears in the system.

## Configuration

**Auto-mount** actions are controlled by config files, which are plain-text
INI-style files with `.conf` extension, consisting of section names (enclosed
in `[]`) followed by actions to be performed.

Config files are parsed in alphabetical order from the following directories
(typically):

`/usr/share/automount/`<br>
`/etc/automount/`

Actions in the most recent config files override the ones in earlier files.

Here is an example of the default config file that comes with **auto-mount**:

```ini
/usr/share/automount/10-default.conf:

[FS_USAGE=filesystem]
auto-mount = yes
```

And, here is an example of the file that keeps a certain drive from being
auto-mounted:

```ini
/etc/automount/20-override.conf:

[FS_UUID=E428-616E]
auto-mount = no
```

### Sections and Properties

Section names consist of one or more space-delimited match conditions, which
can have one of the following forms:

`property=value`, `!property=value`, `property` or `!property`

The first two forms match on equality and inequality respectively, while the
last two match on the presence or absence of a certain property.

Values in match conditions can contain wild-card characters, such as:

`*`, `?`, `[abc]` or `[!def]`

Here is an example of a section that will match optical media containing a
filesystem:

```ini
20-optical.conf:

[FS_USAGE=filesystem CDROM]
on-unmount = /bin/eject ${DEVNAME}
```

and will eject the media once it's unmounted.

Another example of a section, which will cause UDF filesystems on non-optical
drives to be mounted with different options:

```ini
20-vfat.conf:

[FS_TYPE=udf !TYPE=cd]
mount-options = uid=1000,gid=1000
```

You can obtain a list of all properties for a given block device using `udevadm`:

```sh
user@linux:~$ udevadm info -q env /dev/sr0
```
```sh
DEVPATH=/devices/pci0000:00/0000:00:14.0/usb3/3-8/3-8:1.0/host0/target0:0:0/0:0:0:0/block/sr0
DEVNAME=/dev/sr0
DEVTYPE=disk
MAJOR=11
MINOR=0
SUBSYSTEM=block
...
ID_CDROM=1
ID_BUS=usb
ID_MODEL=BD-RE_BU40N
ID_TYPE=cd
ID_USB_DRIVER=usb-storage
...
ID_FS_UUID=d042881731342041
ID_FS_LABEL=FROM_RUSSIA_WITH_LOVE
ID_FS_TYPE=udf
ID_FS_USAGE=filesystem
...
```
or:
```sh
user@linux:~$ udevadm info -q env /dev/sda1
```
```sh
DEVPATH=/devices/pci0000:00/0000:00:0d.0/usb2/2-1/2-1:1.0/host0/target0:0:0/0:0:0:0/block/sda/sda1
DEVNAME=/dev/sda1
DEVTYPE=partition
PARTN=1
MAJOR=8
MINOR=1
SUBSYSTEM=block
...
ID_BUS=usb
ID_MODEL=STORAGE_DEVICE
ID_TYPE=disk
ID_USB_DRIVER=usb-storage
...
ID_PART_TABLE_UUID=d526b372
ID_PART_TABLE_TYPE=dos
ID_FS_LABEL=TEMP
ID_FS_UUID=E428-616E
ID_FS_VERSION=FAT32
...
ID_FS_TYPE=vfat
ID_FS_USAGE=filesystem
...
```

Note: The `ID_` prefix of a property can be omitted in match conditions, so
this:

```ini
[ID_FS_LABEL=rootfs]
...
```

is equivalent to this:

```ini
[FS_LABEL=rootfs]
...
```

When a block-device event occurs, **auto-mount** extracts actions from all
sections with matching conditions, with actions in later sections overriding
the ones in earlier sections.

A special section called `[DEFAULT]` can contain actions that will apply (if
not overridden) to any event.

### Actions

An action can be any of the following:

```
auto-mount = yes|no
mount-options = ...
mount-as = [user][:group]

on-mount = ...
on-unmount = ...
on-add = ...
on-remove = ...
on-change = ...
```

where `...` represents a command to be executed when the action is triggered.
For example:

```ini
[TYPE=cd]
# set spin-down time to 20 minutes
on-add = /sbin/hdparm -S 240 ${DEVNAME}
```

Commands support basic variable substitution in the form `${VARIABLE}`, where
`VARIABLE` can be any of the device properties. Additional properties are
accessible in certain actions:

- The `on-mount` and `on-unmount` actions can use the `${MOUNT_POINT}` property
  to determine the current mount point.

  *Note: The same block device can be mounted at multiple mount points, and the
  `on-mount` and `on-unmount` actions will be executed for each mount point.*

- The `on-add` and `on-change` actions can use the `${SIZE}` property to detect
  empty or ejected media, in which case the value of `SIZE` will be empty.

The `mount-options` and `mount-as` values are only applicable when
`auto-mount = yes`.

## Authors

* **Dimitry Ishenko** - dimitry (dot) ishenko (at) (gee) mail (dot) com

## License

This project is distributed under the GNU GPL license. See the
[LICENSE.md](LICENSE.md) file for details.
