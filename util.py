from configparser import ConfigParser
from pathlib import Path
import re
import subprocess
import sys

_config_dirs = [ "/usr/share/automount", "/etc/automount" ]

def read_config():
    all_paths = []
    for dir in _config_dirs:
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
        print("ERROR: " + proc.stderr.decode(), file=sys.stderr)
        return str()
    return proc.stdout.decode()

def udev_props(device):
    out = run([ "/usr/bin/udevadm", "info", "-q", "env", device ])
    env = {}
    for line in out.splitlines():
        key, value = line.split('=', 1)
        env[key] = value
    return env
