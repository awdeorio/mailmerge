"""Change directory using context manager syntax ('with').

Based on https://stackoverflow.com/questions/431684/how-do-i-cd-in-python

EXAMPLE:
with cd("/tmp"):
    print(os.getcwd())

"""
import os


class cd:
    """Change directory using context manager syntax ('with')."""

    # The name "cd" makes more sense than "CD"
    # pylint: disable=invalid-name

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
