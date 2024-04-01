import argparse
import os
import importlib.machinery
import importlib.util
import sys
from base64 import b64decode
from unittest.mock import create_autospec

original_fns = {}

test_image_id = "TestImageID"
test_image_url = "https://media3.giphy.com/media/TestImageID/giphy.gif?cid=abc123"
test_image_page_url = "https://giphy.com/gifs/someuser-foo-bar-TestImageID"
test_image_base64 = "R0lGODdhCgAIAMQAAAAAAMxHR8lKStBPT81SUtFUVKpVVdZbW91lZd5paeBqauVzc+yAgPCEhPeO" \
                    "jv///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAkA" \
                    "ABAALAAAAAAKAAgAAAUmIAQdh0iKEOI4SLIiULHOczEw9NoQY86iqtkCJVKsFgWiCKFIikIAOw=="


def import_path(path):
    """
    Imports from an arbitrary path.
    We use this to import the extensionless 'giphy' script.
    From https://stackoverflow.com/a/56090741.
    """
    module_name = str(os.path.basename(path).replace('-', '_'))
    spec = importlib.util.spec_from_loader(
        module_name,
        importlib.machinery.SourceFileLoader(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def set_up_function_mocks(giphy, *exceptions):
    # Save original functions so we can restore them later
    global original_fns
    if len(original_fns) == 0:
        fn_names = ["stdout", "stderr", "parse_arguments", "read_dotfile", "choose_image", "download_image",
                    "check_image_capability", "display_image", "display_logo", "is_hidpi_screen",
                    "load_cached_image", "cache_image", "clean_cache"]
        for fn_name in fn_names:
            original_fns[fn_name] = getattr(giphy, fn_name)

    # Initialize some test data
    global test_image_id, test_image_url, test_image_base64
    gif_bytes = b64decode(test_image_base64)

    # Mock functions
    giphy.stdout = create_autospec(giphy.stdout)
    giphy.stderr = create_autospec(giphy.stderr)

    if "parse_arguments" not in exceptions:
        giphy.parse_arguments = create_autospec(giphy.parse_arguments, return_value=argparse.Namespace(
            topic=[],
            help=False,
            mode="best",
            max_rating=None,
            max_size=None,
            max_cache=100,
            force=False,
            show_url=False,
        ))

    if "read_dotfile" not in exceptions:
        giphy.read_dotfile = create_autospec(giphy.read_dotfile, return_value=[[], None])

    if "choose_image" not in exceptions:
        giphy.choose_image = create_autospec(giphy.choose_image, return_value={
            "id": test_image_id,
            "page_url": test_image_page_url,
            "rating": "g",
            "username": "someuser",
            "image_url": test_image_url,
            "width": 10,
            "height": 8,
            "size": 169,
        })

    if "download_image" not in exceptions:
        giphy.download_image = create_autospec(giphy.download_image, return_value=gif_bytes)

    if "check_image_capability" not in exceptions:
        giphy.check_image_capability = create_autospec(giphy.check_image_capability, return_value=None)
    if "display_image" not in exceptions:
        giphy.display_image = create_autospec(giphy.display_image)
    if "display_logo" not in exceptions:
        giphy.display_logo = create_autospec(giphy.display_logo)
    if "is_hidpi_screen" not in exceptions:
        giphy.is_hidpi_screen = create_autospec(giphy.is_hidpi_screen, return_value=True)

    if "load_cached_image" not in exceptions:
        giphy.load_cached_image = create_autospec(giphy.load_cached_image, return_value=gif_bytes)
    if "cache_image" not in exceptions:
        giphy.cache_image = create_autospec(giphy.cache_image)
    if "clean_cache" not in exceptions:
        giphy.clean_cache = create_autospec(giphy.clean_cache)


def tear_down_function_mocks(giphy):
    global original_fns
    for fn_name, fn in original_fns.items():
        setattr(giphy, fn_name, fn)
