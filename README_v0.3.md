# ArgCat - A cute helper for argparse in Python 3

**ArgCat** is a tiny tool designed to make it more joyful to use `argparse` module in Python 3.

It improves both the ''building" and "handling" parts of an argparse process, allowing developers to pay more attention to the business logic without worring about configuring parsers and arguments.

## Building argument parsers

A typical code snippet to build argument parsers for a command-line would be as below:

```python
import argparse

argument_parser = argparse.ArgumentParser(prog='Cool program name', description='Awesome description')
argument_parser.add_argument("-t", "--test", nargs='?', dest='test', metavar='TEST', type=str, help='Just for test')

argument_subparsers = argument_parser.add_subparsers(dest = "sub_command", title='The subparsers title"', description="The subparsers description", help='The subparsers help')
    
init_parser = argument_subparsers.add_parser('init', help="Initialize something.")

info_parser = argument_subparsers.add_parser('info', help="Show information of something.")
info_parser.add_argument("-d", "--detail", nargs='?', dest='detail', metavar='DETAIL', type=str, help='The detail of the information')

config_parser = argument_subparsers.add_parser('config', help="Config something.")
config_arg_group = config_parser.add_mutually_exclusive_group()
config_arg_group.add_argument("-n", "--name", nargs='?', dest='name', metavar='NAME', type=str, help='The name.')
config_arg_group.add_argument("-u", "--username", nargs='?', dest='user_name', metavar='USER_NAME', type=str, help='The user name.')
```

This snippet creates an argument parser which has one `test` argument and 3 sub argument parsers which also has a few arguments and group accordingly. These tedious parameters for setting might not be a big deal. The biggest problem is the structure of the argument parsers are drown in this flood of add_xxx functions and parameters. In other words, **it's easy to get lost in the codes and miss the point of what this argument parser really is and how to use it according to the codes**, though the `argparse`'s APIs themselves are not hard to use and understand. 

To solve the problem, ArgCat provides two different ways to make the building process more structured and clearer. 

### Building from YAML

The first way uses a YAML file. ArgCat allows to define and config ArgumentParser in a YAML format file then creates the ArgumentParser instances by `load()` this file in the runtime without any codes for explicit building.

~~In this way, ArgumentParser can be loaded directly from a YAML file without any codes for building.~~

```python
from argcat import ArgCat
argcat = ArgCat()
argcat.load("simple.yml") # Load the settings from the YAML file.
argcat.parse_args() # Start to parse the args input.
```

The YAML file has a few special requirements, but it basically just contains the parameters/configurations for setting up parser and argument for `argparse`.

For the same ArgumentParser we just built by `argparse` in the above snippet, a corresponding YAML file would be like below:

```yaml
meta: # Include all essential configurations used for creating a new ArgumentParser.
  prog: "Cool program name"
  description: "Awesome description"
  subparser:
    title: "The subparsers title"
    description: "The subparsers description"
    help: "The subparsers help"
parsers:
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



~~As the comments in the YAML file imply, the YAML file has a few special requirements and formats, but it basically just needs the parameters/configurations for setting up parser and argument in `argparse`.~~

### Build from codes:

In addition, ArgCat also provides another way to build ArgumentParser from codes in v0.3. 

```python
argcat = ArgCat()
# This is to create an argcat with the same content as what we created by load(), but through build().
with argcat.build() as builder:
		# Set basic information
    builder.set_prog_info(prog_name='Cool program name', 
                          description='Awesome description')
    
    builder.set_sub_parser_info(title='The subparsers title', 
                                description='The subparsers description', 
                                help='The subparsers help')
        
    # Add an exclusive argument for the main parser.
    builder.main_parser().add_exclusive_argument('test', nargs='?', metavar='TEST', 
                                                 type=str, help='Just for test')
        
    # Add a sub parser without any arguments.
    builder.add_sub_parser('init', help='Initialize something.')
        
    # Add a sub parser with one argument.
    builder.add_sub_parser('info', help='Show information of something.')
    builder.sub_parser('info').add_argument('detail', nargs='?', metavar='DETAIL', 
                                            type='str', 
                                            help='The detail of the information')
        
    # Add a sub parser with one mutually exclusive group and two arguments
    builder.add_sub_parser('config', help="Config something.")
    builder.sub_parser('config').add_group('a_group', description="Group description", 
                                           is_mutually_exclusive=True)
    builder.sub_parser('config').add_argument('-n', '--name', nargs='?', dest='name', 
                                              metavar='NAME', type='str',
                                              help='The name.', group='a_group')
    builder.sub_parser('config').add_argument('-u', '--username', nargs='?',
                                              dest='user_name', metavar='USER_NAME', 
                                              type='str', help='The user name.', 
                                              group='a_group')
