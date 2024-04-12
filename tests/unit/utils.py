import importlib.machinery
import importlib.util
import os
import re
import sys


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


def restore_environment_variable(name, original_value):
    """Restores an environment variable to a previous value, unsetting it if needed."""
    if original_value is None:
        unset_environment_variable(name)
    else:
        os.environ[name] = original_value


def unset_environment_variable(name):
    """Unsets an environment variable."""
    os.environ.pop(name, None)


class AnyStringContaining(str):
    """
    A string that's "equal to" any other string it's a substring of.
    For use with .assert_called_with() etc.
    """
    def __eq__(self, other):
        return self in other


class AnyStringMatching(str):
    """
    A string that's "equal to" any other string it matches as a regex.
    This string should contain the regex pattern.
    For use with .assert_called_with() etc.
    """
    def __eq__(self, other):
        return re.search(str(self), other) is not None
