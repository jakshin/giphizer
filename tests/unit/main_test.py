import argparse
import os.path
import unittest
import utils
from base64 import b64decode
from unittest.mock import create_autospec

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class TestMain(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.original_fns = {}

    def setUp(self):
        fn_names = ["stdout", "stderr", "parse_arguments", "read_dotfile", "choose_image", "download_image",
                    "check_image_capability", "display_image", "display_logo", "is_hidpi_screen",
                    "load_cached_image", "cache_image", "clean_cache"]
        for fn_name in fn_names:
            self.original_fns[fn_name] = getattr(giphy, fn_name)

        giphy.stdout = create_autospec(giphy.stdout)
        giphy.stderr = create_autospec(giphy.stderr)

        giphy.parse_arguments = create_autospec(giphy.parse_arguments, return_value=argparse.Namespace(
            topic="",
            help=False,
            mode="best",
            max_rating=None,
            max_size=None,
            max_cache=100,
            force=False,
            show_url=False,
        ))

        giphy.read_dotfile = create_autospec(giphy.read_dotfile, return_value=[[], None])

        giphy.choose_image = create_autospec(giphy.choose_image, return_value={
            "id": utils.test_image_id,
            "page_url": utils.test_image_page_url,
            "rating": "g",
            "username": "someuser",
            "image_url": utils.test_image_url,
            "width": 10,
            "height": 8,
            "size": 169,
        })

        gif_bytes = b64decode(utils.test_image_base64)
        giphy.download_image = create_autospec(giphy.download_image, return_value=gif_bytes)

        giphy.check_image_capability = create_autospec(giphy.check_image_capability, return_value=None)
        giphy.display_image = create_autospec(giphy.display_image)
        giphy.display_logo = create_autospec(giphy.display_logo)
        giphy.is_hidpi_screen = create_autospec(giphy.is_hidpi_screen, return_value=True)

        giphy.load_cached_image = create_autospec(giphy.load_cached_image, return_value=gif_bytes)
        giphy.cache_image = create_autospec(giphy.cache_image)
        giphy.clean_cache = create_autospec(giphy.clean_cache)

    def tearDown(self):
        for fn_name, fn in self.original_fns.items():
            setattr(giphy, fn_name, fn)

    def test_returns_without_doing_anything_more_after_displaying_usage_info(self):
        # parse_arguments() returns None in any case where it's displayed usage info;
        # it therefore always returns None in any case where args.help would be True
        giphy.parse_arguments.return_value = None

        return_value = giphy.main()
        giphy.parse_arguments.assert_called()  # Sanity check

        giphy.read_dotfile.assert_not_called()
        giphy.choose_image.assert_not_called()
        giphy.download_image.assert_not_called()
        giphy.check_image_capability.assert_not_called()
        giphy.display_image.assert_not_called()
        giphy.display_logo.assert_not_called()
        giphy.is_hidpi_screen.assert_not_called()
        giphy.load_cached_image.assert_not_called()
        giphy.cache_image.assert_not_called()
        giphy.clean_cache.assert_not_called()
        self.assertEqual(return_value, 0)

    def test_returns_an_error_without_displaying_an_image_if_the_terminal_cannot_handle_it(self):
        # check_image_capability() returns None if -f/--force was passed
        giphy.check_image_capability.return_value = "bleh"

        return_value = giphy.main()
        giphy.check_image_capability.assert_called()  # Sanity check

        giphy.display_image.assert_not_called()
        self.assertGreater(return_value, 0)
        self.assertIn("bleh", giphy.stderr.call_args.args[0])

    def test_chooses_an_image(self):
        giphy.main()
        giphy.choose_image.assert_called()

    def test_tries_to_load_a_cached_image(self):
        giphy.main()
        giphy.load_cached_image.assert_called_with(utils.test_image_id)

    def test_does_not_download_an_image_if_it_was_found_in_cache(self):
        giphy.main()
        giphy.download_image.assert_not_called()

    def test_downloads_an_image_if_it_was_not_found_in_cache(self):
        giphy.load_cached_image.return_value = None
        giphy.main()
        giphy.download_image.assert_called_with(utils.test_image_url)

    def test_caches_a_downloaded_image_iff_it_should(self):
        giphy.load_cached_image.return_value = None
        giphy.parse_arguments.return_value.max_cache = 0
        giphy.main()
        giphy.download_image.assert_called()  # Sanity check
        giphy.cache_image.assert_not_called()

        giphy.parse_arguments.return_value.max_cache = 100
        giphy.main()
        giphy.cache_image.assert_called()

    def test_displays_an_image(self):
        return_value = giphy.main()

        giphy.display_image.assert_called()
        self.assertIn(utils.test_image_base64, giphy.display_image.call_args.args[0])
        self.assertEqual(utils.test_image_url, giphy.display_image.call_args.args[3])
        self.assertEqual(return_value, 0)

    def test_displays_a_url_below_the_image_iff_it_should(self):
        giphy.parse_arguments.return_value.show_url = True
        giphy.main()
        giphy.stdout.assert_called_with(utils.test_image_page_url)

    def test_displays_a_logo_image(self):
        giphy.main()
        giphy.display_logo.assert_called()

    def test_cleans_its_cache(self):
        giphy.main()
        giphy.clean_cache.assert_called()

    def test_returns_an_error_if_choosing_an_image_fails(self):
        giphy.choose_image.side_effect = giphy.GiphizerException("blah")

        return_value = giphy.main()

        self.assertGreater(return_value, 0)
        self.assertIn("blah", giphy.stderr.call_args.args[0])

    def test_returns_an_error_if_downloading_an_image_fails(self):
        giphy.load_cached_image.return_value = None
        giphy.download_image.side_effect = giphy.GiphizerException("bluh")

        return_value = giphy.main()

        self.assertGreater(return_value, 0)
        self.assertIn("bluh", giphy.stderr.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
