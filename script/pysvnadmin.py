# -*- coding: UTF-8 -*-
'''
    svnadmin api for python
'''

import os
import subprocess
import locale
import xml.etree.ElementTree as ET

SVNADMIN_BIN = 'svnadmin'

def check_output(args):
    try:
        return True, subprocess.check_output(args, stderr=subprocess.STDOUT, shell=True).decode(locale.getpreferredencoding(False))
    except subprocess.CalledProcessError as e:
        return False, e.stdout.decode(locale.getpreferredencoding(False))

class SvnRepo(object):
    def __init__(self, repopath):
        self.repopath = repopath

    def create(self):
        args = ' '.join([
            SVNADMIN_BIN,
            'create',
            self.repopath,
        ])
        succeed, output = check_output(args)
        return succeed, output

    @property
    def svnserve_conf(self):
        return os.path.join(self.repopath, 'conf/svnserve.conf')

    @property
    def conf_passwd(self):
        return os.path.join(self.repopath, 'conf/passwd')

    def add_user(self, acc, pwd):
        with open(self.conf_passwd, 'a') as f:
            f.write("{} = {}\n".format(acc, pwd))

    def set_attr(self, confpath, attr, val):
        with open(confpath, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if attr in line:
                    lines[i] = "{} = {}\n".format(attr, val)
        with open(confpath, 'w') as f:
            f.writelines(lines)

    def set_anon_access(self, auth="none"):
        self.set_attr(self.svnserve_conf, "anon-access", auth)

    def set_auth_access(self, auth="write"):
        self.set_attr(self.svnserve_conf, "auth-access", auth)
        self.set_attr(self.svnserve_conf, "password-db", "passwd")
