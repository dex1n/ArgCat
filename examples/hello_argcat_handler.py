from argcat import ArgCat

def main():
    
    # sub-command handler functions
    def foo(x, y):
        print(x * y)

    def bar(z):
        print('((%s))' % z)

    argcat = ArgCat()

    with argcat.build() as builder:
        # create the parser for the "foo" command
        builder.add_subparser('foo')
        builder.subparser('foo').add_argument('-x', type=int, default=1)
        builder.subparser('foo').add_argument('y', type=float)

        # create the parser for the "bar" command
        builder.add_subparser('bar')
        builder.subparser('bar').add_argument('z')

    argcat.set_parser_handler('foo', foo)
    argcat.set_parser_handler('bar', bar)
    
    # parse the args and call whatever function was selected
    argcat.parse_args('foo 1 -x 2'.split())
    # parse the args and call whatever function was selected
    argcat.parse_args('bar XYZYX'.split())

if __name__ == '__main__':
    main()