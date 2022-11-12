from argcat import ArgCat
from ..argcat_unit_test import ArgCatUnitTest

class NormalHandlerProvider:
    @ArgCat.handler(parser_name='main')
    def main_handler(self, test: str=None) -> str:
        return 'main'

    @ArgCat.handler(parser_name='init')
    def init_handler(self) -> str:
        return 'init'

    @ArgCat.handler(parser_name='info')
    def info_handler(self, detail: str=None) -> str:
        return 'info'

    @ArgCat.handler(parser_name='config')
    def config_handler(self, name: str=None, user_name: str=None) -> str:
        return 'config'

class IncorrectHandlerProvider:
    @ArgCat.handler(parser_name='git')  # Parser name that does not exist.
    def main_handler(self, test: str=None) -> str:
        return 'main'

    @ArgCat.handler(parser_name='init')     
    def init_handler(self) -> str:
        return 'init'

    # Same parser name and should not be added because there has already been 
    # one above. 
    @ArgCat.handler(parser_name='init')
    def xxxx_handler(self) -> str:
        return 'xxxx'

    #@ArgCat.handler(parser_name='config')  # Missing parser handler
    #def config_handler(self, name: str=None, user_name: str=None) -> str:
    #    return 'config'

class DifferentKindsOfHandlerProvider:
    @staticmethod
    @ArgCat.handler(parser_name='main')  
    def static_main_handler(test: str=None) -> str:
        return 'static_main'

    @classmethod
    @ArgCat.handler(parser_name='info')  
    def static_info_handler(cls, detail: str=None) -> str:
        return 'class_info'
    
    @ArgCat.handler(parser_name='init')  
    def normal_function_init_handler(self) -> str:
        return 'normal_function_init'

class TestHandler(ArgCatUnitTest):
    def setUp(self):
        self._argcat = ArgCat()
        self._argcat.load(self.abs_path_of_test_file("handler.yml"))

    def test_normal_handlers(self) -> None:
        self._argcat.add_handler_provider(NormalHandlerProvider())
        for parser_name in ['main', 'info', 'init', 'config']:
            self.assertIsNotNone(self._argcat._arg_parsers[parser_name].handler_func, 
            f"Parser handler for '{parser_name}' should not be None!")
            self.assertEqual(self._argcat._arg_parsers[parser_name].handler_func(), 
            parser_name, f"Parser handler for '{parser_name}' is wrong!")
    
    def test_incorrect_handlers(self) -> None:
        self._argcat.add_handler_provider(IncorrectHandlerProvider())
        self.assertIsNotNone(self._argcat._arg_parsers['init'].handler_func, 
        "Parser 'init' should not be None!")
        # For the case there are handlers with duplicate name, only the first
        # one should be added. And the order for first and latter is based on
        # the method's name's alphabet order.
        self.assertEqual(self._argcat._arg_parsers['init'].handler_func(), 
        'init', "Parser handler of 'init' is incorrect!")

    def test_different_kinds_of_handlers(self) -> None:
        self._argcat.add_handler_provider(DifferentKindsOfHandlerProvider())
        for parser_name in ['main', 'info', 'init']:
            self.assertIsNotNone(self._argcat._arg_parsers[parser_name].handler_func, 
            f"Parser handler for '{parser_name}' should not be None!")
        self.assertEqual(self._argcat._arg_parsers['main'].handler_func(), 'static_main', 
        "Parser handler for 'main' is wrong!")
        self.assertEqual(self._argcat._arg_parsers['info'].handler_func(), 'class_info', 
        "Parser handler for 'info' is wrong!")
        self.assertEqual(self._argcat._arg_parsers['init'].handler_func(), 'normal_function_init', 
        "Parser handler for 'init' is wrong!")
