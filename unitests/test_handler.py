from argcat import ArgCat
from unitests.argcat_unittest import ArgCatUnitTest

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
        with self._argcat.build() as builder:
            # Set basic information
            builder.set_prog_info(prog='Cool program name', description='Awesome description')
            builder.set_subparsers_info(title='The subparsers title', description='The subparsers description', 
                                        help='The subparsers help')
            
            # Add an exclusive argument for the main parser.
            builder.main_parser().add_exclusive_argument('test', nargs='?', metavar='TEST', type=str, 
                                                         help='Just for test')
            
            # Add a sub parser without any arguments.
            builder.add_subparser('init', help='Initialize something.')
            
            # Add a sub parser with one argument.
            builder.add_subparser('info', help='Show information of something.')
            builder.subparser('info').add_argument('detail', nargs='?', metavar='DETAIL', type='str', 
                                                    help='The detail of the information')
            
            # Add a sub parser with one mutually exclusive group and two arguments
            builder.add_subparser('config', help="Config something.")
            builder.subparser('config').add_group('a_group', description="Group description", 
                                                   is_mutually_exclusive=True)
            builder.subparser('config').add_argument('-n', '--name', nargs='?', dest='name', metavar='NAME',
                                                      type='str', help='The name.', group='a_group')
            builder.subparser('config').add_argument('-u', '--username', nargs='?', dest='user_name', 
                                                      metavar='USER_NAME', type='str', help='The user name.', 
                                                      group='a_group')
        
    def test_normal_handler_provider(self) -> None:
        self._argcat.add_handler_provider(NormalHandlerProvider())
        for parser_name in ['main', 'info', 'init', 'config']:
            self.assertIsNotNone(self._argcat._arg_parsers[parser_name].handler_func, 
            f"Parser handler for `{parser_name}` should not be None!")
            self.assertEqual(self._argcat._arg_parsers[parser_name].handler_func(), 
            parser_name, f"Parser handler for `{parser_name}` is wrong!")
    
    def test_incorrect_handler_provider(self) -> None:
        self._argcat.add_handler_provider(IncorrectHandlerProvider())
        self.assertIsNotNone(self._argcat._arg_parsers['init'].handler_func, 
        "Parser `init` should not be None!")
        # For the case there are handlers with duplicate name, only the first
        # one should be added. And the order for first and latter is based on
        # the method's name's alphabet order.
        self.assertEqual(self._argcat._arg_parsers['init'].handler_func(), 
        'init', "Parser handler of `init` is incorrect!")

    def test_different_kinds_of_handler_provider(self) -> None:
        self._argcat.add_handler_provider(DifferentKindsOfHandlerProvider())
        for parser_name in ['main', 'info', 'init']:
            self.assertIsNotNone(self._argcat._arg_parsers[parser_name].handler_func, 
            f"Parser handler for `{parser_name}` should not be None!")
        self.assertEqual(self._argcat._arg_parsers['main'].handler_func(), 'static_main', 
        "Parser handler for `main` is wrong!")
        self.assertEqual(self._argcat._arg_parsers['info'].handler_func(), 'class_info', 
        "Parser handler for `info` is wrong!")
        self.assertEqual(self._argcat._arg_parsers['init'].handler_func(), 'normal_function_init', 
        "Parser handler for `init` is wrong!")

    def test_default_main_handler(self) -> None:
        self.assertNotEqual(self._argcat._arg_parsers['main'].handler_func, None, 
        "Default `main` parser's handler is not valid!")
        # Run it to prove it's working.
        self.assertEqual(self._argcat._arg_parsers['main'].handler_func(), {}, 
        "Default `main` parser's handler is not working!")
    
    def test_add_normal_handlers(self) -> None:
        # Main handler
        def main_handler(test) -> str:
            return f'main_handler:{test}'
        self._argcat.set_parser_handler(parser_name='main', handler=main_handler)
        self.assertEqual(self._argcat._arg_parsers['main'].handler_func('parameter'), 'main_handler:parameter', 
        "Parser handler for `main` is wrong!")
        
        # Sub handlers
        # init handler with no arguments
        def init_handler() -> str:
            return 'init_handler'
        self._argcat.set_parser_handler(parser_name='init', handler=init_handler)
        self.assertEqual(self._argcat._arg_parsers['init'].handler_func(), 'init_handler', 
        "Parser handler for `init` is wrong!")
        
        # info handler with one argument
        def info_handler(detail) -> str:
            return f'info_handler:{detail}'
        self._argcat.set_parser_handler(parser_name='info', handler=info_handler)
        self.assertEqual(self._argcat._arg_parsers['info'].handler_func('detail'), 'info_handler:detail', 
        "Parser handler for `info` is wrong!")

        # config handler with two arguments
        def config_handler(name, user_name) -> str:
            return f'config_handler:{name},{user_name}'
        self._argcat.set_parser_handler(parser_name='config', handler=config_handler)
        self.assertEqual(self._argcat._arg_parsers['config'].handler_func('Kevin', 'Cool-K'), 'config_handler:Kevin,Cool-K', 
        "Parser handler for `config` is wrong!")
        
    def test_add_incorrect_handlers(self) -> None:
        # add handler without required args for 'main'
        def main_handler_without_required_args() -> str:
            return 'main_handler_without_required_args'
        self._argcat.set_parser_handler(parser_name='main', handler=main_handler_without_required_args)
        self.assertEqual(self._argcat._arg_parsers['main'].handler_func, self._argcat._default_main_handler, 
                         "Parser handler for `main` should not be one without any argument!")
        
        # add handler without required args for 'info'
        def info_handler_without_args() -> str:
            return 'info_handler_without_args'
        self.assertEqual(self._argcat.set_parser_handler(parser_name='info', handler=info_handler_without_args), False, 
                         "A parser handler without any args for `info` parser should not be taken!")
        self.assertEqual(self._argcat._arg_parsers['info'].handler_func, None, 
                         "`info` parser should be None after a failed adding!")
        
        # add handler has less args than required for 'config'
        def config_handler_without_enough_args(name) -> str:
            return f'config_handler_without_enough_args:{name}'
        self.assertEqual(
            self._argcat.set_parser_handler(parser_name='config', handler=config_handler_without_enough_args), False, 
            "A parser handler with less args for `config` parser should not be taken!")
        self.assertEqual(self._argcat._arg_parsers['config'].handler_func, None, 
                         "`config` parser should be None after a failed adding!") 
        
        # add handler for a not existed sub parser
        def foo(one, two) -> str:
            return 'Listen to me~'
        self.assertEqual(self._argcat.set_parser_handler(parser_name='foo', handler=foo), False, 
                         "Parser handler for a not existed `foo` parser should not be set!")
        
        
        