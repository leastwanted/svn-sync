# SVN Sync

automatically sync between two svn repositories
[Error logs](errorlog.md)

## script

- `pysvn.py`: svn usage python export
- `pysvnadmin.py`: svnadmin usage python export
- `syncsvn.py`: sync script between two repository
- `test.py`: test script
- `patycom.py`: compare two directories if they are identical

## prepare

- working copy left: a svn working copy to sync (do not need to be svn root)
- working copy right: a svn working copy to sync of another repository (do not need to be svn root)
- wokring copy json: to save the sync status and config (**DO NOT** to be subdirectory of the above two repository)

## usage

```py
import syncsvn

pathleft = 'wc_left/trunk'
pathright = 'wc_right/trunk'
pathjson = 'wc_left/svnsync.json'

svnSync = syncsvn.SvnSync(pathleft, pathright, pathjson)
SvnSync.SanBanFu() # do one sync
SvnSync.Loop(30) # do infinite sync with interval 30 sec
```

## json config file

```py
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
```

- When first time run, it will do overwite use left to right automatically
- If conflict happened when merge, the `SkpFlag` will set to `1`, and the sync will be skipped (**NEED manual fix**)
- To manual fix sync, you can do
    - reset `SkipFlag` to `0`
    - set `OverwriteUsePathLeft` or `OverwriteUsePathRight` to 1
- `MergeUseLeft` or `MergeUseRight` can do automatically conflict resolve, but
    - it can only handle `file conflicts` or `property conflicts`
    - `tree conflicts` can not be handled
    - it is not active in default. you have to active the feature manually by set `MergeUseLeft` or `MergeUseRight` to 1
