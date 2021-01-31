#!/usr/bin/python

from argcat import ArgCat

class Foo:
    def __init__(self):
        self._value = "NewB"
    def func(self, workspace_name, workspace_user_name):
        print("lala {}".format(self._value))
        print("workspace_name = {}, workspace_user_name = {}".format(workspace_name, workspace_user_name))

def test1():
    print("test1")

def test2():
    print("test2")

def test_main(test):
    print("test_main {}".format(test))

def main():
    argcat = ArgCat()
    argcat.load("argnifest.yml")
    foo = Foo()
    foo._value = 2
    argcat.set_handler('foo', foo)
    argcat.parse()
    
if __name__ == '__main__':
    main()