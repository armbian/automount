import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

org_dbus = "org.freedesktop.DBus"
org_dbus_mngr = org_dbus + ".ObjectManager"
org_dbus_props = org_dbus + ".Properties"

org_udisks = "org.freedesktop.UDisks2"
org_udisks_block = org_udisks + ".Block"
org_udisks_filesys = org_udisks + ".Filesystem"

def dec(a): return bytes(a).decode().rstrip('\0')

class Monitor:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus()
        self._loop = GLib.MainLoop()

        self._bus.add_signal_receiver(self._interfaces_added,
            signal_name="InterfacesAdded",
            dbus_interface=org_dbus_mngr, bus_name=org_udisks
        )
        self._bus.add_signal_receiver(self._interfaces_removed,
            signal_name="InterfacesRemoved",
            dbus_interface=org_dbus_mngr, bus_name=org_udisks
        )
        self._bus.add_signal_receiver(self._properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface=org_dbus_props, bus_name=org_udisks,
            path_keyword="object_path"
        )
        self._added_callback = None
        self._removed_callback = None
        self._mounts_callback = None

    def _interfaces_added(self, object_path, interfaces):
        if self._added_callback and org_udisks_block in interfaces:
            obj = self._bus.get_object(org_udisks, object_path)
            device = dbus.Interface(obj, org_dbus_props).Get(org_udisks_block, "Device")
            self._added_callback(object_path, dec(device))

    def _interfaces_removed(self, object_path, interfaces):
        if self._removed_callback and org_udisks_block in interfaces:
            self._removed_callback(object_path)

    def _properties_changed(self, interface, changed, invalidated, object_path):
        if self._mounts_callback and interface == org_udisks_filesys:
            for prop, value in changed.items():
                if prop == "MountPoints" and isinstance(value, dbus.Array):
                    mounts = [ dec(e) for e in value ]
                    self._mounts_callback(object_path, mounts)

    def on_device_added(self, callback): self._added_callback = callback
    def on_device_removed(self, callback): self._removed_callback = callback
    def on_mounts_changed(self, callback): self._mounts_callback = callback

    def run(self): self._loop.run()
    def quit(self): self._loop.quit()
