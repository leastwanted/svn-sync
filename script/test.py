# -*- coding: UTF-8 -*-
"""
Test for svn
"""

import os
import sys
import shutil
import json
import pysvnadmin
import pysvn
import syncsvn
import pathcmp
import random
import subprocess
import psutil

TEST_ROOT = r"D:\projects\svn-sync\testsvn"
FILE_ROOT = r"file:///" + TEST_ROOT
URL_ROOT = r"svn://127.0.0.1/"
PATH_REPO1 = os.path.join(TEST_ROOT, 'repo1')
PATH_REPO2 = os.path.join(TEST_ROOT, 'repo2')
URL_REPO1 = URL_ROOT + 'repo1'
URL_REPO2 = URL_ROOT + 'repo2'
PATH_WC1 = os.path.join(TEST_ROOT, 'wc1')
PATH_WC2 = os.path.join(TEST_ROOT, 'wc2')
PATH_JSON = os.path.join(PATH_WC1, 'test.json')
PATH_SYNC1 = os.path.join(PATH_WC1, 'sync')
PATH_SYNC2 = os.path.join(PATH_WC2, 'sync')
PATH_WC1_EX = os.path.join(TEST_ROOT, 'wc1ex')
PATH_WC2_EX = os.path.join(TEST_ROOT, 'wc2ex')
PATH_SYNC1_EX = os.path.join(PATH_WC1_EX, 'sync')
PATH_SYNC2_EX = os.path.join(PATH_WC2_EX, 'sync')

def clear_root():
    if os.path.exists(TEST_ROOT):
        # shutil.rmtree(TEST_ROOT)
        os.system('rmdir /S /Q "{}"'.format(TEST_ROOT))
    os.mkdir(TEST_ROOT)

def create_file(path, content=''):
    with open(path, 'w') as f:
        f.write(content)
        f.write('\n')

def append_file(path, content='', head=False):
    if head:
        with open(path, 'r+') as f:
            old = f.read()
            f.seek(0, os.SEEK_SET)
            f.write(content + '\n' + old)
    else:
        with open(path, 'a') as f:
            if head:
                f.seek(0, os.SEEK_SET)
            f.write(content)
            f.write('\n')

def remove_file(path):
    os.remove(path)

def create_path(path):
    os.mkdir(path)

def remove_path(path):
    shutil.rmtree(path)

def start_svnserve(path):
    args = ' '.join([
        "svnserve -d",
        "-r",
        path,
    ])
    subprocess.Popen(args)

def kill_proc(name):
    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()

def clear_svnproc():
    kill_proc('svn.exe')
    kill_proc('svnserve.exe')
    kill_proc('TSVNCache.exe')

def test_repocreate():
    clear_svnproc()
    clear_root()
    repo1 = pysvnadmin.SvnRepo(PATH_REPO1)
    repo1.create()
    repo1.set_anon_access()
    repo1.set_auth_access()
    repo1.add_user("gacc", "gpwd")
    repo1.add_user("acc1", "pwd1")
    repo2 = pysvnadmin.SvnRepo(PATH_REPO2)
    repo2.create()
    repo2.set_anon_access()
    repo2.set_auth_access()
    repo2.add_user("gacc", "gpwd")
    repo2.add_user("acc2", "pwd2")
    start_svnserve(TEST_ROOT)

