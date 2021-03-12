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
    
    @ArgCat.handler("config")
    def config_handler(self, name, user_name):
        print("self._value = {}".format(self._value))
        print("name = {}, user_name = {}".format(name, user_name))

@ArgCat.handler("init")
def init_handler():
    print("init_handler")

@ArgCat.handler("info")
def info_handler(detail):
    print("info_handler with detail: {}".format(detail))

@ArgCat.handler("main")
def main_handler(test):
    print("main_handler {}".format(test))

def main():
    argcat = ArgCat(chatter=False)
    argcat.load("hello_cat.yml")
    foo = Foo()
    foo.value = "new value"
    argcat.add_handler_provider(foo)
    argcat.print_parsers()
    argcat.print_parser_handlers()
    argcat.parse()
    
if __name__ == '__main__':
    main()