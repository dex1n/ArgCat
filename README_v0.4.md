# ArgCat - A cute helper for argparse in Python 3

**ArgCat** is a tiny tool designed to make it more joyful to use `argparse` module in Python 3.

As a bridge between developer and `argparse` module, it wraps `argparse`  and tries to take on all the "dirty works" for you, improving both the ''building" and "handling" parts of an `argparse` process, allowing you to focus more on business logic without worring about creating and configuring parsers and arguments of `argparse` in command-line interfaces.

## Installation

```bash
pip install argcat
```

Once installation done, you should get a **v0.4.x** version in your python package library , as the latest stable version is **v0.4.x**.

## Features

### Build parsers and arguments of `argparse` in a more straightforward and clearer way

A typical code snippet to create a program supports sub-commands using `argparse`:

(Snippet from "Sub-commands" section in https://docs.python.org/3/library/argparse.html)

```python
# Create the top-level parser
parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('--foo', action='store_true', help='foo help')
subparsers = parser.add_subparsers(help='sub-command help')

# Create the parser for the "a" command
parser_a = subparsers.add_parser('a', help='a help')
parser_a.add_argument('bar', type=int, help='bar help')

# Create the parser for the "b" command
parser_b = subparsers.add_parser('b', help='b help')
parser_b.add_argument('--baz', choices='XYZ', help='baz help')

# Parse some argument lists
parser.parse_args(['a', '12'])
parser.parse_args(['--foo', 'b', '--baz', 'Z'])
```

#### But, using ArgCat:

```python
argcat = ArgCat()

# Build parsers and arguments
with argcat.build() as builder:
    # Set descriptive information of the program
    builder.set_prog_info(prog='PROG')
    builder.set_subparsers_info(help='sub-command help')
            
    # Add an argument to the main parser
    builder.main_parser().add_argument('--foo', action='store_true', help='foo help')
            
    # Create the parser for the "a" command
    builder.add_subparser('a', help='a help')
    builder.subparser('a').add_argument('bar', type=int, help='bar help')
            
    # Create the parser for the "b" command
    builder.add_subparser('b', help='b help')
    builder.subparser('b').add_argument('--baz', choices='XYZ', help='baz help')

# Parse some argument lists
argcat.parse_args(['a', '12'])
argcat.parse_args(['--foo', 'b', '--baz', 'Z'])
```

### Handle parsed result from `argparse`  directly and easily

A typical code snippet to create a program supports sub-commands and handles the parsed result using `argparse`:

(Snippet from "Sub-commands" section in https://docs.python.org/3/library/argparse.html)

```python
# Sub-command functions
def foo(args):
    print(args.x * args.y)

def bar(args):
    print('((%s))' % args.z)

# Create the top-level parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

# Create the parser for the "foo" command
parser_foo = subparsers.add_parser('foo')
parser_foo.add_argument('-x', type=int, default=1)
parser_foo.add_argument('y', type=float)
parser_foo.set_defaults(func=foo)

# Create the parser for the "bar" command
parser_bar = subparsers.add_parser('bar')
parser_bar.add_argument('z')
parser_bar.set_defaults(func=bar)

# Parse the args and call whatever function was selected
args = parser.parse_args('foo 1 -x 2'.split())
args.func(args)

# Parse the args and call whatever function was selected
args = parser.parse_args('bar XYZYX'.split())
args.func(args)
```

#### Instead, using ArgCat:

```python
# Sub-command handler functions.
# Note that the parameters of the functions should be the dests of the arguments for 
# the parsers. ArgCat helps you to route the argument's inputs from the parsed args into
# the parsers' handler functions respectively.
def foo(x, y):
    print(x * y)

def bar(z):
    print('((%s))' % z)

argcat = ArgCat()
with argcat.build() as builder:
    # Create the parser for the "foo" command.
    builder.add_subparser('foo')
    builder.subparser('foo').add_argument('-x', type=int, default=1)
    builder.subparser('foo').add_argument('y', type=float)

    # Create the parser for the "bar" command.
    builder.add_subparser('bar')
    builder.subparser('bar').add_argument('z')

# Set handler functions for receiving and processing parsed result.
argcat.set_parser_handler('foo', foo)
argcat.set_parser_handler('bar', bar)

# Parse the args and the handler function `foo()` will be called with required 
# parameters automatically.
argcat.parse_args('foo 1 -x 2'.split())
# Parse the args and the handler function `bar()` will be called with required 
# parameters automatically.
argcat.parse_args('bar XYZYX'.split())
```

#### And, if you would like to set all handler functions at once, using ArgCat:

```python
# Sub-command handler functions, which are decorated for the respective parsers.
@ArgCat.handler(parser_name='foo')
def decorated_foo(x, y):
    print(x * y)
        
@ArgCat.handler(parser_name='bar')
def decorated_bar(z):
    print('((%s))' % z)    

argcat = ArgCat()
with argcat.build() as builder:
    # Create the parser for the "foo" command.
    builder.add_subparser('foo')
    builder.subparser('foo').add_argument('-x', type=int, default=1)
    builder.subparser('foo').add_argument('y', type=float)

    # Create the parser for the "bar" command.
    builder.add_subparser('bar')
    builder.subparser('bar').add_argument('z')

# Set handler functions all at once from a handler provider
# Supposed this code snippet is in a __main__ module, taking the module as the provider.
# ArgCat will try to find all functions decorated by @ArgCat.handler() and set them as 
# the the handlers for the parsers according to the `parser_name` set in the decorator
# respectively.
argcat.add_main_module_as_handler_provider()
# The above function call is a convenient way for below:
# argcat.add_handler_provider(sys.modules['__main__'])

# Parse the args and the handler function `foo()` will be called with required 
# parameters automatically.
argcat.parse_args('foo 1 -x 2'.split())
# Parse the args and the handler function `bar()` will be called with required 
# parameters automatically.
argcat.parse_args('bar XYZYX'.split())
```

#### A Few Further Explanations: (You may be curious about)

1. Handler Provider

   - A handler provider can be any object owns any functions decorated by `@ArgCat.handler()` with a parameter as a parser name. 

   - When setting a handler provider, ArgCat tries to find all handler functions of the provider at first. Then it collects all the parsers of the specified names from the decorated functions. In the end, it tries to link the functions to each parser picked respectively. 

2. Handler Functions

   - ArgCat supports all kinds of functions to be handler functions, such as instance methods, @staticmethod, @classmethod and the other callables. 

   - When decorating a callable to be a handler function, please make sure to place `@ArgCat.handler()` in the nearest place to the function definition, like below:

   ```python
   @classmethod
   @ArgCat.handler(parser_name='foo')
   def foo(cls):
       ...
   ```

   - A handler function's signature must match arguments' dests of its parsers. For example, if a parser has two arguments ['--x'] and ['-y'], its handler function should have a signature contains the exact two parameters: `(x, y)` . By contrast, the name of the function is arbitary. So, either `foo(x, y)` or `go(x, y)` can be the parser's handler function. 

     **Note:** There is a scenario which you may need to be aware of. Supposed you have one argument ['verbose'] for the main parser and also have a ['--file'] argument for the subparser 'load'. Then the handler function for the subparser should be in a form as `foo(verbose, file)` instead of `foo(file)` . Becase the subparser's handler function will also take the arguments from the main parser by default, unless the argument added to the main handler is through `add_exlusive_argument()` . Nevertheless, don't panic. Both `set_parser_handler()` and `add_handler_provider()` will check the signature for you and let you know what is the correct one.

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