#!/usr/bin/python

from argcat import ArgCat
import sys

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
@ArgCat.handler("maina")
def main_handler():
    test = "main"
    print("main_handler {}".format(test))

@ArgCat.handler("data_file")
def data_file_handler(filename):
    print("data_file_handler {}".format(filename))

def main():
    argcat = ArgCat(chatter=False)
    
    with argcat.build() as builder:
        builder.add_group(name='test_group', parser_name='haha', description="a test group", is_mutually_exclusive=True)
        builder.add_argument(parser_name='haha', recipe="-f/--file 1>filename?=\"./__init__.py\"", arg_type='int', 
                             group_name='test_group')
    
    argcat.add_handler_provider(sys.modules['__main__'])
    #argcat.print_parsers()
    #argcat.print_parser_handlers()
    argcat.parse_args()
    
    
if __name__ == '__main__':
    main()