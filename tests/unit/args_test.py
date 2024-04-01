import os.path
import random
import shutil
import string
import unittest
import utils
from io import StringIO
from unittest.mock import create_autospec, patch

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class AnyStringContaining(str):
    def __eq__(self, other):
        # This string is "equal to" any other string it's a substring of
        return self in other


class TestArgs(unittest.TestCase):
    def setUp(self):
        utils.set_up_function_mocks(giphy, "parse_arguments", "read_dotfile")

    def tearDown(self):
        utils.tear_down_function_mocks(giphy)

    def test_reads_from_a_dotfile(self):
        args = giphy.parse_arguments(["foo"])
        self.assertFalse(args.show_url)  # Sanity check

        temp_dir_name = "giphizer-test-%s" % "".join(random.choices(string.ascii_lowercase, k=10))
        temp_dir = os.path.join(os.environ.get("TMPDIR"), temp_dir_name)
        original_home = os.environ.get("HOME")
        original_userprofile = os.environ.get("USERPROFILE")

        try:
            os.makedirs(temp_dir)
            dotfile_path = os.path.join(temp_dir, ".giphyrc")
            with open(dotfile_path, "w+") as fake_dotfile:
                fake_dotfile.write("--show-url")

            os.environ["HOME"] = temp_dir
            os.environ["USERPROFILE"] = temp_dir

            args = giphy.parse_arguments(["foo"])
            self.assertTrue(args.show_url)
        finally:
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)

            if original_home:
                os.environ["HOME"] = original_home
            else:
                os.environ.pop("HOME", None)

            if original_userprofile:
                os.environ["USERPROFILE"] = original_userprofile
            else:
                os.environ.pop("USERPROFILE", None)

    def test_overrides_dotfile_options_with_command_line_options(self):
        original_read_dotfile_fn = giphy.read_dotfile
        try:
            giphy.read_dotfile = create_autospec(giphy.read_dotfile, return_value=[["--max-cache=9999"], "~/.dot"])
            args = giphy.parse_arguments(["foo"])
            self.assertEqual(args.max_cache, 9999)  # Sanity check

            args = giphy.parse_arguments(["foo", "--max-cache=9998"])
            self.assertEqual(args.max_cache, 9998)
        finally:
            giphy.read_dotfile = original_read_dotfile_fn

    def test_errors_when_an_invalid_argument_is_passed_in_a_dotfile(self):
        original_read_dotfile_fn = giphy.read_dotfile
        try:
            giphy.read_dotfile = create_autospec(giphy.read_dotfile, return_value=[["--foo=goo"], "~/.dot"])

            with self.assertRaises(giphy.GiphizerException):
                args = giphy.parse_arguments(["sweet"])

                self.assertIsNone(args)
                giphy.stderr.assert_called_once_with(AnyStringContaining("Error in ~/.dot:"))
                giphy.stderr.assert_called_once_with(AnyStringContaining("--foo=goo"))
                giphy.stderr.assert_called_once_with(AnyStringContaining("giphy --help"))
        finally:
            giphy.read_dotfile = original_read_dotfile_fn

    def test_errors_when_an_invalid_argument_is_passed_on_the_command_line(self):
        original_read_dotfile_fn = giphy.read_dotfile
        try:
            giphy.read_dotfile = create_autospec(giphy.read_dotfile, return_value=[[], "~/.dot"])

            with self.assertRaises(giphy.GiphizerException):
                args = giphy.parse_arguments(["sweet", "--foo=goo"])

                self.assertIsNone(args)
                giphy.stderr.assert_called_once_with(AnyStringContaining("Error:"))
                giphy.stderr.assert_called_once_with(AnyStringContaining("--foo=goo"))
                giphy.stderr.assert_called_once_with(AnyStringContaining("giphy --help"))
                giphy.stderr.assert_not_called_with(AnyStringContaining("~/.dot"))
        finally:
            giphy.read_dotfile = original_read_dotfile_fn

    def test_normalizes_whitespace_in_the_topic(self):
        args = giphy.parse_arguments(["   something  ", "\t and more\n", "and  \v  even \t  more"])
        self.assertEqual(args.topic, "something and more and even more")

    def test_prevents_negative_max_cache(self):
        args = giphy.parse_arguments(["woot"])
        self.assertEqual(args.max_cache, 100)  # Default value

        args = giphy.parse_arguments(["woot", "--max-cache=-42"])
        self.assertEqual(args.max_cache, 0)

    def test_limits_usage_info_to_100_columns(self):
        def stdout_mock(*_):
            columns = os.environ.get("COLUMNS")
            self.assertEqual(columns, expected_columns)

        original_stdout_fn = giphy.stdout
        original_columns = os.environ.get("COLUMNS")

        try:
            giphy.stdout = stdout_mock

            with patch('sys.stdout', new=StringIO()):
                os.environ.pop("COLUMNS", None)
                expected_columns = "100"
                giphy.parse_arguments(["--help"])

                os.environ["COLUMNS"] = "120"
                expected_columns = "100"
                giphy.parse_arguments(["--help"])

                os.environ["COLUMNS"] = "90"
                expected_columns = "90"
                giphy.parse_arguments(["--help"])
        finally:
            giphy.stdout = original_stdout_fn
            if original_columns:
                os.environ["COLUMNS"] = original_columns
            else:
                os.environ.pop("COLUMNS", None)

    def test_appends_a_giphy_logo_to_usage_info(self):
        with patch('sys.stdout', new=StringIO()):
            giphy.check_image_capability.return_value = None  # Terminal handles images, or -f/--force
            giphy.parse_arguments(["--help"])
            giphy.display_logo.assert_called()

            giphy.display_logo.reset_mock()
            giphy.check_image_capability.return_value = "some reason images aren't supported"
            giphy.parse_arguments(["--help"])
            giphy.display_logo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
