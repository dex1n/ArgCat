from argcat import ArgCat, _ManifestConstants
from ..argcat_unit_test import ArgCatUnitTest

class TestLoad(ArgCatUnitTest):
    def setUp(self):
        self._argcat = ArgCat()

    def test_load_normal(self):
        self._argcat.load(self.abs_path_of_test_file("normal.yml"))
        # Total size
        self.assertEqual(len(self._argcat._arg_parsers), 4, 'Incorrect size of all parsers.')
        # Parsers
        # -- main parser
        self.assertIsNotNone(self._argcat._arg_parsers['main'], "'main' parser missing.")
        main_parser = self._argcat._arg_parsers['main']
        self.assertEqual(main_parser.name, 'main', f"Incorrect parser name {main_parser.name} for 'main' parser")
        self.assertEqual(len(main_parser.arguments), 1, "Incorrect size of arguments for 'main' parser.")
        main_parser_arguments = main_parser.arguments
        self.assertEqual(main_parser_arguments[0].get(_ManifestConstants.DEST, None), 'test', "Incorrect argument DEST for 'main' parser.")
        # -- init parser
        self.assertIsNotNone(self._argcat._arg_parsers['init'], "'init' parser missing.")
        init_parser = self._argcat._arg_parsers['init']
        self.assertEqual(len(init_parser.arguments), 0, "Incorrect size of arguments for 'init' parser.")
        self.assertIsNotNone(self._argcat._arg_parsers['info'], "'info' parser missing.")
        # -- config parser
        self.assertIsNotNone(self._argcat._arg_parsers['config'], "'config' parser missing.")
        config_parser = self._argcat._arg_parsers['config']
        self.assertEqual(len(config_parser.arguments), 2, "Incorrect size of arguments for 'config' parser.")
        self.assertEqual(len(config_parser.groups), 1, "Incorrect size of groups for 'config' parser.")
        # Handler
        self.assertIsNone(self._argcat._arg_parsers['main'].handler_func, "'main' parser handler should be None.")
        self.assertIsNone(self._argcat._arg_parsers['init'].handler_func, "'init' parser handler should be None.")
        self.assertIsNone(self._argcat._arg_parsers['info'].handler_func, "'info' parser handler should be None.")
        self.assertIsNone(self._argcat._arg_parsers['config'].handler_func, "'config' parser handler should be None.")
        # Try to print method.
        self._argcat.print_parsers()

    def test_load_incorrect_file_path(self):
        self._argcat.load(self.abs_path_of_test_file("file_not_exist.yml"))
        # Try to print method.
        self._argcat.print_parsers()
    
    def test_load_empty_file(self):
        self._argcat.load(self.abs_path_of_test_file("empty.yml"))
        # Try to print method.
        self._argcat.print_parsers()
    
    def test_load_incorrect_file(self):
        self._argcat.load(self.abs_path_of_test_file("incorrect.yml"))
# We don't need this and we only run all tests from the root folder.
# This is mainly for the right test file used in the tests.
# if __name__ == '__main__':
#    unittest.main()