```

With an ArgCat builder, ArgumentParser can be created in a pretty clear and structured way. 

## Handling parsed arguments

Now we've already had an ArgumentParser for work, then how do we handle the parsed arguments? 

A typical code snippet would be like this:

```python
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

As we can see, the problem is that we would have to manually route the parsed result into the different handler functions. This may include multiple tedious if-else checks and function calls with parameters retrieved from the parsed arguments, which might be buggy and hard to maintain.

To solve the problem, ArgCat takes care of the routing and make it an automatic and transparent process to us. What we need to do is only to inform ArgCat with handler functions for each parsers of the ArgumentParser. Once ArgCat receives the parsed arguments, it will pass the argument values to each handler functions respectively according to their dests. 

```python
def main_handler(test):
    print("Test:", test)
   
def config_handler(name, user_name):
  	print(f"name:{name}, user name: {user_name}")
    
argcat = ArgCat()
...
argcat.set_parser_handler(parser_name='main', handler=main_handler)
argcat.set_parser_handler(parser_name='config', handler=config_handler)
argcat.parse_args()
```

What's more, ArgCat can check the signature of the handler functions to be set to make sure it can receive the parsed argument values correctly. If the signature does not match the parser's dests, an error will be reported and the setting will fail.

```python
# This signature does not match the `info` parser's dests: ['detail']
def info_handler(verbose): 
    print(f"verbose: {verbose}")
# Below will fail and report error.
argcat.set_parser_handler(parser_name='info', handler=info_handler) 
```

ArgCat provides two ways for us to let it know handler functions for the parsers. 

### Handler Provider

A handler provider can be any object contains any functions decorated by decorator  `ArgCat.handler()` with a parameter for a parser name. 

When setting a handler provider, ArgCat firstly finds all handler functions of the provider. Then it find all the parsers of the specified names and tries to link the functions to each parser respectively. 

```python
class Foo:
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
		# Find handlers in __main__
		argcat.add_handler_provider(sys.modules['__main__'])
		# Find handlers in Foo
		argcat.add_handler_provider(foo)
```

###### Notes

1. The function `main_handler()` is in `__main__`, so the corresponding `provider` should be `sys.modules['__main__']` which returns the `__main__` scope object contains the function. 
2. As you can see in the snippet, ArgCat supports different kinds of handler functions including class instance methods, @staticmethod, @classmethod and regular functions. 
3. As for decorating function with a decorator, please make sure to put  `ArgCat.handler()`  in the nearest place to the function definition.

### Direct Set

Another way is much more straightforward. ArgCat provides us a method  `ArgCat.set_parser_handler()` to set any function as the handler function for a parser directly. Note that no decorator is needed for the functions to be set in this way.

```python
# Regular function
#@ArgCat.handler("main") 
# This decorator is not needed if we just set it through set_parser_handler().
def main_handler(test):
    print("main_handler {}".format(test))
argcat = ArgCat()
...
argcat.set_parser_handler(parser_name='main', handler=main_handler)
```

### The requirement of A Handler Function

#### Parser name

The parser's name must be exactly the same as the one of a created parser.

So, if you define a parser named "init" in the config file, 

```YAML
init: # This is a subparser without any argument but only a help tip.
    help: "Initialize something."
```

then the parameter `parser_name ` of the decorator must be "init" if this handler function is for the parser named "init".

```Python
@ArgCat.handler("init") # Handle arguments for parser named "init"
    def init_handler():
      print("init_handler")
```

#### Decorators

If a handler function is a function with decorators such as `@staticmethod` or `@classmethod`, the decorator `@ArgCat.handler()` should be put closest to the function's definition:

```python
# Class method
@classmethod
@ArgCat.handler("info")  # This decorator must be placed closest to the method.
def info_handler(cls, detail):
    print("info_handler with detail: {}".format(detail))
```

#### Signature

Handler function's signature must match the dests of the parsers. 

A dest should be the most important property for an argument of an ArgumentParser. Every argument has a dest to receive an input from command-line, and `argparse` parses the raw inputs into each dest, packing the dests of all the parsers into a tuple. ArgCat picks all the values needed for a parser according to its dests in the tuple, and then it packs these values with dests as the keys into a dict and passes it into the parser's handler function. 





For instances, in the above codes, `config_handler()` has two parameters `name` and `user_name` except `self`. They exactly match what `config`'s declared arguments below. In other words, if `config` parser has only 2 arguments and their `dest` are `name` and `user_name`, the handler function must also have 2 parameters which must be `name` and `user_name`.

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

### 















ArgCat provides two different ways for building an argument parser. 



































## License

```
MIT License

Copyright (c) 2022 Chunxi Xin

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