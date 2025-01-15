from configparser import ConfigParser
from fnmatch import fnmatch
from pathlib import Path
import re
import subprocess
import sys

def read_config():
    dir = Path("@CMAKE_INSTALL_FULL_SYSCONFDIR@/automount")
    paths = [ path for path in sorted(dir.glob("*.conf")) if path.is_file() ]
    config = ConfigParser()
    config.read(paths)
    return config

def quote(s): return '"' + s + '"'

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
    return re.sub(pattern, lambda match: env.get(match.group(1), ""), s)

def run(args, env={}):
    if isinstance(args, str):
        args = split_quoted(subst_vars(args, env))

    print(f"Executing: {args}")
    try:
        proc = subprocess.run(args, capture_output=True)
        if not proc.returncode: return proc.stdout.decode()
        err = proc.stderr.decode()
    except Exception as e:
        err = str(e)

    print(f"ERROR: {err}", file=sys.stderr)
    return None

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
        for prop in split_quoted(section):
            kv = prop.split("=", 1)
            if not kv[0]: continue # ignore empty keys

            if kv[0][0] == '!':
                value = env.get(kv[0][1:])
                match = value is None or not fnmatch(value, kv[1]) if len(kv) > 1 else False
            else:
                value = env.get(kv[0])
                match = value is not None and fnmatch(value, kv[1]) if len(kv) > 1 else True

            if not match: break

        if match:
            for option in config.options(section):
                options[option] = config[section][option]

    return options
