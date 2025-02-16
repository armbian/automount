import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

O_F_DB_OM = "org.freedesktop.DBus.ObjectManager"
O_F_DB_P = "org.freedesktop.DBus.Properties"

O_F_UD2 = "org.freedesktop.UDisks2"
O_F_UD2_B = "org.freedesktop.UDisks2.Block"
O_F_UD2_FS = "org.freedesktop.UDisks2.Filesystem"

def decode(a): return bytes(a).decode().rstrip('\0')

class Monitor:
    def __init__(self, on_device_added=None, on_device_removed=None, on_device_changed=None, on_mounts_changed=None):
        self._added_callback = on_device_added
        self._removed_callback = on_device_removed
        self._changed_callback = on_device_changed
        self._mounts_callback = on_mounts_changed

        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SystemBus()
        self._loop = GLib.MainLoop()

        self._bus.add_signal_receiver(self._interfaces_added,
            signal_name="InterfacesAdded",
            dbus_interface=O_F_DB_OM, bus_name=O_F_UD2
        )
        self._bus.add_signal_receiver(self._interfaces_removed,
            signal_name="InterfacesRemoved",
            dbus_interface=O_F_DB_OM, bus_name=O_F_UD2
        )
        self._bus.add_signal_receiver(self._properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface=O_F_DB_P, bus_name=O_F_UD2,
            path_keyword="object_path"
        )

    def _interfaces_added(self, object_path, interfaces):
        if self._added_callback and O_F_UD2_B in interfaces:
            obj = self._bus.get_object(O_F_UD2, object_path)
            device = dbus.Interface(obj, O_F_DB_P).Get(O_F_UD2_B, "Device")
            self._added_callback(object_path, decode(device))

    def _interfaces_removed(self, object_path, interfaces):
        if self._removed_callback and O_F_UD2_B in interfaces:
            self._removed_callback(object_path)

    def _properties_changed(self, interface, changed, invalidated, object_path):
        if self._changed_callback and interface == O_F_UD2_B:
            for prop, value in changed.items():
                if prop == "Size":
                    obj = self._bus.get_object(O_F_UD2, object_path)
                    device = dbus.Interface(obj, O_F_DB_P).Get(O_F_UD2_B, "Device")
                    self._changed_callback(object_path, decode(device))
                    break

        elif self._mounts_callback and interface == O_F_UD2_FS:
            for prop, value in changed.items():
                if prop == "MountPoints" and isinstance(value, dbus.Array):
                    mounts = [ decode(e) for e in value ]
                    self._mounts_callback(object_path, mounts)
                    break

    def run(self): self._loop.run()
    def quit(self): self._loop.quit()
