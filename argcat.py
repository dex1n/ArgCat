#!/usr/bin/env python3

import os
import sys
import argparse
import inspect
import yaml
from pathlib import Path
from pydoc import locate

class ArgCatParser:
    def __init__(self, parser, name, arguments, handler_func=None):
        self._parser = parser
        self._name = name
        self._arguments = arguments
        self._handler_func = handler_func
    
    def set_handler_func(self, handler_func):           
        self._handler_func = handler_func

    def parser_args(self):
        # Call the main parser's parse_args() to parse the arguments input.
        args = self._parser.parse_args()
        print("# Parsing args: {}".format(args))
        sub_parser_name = args.sub_parser_name
        parsed_arguments_dict = dict(vars(args))
        del parsed_arguments_dict['sub_parser_name']
        # If the sub parser is needed, remove all arguments from the 
        # namspace belong to the main parser(parent parser). 
        # By default, all main parser's arguments will
        # stored in the args namespace even there is no the main arguments 
        # input. So, this step is to make sure the arguments input
        # into the handler function correct.
        if sub_parser_name is not None:
            for argument_dict in self._arguments:
                # 'dest' value is the key of the argument in the 
                # parsed_arguments_dict.
                dest = argument_dict.get('dest', None)
                # Remove the argument by key in the parsed_arguments_dict.
                if dest is not None:
                    del parsed_arguments_dict[dest]
        else:
            sub_parser_name = self._name
        return sub_parser_name, parsed_arguments_dict


    @property
    def name(self):
        return self._name

    @property
    def arguments(self):
        return self._arguments

    @property
    def handler_name(self):
        return self._handler_name

    @property
    def handler(self):
        return self._handler