def test_overwrite(right_to_left=False):
    test_repocreate()
    pysvn.setglobal_accpwd("gacc", 'gpwd')
    wc1 = pysvn.SvnWorkingCopy(PATH_WC1, URL_REPO1)
    wc1.checkout()
    wc2 = pysvn.SvnWorkingCopy(PATH_WC2, URL_REPO2, acc="acc2", pwd="pwd2")
    wc2.checkout()
    # add something to wc1
    create_path(PATH_SYNC1)
    create_file(os.path.join(PATH_SYNC1, 'text01.txt'), 'text01')
    create_path(os.path.join(PATH_SYNC1, 'sub00'))
    create_path(os.path.join(PATH_SYNC1, 'sub01'))
    create_file(os.path.join(PATH_SYNC1, 'sub01/text01   .txt'), 'text01')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text03.txt'), 'text03')
    create_path(os.path.join(PATH_SYNC1, 'sub02'))
    create_file(os.path.join(PATH_SYNC1, 'sub02/bin02.a'), 'bin02')
    create_path(os.path.join(PATH_SYNC1, '中文目录03'))
    create_file(os.path.join(PATH_SYNC1, '中文目录03/bin03.a'), 'bin03')
    wc1.full_modify()
    wc1.commit('init')
    wc1ex = pysvn.SvnWorkingCopy(PATH_WC1_EX, URL_REPO1)
    wc1ex.checkout()
    if right_to_left:
        jsoncontent = {}
        jsoncontent.update(syncsvn.DEFAULT_JSON)
        jsoncontent['OverwriteUsePathLeft'] = 0
        jsoncontent['OverwriteUsePathRight'] = 1
        with open(PATH_JSON, 'w') as f:
            json.dump(jsoncontent, f)
    # add something to wc2
    create_path(PATH_SYNC2)
    create_file(os.path.join(PATH_SYNC2, 'text01.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'text02.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub000'))
    create_path(os.path.join(PATH_SYNC2, 'sub01'))
    create_file(os.path.join(PATH_SYNC2, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'sub01/text03.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub03'))
    create_file(os.path.join(PATH_SYNC2, 'sub03/bin03.a'), 'bin03')
    wc2.full_modify()
    wc2.commit('init')
    wc2ex = pysvn.SvnWorkingCopy(PATH_WC2_EX, URL_REPO2)
    wc2ex.checkout()
    # overwrite wc2
    sync = syncsvn.SvnSync(PATH_SYNC1, PATH_SYNC2, PATH_JSON)
    sync.Refresh()
    # modify on the other way
    create_file(os.path.join(PATH_SYNC1_EX, '不存在文件.txt'), '不存在.txt')
    wc1ex.full_modify()
    wc1ex.commit('extra add')
    create_file(os.path.join(PATH_SYNC2_EX, '额外文件.txt'), '额外文件.txt')
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text03.txt'), 'something extra')
    wc2ex.full_modify()
    wc2ex.commit('extra modify')
    # go on sync
    if sync.CheckSync():
        sync.TrySync()
    # 测试结果
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
    sync.Refresh()
    if sync.CheckSync():
        sync.TrySync()
    res, _, _, _ = pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
    # loop test
    sync.Loop(10)
    return res

def test_getmergerevlist():
    def cmp_list(l, r):
        print('cmp_list')
        print(l)
        print(r)
        if len(l) != len(r):
            return False
        for x, y in zip(l, r):
            if x[0] != y[0]:
                return False
            if x[1] != y[1]:
                return False
        print('compare passed')
        return True
    # case 1
    start = 1
    end = 100
    jumplist = []
    expected = [(1, 100)]
    revlist = syncsvn.GetMergeRevList(start, end, jumplist)
    cmp_list(revlist, expected)

    # case 2
    start = 100
    end = 20
    jumplist = [1, 3, 5, 50, 105]
    expected = []
    revlist = syncsvn.GetMergeRevList(start, end, jumplist)
    cmp_list(revlist, expected)

    # case 3
    start = 100
    end = 2000
    jumplist = [1, 3, 5, 50, 105, 500, 888, 766, 345, 1999, 2000, 2500]
    expected = [(100, 104), (105, 344), (345, 499), (500, 765), (766, 887), (888, 1998)]
    revlist = syncsvn.GetMergeRevList(start, end, jumplist)
    cmp_list(revlist, expected)

    # case 4
    start = 100
    end = 2000
    jumplist = [1, 3, 5, 50, 105, 500, 888, 766, 345, 1999, 2000, 2500]
    random.shuffle(jumplist)
    expected = [(100, 104), (105, 344), (345, 499), (500, 765), (766, 887), (888, 1998)]
    revlist = syncsvn.GetMergeRevList(start, end, jumplist)
    cmp_list(revlist, expected)

def test_merge(reverse=False):
    test_repocreate()
    wc1 = pysvn.SvnWorkingCopy(PATH_WC1, URL_REPO1, acc='acc1', pwd='pwd1')
    wc1.checkout()
    wc2 = pysvn.SvnWorkingCopy(PATH_WC2, URL_REPO2, acc='acc2', pwd='pwd2')
    wc2.checkout()
    pysvn.setglobal_accpwd("gacc", 'gpwd')
    # add something to wc1
    create_path(PATH_SYNC1)
    create_file(os.path.join(PATH_SYNC1, 'text01.txt'), 'text01')
    create_path(os.path.join(PATH_SYNC1, 'sub00'))
    create_path(os.path.join(PATH_SYNC1, 'sub01'))
    create_file(os.path.join(PATH_SYNC1, 'sub01/text01.txt'), 'text01')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text03.txt'), 'text03')
    create_path(os.path.join(PATH_SYNC1, 'sub02'))
    create_file(os.path.join(PATH_SYNC1, 'sub02/bin02.a'), 'bin02')
    create_path(os.path.join(PATH_SYNC1, '中文目录03'))
    create_file(os.path.join(PATH_SYNC1, '中文目录03/bin03.a'), 'bin03')
    wc1.full_modify()
    wc1.commit('init')
    wc1ex = pysvn.SvnWorkingCopy(PATH_WC1_EX, URL_REPO1)
    wc1ex.checkout()
    # add something to wc2
    create_path(PATH_SYNC2)
    create_file(os.path.join(PATH_SYNC2, 'text01.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'text02.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub000'))
    create_path(os.path.join(PATH_SYNC2, 'sub01'))
    create_file(os.path.join(PATH_SYNC2, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'sub01/text03.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub03'))
    create_file(os.path.join(PATH_SYNC2, 'sub03/bin03.a'), 'bin03')
    wc2.full_modify()
    wc2.commit('init')
    wc2ex = pysvn.SvnWorkingCopy(PATH_WC2_EX, URL_REPO2)
    wc2ex.checkout()

    # first sync
    # overwrite wc2
    print('merge test 0')
    if reverse:
        sync = syncsvn.SvnSync(PATH_SYNC2, PATH_SYNC1, PATH_JSON)
    else:
        sync = syncsvn.SvnSync(PATH_SYNC1, PATH_SYNC2, PATH_JSON)

    sync.Refresh()
    # modify on the other way
    create_file(os.path.join(PATH_SYNC1_EX, '不存在文件.txt'), '不存在.txt')
    wc1ex.full_modify()
    wc1ex.commit('extra add')
    create_file(os.path.join(PATH_SYNC2_EX, '额外文件.txt'), '额外文件.txt')
    wc2ex.full_modify()
    wc2ex.commit('extra modify')
    # go on sync
    if sync.CheckSync():
        sync.TrySync()
    # sync with merge
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # sync with merge
    print('merge test 1')
    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text03.txt'), 'append other')
    create_file(os.path.join(PATH_SYNC1_EX, 'sub01/test04.txt'), 'text04')
    remove_file(os.path.join(PATH_SYNC1_EX, 'sub01/text02.txt'))
    wc1ex.full_modify()
    wc1ex.commit('extra add')
    # sync
    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # sync with merge, commit fail
    print('merge test 2')
    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text03.txt'), 'append left')
    wc1ex.full_modify()
    wc1ex.commit('modify')
    sync.Refresh()
    wc2ex.update()
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text03.txt'), 'append right', True)
    wc2ex.full_modify()
    wc2ex.commit('extra modify')
    # sync
    if sync.CheckSync():
        sync.TrySync()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # sync with merge, conflict
    print('merge test 3')
    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text03.txt'), 'append left again')
    wc1ex.full_modify()
    wc1ex.commit('modify')
    sync.Refresh()
    wc2ex.update()
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text03.txt'), 'append right again')
    wc2ex.full_modify()
    wc2ex.commit('extra modify')
    # sync
    if sync.CheckSync():
        sync.TrySync()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # Loop test
    sync.Loop(10)

def test_merge_withsolve(reverse=False):
    test_repocreate()
    wc1 = pysvn.SvnWorkingCopy(PATH_WC1, URL_REPO1, acc='acc1', pwd='pwd1')
    wc1.checkout()
    wc2 = pysvn.SvnWorkingCopy(PATH_WC2, URL_REPO2, acc='acc2', pwd='pwd2')
    wc2.checkout()

    # add something to wc1
    create_path(PATH_SYNC1)
    create_file(os.path.join(PATH_SYNC1, 'text01.txt'), 'text01')
    create_path(os.path.join(PATH_SYNC1, 'sub00'))
    create_path(os.path.join(PATH_SYNC1, 'sub01'))
    create_file(os.path.join(PATH_SYNC1, 'sub01/text01.txt'), 'text01')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text03.txt'), 'text03')
    create_path(os.path.join(PATH_SYNC1, 'sub02'))
    create_file(os.path.join(PATH_SYNC1, 'sub02/bin02.a'), 'bin02')
    create_path(os.path.join(PATH_SYNC1, '中文目录03'))
    create_file(os.path.join(PATH_SYNC1, '中文目录03/bin03.a'), 'bin03')
    wc1.full_modify()
    wc1.commit('init')
    wc1ex = pysvn.SvnWorkingCopy(PATH_WC1_EX, URL_REPO1, acc='acc1', pwd='pwd1')
    wc1ex.checkout()
    # add something to wc2
    create_path(PATH_SYNC2)
    create_file(os.path.join(PATH_SYNC2, 'text01.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'text02.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub000'))
    create_path(os.path.join(PATH_SYNC2, 'sub01'))
    create_file(os.path.join(PATH_SYNC2, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC2, 'sub01/text03.txt'), 'text02')
    create_path(os.path.join(PATH_SYNC2, 'sub03'))
    create_file(os.path.join(PATH_SYNC2, 'sub03/bin03.a'), 'bin03')
    wc2.full_modify()
    wc2.commit('init')
    wc2ex = pysvn.SvnWorkingCopy(PATH_WC2_EX, URL_REPO2, acc='acc2', pwd='pwd2')
    wc2ex.checkout()

    # first sync
    # overwrite wc2
    print('merge test 0')
    if reverse:
        sync = syncsvn.SvnSync(PATH_SYNC2, PATH_SYNC1, PATH_JSON, accleft='acc2', pwdleft='pwd2', accright='acc1', pwdright='pwd1', accjson='acc1', pwdjson='pwd1')
        sync.json['MergeUseLeft'] = 1
        sync.json['OverwriteUsePathRight'] = 1
        sync.json['OverwriteUsePathLeft'] = 0
    else:
        sync = syncsvn.SvnSync(PATH_SYNC1, PATH_SYNC2, PATH_JSON, accleft='acc1', pwdleft='pwd1', accright='acc2', pwdright='pwd2', accjson='acc1', pwdjson='pwd1')
        sync.json['MergeUseRight'] = 1
    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # conflict 1, modify same file
    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text01.txt'), 'append left')
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text03.txt'), 'append left')
    remove_file(os.path.join(PATH_SYNC1_EX, 'sub02/bin02.a'))
    create_file(os.path.join(PATH_SYNC1_EX, 'sub02/bin02.a'), 'wtf\n' * 100)
    wc1ex.propset(os.path.join(PATH_SYNC1_EX, 'sub00'), 'svn:ignore', 'ignore001')
    # remove_path(os.path.join(PATH_SYNC1_EX, '中文目录03'))
    wc1ex.full_modify()
    wc1ex.commit('modify')
    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text01.txt'), 'append left')
    wc1ex.full_modify()
    wc1ex.commit('左侧中文log')
    wc2ex.update()
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text02.txt'), 'append right')
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text03.txt'), 'append right')
    remove_file(os.path.join(PATH_SYNC2_EX, 'sub02/bin02.a'))
    create_file(os.path.join(PATH_SYNC2_EX, 'sub02/bin02.a'), 'ftw\n' * 500)
    # append_file(os.path.join(PATH_SYNC2_EX, '中文目录03/bin03.a'), 'append right')
    wc2ex.propset(os.path.join(PATH_SYNC2_EX, 'sub00'), 'svn:ignore', 'ignore002')
    wc2ex.full_modify()
    wc2ex.commit('extra modify')
    append_file(os.path.join(PATH_SYNC2_EX, 'sub01/text02.txt'), 'append right')
    wc2ex.full_modify()
    wc2ex.commit('右侧中文log')

    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    # tree conflict
    wc1ex.update()
    remove_path(os.path.join(PATH_SYNC1_EX, '中文目录03'))
    wc1ex.full_modify()
    wc1ex.commit('modify')
    wc2ex.update()
    append_file(os.path.join(PATH_SYNC2_EX, '中文目录03/bin03.a'), 'append right')
    wc2ex.full_modify()
    print(wc2ex.commit('extra modify'))

    sync.SanBanFu()
    pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)

    sync.SanBanFu()

def test_svnlog():
    test_repocreate()
    wc1 = pysvn.SvnWorkingCopy(PATH_WC1, URL_REPO1, acc='acc1', pwd='pwd1')
    wc1.checkout()
    wc2 = pysvn.SvnWorkingCopy(PATH_WC2, URL_REPO2, acc='acc2', pwd='pwd2')
    wc2.checkout()

    # add something to wc1
    create_path(PATH_SYNC1)
    create_file(os.path.join(PATH_SYNC1, 'text01.txt'), 'text01')
    create_path(os.path.join(PATH_SYNC1, 'sub00'))
    create_path(os.path.join(PATH_SYNC1, 'sub01'))
    create_file(os.path.join(PATH_SYNC1, 'sub01/text01.txt'), 'text01')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text02.txt'), 'text02')
    create_file(os.path.join(PATH_SYNC1, 'sub01/text03.txt'), 'text03')
    create_path(os.path.join(PATH_SYNC1, 'sub02'))
    create_file(os.path.join(PATH_SYNC1, 'sub02/bin02.a'), 'bin02')
    create_path(os.path.join(PATH_SYNC1, '中文目录03'))
    create_file(os.path.join(PATH_SYNC1, '中文目录03/bin03.a'), 'bin03')
    wc1.full_modify()
    wc1.commit('init')
    wc1ex = pysvn.SvnWorkingCopy(PATH_WC1_EX, URL_REPO1, acc='acc1', pwd='pwd1')
    wc1ex.checkout()

    wc1ex.update()
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text01.txt'), 'append left')
    append_file(os.path.join(PATH_SYNC1_EX, 'sub01/text03.txt'), 'append left')
    remove_file(os.path.join(PATH_SYNC1_EX, 'sub02/bin02.a'))
    create_file(os.path.join(PATH_SYNC1_EX, 'sub02/bin02.a'), 'wtf\n' * 100)
    wc1ex.propset(os.path.join(PATH_SYNC1_EX, 'sub00'), 'svn:ignore', 'ignore001')
    # remove_path(os.path.join(PATH_SYNC1_EX, '中文目录03'))
    wc1ex.full_modify()
    wc1ex.commit('modify')

    wc1.update()
    print(wc1.log([(1,2)])[1])

def test_isworkingcopy():
    path = PATH_JSON
    print('{} is working copy? {}'.format(path, pysvn.is_workingcopy(path)))
    path = os.path.dirname(PATH_JSON)
    print('{} is working copy? {}'.format(path, pysvn.is_workingcopy(path)))
    path = PATH_JSON
    pysvn.svnadd(path)
    print('{} is working copy? {}'.format(path, pysvn.is_workingcopy(path)))

if __name__ == "__main__":
    # test_repocreate()
    print('test_overwrite:', test_overwrite())
    # print('test_overwrite2:', test_overwrite(right_to_left=True))
    # test_getmergerevlist()
    # test_merge(reverse=False)
    # test_merge_withsolve(reverse=False)
    # test_isworkingcopy()
    # test_svnlog()
    # pathcmp.compare_path(PATH_SYNC1, PATH_SYNC2)
