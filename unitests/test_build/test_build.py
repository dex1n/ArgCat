from argcat import ArgCat
from ..argcat_unit_test import ArgCatUnitTest
from argparse import _StoreTrueAction, _ArgumentGroup, _MutuallyExclusiveGroup

class TestBuild(ArgCatUnitTest):
    def setUp(self):
        self._argcat = ArgCat()
        
    def test_normal_build(self) -> None:
        with self._argcat.build() as builder:
            # NOTE: Need to test all ways that argparse.add_argument() supports.
            #def add_argument(self, *args, **kwargs):
            #1. add_argument(dest, ..., name=value, ...)
            #2. add_argument(option_string, option_string, ..., name=value, ...)
        
            # Add argument to the main parser
            builder.new_argument(ignored_by_subparser=True).add('verbose', action='store_true')
            #builder.add_argument('main', 'foo', '-o', '--fooa', action='store_false')  # This is a wrong usage.
            #builder.add_argument('main', '-v', '--verbose', action='store_true')
            # Add group for the sub parser
            builder.add_group(parser_name='process', group_name='process_group_1', 
                              description='This is the first group for process, which is not mutually exclusive', 
                              is_mutually_exclusive=False)
            builder.add_group(parser_name='process', group_name='process_group_2', 
                              description='This is the second group for process, which IS mutually exclusive', 
                              is_mutually_exclusive=True)
            # Add argument to sub parsers
            builder.new_argument('process').add('-f', '--file', 
                                 nargs='?', dest='filename', type='str', group='process_group_1', required=True,
                                 help='The target file name.')
            builder.new_argument('process').add('-s', '--size', nargs='1', dest='filesize', type='int', 
                                 group='process_group_1', required=False, default='1024')
            

        self.assertNotEqual(self._argcat._arg_parsers['main'], None, "`main` parser should be created by default!")
        self.assertNotEqual(self._argcat._arg_parsers['process'], None, "`process` parser should be created!")

        # Check the main parser
        main_parser = self._argcat._arg_parsers['main']

        self.assertEqual(main_parser.name, 'main', "`main` parser's name is incorrect!")
        self.assertEqual(main_parser.dests, ['verbose'], "`main` parser's dests are incorrect!")
        self.assertNotEqual(main_parser.handler_func, None, 
                            "`main` parser's handler should not be None, since it has a default one!")
        self.assertNotEqual(main_parser.parser, None, "`main` parser's argument parser should be valid!")
        self.assertTrue(len(main_parser.arguments) == 1, 
                        "The number of the arguments in the `main` parser should be 1!")

        verbose_argument = main_parser.arguments[0]
        
        # If dest is provided in *args, the `required` is set to True by default.
        # Otherwise, `required` is False by default.         
        self.assertNotEqual(verbose_argument, None, "`main` parser's `verbose` argument should not be None!")

        self.assertEqual(verbose_argument.option_strings, [], "The `option_strings` of `verbose` argument is not correct!")
        self.assertEqual(verbose_argument.required, True, "The `required` of `verbose` argument is wrong!")
        self.assertTrue(isinstance(verbose_argument, _StoreTrueAction), "The `action` of `verbose` argument is wrong!")
        
        # Check the sub parser `process`
        process_parser = self._argcat._arg_parsers['process']
        
        self.assertEqual(process_parser.name, 'process', "`process` parser's name is incorrect!")
        self.assertEqual(process_parser.dests, ['filename', 'filesize'], "`process` parser's dests are incorrect!")
        self.assertEqual(process_parser.handler_func, None, "`process` parser's handler should be None!")
        self.assertNotEqual(process_parser.parser, None, "`process` parser's argument parser should be valid!")
        self.assertTrue(len(process_parser.arguments) == 2, 
                        "The number of the arguments in the `process` parser should be 2!")
        
        # Check the first argument of `process` parser: filename
        first_matches = [arg for arg in process_parser.arguments if arg.dest == 'filename']
        
        self.assertTrue(len(first_matches) == 1, "The `filename` argument should be only one!")
        
        filename_arg = first_matches[0]
        
        self.assertEqual(filename_arg.nargs, '?', "The `nargs` of `filename` argument should be `?`!")
        self.assertTrue(filename_arg.type is str, "The `type` of `filename` argument should be str!")
        self.assertEqual(filename_arg.option_strings, ['-f', '--file'], 
                         "The `option_strings` of `filename` argument is not correct!")
        self.assertEqual(filename_arg.metavar, None, "The `metavar` of `filename` argument is wrong!")
        self.assertEqual(filename_arg.help, "The target file name.", "The `help` of `filename` argument is wrong!")
        self.assertEqual(filename_arg.required, True, "The `required` of `filename` argument is wrong!")
        self.assertEqual(filename_arg.default, None, "The `default` of `filename` argument should be None!")
        
        group_name = process_parser.additional_arguments_info[filename_arg.dest]['group']
        self.assertEqual(group_name, 'process_group_1', "The `group` of `filename` argument is wrong!")
        
        # Check the second argument of `process` parser: filesize
        second_matches = [arg for arg in process_parser.arguments if arg.dest == 'filesize']
        
        self.assertTrue(len(second_matches) == 1, "The `filesize` argument should be only one!")
        
        filesize_arg = second_matches[0]
        
        self.assertEqual(filesize_arg.nargs, '1', "The `nargs` of `filesize` argument should be `1`!")
        self.assertTrue(filesize_arg.type is int, "The `type` of `filesize` argument should be int!")
        self.assertEqual(filesize_arg.option_strings, ['-s', '--size'], 
                         "The `option_strings` of `filesize` argument is not correct!")
        self.assertEqual(filesize_arg.metavar, None, "The `metavar` of `filesize` argument is wrong!")
        self.assertEqual(filesize_arg.default, '1024', "The `default` of `filesize` is incorrect!")
        self.assertEqual(filesize_arg.required, False, "The `required` of `filesize` argument is wrong!")
        
        # Test groups
        
        group_name = process_parser.additional_arguments_info[filename_arg.dest]['group']
        self.assertEqual(group_name, 'process_group_1', "The `group` of `filename` argument is wrong!")
        
        group_name = process_parser.additional_arguments_info[filesize_arg.dest]['group']
        self.assertEqual(group_name, 'process_group_1', "The `group` of `filename` argument is wrong!")
        
        self.assertEqual(len(process_parser.groups), 2, "The number of groups for `process` parser is wrong!")
        
        process_group_1 = process_parser.groups['process_group_1']
        self.assertTrue(isinstance(process_group_1, _ArgumentGroup), 
                        "The type of the first group for `process` parser is wrong!")
        
        process_group_2 = process_parser.groups['process_group_2']
        self.assertTrue(isinstance(process_group_2, _MutuallyExclusiveGroup), 
                        "The type of the second group for `process` parser is wrong!")
        
        # Test handlers
        
        # Set a handler with incorrect parameters
        def process_handler_with_incorrect_parameters(filename: str, type: int) -> str:
            return f"process_handler: {filename}, {type}"
        self._argcat.add_parser_handler(parser_name='process', handler=process_handler_with_incorrect_parameters)
        
        self.assertEqual(process_parser.handler_func, None, 
                         "`process` parser's handler should be None after receiving an incorrect handler!")
        
        # Set a handler with correct paramters
        def process_handler_with_correct_parameters(filename: str, filesize: int) -> str:
            return f"process_handler: {filename}, {filesize}"
        self._argcat.add_parser_handler(parser_name='process', handler=process_handler_with_correct_parameters)
        
        self.assertEqual(process_parser.handler_func, process_handler_with_correct_parameters, 
                         "`process` parser's handler should be valid after receiving a correct handler!")
        
        