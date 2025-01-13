from configparser import ConfigParser
from pathlib import Path
import re
import subprocess
import sys

config_dirs = [ "/usr/share/automount", "/etc/automount" ]

def read_config():
    all_paths = []
    for dir in config_dirs:
        paths = [ path for path in sorted(Path(dir).glob("*.conf")) if path.is_file() ]
        all_paths.extend(paths)
    config = ConfigParser()
    config.read(all_paths)
    return config

def unquote(s):
    if s and (s[0] == '"' or s[0] == "'") and s[0] == s[-1]:
        s = s[1:-1]
    return s.replace('\\"', '"').replace("\\'", "'")

def split_quoted(s):
    # ref: https://stackoverflow.com/a/51560564
    pattern = re.compile(r'(?:[^"\s]*"(?:\\.|[^"])*"[^"\s]*)+|(?:[^\'\s]*\'(?:\\.|[^\'])*\'[^\'\s]*)+|[^\s]+')
    return [ unquote(p) for p in re.findall(pattern, s) ]

def subst_vars(s, env):
    pattern = re.compile(r'\$\{([^}]+)\}')
    return re.sub(pattern, lambda match: env.get(match.group(1), match.group(0)), s)

def run(args, env={}):
    if isinstance(args, str):
        args = split_quoted(subst_vars(args, env))

    proc = subprocess.run(args, capture_output=True)
    if proc.returncode:
        print(f"ERROR: {proc.stderr.decode()}", file=sys.stderr)
        return None
    return proc.stdout.decode()

def udev_props(device):
    out = run([ "/usr/bin/udevadm", "info", "-q", "env", device ])
    env = {}
    for line in out.splitlines():
        key, value = line.split('=', 1)
        env[key] = value
    return env

def device_options(config, env):
    options = {}

    for section in config.sections():
        match = True
        if section != "DEFAULT":
            for prop in split_quoted(section):
                kv = prop.split("=", 1)
                if not kv[0]: continue # ignore empty keys

                if kv[0][0] == '!':
                    value = env.get(kv[0][1:]) or env.get("ID_" + kv[0][1:])
                    match = (value != kv[1]) if len(kv) > 1 else (value is None)
                else:
                    value = env.get(kv[0]) or env.get("ID_" + kv[0])
                    match = (value == kv[1]) if len(kv) > 1 else (value is not None)

                if not match: break

        if match:
            for option in config.options(section):
                options[option] = config[section][option]

    return options

def get_sudo(s):
    sudo = []
    ug = s.split(":", 1)
    if ug[0]: sudo = sudo + ["-u", ug[0]]
    if len(ug) > 1 and ug[1]: sudo = sudo + ["-g", ug[1]]
    if len(sudo): sudo = ["sudo"] + sudo
    return sudo
