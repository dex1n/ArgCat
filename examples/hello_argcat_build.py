from argcat import ArgCat

def main():
    
    argcat = ArgCat()
            
    with argcat.build() as builder:
        # Set descriptive information of the program
        builder.set_prog_info(prog='PROG')
        builder.set_subparsers_info(help='sub-command help')
        
        # Add an argument to the main parser
        builder.main_parser().add_argument('--foo', action='store_true', help='foo help')
        
        # create the parser for the "a" command
        builder.add_subparser('a', help='a help')
        builder.subparser('a').add_argument('bar', type=int, help='bar help')
        
        # create the parser for the "b" command
        builder.add_subparser('b', help='b help')
        builder.subparser('b').add_argument('--baz', choices='XYZ', help='baz help')

    # parse some argument lists
    argcat.parse_args(['a', '12'])
    argcat.parse_args(['--foo', 'b', '--baz', 'Z'])
        
        
if __name__ == '__main__':
    main()