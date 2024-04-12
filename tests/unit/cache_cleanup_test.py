import argparse
import os
import os.path
import random
import shutil
import string
import unittest
import utils
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import create_autospec

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


def init_cache_dir(num_files, mode=None):
    cache_dir = "%s/giphizer" % os.environ.get("XDG_CACHE_HOME")
    Path(cache_dir).mkdir(parents=True)

    for i in range(num_files):
        file_name = "%s/file-%d" % (cache_dir, i)
        open(file_name, 'a').close()

        if i % 2 == 0:
            # Set the file's access time, without changing its modification time
            access_time = datetime.now() - timedelta(minutes=15)
            stat = os.stat(file_name)
            os.utime(file_name, (access_time.timestamp(), stat.st_mtime))

    if mode is not None:
        os.chmod(cache_dir, mode)


def count_cached_files(pattern="*"):
    cache_dir = "%s/giphizer" % os.environ.get("XDG_CACHE_HOME")
    return len([file for file in Path(cache_dir).rglob(pattern)
               if file.is_file()])


class TestCacheCleanup(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.test_cache_home = None
        self.original_xdg_cache_home = None

    def setUp(self):
        test_cache_dir_name = "giphizer-test-%s" % "".join(random.choices(string.ascii_lowercase, k=11))
        self.test_cache_home = os.path.join(os.environ.get("TMPDIR"), test_cache_dir_name)
        self.original_xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = self.test_cache_home

    def tearDown(self):
        if os.path.isdir(self.test_cache_home):
            cache_dir = "%s/giphizer" % self.test_cache_home
            if os.path.exists(cache_dir):
                os.chmod(cache_dir, 0o755, follow_symlinks=False)
            shutil.rmtree(self.test_cache_home)

        utils.restore_environment_variable("XDG_CACHE_HOME", self.original_xdg_cache_home)

    def test_does_nothing_if_the_cache_directory_does_not_exist(self):
        args = argparse.Namespace(max_cache=10)
        original_listdir_fn = os.listdir
        original_remove_fn = os.remove
        os.listdir = create_autospec(os.listdir)
        os.remove = create_autospec(os.remove)

        try:
            giphy.clean_cache(args)

            os.listdir.assert_not_called()
            os.remove.assert_not_called()
            self.assertFalse(os.path.exists(self.test_cache_home))  # Didn't create the cache dir
        finally:
            os.listdir = original_listdir_fn
            os.remove = original_remove_fn

    def test_retains_only_max_cache_items(self):
        init_cache_dir(10)
        args = argparse.Namespace()

        for i in (10, 5, 0):
            args.max_cache = i
            giphy.clean_cache(args)
            self.assertEqual(count_cached_files(), i)

    def test_removes_files_based_on_last_access_time(self):
        init_cache_dir(10)  # file-0 through file-9
        args = argparse.Namespace(max_cache=5)

        giphy.clean_cache(args)

        # We gave even-numbered files an older access time in init_cache_dir(),
        # so clean_cache() should've ended up keeping the odd-numbered ones
        self.assertEqual(count_cached_files("file-[13579]"), 5)
        self.assertEqual(count_cached_files("file-[02468]"), 0)

    def test_errors_if_it_cannot_read_the_cache_directory(self):
        init_cache_dir(1, 0o333)
        args = argparse.Namespace(max_cache=0)

        with self.assertRaises(OSError):
            giphy.clean_cache(args)

    def test_errors_if_it_cannot_delete_a_cached_file(self):
        init_cache_dir(1, 0o555)
        args = argparse.Namespace(max_cache=0)

        with self.assertRaises(OSError):
            giphy.clean_cache(args)

    def test_does_not_error_if_it_cannot_delete_a_cached_file_that_no_longer_exists(self):
        init_cache_dir(3)
        args = argparse.Namespace(max_cache=0)
        original_remove_fn = os.remove
        os.remove = create_autospec(os.remove, side_effect=FileNotFoundError())

        try:
            giphy.clean_cache(args)

            # If we get here, no error was raised, and we're good
            self.assertEqual(count_cached_files(), 3)  # Sanity check
        finally:
            os.remove = original_remove_fn

    def test_does_not_error_if_files_disappear_before_sorting_completes(self):
        init_cache_dir(5)
        args = argparse.Namespace(max_cache=0)
        original_getatime_fn = os.path.getatime
        os.path.getatime = create_autospec(os.path.getatime, side_effect=FileNotFoundError())

        try:
            giphy.clean_cache(args)
        finally:
            os.path.getatime = original_getatime_fn


if __name__ == "__main__":
    unittest.main()
