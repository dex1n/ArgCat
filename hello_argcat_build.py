#!/usr/bin/python

from argcat import ArgCat

class Foo:
    def __init__(self):
        self._value = "foo value."
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
    
    # Regular class instance method
    @ArgCat.handler("config")
    def config_handler(self, name, user_name):
        print("self._value = {}".format(self._value))
        print("name = {}, user_name = {}".format(name, user_name))

    # Static method of class
    @staticmethod
    @ArgCat.handler("init")
    def init_handler():
        print("init_handler")

    # Class method
    @classmethod
    @ArgCat.handler("info")
    def info_handler(cls, detail):
        print("info_handler with detail: {}".format(detail))

# Regular function
#@ArgCat.handler("main") 
# This decorator is not needed if we just set it through set_parser_handler().
def main_handler(test):
    print("main_handler {}".format(test))

def main():
    argcat = ArgCat(chatter=False)
    foo = Foo()
    foo.value = "new value"
    
    # This is to create an argcat with the same content as what we created by load(), but through build().
    with argcat.build() as builder:
        # Set basic information
        builder.set_prog_info(prog_name='Cool program name', description='Awesome description')
        builder.set_sub_parser_info(title='The subparsers title', description='The subparsers description', 
                                    help='The subparsers help')
        
        # Add an exclusive argument for the main parser.
        builder.main_parser().add_exclusive_argument('test', nargs='?', metavar='TEST', type=str, help='Just for test')
        
        # Add a sub parser without any arguments.
        builder.add_sub_parser('init', help='Initialize something.')
        
        # Add a sub parser with one argument.
        builder.add_sub_parser('info', help='Show information of something.')
        builder.sub_parser('info').add_argument('detail', nargs='?', metavar='DETAIL', type='str', 
                                                help='The detail of the information')
        
        # Add a sub parser with one mutually exclusive group and two arguments
        builder.add_sub_parser('config', help="Config something.")
        builder.sub_parser('config').add_group('a_group', description="Group description", is_mutually_exclusive=True)
        builder.sub_parser('config').add_argument('-n', '--name', nargs='?', dest='name', metavar='NAME', type='str',
                                                  help='The name.', group='a_group')
        builder.sub_parser('config').add_argument('-u', '--username', nargs='?', dest='user_name', metavar='USER_NAME', 
                                                  type='str', help='The user name.', group='a_group')
        
    # Find handlers in Foo
    argcat.add_handler_provider(foo)
    argcat.set_parser_handler(parser_name='main', handler=main_handler)
    
    argcat.print_parsers()
    argcat.print_parser_handlers()
    argcat.parse_args()
    
if __name__ == '__main__':
    main()