class ArgCat:
    def __init__(self):
        pass

    def _initialize(self):
        # A little bit of my naming convensions:
        # Member variables' names don't need to contain the type information
        # string, such as, 'dict', 'path', 'list'
        # By contrast, all local variables' names must contain the type 
        # information.
        self._parsers = {}
        self._parser_handler_funcs = {}
        self._parser_arguments = {}
        self._parser_custom_handlers = {}
        self._parser_custom_handler_funcs = {}
        self._manifest_data = None

    def _load_manifest(self, manifest_file_path):
        print("# Loading manifest file: {}".format(manifest_file_path))
        resolved_file_path = str(Path(manifest_file_path).resolve())
        if os.path.exists(resolved_file_path):
            with open(resolved_file_path) as f:
                try:
                    self._manifest_data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    self._manifest_data = None
                    print("  Manifest file with path {} failed to load for exception: {}.".format(resolved_file_path, exc))
        else:
            print("  Manifest file with path {} cannot be found.".format(manifest_file_path))

    def _create_parsers(self):
        if self._manifest_data is None:
            return
        print("# Creating parsers...")
        meta_dict = self._manifest_data['meta']
        main_parser_meta_dict = dict(meta_dict)
        del main_parser_meta_dict['subparser']

        # Main parser
        main_parser = argparse.ArgumentParser(**main_parser_meta_dict)
        parsers_dict = self._manifest_data['parsers']

        # Sub parsers
        sub_parser_meta_dict = meta_dict['subparser']
        sub_parser_meta_dict['dest'] = 'sub_parser_name' # reserved 
        argument_subparsers = main_parser.add_subparsers(**sub_parser_meta_dict)

        for parser_name, parser_dict in parsers_dict.items():
            # Add new parser
            if parser_name == 'main':
                new_parser = main_parser
            else:
                parser_meta_dict = dict(parser_dict)
                if 'arguments' in parser_meta_dict:
                    del parser_meta_dict['arguments']
                new_parser = argument_subparsers.add_parser(parser_name, **parser_meta_dict)
            self._parsers[parser_name] = new_parser    
            # Add arguments into this new parser
            parser_arguments_list = parser_dict.get('arguments', [])   # might be None
            self._parser_arguments[parser_name] = parser_arguments_list
            for argument_dict in parser_arguments_list:
                name_or_flags = argument_dict['name_or_flags']
                argument_meta_dict = dict(argument_dict)
                del argument_meta_dict['name_or_flags']
                # from lexcical type to real type
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                argument_meta_dict['type'] = locate(argument_meta_dict['type'])
                # Add arguments
                self._parsers[parser_name].add_argument(*name_or_flags, **argument_meta_dict)
            # Initialize _parser_handler_funcs to set all function slot to None.     
            self._parser_handler_funcs[parser_name] = None

        # Handler
        handlers_dict = self._manifest_data['handlers']
        for handler_name, handler_dict in handlers_dict.items():
            # Default handler is __main__
            if handler_name == "default":
                # Find all funtions in __main__
                main_functions = self._all_functions_in_main()
                # Find the actual function exists in __main__ of the handler.
                for handler_parser_name, handler_func_name in handler_dict.items():
                    funcs = [item['func'] for item in main_functions if item['name'] == handler_func_name]
                    if len(funcs) > 0:
                        handler_func = funcs[0]
                    else:
                        handler_func = None       
                    self._parser_handler_funcs[handler_parser_name] = handler_func
            else:
                # Custom object handler
                # This has to be configured by set_handler() before parse() being called
                self._parser_custom_handlers[handler_name] = handler_dict
            
        self._list_parser_handler_funcs()

    def _list_parser_handler_funcs(self):
        print("# Handler functions: ")
        for parser_name, handler_func in self._parser_handler_funcs.items():
            if handler_func is None:
                warning_msg = "- *WARNING* -"
            else:
                warning_msg = ""
            print("  {} => {}  {}".format(parser_name, handler_func, warning_msg))

    def _all_functions_in_main(self):
        # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
        # https://stackoverflow.com/questions/18907712/python-get-list-of-all-functions-in-current-module-inspecting-current-module
        functions = [{'name': name, 'func': obj} for name, obj in 
        inspect.getmembers(sys.modules['__main__']) 
        if (inspect.isfunction(obj))]
        #print("-------main functions-------")
        #print(functions)
        #print("----------------------------")
        return functions

    def load(self, manifest_file_path):
        self._initialize()
        self._load_manifest(manifest_file_path)
        self._create_parsers()

    def parse(self):
        # Call the main parser's parse_args() to parse the arguments input.
        args = self._parsers['main'].parse_args()
        print("# Parsing args: {}".format(args))
        sub_parser_name = args.sub_parser_name
        parsed_arguments_dict = dict(vars(args))
        del parsed_arguments_dict['sub_parser_name']
        # If the needed parser is not 'main', remove all arguments from the 
        # namspace of 'main'. By default, all 'main' parser's arguments will
        # stored in the args namespace even there is no 'main' arguments 
        # input. So, this step is to make sure the arguments input
        # into the handler function correct.
        if sub_parser_name is not None:
            for argument_dict in self._parser_arguments["main"]:
                # 'dest' value is the key of the argument in the 
                # parsed_arguments_dict.
                dest = argument_dict.get('dest', None)
                # Remove the argument by key in the parsed_arguments_dict.
                if dest is not None:
                    del parsed_arguments_dict[dest]
        else:
            sub_parser_name = "main"
        handler_func = self._parser_handler_funcs.get(sub_parser_name, None)
        if handler_func is not None:
            try:
                result = handler_func(**parsed_arguments_dict)               
            except TypeError:
                print("Handler function {} can not handle \'{}\' with args: {}".format(handler_func, sub_parser_name, parsed_arguments_dict))
            else:
                return result
        else:
            print("{} does not have any handler function.".format(sub_parser_name))

    def set_handler(self, handler_name, handler):
        print("# Setting handler: \'{}\' .".format(handler_name))
        handler_dict = self._parser_custom_handlers[handler_name]
        for handler_parser_name, handler_func_name in handler_dict.items():
            self._parser_handler_funcs[handler_parser_name] = getattr(handler, handler_func_name)
        self._list_parser_handler_funcs()