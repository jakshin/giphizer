import os.path
import unittest
import utils

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)


class TestMain(unittest.TestCase):
    def setUp(self):
        utils.set_up_function_mocks(giphy)

    def tearDown(self):
        utils.tear_down_function_mocks(giphy)

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
