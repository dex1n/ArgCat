#!/usr/bin/python
"""
Example codes for a regular usage of ArgCat.
"""
from argcat import ArgCat

class FooCls:
    """
    Example class as both the handler parser provider and the class to interact with ArgCat.
    """
    def __init__(self):
        self._value = "foo value."

    @property
    def value(self):
        """
        A valuable value.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    # Regular class instance method
    @ArgCat.handler(parser_name="config")
    def config_handler(self, name, user_name):
        """
        The parser handler for 'config'
        """
        print(f"self._value = {self._value}")
        print(f"name = {name}, user_name = {user_name}")

    # Static method of class
    @staticmethod
    @ArgCat.handler(parser_name="init")
    def init_handler():
        """
        The parser handler for 'init'
        """
        print("init_handler")

    # Class method
    @classmethod
    @ArgCat.handler(parser_name="info")
    def info_handler(cls, detail):
        """
        The parser handler for 'info'
        """
        print(f"info_handler with detail: {detail}")

#@ArgCat.handler("main")
# This decorator is not needed if we just set it through set_parser_handler().
def main_handler(test):
    """
    The parser handler for 'main' in the main scope.
    """
    print(f"main_handler {test}")

def main():
    """
    Main func
    """
    argcat = ArgCat(chatter=False)
    foo_cls_instance = FooCls()
    foo_cls_instance.value = "new value"

    with argcat.build() as builder:
        # Set basic information
        builder.set_prog_info(prog='Cool program name', description='Awesome description')
        builder.set_subparsers_info(title='The subparsers title',
                                    description='The subparsers description',
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
        builder.subparser('config').add_argument('-n', '--name', nargs='?', dest='name',
                                                 metavar='NAME', type='str', help='The name.',
                                                 group='a_group')
        builder.subparser('config').add_argument('-u', '--username', nargs='?', dest='user_name',
                                                 metavar='USER_NAME',
                                                type='str', help='The user name.', group='a_group')

    argcat.add_handler_provider(foo_cls_instance)
    argcat.set_parser_handler(parser_name='main', handler=main_handler)

    argcat.print_parsers()
    argcat.print_parser_handlers()
    argcat.parse_args()

if __name__ == '__main__':
    main()
