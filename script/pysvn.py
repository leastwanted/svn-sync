# -*- coding: utf-8 -*-
'''
    svn api for python
'''

import os
import sys
import shutil
import locale
import subprocess
import xml.etree.ElementTree as ET
import tempfile

def loginfo(msg):
    print(msg)

SVN_BIN = 'svn'
DEFAULT_ARG = '--no-auth-cache --non-interactive'

g_ACC = ""
g_PWD = ""

def setglobal_accpwd(acc, pwd):
    global g_ACC
    global g_PWD
    g_ACC = acc
    g_PWD = pwd

def check_output(args):
    try:
        # loginfo(args)
        return True, subprocess.check_output(args, stderr=subprocess.STDOUT, shell=True).decode(locale.getpreferredencoding(False))
    except subprocess.CalledProcessError as e:
        # loginfo(e.output.decode(locale.getpreferredencoding(False)))
        return False, e.output.decode(locale.getpreferredencoding(False))

def remove(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def is_workingcopy(path):
    args = ' '.join([
        SVN_BIN,
        'info',
        path,
        DEFAULT_ARG,
    ])
    succeed, output = check_output(args)
    return succeed

def svnadd(path):
    args = ' '.join([
        SVN_BIN,
        'add --no-ignore',
        path,
        DEFAULT_ARG,
    ])
    succeed, output = check_output(args)
    return succeed, output

class SvnWorkingCopy(object):
    def __init__(self, path, url=None, acc="", pwd=""):
        self.path = path
        self.url = url if url else self.load_url()
        self.acc = acc
        self.pwd = pwd

    def get_accpwd_arg(self):
        if self.acc and self.pwd:
            return "--username={} --password={}".format(self.acc, self.pwd)
        elif g_ACC and g_PWD:
            return "--username={} --password={}".format(g_ACC, g_PWD)
        return ""

    def load_url(self):
        args = ' '.join([
            SVN_BIN,
            'info --xml',
            self.path,
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        root = ET.fromstring(output)
        return root.find('entry').find('url').text

    def cleanup(self):
        args = ' '.join([
            SVN_BIN,
            'cleanup',
            self.path,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output

    def checkout(self, rev='HEAD'):
        args = ' '.join([
            SVN_BIN,
            'checkout',
            '-r %s' % rev,
            self.url,
            self.path,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output

    def update(self, rev='HEAD', accept_action=""):
        args = ' '.join([
            SVN_BIN,
            'update',
            '-r %s' % rev,
            self.path,
            "--accept={}".format(accept_action) if accept_action else '',
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output

    def reset(self):
        self.cleanup()
        self.revert()
        _, output = self.status()
        for line in output.splitlines():
            status = line[0]
            path = line[8:]
            if status == '?':
                remove(path)
            if status == 'I':
                remove(path)

    def revert(self):
        args = ' '.join([
            SVN_BIN,
            'revert -R',
            '--depth=infinity',
            self.path,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output

    def get_revision(self):
        args = ' '.join([
            SVN_BIN,
            'info --xml',
            self.path,
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        root = ET.fromstring(output)
        return int(root.find('entry').get('revision'))

    def status(self):
        args = ' '.join([
            SVN_BIN,
            'status --no-ignore',
            self.path,
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        # for line in output.splitlines():
        #     loginfo(line)
        return succeed, output

    def add(self, path):
        args = ' '.join([
            SVN_BIN,
            'add --no-ignore',
            '"{}@"'.format(path) if "@" in path else '"{}"'.format(path),
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        return succeed, output

    def delete(self, path):
        args = ' '.join([
            SVN_BIN,
            'delete',
            '"{}@"'.format(path) if "@" in path else '"{}"'.format(path),
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        return succeed, output

    def merge(self, wc, revlist=[], accept_action=None):
        args = ' '.join([
            SVN_BIN,
            'merge',
            ' '.join("-r %d:%d" % v for v in revlist),
            wc.path,
            self.path,
            '--accept={}'.format(accept_action) if accept_action else "",
            DEFAULT_ARG,
            wc.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        if 'conflict' in output:
            if accept_action and "Tree conflicts" not in output:
                return 'conflict-resolved', output
            return 'conflict', output
        if succeed and output:
            return 'succeed', output
        elif succeed:
            return 'nothing', output
        else:
            return 'error', output

    def full_modify(self):
        _, output = self.status()
        for line in output.splitlines():
            status = line[0]
            path = line[8:]
            if status == '?':
                self.add(path)
            elif status == 'I':
                self.add(path)
            elif status == "!":
                self.delete(path)
        return output

    def commit(self, msg):
        # loginfo("commit msg:", msg)
        msg = "\n".join([line for line in msg.splitlines()])
        fp = tempfile.NamedTemporaryFile(mode="w+t", encoding=locale.getpreferredencoding(False), delete=False)
        fp.write(msg)
        args = ' '.join([
            SVN_BIN,
            # 'commit -m',
            # '"%s"' % msg,
            'commit -F "{}"'.format(fp.name),
            self.path,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        fp.close()
        succeed, output = check_output(args)
        if succeed and not output:
            return 'nothing', output, 0
        if succeed and "revision" in output:
            # loginfo('cmommit output:', repr(output))
            rev = int(output.splitlines()[-1].split()[-1].replace('.', ''))
            return succeed, output, rev
        return False, output, 0

    def export(self, dest):
        args = ' '.join([
            SVN_BIN,
            'export --force',
            self.path,
            dest,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output

    def propset(self, path, name, val):
        args = ' '.join([
            SVN_BIN,
            'propset',
            name,
            val,
            "{}".format(path),
            DEFAULT_ARG,
        ])
        succeed, output = check_output(args)
        return succeed, output

    def log(self, revlist):
        args = ' '.join([
            SVN_BIN,
            'log',
            ' '.join("-r %d:%d" % v for v in revlist),
            self.path,
            DEFAULT_ARG,
            self.get_accpwd_arg(),
        ])
        succeed, output = check_output(args)
        return succeed, output
