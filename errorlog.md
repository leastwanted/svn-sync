# Error logs

## E155004

svn: E155004: Run 'svn cleanup' to remove locks (type 'svn help cleanup' for details)

explain:
- svn update is interrupted by extra forces, then the working copy is locked
- solution: add `svn cleanup` in reset, when failed
