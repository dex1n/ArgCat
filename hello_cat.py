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
    
    def config_handler(self, name, user_name):
        print("self._value = {}".format(self._value))
        print("name = {}, user_name = {}".format(name, user_name))

def init_handler():
    print("init_handler")

def info_handler():
    print("info_handler")

def main_handler(test):
    print("main_handler {}".format(test))

def main():
    argcat = ArgCat()
    argcat.load("hello_cat.yml")
    foo = Foo()
    foo._value = "new value"
    argcat.set_handler('foo', foo)
    argcat.parse()
    
if __name__ == '__main__':
    main()