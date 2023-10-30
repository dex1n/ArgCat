"""All UnitTests for ArgCat's parse_args()."""
from argcat import ArgCat
from unitests.argcat_unittest import ArgCatUnitTest

class DifferentKindsOfHandlerProvider:
    """A handler provider which gives different kinds of handlers."""
    @classmethod
    @ArgCat.handler(parser_name='info')
    def info_handler(cls, detail: str=None) -> None:
        """A classmethod handler."""
        return f'info {detail}'

    @staticmethod
    @ArgCat.handler(parser_name='init')
    def init_handler() -> None:
        """A staticmethod handler."""
        return 'init'

    @ArgCat.handler(parser_name='config')
    def config_handler(self, name: str=None, user_name: str=None) -> str:
        """A normal method handler."""
        return f"config name = {name}, user_name = {user_name}"

class TestParseArgs(ArgCatUnitTest):
    """TestParseArgs."""
    def setUp(self):
        self._argcat = ArgCat()

    def test_parse_args_with_handler_provider(self) -> None:
        """Test parse_args() with handler provider."""
        with self._argcat.build() as builder:

            # Set basic information
            builder.set_prog_info(prog='Cool program name', description='Awesome description')
            builder.set_subparsers_info(title='The subparsers title',
                                        description='The subparsers description',
                                        help='The subparsers help')

            # Add an exclusive argument for the main parser.
            builder.main_parser().add_exclusive_argument('test', nargs='?', metavar='TEST',
                                                         type=str, help='Just for test')

            # Add a sub parser without any arguments.
            builder.add_subparser('init', help='Initialize something.')

            # Add a sub parser with one argument.
            builder.add_subparser('info', help='Show information of something.')
            builder.subparser('info').add_argument('detail', nargs='?', metavar='DETAIL',
                                                   type='str', help='The detail of the information')

            # Add a sub parser with one mutually exclusive group and two arguments
            builder.add_subparser('config', help="Config something.")
            builder.subparser('config').add_group('a_group', description="Group description",
                                                   is_mutually_exclusive=True)
            builder.subparser('config').add_argument('-n', '--name', nargs='?', dest='name',
                                                     metavar='NAME', type='str', help='The name.',
                                                     group='a_group')
            builder.subparser('config').add_argument('-u', '--username', nargs='?',
                                                     dest='user_name', metavar='USER_NAME',
                                                     type='str', help='The user name.',
                                                     group='a_group')

        self._argcat.add_handler_provider(DifferentKindsOfHandlerProvider())
        # 'test' is the positional argument for 'main'.
        init_result = self._argcat.parse_args(['test', 'init'])
        self.assertEqual(init_result, {'main': {'test': 'test'}, 'init': 'init'},
                         "Incorrect result for 'init' parser")

        info_result = self._argcat.parse_args(['test', 'info', 'this'])
        self.assertEqual(info_result, {'main': {'test': 'test'}, 'info': 'info this'},
                         "Incorrect result for 'info' parser")

        # config parser has a mutually exclusive group which contains --name and --username
        # So, this would raise argparse.ArgumentError
        # config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name',
        # '--username', 'cool_user_name'])

        config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name'])
        self.assertEqual(config_result,
                         {'main': {'test': 'test'},
                          'config': 'config name = cool_name, user_name = None'},
                         "Incorrect result for 'config' parser")

        #config_result = self._argcat.parse_args(['test', 'config', '--username', 'cool_user_name'])
        #self.assertEqual(config_result, {'main': {'test': 'test'}, 'config': 'config name = None,
        # user_name = cool_user_name'}, f"Incorrect result for 'config' parser")

    def test_parse_args_with_set_handler(self) -> None:
        """Test parse_args() with setting handler."""
        with self._argcat.build() as builder:
            builder.main_parser().add_exclusive_argument('first')
            builder.main_parser().add_exclusive_argument('-v','--verbose', action='store_true',
                                                         default=False)
            builder.main_parser().add_argument('-d', '--debug', action='store_true', default=False)
            # Add sub parser
            builder.add_subparser('process')
            # Add group for the sub parser
            builder.subparser('process')\
            .add_group('process_group',
                       description='This is a mutually exclusive group for `process`.',
                       is_mutually_exclusive=True)
            # Add argument to sub parsers
            builder.subparser('process').add_argument('-f', '--file',
                                 nargs='?', dest='filename', type='str', group='process_group',
                                 required=False, help='The target file name.')
            builder.subparser('process').add_argument('-l', '--link',
                                 nargs='?', dest='link', type='str', group='process_group',
                                 required=False, help='The target link.')

        # Test normal parse without any args and the default main handler
        # If there is no set-up args, the ArgumentParse will be using the last argument of the
        # unit test command line: python -m unittest discover unitests, which is 'unitests'.
        # This unfornately can break the test. So, here we have to set args=['False'] if we don't
        # want any argument we don't want. In the real world, I guess we also need to set it up
        # if we really need a specific argument like an empty one to pevent any accidental input
        # from the command line.
        parsed = self._argcat.parse_args(['False'])
        self.assertEqual(parsed,
                         {'main':
                             {'debug': False,
                              'first': 'False',
                              'verbose': False}
                             },
                         "Failed to parse no args input with the default main handler.")

        # Test normal parse with args for main parser and the default main handler
        parsed = self._argcat.parse_args(['-v', '-d', 'False'])

        self.assertEqual(parsed,
                         {'main':
                             {'debug': True,
                              # Note there, we input `first` as string, so return value is string.
                              'first': 'False',
                              'verbose': True}
                             },
                         "Failed to parse main parser's args with the default main handler.")

        # Test normal parse with args for main parser and sub parser, and the default main handler
        parsed = self._argcat.parse_args(['-v', 'True', 'process', '-f', 'a_code_file.py'])

        self.assertEqual(parsed,
                         {'main':
                             {'debug': False,
                              'first': 'True',
                              'verbose': True},
                          'process': None},
                         "Failed to parse args input for both main parser and sub parser \
                         with the default main handler.")

        # Test custom main handler with args input only for main parser
        def main_handler(first, verbose, debug):
            return f"main_handler => first: {first}, verbose: {verbose}, debug: {debug}."

        self._argcat.set_parser_handler(parser_name='main', handler=main_handler)

        parsed = self._argcat.parse_args(['-v', '-d', 'False'])

        self.assertEqual(parsed,
                         {'main': "main_handler => first: False, verbose: True, debug: True."},
                         "Failed to parse main parser's args with the custom main handler.")

        # Test custom main handler and process handler with args input only for main parser
        def process_handler(debug, filename, link):
            return f"process_handler => debug: {debug}, filename: {filename}, link: {link}."

        self._argcat.set_parser_handler(parser_name='process', handler=process_handler)

        parsed = self._argcat.parse_args(['-v', '-d', 'False'])

        self.assertEqual(parsed,
                         {'main': "main_handler => first: False, verbose: True, debug: True."},
                         "Failed to parse main parser's args with the custom main handler \
                             and process handler.")

        # Test custom main handler and process handler with args input for both main parser and
        # subparser
        parsed = self._argcat.parse_args(['-v', 'True', 'process', '--file', 'foo.py'])

        self.assertEqual(parsed,
                         {'main': 'main_handler => first: True, verbose: True, debug: False.',
                         'process': 
                             'process_handler => debug: False, filename: foo.py, link: None.'},
                         "Failed to parse args input for both main parser and sub parser with " + 
                         "the custom main handler and custom process handler.")

        # Test custom main handler and process handler with args input for both main parser and
        # subparser, but use incorrect args for sub parser. Since `--file` and `--link` is in a
        # mutually exclusive group, they cannot appear at the same time in **kwargs.
        # parsed = self._argcat.parse_args(['-v', 'True', 'process', '--file', 'foo.py', '--link',
        # 'www.haha.com'])
        # The error should be `argparse.ArgumentError: argument -l/--link: not allowed with argument
        # -f/--file`
        self._argcat.print_parser_handlers()
        self._argcat.print_parsers()
