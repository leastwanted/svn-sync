#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
sync two different svn repos
'''

import os
import shutil
import json
import argparse
import pysvn
import time
import datetime

DEFAULT_JSON = {
    'OverwriteUsePathLeft' : 1, # 1/0 if 1, use pathleft to overwrite pathleft
    'OverwriteUsePathRight' : 0, # 1/0 if 1, use pathright to overwrite pathright
    'LeftRev' : 0, # int, the last sync revision of left
    'RightRev' : 0, # int, the last sync revision of right
    'LeftJump' : [], # list, the revisions do not need to be merge of left
    'RightJump' : [], # list the revisions do not need to be merge of right
    'SkipFlag' : 0, # 1/0 if 1, something unexpected happend(like conflict) and needs manual fix
    'MergeUseLeft' : 0, # 1/0 if 1, use path left to solve conflict
    'MergeUseRight' : 0, # 1/0 if 1, use path right to solve conflict
}

def loginfo(msg):
    print(msg)

def notify(msg):
    # something happend and need notify
    print("=notify=")
    print(msg)
    print("=end notify=")

def rmtree(dirpath, folder_to_exclude='.svn'):
    for root, dirs, files in os.walk(dirpath, topdown=True):
        for file_ in files:
            full_path = os.path.join(root, file_)
            if folder_to_exclude not in full_path:
                os.remove(full_path)
        for folder in dirs:
            full_path = os.path.join(root, folder)
            if folder_to_exclude not in full_path:
                shutil.rmtree(full_path)
        return

def GetMergeRevList(start, end, jumplist):
    jumplist = sorted(v for v in jumplist if v > start and v <= end)
    revlist = []
    for v in jumplist:
        if v-1 > start:
            revlist.append((start, v-1))
        start = v
    if end > start:
        revlist.append((start, end))
    return revlist

class SvnSync(object):
    def __init__(self, pathleft, pathright, pathjson, accleft="", pwdleft="", accright="", pwdright="", accjson="", pwdjson=""):
        self.pathleft = pathleft
        self.pathright = pathright
        self.pathjson = pathjson
        self.json = {}
        self.LoadJson()
        self.left_wc = pysvn.SvnWorkingCopy(self.pathleft, acc=accleft, pwd=pwdleft)
        self.right_wc = pysvn.SvnWorkingCopy(self.pathright, acc=accright, pwd=pwdright)
        self.json_wc = None
        self.accjson = accjson
        self.pwdjson = pwdjson

    def LoadJson(self):
        if os.path.exists(self.pathjson):
            with open(self.pathjson, 'r') as f:
                self.json = json.load(f)
            # json version update
            for k, v in DEFAULT_JSON.items():
                if k not in self.json:
                    self.json[k] = v
        else:
            self.json.update(DEFAULT_JSON)
        return self.json

    def DumpJson(self, commit=True):
        self.ClearJump()
        with open(self.pathjson, 'w') as f:
            json.dump(self.json, f, indent=4)
        if not self.json_wc:
            if not pysvn.is_workingcopy(self.pathjson) and pysvn.is_workingcopy(os.path.dirname(self.pathjson)):
                pysvn.svnadd(self.pathjson)
            if pysvn.is_workingcopy(self.pathjson):
                self.json_wc = pysvn.SvnWorkingCopy(self.pathjson, acc=self.accjson, pwd=self.pwdjson)
        if self.json_wc and commit:
            self.json_wc.commit('sync json')

    def ClearJump(self):
        self.json['LeftJump'] = [v for v in self.json['LeftJump'] if v > self.json['LeftRev']]
        self.json['RightJump'] = [v for v in self.json['RightJump'] if v > self.json['RightRev']]

    def Overwrite(self, src, dest):
        rmtree(dest)
        src.export(dest)

    def Reset(self):
        self.left_wc.reset()
        self.right_wc.reset()

    def Loop(self, sec):
        while 1:
            self.SanBanFu()
            time.sleep(sec)

    def SanBanFu(self):
        self.Refresh()
        if self.CheckSync():
            loginfo('start SVN sync on {}'.format(datetime.datetime.now()))
            self.TrySync()

    def Refresh(self):
        if self.json_wc:
            self.json_wc.update(accept_action='theirs-full')
            self.LoadJson()
        self.left_wc.update()
        self.right_wc.update()

    def CheckSync(self):
        # return need sync?
        if self.json['SkipFlag']:
            loginfo('sync skipped')
            return False
        elif self.json['OverwriteUsePathLeft']:
            return True
        elif self.json['OverwriteUsePathRight']:
            return True
        elif self.left_wc.get_revision() > self.json['LeftRev']:
            return True
        elif self.right_wc.get_revision() > self.json['RightRev']:
            return True
        # loginfo('no need sync')
        return False

    def TrySync(self):
        # loginfo('try sync')
        if self.json['OverwriteUsePathLeft']:
            self.Overwrite(self.left_wc, self.pathright)
            loginfo('Overwrite use left:\n{}'.format(self.right_wc.full_modify()))
            succeed, output, newrev = self.right_wc.commit('sync from left {}'.format(self.left_wc.get_revision()))
            if succeed == 'nothing':
                loginfo('overwrite use left failed due to nothing: {}'.format(output))
                self.json['OverwriteUsePathLeft'] = 0
                self.json['LeftRev'] = self.left_wc.get_revision()
                self.json['RightRev'] = self.right_wc.get_revision()
                self.DumpJson()
            elif succeed:
                loginfo('overwrite use left succeed: \n{}'.format(output))
                self.json['OverwriteUsePathLeft'] = 0
                self.json['LeftRev'] = self.left_wc.get_revision()
                self.json['RightRev'] = self.right_wc.get_revision()
                self.json['RightJump'].append(newrev)
                self.DumpJson()
            else:
                loginfo('overwrite use left failed due to commit: {}'.format(output))
                self.right_wc.reset()
            return

        elif self.json['OverwriteUsePathRight']:
            self.Overwrite(self.right_wc, self.pathleft)
            loginfo('Overwrite use right:\n{}'.format(self.left_wc.full_modify()))
            succeed, output, newrev = self.left_wc.commit('sync from right {}'.format(self.right_wc.get_revision()))
            if succeed == 'nothing':
                loginfo('overwrite use right failed due to nothing: {}'.format(output))
                self.json['OverwriteUsePathRight'] = 0
                self.json['LeftRev'] = self.left_wc.get_revision()
                self.json['RightRev'] = self.right_wc.get_revision()
                self.DumpJson()
            elif succeed:
                loginfo('overwrite use right succeed: \n{}'.format(output))
                self.json['OverwriteUsePathRight'] = 0
                self.json['LeftRev'] = self.left_wc.get_revision()
                self.json['RightRev'] = self.right_wc.get_revision()
                self.json['LeftJump'].append(newrev)
                self.DumpJson()
            else:
                loginfo('overwrite use right failed due to commit: {}'.format(output))
                self.left_wc.reset()
            return

        if self.left_wc.get_revision() > self.json['LeftRev']:
            revlist = GetMergeRevList(self.json['LeftRev'], self.left_wc.get_revision(), self.json['LeftJump'])
            if revlist:
                loginfo('try merge left to right: {}'.format(revlist))
                if self.json['MergeUseLeft']:
                    accept_action = "theirs-full"
                elif self.json['MergeUseRight']:
                    accept_action = "mine-full"
                else:
                    accept_action = None
                res, output = self.right_wc.merge(self.left_wc, revlist, accept_action)
                loginfo('merge result {}: {}'.format(res, output))
                if res == 'conflict':
                    loginfo('merge left to right failed due to conflict')
                    self.json['SkipFlag'] = 1
                    self.DumpJson()
                    self.right_wc.reset()
                    msg = "\n".join([
                        'conflict happened when merge from left to right (DO NEED MANUAL RESOLVE):',
                        '\n'.join([line for line in output.splitlines() if not(line.startswith('A') or line.startswith('U') or line.startswith('D'))]),
                        ])
                    notify(msg)
                    return
                elif res in ('succeed', 'conflict-resolved'):
                    if res == 'conflict-resolved':
                        msg = "\n".join([
                            'conflict happened when merge from left to right (auto resolved):',
                            '\n'.join([line for line in output.splitlines() if not(line.startswith('A') or line.startswith('U') or line.startswith('D'))]),
                            ])
                        notify(msg)
                    _, svnlog = self.left_wc.log(revlist)
                    succeed, output, rev = self.right_wc.commit('merge from left {}\n{}'.format(revlist, svnlog))
                    if succeed:
                        loginfo('successfully commit to right: \n{}'.format(output))
                        self.json['LeftRev'] = self.left_wc.get_revision()
                        self.json['RightJump'].append(rev)
                        self.DumpJson()
                    else:
                        loginfo('merge left to right failed due to commit:\n{}'.format(output))
                        self.right_wc.reset()
                        return
                elif res == 'nothing':
                    # loginfo('nothing to merge')
                    self.json['LeftRev'] = self.left_wc.get_revision()
                    self.DumpJson(False)
                else:
                    self.right_wc.reset()
            else:
                self.json['LeftRev'] = self.left_wc.get_revision()
                self.DumpJson(False)

        if self.right_wc.get_revision() > self.json['RightRev']:
            revlist = GetMergeRevList(self.json['RightRev'], self.right_wc.get_revision(), self.json['RightJump'])
            if revlist:
                loginfo('try merge right to left: {}'.format(revlist))
                if self.json['MergeUseLeft']:
                    accept_action = "mine-full"
                elif self.json['MergeUseRight']:
                    accept_action = "theirs-full"
                else:
                    accept_action = None
                res, output = self.left_wc.merge(self.right_wc, revlist, accept_action)
                loginfo('merge result {}: {}'.format(res, output))
                if res == 'conflict':
                    loginfo('merge right to left failed due to conflict')
                    self.json['SkipFlag'] = 1
                    self.DumpJson()
                    self.left_wc.reset()
                    msg = "\n".join([
                        'conflict happened when merge from right to left (DO NEED MANUAL RESOLVE):',
                        '\n'.join([line for line in output.splitlines() if not(line.startswith('A') or line.startswith('U') or line.startswith('D'))]),
                        ])
                    notify(msg)
                    return
                elif res in ('succeed', 'conflict-resolved'):
                    if res == 'conflict-resolved':
                        msg = "\n".join([
                            'conflict happened when merge from right to left (auto resolved):',
                            '\n'.join([line for line in output.splitlines() if not(line.startswith('A') or line.startswith('U') or line.startswith('D'))]),
                            ])
                        notify(msg)
                    _, svnlog = self.right_wc.log(revlist)
                    succeed, output, rev = self.left_wc.commit('merge from right {}\n{}'.format(revlist, svnlog))
                    if succeed:
                        loginfo('successfully commit to left: \n{}'.format(output))
                        self.json['RightRev'] = self.right_wc.get_revision()
                        self.json['LeftJump'].append(rev)
                        self.DumpJson()
                    else:
                        loginfo('merge right to left failed due to commit:\n{}'.format(output))
                        self.left_wc.reset()
                        return
                elif res == 'nothing':
                    # loginfo('nothing to merge')
                    self.json['RightRev'] = self.right_wc.get_revision()
                    self.DumpJson(False)
                else:
                    self.left_wc.reset()
            else:
                self.json['RightRev'] = self.right_wc.get_revision()
                self.DumpJson(False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('pathleft')
    parser.add_argument('pathright')
    parser.add_argument('pathjson')
    args = parser.parse_args()
    sync = SvnSync(args.pathleft, args.pathright, args.pathjson)
    sync.SanBanFu()
