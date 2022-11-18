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
        self.assertEqual(init_result, 'init', f"Incorrect result {init_result} for 'init' parser")

        info_result = self._argcat.parse_args(['test', 'info', 'this'])
        self.assertEqual(info_result, 'info this', f"Incorrect result {info_result} for 'info' parser")

        # config parser has a mutually exclusive group which contains --name and --username
        # So, this would raise argparse.ArgumentErro
        # config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name', '--username', 'cool_user_name'])
        config_result = self._argcat.parse_args(['test', 'config', '--name', 'cool_name'])
        self.assertEqual(config_result, 'config name = cool_name, user_name = None', f"Incorrect result '{config_result}' for 'config' parser")

        config_result = self._argcat.parse_args(['test', 'config', '--username', 'cool_user_name'])
        self.assertEqual(config_result, 'config name = None, user_name = cool_user_name', f"Incorrect result '{config_result}' for 'config' parser")

    def test_parse_args_from_build(self) -> None:
        with self._argcat.build() as builder:
            builder.main_parser().add_argument('verbose', action='store_true')
            # Add group for the sub parser
            builder.sub_parser('load').add_group('load_group', 
                                                 description='This is a group for `load`, which IS mutually exclusive.', 
                                                 is_mutually_exclusive=True)
            # Add argument to sub parsers
            builder.sub_parser('load').add_argument('-f', '--file', 
                                 nargs='?', dest='filename', type='str', group='load_group', required=False,
                                 help='The target file name.')
            builder.sub_parser('load').add_argument('-l', '--link', 
                                 nargs='?', dest='link', type='str', group='load_group', required=False, 
                                 help='The target link.')
        
        def main_handler(verbose):
            print(f"main_handler => verbose: {verbose} .")
        
        def load_handler(filename, link):
            print(f"load_handler => filename: {filename}, link: {link} .")
        
        self._argcat.add_parser_handler('main', main_handler)
        self._argcat.add_parser_handler('load', load_handler)