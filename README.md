# ArgCat

### A cute helper for python argument parsing

Have you already been tired of writing argument parsing codes for your python command line program? 

###### YES, I AM! (Why do you yell as hell?!) 

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

So, (another so, you know, we love say so) eventually I create this ArgCat as the solution.

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
      -
        name_or_flags: ["-t", "--test"]
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
        name_or_flags: ["-d", "--detail"]
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
handlers: # All handlers for acutally handle the arguments input.
  default:  # ArgCat will try to find functions in this default section in __main__
    init: "init_handler"
    info: "info_handler"
    main: "main_handler"
  foo:  # Custom class/instance/module has the functions for the parsers. This must be set before parse() being called.
    config: "config_handler"
```

Quite simple, right? (Not short, but really simple and straightforward. :P )

And use it in your codes like:

```python
argcat = ArgCat()
argcat.load("simple.yml")	# Simple!
argcat.parse()
```

That's it! When `argcat.parse()` is called, ArgCat will start to process the input arguments like what `ArgumentParser.parse_args()` does. ArgCat will send the corresponding arguments it received into the handler functions you define in the `handlers` part of the YAML file. And ArgCat will consider all functions in the `default` section as being in your `__main__` file. A complete `__main__` file example is below:

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
```

As you can see from the above codes, ArgCat also supports class function as the handler functions. If you would like to use the class functions, define them in the `handlers` part of the YAML file with a valid name ("foo" as below) and set the parser name and function name pair. 

```yaml
handlers: # All handlers for acutally handle the arguments input.
  foo:  # Custom class/instance/module has the functions for the parsers. This must be set before parse() being called.
    config: "config_handler"
```

Then in your codes use `argcat.set_handler('foo', foo)` to link the handler to your valid object.

```python
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
        
def main():
    argcat = ArgCat()
    argcat.load("hello_cat.yml")
    foo = Foo()
    foo._value = "new value"
    argcat.set_handler('foo', foo)	# Link the handler to a valid instance object.
    argcat.parse()
```

Phew...

Ok. I think that's all for this README at this point. 

ArgCat is good, but not perfect. I will continue to improve it and update this documentation.

Hope you enjoy coding in Python.

`~Peace & Love~`

