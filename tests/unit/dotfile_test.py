import os.path
import random
import shutil
import string
import unittest
import utils
from pathlib import Path

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class TestDotfile(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.temp_dir = None
        self.original_home = None
        self.original_userprofile = None
        self.original_xdg_config_home = None

    def setUp(self):
        self.original_home = os.environ.get("HOME")
        self.original_userprofile = os.environ.get("USERPROFILE")
        self.original_xdg_config_home = os.environ.get("XDG_CONFIG_HOME")

        test_dir_name = "giphizer-test-%s" % "".join(random.choices(string.ascii_lowercase, k=9))
        self.temp_dir = os.path.join(os.environ.get("TMPDIR"), test_dir_name)

        os.environ["HOME"] = self.temp_dir
        os.environ["USERPROFILE"] = self.temp_dir
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self.temp_dir, ".xdg_config")

        os.makedirs(self.temp_dir)
        os.makedirs(os.path.join(os.environ.get("XDG_CONFIG_HOME"), "giphy"))
        os.makedirs(os.path.join(self.temp_dir, ".config", "giphy"))

    def tearDown(self):
        utils.restore_environment_variable("HOME", self.original_home)
        utils.restore_environment_variable("USERPROFILE", self.original_userprofile)
        utils.restore_environment_variable("XDG_CONFIG_HOME", self.original_xdg_config_home)

        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def write_dotfile(self, pretty_path, content):
        dotfile_path = os.path.expanduser(pretty_path)
        if dotfile_path.startswith(self.temp_dir):
            with open(dotfile_path, "w+") as fake_dotfile:
                fake_dotfile.write(content)
                fake_dotfile.write("\n")

    def remove_dotfile(self, pretty_path):
        dotfile_path = os.path.expanduser(pretty_path)
        if dotfile_path.startswith(self.temp_dir):
            Path(dotfile_path).unlink(missing_ok=True)

    def test_reads_from_a_dotfile(self):
        self.write_dotfile("~/.giphyrc", "--max-cache=42")
        self.write_dotfile("~/.xdg_config/giphy/giphyrc", "--max-cache=43")
        self.write_dotfile("~/.config/giphy/giphyrc", "--max-cache=44")

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, ["--max-cache=42"])

        self.remove_dotfile("~/.giphyrc")

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, ["--max-cache=43"])

        self.remove_dotfile("~/.xdg_config/giphy/giphyrc")
        os.environ.pop("XDG_CONFIG_HOME", None)

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, ["--max-cache=44"])

    def test_ignores_comment_lines_in_a_dotfile(self):
        self.write_dotfile("~/.giphyrc", "# comment\n\n\n--max-cache=88\n# --max-cache=99")
        args, _ = giphy.read_dotfile()
        self.assertEqual(args, ["--max-cache=88"])

    def test_ignores_a_dotfile_without_read_permission(self):
        self.write_dotfile("~/.giphyrc", "--show-url")
        dotfile_path = os.path.expanduser("~/.giphyrc")
        os.chmod(dotfile_path, 0)

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, [])

    def test_ignores_a_directory_where_a_dotfile_should_be(self):
        dotfile_path = os.path.expanduser("~/.giphyrc")
        os.makedirs(dotfile_path)

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, [])

    def test_ignores_a_symlink_to_a_device_where_a_dotfile_should_be(self):
        dotfile_path = os.path.expanduser("~/.giphyrc")
        os.symlink("/dev/urandom", dotfile_path)

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, [])

    def test_ignores_a_broken_symlink_where_a_dotfile_should_be(self):
        dotfile_path = os.path.expanduser("~/.giphyrc")
        os.symlink("/does-not-exist", dotfile_path)

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, [])

    def test_follows_a_symlink_to_a_dotfile(self):
        self.write_dotfile("~/actual-giphyrc", "--force --max-rating=pg")
        relative_link_path = os.path.expanduser("~/relative-link")
        os.symlink("actual-giphyrc", relative_link_path)
        os.symlink(relative_link_path, os.path.expanduser("~/.giphyrc"))

        args, _ = giphy.read_dotfile()
        self.assertEqual(args, ["--force", "--max-rating=pg"])


if __name__ == "__main__":
    unittest.main()
