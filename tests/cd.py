"""Change directory using context manager syntax ('with').

Based on https://stackoverflow.com/questions/431684/how-do-i-cd-in-python

EXAMPLE:
with cd("/tmp"):
    print(os.getcwd())

"""
import os


class cd(object):
    """Change directory using context manager syntax ('with')."""

    # The name "cd" makes more sense than "CD"
    # pylint: disable=invalid-name
    #
    # We need to inherit from object for Python 2 compantibility
    # https://python-future.org/compatible_idioms.html#custom-class-behaviour
    # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(self, new_pwd):
        """Save future pwd."""
        self.new_pwd = os.path.expanduser(new_pwd)
        self.old_pwd = None

    def __enter__(self):
        """Save old pwd and change directory."""
        self.old_pwd = os.getcwd()
        os.chdir(self.new_pwd)

    def __exit__(self, etype, value, traceback):
        """Change back to old pwd."""
        os.chdir(self.old_pwd)
