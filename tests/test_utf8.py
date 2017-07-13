"""Test mailmerge UTF8 compatibility."""
import unittest
import mailmerge


class TestUTF8(unittest.TestCase):
    def test_utf8(self):
        print("hello world")
