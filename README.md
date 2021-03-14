# ArgCat

### A cute helper for python argument parsing

Have you already been tired of writing argument parsing codes for your python command line program? 

#### YES, I AM! (Why do you yell as hell?!) 

(This is the reason:) To me defining the argument parsers and adding varities of arguments in python are absolute chores and the most boring part of writing a python program. 

You know, __Life is short, I use Python__...just to write the creative and fun stuffs. But not these:

```python
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
```

Codes above really destroy every happy and exciting things and steal the most valuable thing from me: TIME!

So, in the end, it does really matter! (Sorry Linkin Park) 

So, (another so, you know, we love say so) eventually I create this __ArgCat__ as the solution.

Generally speaking, ArgCat will allow you to define and config your parsers, arguments and handler functions in an YAML file, and then will create the actual parser instances according to the settings in the YAML and link the handler functions to resolve the input arguments of the parsers in the runtime. 

Below is an example of a YAML file:

```yaml
meta: # Include all essential configurations used for creating a new ArgumentParser.
  prog: "Cool program name"
  description: "Awesome description"
  subparser:
    title: "The subparsers title"
    description: "The subparsers description"
    help: "The subparsers help"
parsers:  # All parsers including the "main" parser below, which is the very first parser created by argparse.ArgumentParser()
  main:
    arguments:
      # Declare a positional argument for the main parser.
      -
        # Mainly used for main arguments. If this is set to True, the argument will be filtered out before being passed
        # into subparser's handler. Default value is False.
        # In below case, the argument test will not be passed into any subparser's handler even this test 
        # argument has a valid value instead of None.
        ignored_by_subparser: True
        nargs: "?"
        dest: "test"
        metavar: "TEST"
        type: "str" # The default type for this is "str". Use the type's lexical name here and ArgCat will try to convert it to the type object.
        help: "Just for test"
  init: # This is a subparser without any argument.
    help: "Initialize something."
  info: # This is a subparser has only one argument.
    help: "Show information of something."
    arguments:
      -
        nargs: "?"
        dest: "detail"
        metavar: "DETAIL"
        type: "str" # The default type is "str". For this attribute we need to generate the right type from this type string when loading this file.
        help: "The detail of the information"
  config: # This is a sub parser has a few arguments and one group.
    help: "Config something."
    argument_groups:  # All groups this subparser has.
      a_group:  # Group name can be any valid string. And any argument in the group should declare this in its argument config.
        name: "Actual group name"
        description: "Group description"
        is_mutually_exclusive: true # Whether the group is mutually exclusive.
    arguments:
      -
        name_or_flags: ["-n", "--name"]
        nargs: "?"
        dest: "name"
        metavar: "NAME"
        type: "str"
        help: "The name."
        group: "a_group"  # Declare that this argument is in the group whose name is "a_group" declared above.
      - 
        name_or_flags: ["-u", "--username"]
        nargs: "?"
        dest: "user_name"
        metavar: "USER_NAME"
        type: "str" 
        help: "The user name."
        group: "a_group"

```

Quite simple, right? (Not short, but really simple and straightforward. :P )

And use it in your codes like:

```python
argcat = ArgCat()
argcat.load("simple.yml")	# Simple!
argcat.parse()
```

That's it! When `argcat.parse()` is called, ArgCat will start to process the input arguments like what `ArgumentParser.parse_args()` does. It will send the corresponding arguments it received and parsed and passed into the handlers you **defined** in your codes. 

Here are two steps you need to define the handlers that ArgCat can know and use:

1. The handler (function/method) must be decorated by the `@ArgCat.handler` decorator with the parser's name it's for. See an example below:

```python
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
```

As you can see, a few functions and one method of the class `Foo` are decorated. 

2. With the decorations,  you must let ArgCat know where to find the handlers by calling `ArgCat.add_handler_provider(provider: Any) -> None` like below:

```python
def main():
    argcat = ArgCat(chatter=False)
    argcat.load("hello_cat.yml")
    foo = Foo()
    foo.value = "new value"
    # Find handlers in __main__
    argcat.add_handler_provider(sys.modules['__main__'])
    # Find handlers in Foo
    argcat.add_handler_provider(foo)
    argcat.print_parsers()
    argcat.print_parser_handlers()
    argcat.parse()
    
if __name__ == '__main__':
    main()
```

When `ArgCat.add_handler_provider(provider: Any) -> None` is called, ArgCat will try to find the decorated handlers from the `provider`. Note that the functions above such as `init_handler()` is in `__main__`, so the corresponding `provider` should be `sys.modules['__main__']` which returns the `__main__` namespace.  

In above example there are four handlers in detail:

- `init_handler()` for a parser named `init` 
- `info_handler()` for a parser named `info`
- `main_handler()` for a parser named `main`
- `config_handler()` of `Foo` for a parser named `config`

The parser's name must be exactly the same as the one declared in the manifest YAML file, but the handler's name can be arbitary. 

And handler's parameters must be exactly the same as the parsed arguments. For instances, in the above codes, `config_handler()` has two parameters `name` and `user_name` except `self`. They are totally the same as what `config` 's declared arguments below, 

```yaml
arguments:
      -
        name_or_flags: ["-n", "--name"]
        nargs: "?"
        dest: "name"			# NOTE THIS DEST
        metavar: "NAME"
        type: "str"
        help: "The name."
        group: "a_group"  
      - 
        name_or_flags: ["-u", "--username"]
        nargs: "?"
        dest: "user_name"	# NOTE THIS DEST
        metavar: "USER_NAME"
        type: "str" 
        help: "The user name."
        group: "a_group"
```

because the parsed argument dict would be something like `{'name': '1', 'user_name': None}` for `config`'s case. Otherwise, if one of `config_handler()` parameters is `foo_user_name` instead of `user_name`, the handler would not be able to receive the parsed arguments and an error would be reported by ArgCat like:

`ERROR: Handling function Exception: "config_handler() got an unexpected keyword argument 'user_name'", with function sig: (name, foo_user_name) and received parameters: (name, user_name).`



Phew...

Ok. I think that's all for this README at this point for v0.2.

ArgCat is good, but not perfect. I will continue to improve it and update this documentation.

Hope you enjoy coding in Python.

`~Peace & Love~`

