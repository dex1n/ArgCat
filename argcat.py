#!/usr/bin/env python3

import os
import sys
import argparse
import inspect
import yaml
from pathlib import Path
from pydoc import locate

class ManifestLoadError(Exception):
    pass

class ArgCat:
    def __init__(self):
        self._parsers = {}
        self._parser_handler_funcs = {}
        self._parser_arguments = {}
        self._parser_custom_handlers = {}
        self._parser_custom_handler_funcs = {}
        self._manifest_file_path = None
        self._manifest_data = None

    def _load_manifest(self, arguments_manifest):
        file_path = str(Path(arguments_manifest).resolve())
        if os.path.exists(file_path):
            with open(file_path) as f:
                try:
                    raw_data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    raise ManifestLoadError from exc
                else:
                    self._manifest_data = raw_data
        else:
            print("Manifest file with path {} cannot be found.".format(arguments_manifest))

    def _create_parsers(self):
        meta_dict = self._manifest_data['meta']
        argument_parser_meta_arguments_dict = dict(meta_dict)
        del argument_parser_meta_arguments_dict['subparser']

        # Main parser
        main_argument_parser = argparse.ArgumentParser(**argument_parser_meta_arguments_dict)
        parsers_dict = self._manifest_data['parsers']

        # Sub parsers
        subparser_meta_dict = meta_dict['subparser']
        subparser_meta_dict['dest'] = 'sub_parser_name' # reserved 
        argument_subparsers = main_argument_parser.add_subparsers(**subparser_meta_dict)

        for parser_name, parser_dict in parsers_dict.items():
            if parser_name == 'main':
                argument_parser = main_argument_parser
            else:
                meta_parser_dict = dict(parser_dict)
                if 'arguments' in meta_parser_dict:
                    del meta_parser_dict['arguments']
                argument_parser = argument_subparsers.add_parser(parser_name, **meta_parser_dict)
            self._parsers[parser_name] = argument_parser    
            # Add arguments
            parser_arguments_dict = parser_dict.get('arguments', [])   # might be None
            self._parser_arguments[parser_name] = parser_arguments_dict
            for args_dict in parser_arguments_dict:
                name_or_flags = args_dict['name_or_flags']
                meta_args_dict = dict(args_dict)
                del meta_args_dict['name_or_flags']
                # from type string to type class
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                meta_args_dict['type'] = locate(meta_args_dict['type'])
                argument_parser.add_argument(*name_or_flags, **meta_args_dict)
            self._parser_handler_funcs[parser_name] = None

        # Handler
        handlers_dict = self._manifest_data['handlers']
        for handler_name, handler_dict in handlers_dict.items():
            # Default handler is __main__
            if handler_name == "default":
                # find handler funtions in __main__
                main_functions = self._all_functions_in_main()
                for handler_parser_name, handler_func_name in handler_dict.items():
                    funcs = [item['func'] for item in main_functions if item['name'] == handler_func_name]
                    if len(funcs) > 0:
                        handler_func = funcs[0]
                    else:
                        handler_func = None       
                    self._parser_handler_funcs[handler_parser_name] = handler_func
            else:
                # Custom object handler
                # This has to be configured before parse() being called
                self._parser_custom_handlers[handler_name] = handler_dict
            
        self._list_parser_handler_funcs()

    def _list_parser_handler_funcs(self):
        for k, v in self._parser_handler_funcs.items():
            if v is None:
                print("WARNING: No handler function for parser \"{}\"".format(k))
            else:
                print("Handler function {} for parser {}".format(k, v))

    def _all_functions_in_main(self):
        # print(inspect.stack()) 
        # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
        # https://stackoverflow.com/questions/18907712/python-get-list-of-all-functions-in-current-module-inspecting-current-module
        functions = [{'name': name, 'func': obj} for name, obj in inspect.getmembers(sys.modules['__main__']) 
        if (inspect.isfunction(obj))]
        print("-------main functions-------")
        print(functions)
        print("----------------------------")
        return functions

    def load(self, arguments_manifest):
        self._load_manifest(arguments_manifest)
        self._create_parsers()
        # print(sys.modules)

    def set_handler(self, handler_name, handler):
        handler_dict = self._parser_custom_handlers[handler_name]
        for handler_parser_name, handler_func_name in handler_dict.items():
            self._parser_handler_funcs[handler_parser_name] = getattr(handler, handler_func_name)
        print("Setting handler {}".format(handler_name))
        self._list_parser_handler_funcs()

    def parse(self):
        args = self._parsers['main'].parse_args()
        args_dict = dict(vars(args))
        del args_dict['sub_parser_name']
        # If current parser is not 'main', remove all arguments from the 
        # namspace of 'main'. This step is to make sure the arguments input
        # into the handler function correct.
        if args.sub_parser_name != "main":
            for ad in self._parser_arguments["main"]:
                dest = ad.get('dest', None)
                if dest is not None:
                    del args_dict[dest]
        print("args_dict after process: {}".format(args_dict))
        handler_func = self._parser_handler_funcs.get(args.sub_parser_name, None)
        if handler_func is not None:
            try:
                handler_func(**args_dict)               
            except TypeError:
                print("Handler function {} can not handle \'{}\' with args: {}".format(handler_func, args.sub_parser_name, args_dict))
        



