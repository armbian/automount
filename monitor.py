import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

class Monitor:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus()

        self._bus.add_signal_receiver(self._interfaces_added,
            signal_name="InterfacesAdded",
            dbus_interface="org.freedesktop.DBus.ObjectManager",
            bus_name="org.freedesktop.UDisks2"
        )
        self._bus.add_signal_receiver(self._interfaces_removed,
            signal_name="InterfacesRemoved",
            dbus_interface="org.freedesktop.DBus.ObjectManager",
            bus_name="org.freedesktop.UDisks2"
        )
        self._bus.add_signal_receiver(self._properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface="org.freedesktop.DBus.Properties",
            bus_name="org.freedesktop.UDisks2",
            path_keyword="object_path"
        )
        self._added_callback = None
        self._removed_callback = None
        self._mounts_callback = None

    def _interfaces_added(self, object_path, interfaces):
        if "org.freedesktop.UDisks2.Block" in interfaces:
            obj = self._bus.get_object("org.freedesktop.UDisks2", object_path)
            props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
            dev = bytes(props.Get("org.freedesktop.UDisks2.Block", "Device")).decode()
            if self._added_callback: self._added_callback(object_path, dev)

    def _interfaces_removed(self, object_path, interfaces):
        if "org.freedesktop.UDisks2.Block" in interfaces:
            if self._removed_callback: self._removed_callback(object_path)

    def _properties_changed(self, interface, changed, invalidated, object_path):
        if interface == "org.freedesktop.UDisks2.Filesystem":
            for prop, value in changed.items():
                if prop == "MountPoints" and isinstance(value, dbus.Array):
                    mounts = [ bytes(e[:-1]).decode() for e in value ]
                    if self._mounts_callback: self._mounts_callback(object_path, mounts)

    def on_device_added(self, callback): self._added_callback = callback
    def on_device_removed(self, callback): self._removed_callback = callback
    def on_mounts_changed(self, callback): self._mounts_callback = callback

    def run(self):
        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            pass
