#!/usr/bin/python

from argcat import ArgCat
#import sys
#import re

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
@ArgCat.handler("main")
def main_handler(test):
    print("main_handler {}".format(test))

def main():
    argcat = ArgCat(chatter=False)
    #argcat.load("hello_cat.yml")
    #foo = Foo()
    #foo.value = "new value"
    # Find handlers in __main__
    #argcat.add_handler_provider(sys.modules['__main__'])
    # Find handlers in Foo
    #argcat.add_handler_provider(foo)
    #argcat.print_parsers()
    #argcat.print_parser_handlers()
    #argcat.parse_args()
    
    arg_recipes = ["   data_file -f/--file filename=\"./__init__.py\""] 
    
    argcat.easy_load(arg_recipes)
    
    argcat.print_parsers()
    #argcat.print_parser_handlers()
    
if __name__ == '__main__':
    main()