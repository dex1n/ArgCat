# ArgCat - A cute helper for ArgumentParser in Python 3

## Background

Have you already been tired of writing argument parsing codes for your python command line program? **YES, I AM! (Why I'm yelling as hell?!)**

(This is the reason:) To me, adding/updating the argument parsers and setting varities of arguments in python are absolute chores and the most boring part of writing a python program.

You know, __Life is short, I use Python__ ... to write the creative and fun stuffs. But NOT these:

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

These codes for me really destroy every happy and exciting moment and kill the most valuable thing: **TIME!**

So, in the end, it does really matter! (BTW, I love Linkin Park)

So, (another so, you know, we love saying so) eventually I create __ArgCat__ as the way to get out of the boring hell.

## About

Generally speaking, __ArgCat__ allows you to define and config your ArgumentParsers in a YAML format file then create the ArgumentParser instances according to the YAML in the runtime.

## Installation

Why not install it before diving into details :)

```bash
pip install argcat
```

## Usage

### YAML

An example YAML file name `simple.yml` for __ArgCat__:

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
        # Mainly used for main arguments. 
        # If this is set to True, the argument will be filtered out before being passed into subparser's handler. 
        # Default value is False.
        # In this case, the argument test will not be passed into any subparser's handler,
        # even this test argument has a valid value instead of None.
        ignored_by_subparser: True
        nargs: "?"
        dest: "test"
        metavar: "TEST"
        type: "str" # The default type for this is "str". Use the type's lexical name here and ArgCat will try to convert it to the type object.
        help: "Just for test"
  init: # This is a subparser without any argument but only a help tip.
    help: "Initialize something."
  info: # This is a subparser has only one positional argument.
    help: "Show information of something."
    arguments:
      -
        nargs: "?"
        dest: "detail"
        metavar: "DETAIL"
        type: "str"
        help: "The detail of the information"
  config: # This is a sub parser has a few named arguments and one group.
    help: "Config something."
    argument_groups:  # All groups this subparser has.
      a_group:  # Group name can be any valid string. And any argument in the group should declare this in its argument config.
        name: "Actual group name"
        description: "Group description"
        is_mutually_exclusive: true # Whether the group is mutually exclusive. This is an useful property for some cases.
    arguments:
      -
        name_or_flags: ["-n", "--name"]
        nargs: "?"
        dest: "name"
        metavar: "NAME"
        type: "str"
        help: "The name."
        group: "a_group"  # Declare this argument is in the group whose name is "a_group" declared above.
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

### Simple codes

```python
from argcat import ArgCat
argcat = ArgCat()
argcat.load("simple.yml") # Load the settings from the YAML file.
argcat.parse_args() # Start to parse the args input.
```

That's it!

When `argcat.parse_args()` gets called, __ArgCat__ starts to process the input arguments like what `ArgumentParser.parse_args()` does. It sends the corresponding arguments received and parsed, and then passes into the _Handlers_ you defined in your codes. Speaking of _Handlers_:

### Handlers

The _Handler_ is a function for handling arguments processed by __ArgCat__. It's place you really deal with the arguments.

#### How to define a Handler

There are two steps you need for defining __ArgCat__ _Handler_:

1. Decorate the handler function with the `@ArgCat.handler` decorator and set the corresonding parser name. See a full example below:

    ```python
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
        @ArgCat.handler("config") # Handle arguments for parser named "config"
        def config_handler(self, name, user_name):
            print("self._value = {}".format(self._value))
            print("name = {}, user_name = {}".format(name, user_name))

        # Static method of class
        @staticmethod
        @ArgCat.handler("init") # Handle arguments for parser named "init"
        def init_handler():
            print("init_handler")

        # Class method
        @classmethod
        @ArgCat.handler("info") # Handle arguments for parser named "info"
        def info_handler(cls, detail):
            print("info_handler with detail: {}".format(detail))

    # Regular function
    @ArgCat.handler("main")
    def main_handler(test):
        print("main_handler {}".format(test))
    ```

    As you can see, there are four different kinds of functions of the class `Foo` decorated.

