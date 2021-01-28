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
        self._argument_parsers = {}
        self._argument_parser_handlers = {}
        self._argument_parser_arguments = {}
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

    def _create_argument_parsers(self):
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

        for key, value in parsers_dict.items():
            if key == 'main':
                argument_parser = main_argument_parser
            else:
                meta_value_dict = dict(value)
                if 'arguments' in meta_value_dict:
                    del meta_value_dict['arguments']
                argument_parser = argument_subparsers.add_parser(key, **meta_value_dict)
            self._argument_parsers[key] = argument_parser    
            # Add arguments
            parser_arguments_dict = value.get('arguments', [])   # might be None
            self._argument_parser_arguments[key] = parser_arguments_dict
            for args_dict in parser_arguments_dict:
                name_or_flags = args_dict['name_or_flags']
                meta_args_dict = dict(args_dict)
                del meta_args_dict['name_or_flags']
                # from type string to type class
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                meta_args_dict['type'] = locate(meta_args_dict['type'])
                argument_parser.add_argument(*name_or_flags, **meta_args_dict)
                

        # Handler
        handlers_dict = self._manifest_data['handlers']
        for handler_dict in handlers_dict:
            handler_object = handler_dict.get('object', None)
            links = handler_dict.get('links')
            print(links)
            if handler_object is not None:
                # TODO: functions from a class's instance
                pass
            else:
                # find hanlder funtions in __main__
                main_functions = self._all_functions_in_main()
                for link in links:
                    for k, v in link.items():
                        print("{},{}".format(k, v))
                        funcs = [item['func'] for item in main_functions if item['name'] == v]
                        if len(funcs) > 0:
                            theFunc = funcs[0]
                        else:
                            theFunc = None       
                        self._argument_parser_handlers[k] = theFunc
        print('---------')
        print(self._argument_parser_handlers)
        for k, v in self._argument_parser_handlers.items():
            if v is None:
                print("WARNING: No handler function for parser \"{}\"".format(k))

    def _all_functions_in_main(self):
        # print(inspect.stack()) 
        # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
        # https://stackoverflow.com/questions/18907712/python-get-list-of-all-functions-in-current-module-inspecting-current-module
        functions = [{'name': name, 'func': obj} for name, obj in inspect.getmembers(sys.modules['__main__']) 
        if (inspect.isfunction(obj))]
        
        print(functions)
        return functions

    def load(self, arguments_manifest):
        self._load_manifest(arguments_manifest)
        self._create_argument_parsers()
        # print(sys.modules)

    def parse(self):
        args = self._argument_parsers['main'].parse_args()
        args_dict = dict(vars(args))
        del args_dict['sub_parser_name']
        # If current parser is not 'main', remove all arguments from the 
        # namspace of 'main'. This step is to make sure the arguments input
        # into the handler function correct.
        if args.sub_parser_name != "main":
            for ad in self._argument_parser_arguments["main"]:
                dest = ad.get('dest', None)
                if dest is not None:
                    del args_dict[dest]
        print("args_dict after process:{}".format(args_dict))
        handler_func = self._argument_parser_handlers.get(args.sub_parser_name, None)
        if handler_func is not None:
            try:
                handler_func(**args_dict)               
            except TypeError:
                print("Handler function {} can not handle {} with args: {}".format(handler_func, args.sub_parser_name, args_dict))
        



