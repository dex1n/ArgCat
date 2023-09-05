"""ArgCatUnitTest"""
import unittest
import os
import sys

class ArgCatUnitTest(unittest.TestCase):
    """ArgCast Base UnitTest Class.
    Any UnitTest should inherit this.
    """
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self._cur_path = os.path.dirname(os.path.abspath(sys.modules[self.__module__].__file__))

    def abs_path_of_test_file(self, file_name: str) -> str:
        """Retrieve the absolute path of this test file."""
        return os.path.join(self._cur_path, file_name)