2. Let __ArgCat__ know where to find the handlers by `ArgCat.add_handler_provider(provider: Any)`:

    ```python
    def main():
        argcat = ArgCat(chatter=False)
        argcat.load("hello_cat.yml")
        foo = Foo()
        foo.value = "new value"
        # Set module __main__ as a handler provider
        argcat.add_handler_provider(sys.modules['__main__'])
        # Set Foo as a handler provider
        argcat.add_handler_provider(foo)
        argcat.print_parsers()
        argcat.print_parser_handlers()
        argcat.parse()
        
    if __name__ == '__main__':
        main()
    ```

    When `ArgCat.add_handler_provider(provider: Any)` is called, ArgCat will try to find the decorated handlers from the providers. Note that the function `init_handler()` is in `__main__`, so the corresponding `provider` should be `sys.modules['__main__']` which returns the `__main__` scope.  

To sum it up, there are four handlers in above example:

- `init_handler()`: a `@staticmethod` method of the class for a parser named `init`
- `info_handler()`: a `@classmethod` method of the class for a parser named `info`
- `main_handler()`: a regular function for a parser named `main`
- `config_handler()`:  a regular instance method of the class for a parser named `config`

#### The requirement of Handler

##### Parser name and function name

The parser's name must be exactly the same as the one declared in the YAML file, but the handler function name can be arbitary.

So, if you define a parser named init in the config file, 

```YAML
init: # This is a subparser without any argument but only a help tip.
    help: "Initialize something."
```

then the decorated function must set the correct name `init`.

```Python
@ArgCat.handler("init") # Handle arguments for parser named "init"
    def init_handler():
      print("init_handler")
```

##### Function type

If the method of the handler is `@staticmethod` or `@classmethod`, the decorations should be closest to the method like:

```python
# Class method
@classmethod
@ArgCat.handler("info")  # This decorator must be placed closest to the method.
def info_handler(cls, detail):
    print("info_handler with detail: {}".format(detail))
```

##### Signature

Handler's signature must match the parsed arguments. For instances, in the above codes, `config_handler()` has two parameters `name` and `user_name` except `self`. They exactly match what `config`'s declared arguments below. In other words, if `config` parser has only 2 arguments and their `dest` are `name` and `user_name`, the handler function must also have 2 parameters which must be `name` and `user_name`.

```yaml
arguments:
      -
        name_or_flags: ["-n", "--name"]
        nargs: "?"
        dest: "name" # NOTE THIS DEST
        metavar: "NAME"
        type: "str"
        help: "The name."
        group: "a_group"  
      - 
        name_or_flags: ["-u", "--username"]
        nargs: "?"
        dest: "user_name" # NOTE THIS DEST
        metavar: "USER_NAME"
        type: "str" 
        help: "The user name."
        group: "a_group"
```

##### Underneath the surface

The parsed argument dict would be something like `{'name': '1', 'user_name': None}` for `config`'s case. And the handler function `config_handler()` will be called with key arguments given by `**theDict` , which means the function will be called like this: `config_handler(**theDict)`. As a result, if one of `config_handler()` parameters is `foo_user_name` instead of `user_name`, the handler would not be able to receive the parsed arguments and an error would be reported by __ArgCat__ like:

```Python
ERROR: Handling function Exception: "config_handler() got an unexpected keyword argument 'user_name'", with function sig: (name, foo_user_name) and received parameters: (name, user_name).
```

### Example

There are files of two examples in this project.

One includes two files: `hello_cat.py`, `hello_cat.yml`. The first one is a main file shows how to use __ArgCat__ and also contains the codes demonstrated in this README. And the latter one is the YAML config file. You can take them as reference, when you are using __ArgCat__.

Another file named `hello_chore.py` shows the traditional way to use the ArgumentParser.

If you encounter any issue or have any question please feel free to open an issue ticket or send me email.

## In the end

Phew...

Ok. I think that's all for this README at this point for v0.2.1.

ArgCat is good, but not perfect. I will continue to improve it and update this documentation.

Hope you enjoy coding in Python.

`~Peace & Love~`

## License

```
MIT License

Copyright (c) 2021 Chunxi Xin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```