#!/usr/bin/python
"""
Example codes for building an ArgumentParser using Argcat.build() and setting handler parsers by
the handler provider.
"""
from argcat import ArgCat

@ArgCat.handler(parser_name='foo')
def foo_handler(x: int, y: float):
    """
    The parser handler for the parser "foo"
    """
    print(x * y)

@ArgCat.handler(parser_name='bar')
def bar_handler(z):
    """
    The parser handler for the parser "bar"
    """
    print(f'(({z}))')

def main():
    """
    Main func
    """
    argcat = ArgCat()

    with argcat.build() as builder:
        # create the parser for the "foo" command
        builder.add_subparser('foo')
        builder.subparser('foo').add_argument('-x', type=int, default=1)
        builder.subparser('foo').add_argument('y', type=float)

        # create the parser for the "bar" command
        builder.add_subparser('bar')
        builder.subparser('bar').add_argument('z')

    # Argcat will try to find the handler parsers defined in the main module scope.
    argcat.add_main_module_as_handler_provider()

    # parse the args and the parsed result will be passed into the handler
    # functions automatically
    argcat.parse_args('foo 1 -x 2'.split())
    argcat.parse_args('bar XYZYX'.split())

# Or if you would like to put the handler functions in this function:
def main_alt():
    """
    Main alternative
    """
    @ArgCat.handler(parser_name='foo')
    def foo_handler_alt(x, y):
        print(x * y)

    @ArgCat.handler(parser_name='bar')
    def bar_handler_alt(z):
        print(f'(({z}))')

    main_alt.foo = foo_handler_alt
    main_alt.bar = bar_handler_alt

    argcat = ArgCat()

    with argcat.build() as builder:
        # create the parser for the "foo" command
        builder.add_subparser('foo')
        builder.subparser('foo').add_argument('-x', type=int, default=1)
        builder.subparser('foo').add_argument('y', type=float)

        # create the parser for the "bar" command
        builder.add_subparser('bar')
        builder.subparser('bar').add_argument('z')

    argcat.add_handler_provider(main_alt)

    # parse the args and the parsed result will be passed into the handler
    # functions automatically
    argcat.parse_args('foo 1 -x 2'.split())
    argcat.parse_args('bar XYZYX'.split())


if __name__ == '__main__':
    main()
    #main_alt()
