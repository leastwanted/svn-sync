'''
Compare two paths and return if their diffs
'''

import filecmp
import argparse

def print_diffs(dcmp):
    left = []
    right = []
    diffs = []
    for f in dcmp.left_only:
        # print('left only:', f)
        left.append(f)
    for f in dcmp.right_only:
        # print('right only:', f)
        right.append(f)
    for f in dcmp.diff_files:
        # print('diff files:', f)
        diffs.append(f)
    for sub_dcmp in dcmp.subdirs.values():
        l, r, d = print_diffs(sub_dcmp)
        left += l
        right += r
        diffs += d
    return left, right, diffs

def compare_path(path1, path2):
    dcmp = filecmp.dircmp(path1, path2)
    left, right, diffs = print_diffs(dcmp)
    if not left and not right and not diffs:
        print('path are the same')
        return True, left, right, diffs
    if left:
        print('left only:', left)
    if right:
        print('right only:', right)
    if diffs:
        print('diff files:', diffs)
    return False, left, right, diffs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path1')
    parser.add_argument('path2')
    args = parser.parse_args()
    compare_path(args.path1, args.path2)
