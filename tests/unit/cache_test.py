import os
import os.path
import random
import shutil
import string
import unittest
import utils
from base64 import b64decode
from pathlib import Path
from unittest.mock import create_autospec

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class TestCache(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.test_cache_home = None
        self.original_xdg_cache_home = None

    def setUp(self):
        test_cache_dir_name = "giphizer-test-%s" % "".join(random.choices(string.ascii_lowercase, k=10))
        self.test_cache_home = os.path.join(os.environ.get("TMPDIR"), test_cache_dir_name)
        self.original_xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = self.test_cache_home

    def tearDown(self):
        if os.path.isdir(self.test_cache_home):
            shutil.rmtree(self.test_cache_home)

        if self.original_xdg_cache_home:
            os.environ["XDG_CACHE_HOME"] = self.original_xdg_cache_home
        else:
            os.environ.pop("XDG_CACHE_HOME", None)

    def count_cached_files(self, pattern):
        """
        Utility function that counts files matching a glob pattern
        in a directory and all of its subdirectories.
        """
        return len([file for file in Path(self.test_cache_home).rglob(pattern)
                   if file.is_file()])

    def test_returns_a_cached_file(self):
        cache_dir = "%s/giphizer" % os.environ["XDG_CACHE_HOME"]
        Path(cache_dir).mkdir(parents=True)
        self.assertTrue(os.path.isdir(self.test_cache_home))  # Sanity check

        image_id = "test-image-1"
        cache_path = "%s/%s.gif" % (cache_dir, image_id)

        fake_image_data = b"fake-image-data"
        with open(cache_path, "wb") as fake_cache_file:
            fake_cache_file.write(fake_image_data)

        image_data = giphy.load_cached_image(image_id)

        self.assertEqual(image_data, fake_image_data)

    def test_returns_none_if_a_file_is_not_cached(self):
        cache_dir = "%s/giphizer" % os.environ["XDG_CACHE_HOME"]
        Path(cache_dir).mkdir(parents=True)
        self.assertTrue(os.path.isdir(self.test_cache_home))  # Sanity check

        image_id = "test-image-2"
        image_data = giphy.load_cached_image(image_id)

        self.assertIsNone(image_data)

    def test_returns_none_if_the_cache_dir_does_not_exist(self):
        self.assertFalse(os.path.isdir(self.test_cache_home))  # Sanity check

        image_id = "test-image-3"
        image_data = giphy.load_cached_image(image_id)

        self.assertIsNone(image_data)

    def test_caches_a_file(self):
        self.assertFalse(os.path.isdir(self.test_cache_home))  # Sanity check

        image_id = "heart1"
        giphy.cache_image(image_id, b64decode(utils.test_image_base64))

        # Ensure the cache dir now exists, and the gif exists in it or a subdirectory
        file_count = self.count_cached_files("%s.gif" % image_id)
        self.assertEqual(file_count, 1)

    def test_works_if_the_cache_dir_already_exists(self):
        image_id = "heart2"
        cache_dir, cache_path = giphy.get_cache_paths(image_id)
        os.makedirs(cache_dir)
        self.assertTrue(os.path.isdir(cache_dir))     # Sanity check
        self.assertFalse(os.path.exists(cache_path))  # Sanity check

        file_count = self.count_cached_files("%s.gif" % image_id)
        self.assertEqual(file_count, 0)  # Sanity check

        giphy.cache_image(image_id, b64decode(utils.test_image_base64))

        self.assertTrue(os.path.exists(cache_path))
        file_count = self.count_cached_files("%s.gif" % image_id)
        self.assertEqual(file_count, 1)

    def test_errors_if_creating_the_cache_directory_fails(self):
        original_makedirs_fn = os.makedirs
        os.makedirs = create_autospec(os.makedirs, side_effect=OSError("splat"))

        try:
            with self.assertRaises(OSError):
                image_id = "heart3"
                giphy.cache_image(image_id, b64decode(utils.test_image_base64))
        finally:
            os.makedirs = original_makedirs_fn

    def test_carries_on_if_writing_a_temp_file_fails(self):
        original_fsync_fn = giphy.fsync
        giphy.fsync = create_autospec(giphy.fsync, side_effect=OSError("erk!"))

        try:
            image_id = "heart4"
            giphy.cache_image(image_id, b64decode(utils.test_image_base64))

            # It should clean up the temp file, if it got as far as creating it before failing
            self.assertEqual(self.count_cached_files("*"), 0)
        finally:
            giphy.fsync = original_fsync_fn

    def test_carries_on_if_renaming_a_temp_file_fails(self):
        original_replace_fn = os.replace
        os.replace = create_autospec(os.replace, side_effect=OSError("d'oh!"))

        try:
            image_id = "heart5"
            giphy.cache_image(image_id, b64decode(utils.test_image_base64))

            # It should clean up the temp file
            self.assertEqual(self.count_cached_files("*"), 0)
        finally:
            os.replace = original_replace_fn


if __name__ == "__main__":
    unittest.main()
