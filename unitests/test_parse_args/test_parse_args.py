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
        self._argcat.load(self.abs_path_of_test_file("parse_args.yml"))

    def test_normal_parse_args(self) -> None:
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

        
        
        