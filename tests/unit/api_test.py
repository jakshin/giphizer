import argparse
import http.client
import os.path
import re
import unittest
import urllib.error
import utils
from unittest.mock import create_autospec
from utils import AnyStringContaining, AnyStringMatching

this_dir = os.path.dirname(os.path.abspath(__file__))
giphy = utils.import_path("%s/../../giphy" % this_dir)

unused_by_mock = None


def get_mock_args(mode="best", topic="happy fun times"):
    return argparse.Namespace(
        topic=topic,
        mode=mode,
        max_rating=None,
        max_size=None,
    )


class TestApiUsage(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.original_open_url_fn = None

    def setUp(self):
        utils.set_up_function_mocks(giphy, "choose_image", "get_giphy_api_err_msg")

        mock_http_response = create_autospec(http.client.HTTPResponse)
        with open("%s/api_sample.json" % this_dir, "r") as sample_api_response_file:
            mock_http_response.read.return_value = sample_api_response_file.read()

        if self.original_open_url_fn is None:
            self.original_open_url_fn = giphy.open_url
        giphy.open_url = create_autospec(giphy.open_url, return_value=mock_http_response)

    def tearDown(self):
        utils.tear_down_function_mocks(giphy)
        if self.original_open_url_fn is not None:
            giphy.open_url = self.original_open_url_fn

    def test_returns_image_info(self):
        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            image_info = giphy.choose_image(args)

            self.assertIsInstance(image_info["id"], str)
            self.assertIsInstance(image_info["page_url"], str)
            self.assertIsInstance(image_info["rating"], str)
            self.assertIsInstance(image_info["username"], str)
            self.assertIsInstance(image_info["image_url"], str)
            self.assertIsInstance(image_info["width"], int)
            self.assertIsInstance(image_info["height"], int)
            self.assertIsInstance(image_info["size"], int)

    def test_uses_the_topic_to_choose_an_image(self):
        topic = "blah-blah-blah"

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode, topic)
            giphy.choose_image(args)
            giphy.open_url.assert_called_with(AnyStringContaining(topic))

    def test_uses_the_right_giphy_api_endpoint(self):
        args = get_mock_args(mode="id", topic="JJptubufblBJP3E3DK")
        giphy.choose_image(args)
        giphy.open_url.assert_called_with(AnyStringContaining("/JJptubufblBJP3E3DK?"))

        args = get_mock_args(mode="random", topic="what what")
        giphy.choose_image(args)
        giphy.open_url.assert_called_with(AnyStringContaining("/random?"))
        giphy.open_url.assert_called_with(AnyStringContaining("&tag=what+what"))

        args = get_mock_args(mode="best", topic="hey hey")
        giphy.choose_image(args)
        giphy.open_url.assert_called_with(AnyStringContaining("/translate?"))
        giphy.open_url.assert_called_with(AnyStringContaining("&s=hey+hey"))

    def test_uses_the_max_rating_option(self):
        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            args.max_rating = "pg"
            giphy.choose_image(args)
            giphy.open_url.assert_called_with(AnyStringContaining("&rating=pg"))

    def test_uses_the_max_size_option(self):
        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            image_info = giphy.choose_image(args)
            self.assertEqual(image_info["size"], 2072738)  # From api_sample.json

            args.max_size = "2MB"
            image_info = giphy.choose_image(args)
            self.assertEqual(image_info["size"], 1706369)

            args.max_size = "5MB"
            image_info = giphy.choose_image(args)
            self.assertEqual(image_info["size"], 2052500)

            args.max_size = "8MB"
            image_info = giphy.choose_image(args)
            self.assertEqual(image_info["size"], 2062600)

    def test_uses_api_key_from_environment(self):
        fake_api_key = "fake-api-key"
        os.environ["GIPHY_API_KEY"] = fake_api_key

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            giphy.choose_image(args)
            giphy.open_url.assert_called_with(AnyStringContaining("api_key=%s" % fake_api_key))

    def test_falls_back_to_default_api_key(self):
        original_api_key = os.environ.get("GIPHY_API_KEY")
        os.environ.pop("GIPHY_API_KEY", None)

        try:
            for mode in ["id", "random", "best"]:
                args = get_mock_args(mode)
                giphy.choose_image(args)
                giphy.open_url.assert_called_with(AnyStringMatching("api_key=[A-Za-z0-9]{32}"))
        finally:
            if original_api_key:
                os.environ["GIPHY_API_KEY"] = original_api_key

    def test_raises_an_error_when_using_the_giphy_api_fails(self):
        giphy.open_url.side_effect = urllib.error.URLError("something went wrong")

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            with self.assertRaises(giphy.GiphizerException):
                giphy.choose_image(args)

    def test_raises_an_error_when_the_giphy_api_returns_invalid_json(self):
        mock_http_response = create_autospec(http.client.HTTPResponse)
        mock_http_response.read.return_value = "not-valid-json"

        if self.original_open_url_fn is not None:
            giphy.open_url = self.original_open_url_fn
        giphy.open_url = create_autospec(giphy.open_url, return_value=mock_http_response)

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            with self.assertRaises(giphy.GiphizerException):
                giphy.choose_image(args)

    def test_raises_an_error_when_the_giphy_api_returns_missing_data(self):
        # Remove every "url" value from the sample API-response JSON
        mock_http_response = giphy.open_url.return_value
        mock_http_response.read.return_value = re.sub(r'\s*"url":\s*[^\n]+', "",
                                                      mock_http_response.read.return_value)

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            with self.assertRaises(giphy.GiphizerException):
                giphy.choose_image(args)

    def test_raises_an_error_when_the_giphy_api_returns_invalid_number(self):
        # Replace every numeric "height" value with a non-number in the sample API-response JSON
        mock_http_response = giphy.open_url.return_value
        mock_http_response.read.return_value = re.sub(r'"height":\s*"\d+"', '"height": "tall"',
                                                      mock_http_response.read.return_value)

        for mode in ["id", "random", "best"]:
            args = get_mock_args(mode)
            with self.assertRaises(giphy.GiphizerException):
                giphy.choose_image(args)


if __name__ == "__main__":
    unittest.main()
