import os
import os.path
import platform
import unittest
import utils

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class TestCacheDir(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.original_system_fn = None
        self.original_xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        self.original_localappdata = os.environ.get("LOCALAPPDATA")

    def setUp(self):
        return  # All relevant setup is done in __init__()

    def tearDown(self):
        if self.original_system_fn:
            platform.system = self.original_system_fn
            self.original_system_fn = None

        utils.restore_environment_variable("XDG_CACHE_HOME", self.original_xdg_cache_home)
        utils.restore_environment_variable("LOCALAPPDATA", self.original_localappdata)

    def check_cache_paths(self, expected_in_cache_dir):
        """Utility method for checking cache directory use."""
        image_id = "d8MQjoGL"
        utils.restore_environment_variable("XDG_CACHE_HOME", None)
        cache_dir, cache_path = giphy.get_cache_paths(image_id)

        self.assertIn(expected_in_cache_dir, cache_dir)
        self.assertIn(cache_dir, cache_path)
        self.assertIn(image_id, cache_path)

        os.environ["XDG_CACHE_HOME"] = "%s/.foo/cache" % (os.environ.get("HOME") or "/home")
        cache_dir, cache_path = giphy.get_cache_paths(image_id)

        self.assertIn("/.foo/cache/giphizer", cache_dir)
        self.assertIn(cache_dir, cache_path)
        self.assertIn(image_id, cache_path)

    def test_uses_a_dot_directory_in_the_home_directory_by_default(self):
        self.original_system_fn = platform.system
        platform.system = lambda: "Linux"
        self.check_cache_paths("%s/.cache" % (os.environ.get("HOME") or "/home"))

    def test_uses_ideomatic_cache_dir_on_mac(self):
        self.original_system_fn = platform.system
        platform.system = lambda: "Darwin"
        self.check_cache_paths("/Library/Caches/Giphizer")

    def test_uses_ideomatic_cache_dir_on_windows(self):
        self.original_system_fn = platform.system
        platform.system = lambda: "Windows"
        os.environ["LOCALAPPDATA"] = "C:\\foo"
        self.check_cache_paths("%s\\%s" % ("C:\\foo", "Giphizer\\cache"))


if __name__ == "__main__":
    unittest.main()
