#!/usr/bin/python

import argparse

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
    argument_parser = argparse.ArgumentParser(prog='Cool program name', description='Awesome description')
    argument_parser.add_argument("-t", "--test", nargs='?', dest='test', metavar='TEST', type=str, help='Just for test')

    argument_subparsers = argument_parser.add_subparsers(dest = "sub_command", title='The subparsers title"', 
    description="The subparsers description", help='The subparsers help')
    
    init_parser = argument_subparsers.add_parser('init', help="Initialize something.")

    info_parser = argument_subparsers.add_parser('info', help="Show information of something.")
    info_parser.add_argument("-d", "--detail", nargs='?', dest='detail', metavar='DETAIL', type=str, 
    help='The detail of the information')

    config_parser = argument_subparsers.add_parser('config', help="Config something.")
    config_arg_group = config_parser.add_mutually_exclusive_group()
    config_arg_group.add_argument("-n", "--name", nargs='?', dest='name', metavar='NAME', type=str, help='The name.')
    config_arg_group.add_argument("-u", "--username", nargs='?', dest='user_name', metavar='USER_NAME', type=str, help='The user name.')

    args = argument_parser.parse_args()
    sub_command = args.sub_command
    if sub_command == "init":
        init_handler()
    elif sub_command == "info":
        info_handler()
    elif sub_command == "config":
        foo = Foo()
        foo.config_handler(args.name, args.user_name)
    elif sub_command is None:
        main_handler(args.test)
    
    
if __name__ == '__main__':
    main()