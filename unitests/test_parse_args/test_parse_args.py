from argcat import ArgCat
from ..argcat_unit_test import ArgCatUnitTest

class DifferentKindsOfHandlerProvider:
    @classmethod
    @ArgCat.handler(parser_name='info')  
    def info_handler(cls, detail: str=None) -> None:
        return f'info {detail}'

    @staticmethod
    @ArgCat.handler(parser_name='init')  
    def init_handler() -> None:
        return 'init'

    @ArgCat.handler(parser_name='config')  
    def config_handler(self, name: str=None, user_name: str=None) -> str:
        return f"config name = {name}, user_name = {user_name}"

class TestHandler(ArgCatUnitTest):
    def setUp(self):
        self._argcat = ArgCat()

    def test_parse_args_from_load(self) -> None:
        self._argcat.load(self.abs_path_of_test_file("parse_args.yml"))
        self._argcat.add_handler_provider(DifferentKindsOfHandlerProvider())
        # 'test' is the positional argument for 'main'.
        init_result = self._argcat.parse_args(['test', 'init'])
        self.assertEqual(init_result, {'main': {'test': 'test'}, 'init': 'init'}, f"Incorrect result for 'init' parser")

        info_result = self._argcat.parse_args(['test', 'info', 'this'])
        self.assertEqual(info_result, {'main': {'test': 'test'}, 'info': 'info this'}, f"Incorrect result for 'info' parser")

        # config parser has a mutually exclusive group which contains --name and --username
        # So, this would raise argparse.ArgumentErro
        # config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name', '--username', 'cool_user_name'])
        config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name'])
        self.assertEqual(config_result, {'main': {'test': 'test'}, 'config': 'config name = cool_name, user_name = None'}, f"Incorrect result for 'config' parser")

        config_result = self._argcat.parse_args(['test', 'config', '--username', 'cool_user_name'])
        self.assertEqual(config_result, {'main': {'test': 'test'}, 'config': 'config name = None, user_name = cool_user_name'}, 
                         f"Incorrect result for 'config' parser")

    def test_parse_args_from_build(self) -> None:
        with self._argcat.build() as builder:
            builder.main_parser().add_exclusive_argument('foo')
            builder.main_parser().add_exclusive_argument('-v','--verbose', action='store_true', default=False)
            builder.main_parser().add_argument('-d', '--debug', action='store_true', default=False)
            # Add group for the sub parser
            builder.add_sub_parser('process')
            builder.sub_parser('process').add_group('process_group', 
                                                 description='This is a mutually exclusive group for `process`.', 
                                                 is_mutually_exclusive=True)
            # Add argument to sub parsers
            builder.sub_parser('process').add_argument('-f', '--file', 
                                 nargs='?', dest='filename', type='str', group='process_group', required=False,
                                 help='The target file name.')
            builder.sub_parser('process').add_argument('-l', '--link', 
                                 nargs='?', dest='link', type='str', group='process_group', required=False, 
                                 help='The target link.')
        
        # Test normal parse without any args and the default main handler
        parsed = self._argcat.parse_args()
        self.assertEqual(parsed, 
                         {'main': 
                             {'debug': False, 
                              'foo': 'unitests/test_parse_args/test_parse_args.py', 
                              'verbose': True} 
                             }, 
                         "Failed to parse no args input with the default main handler.")
        
        # Test normal parse with args for main parser and the default main handler
        parsed = self._argcat.parse_args(['-v', '-d', 'False'])
        
        self.assertEqual(parsed, 
                         {'main': 
                             {'debug': True, 
                              'foo': 'False',       # Note there, we input `foo` as string, so return value is string. 
                              'verbose': True} 
                             }, 
                         "Failed to parse main parser's args with the default main handler.")
        
        # Test normal parse with args for main parser and sub parser, and the default main handler
        parsed = self._argcat.parse_args(['-v', 'True', 'process', '-f', 'a_code_file.py'])
        
        self.assertEqual(parsed, 
                         {'main': 
                             {'debug': False, 
                              'foo': 'True', 
                              'verbose': True},
                          'process': None}, 
                         "Failed to parse args input for both main parser and sub parser \
                         with the default main handler.")
        
        # Test custom main handler with args input only for main parser
        def main_handler(foo, verbose, debug):
            return f"main_handler => foo: {foo}, verbose: {verbose}, debug: {debug}."
        
        self._argcat.add_parser_handler(parser_name='main', handler=main_handler)
        
        parsed = self._argcat.parse_args(['-v', '-d', 'False'])
        
        self.assertEqual(parsed, 
                         {'main': "main_handler => foo: False, verbose: True, debug: True."}, 
                         "Failed to parse main parser's args with the custom main handler.")
        
        # Test custom main handler and process handler with args input only for main parser
        def process_handler(debug, filename, link):
            return f"process_handler => debug: {debug}, filename: {filename}, link: {link}."

        self._argcat.add_parser_handler(parser_name='process', handler=process_handler)
        
        parsed = self._argcat.parse_args(['-v', '-d', 'False'])
        
        self.assertEqual(parsed, 
                         {'main': "main_handler => foo: False, verbose: True, debug: True."}, 
                         "Failed to parse main parser's args with the custom main handler and process handler.")
        
        # Test custom main handler and process handler with args input for both main parser and sub parser
        parsed = self._argcat.parse_args(['-v', 'True', 'process', '--file', 'foo.py'])
        
        self.assertEqual(parsed, 
                         {'main': 'main_handler => foo: True, verbose: True, debug: False.', 
                         'process': 'process_handler => debug: False, filename: foo.py, link: None.'}, 
                         "Failed to parse args input for both main parser and sub parser \
                         with the custom main handler and custom process handler.")
        
        # Test custom main handler and process handler with args input for both main parser and sub parser, but use
        # incorrect args for sub parser. Since `--file` and `--link` is in a mutually exclusive group, they cannot 
        # appear at the same time in **kwargs.
        # parsed = self._argcat.parse_args(['-v', 'True', 'process', '--file', 'foo.py', '--link', 'www.haha.com'])
        # The error should be `argparse.ArgumentError: argument -l/--link: not allowed with argument -f/--file`
        
        self._argcat.print_parser_handlers()
        self._argcat.print_parsers()