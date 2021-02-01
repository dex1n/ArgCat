#!/usr/bin/env python3

import os
import sys
import argparse
import inspect
import yaml
from pathlib import Path
from pydoc import locate
from enum import Enum


class ArgCatPrintLevel(Enum):
    NORMAL = ""
    WARNING = "WARNING: "
    ERROR = "ERROR: "

class ArgCatPrinter:
    def print(msg: str, level: ArgCatPrintLevel = ArgCatPrintLevel.NORMAL, indent: int = 0):
        level_str = level.value
        if indent <= 0 and level is ArgCatPrintLevel.NORMAL:
            indent_str = "# "
        else:
            indent_str = "  " * indent
        final_msg = indent_str + level_str + msg
        print(final_msg)

class ArgCatParser:
    def __init__(self, parser, name, arguments, groups=None, handler_func=None):
        self._parser = parser
        self._name = name
        self._arguments = arguments
        self._handler_func = handler_func
        self._groups = groups
    
    def set_handler_func(self, handler_func):           
        self._handler_func = handler_func

    def parse_args(self):
        # Call the main parser's parse_args() to parse the arguments input.
        args = self._parser.parse_args()
        ArgCatPrinter.print("Parsing args: {}".format(args))
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
    def handler_func(self):
        return self._handler_func
    
    @handler_func.setter
    def handler_func(self, value):        
        self._handler_func = value

    @property
    def groups(self):
        return self._groups
        
class ArgCat:
    def __init__(self):
        self._reset()

    def _reset(self):
        # A little bit of my naming convensions:
        # Member variables' names don't need to contain the type information
        # string, such as, 'dict', 'path', 'list'
        # By contrast, all local variables' names must contain the type 
        # information.
        self._arg_parsers = {}
        self._parser_handlers = {}
        self._manifest_data = None

    def _load_manifest(self, manifest_file_path):
        ArgCatPrinter.print("Loading manifest file: {}".format(manifest_file_path))
        resolved_file_path = str(Path(manifest_file_path).resolve())
        if os.path.exists(resolved_file_path):
            with open(resolved_file_path) as f:
                try:
                    self._manifest_data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    self._manifest_data = None
                    ArgCatPrinter.print("Manifest file with path {} failed to load for exception: {}."
                    .format(resolved_file_path, exc), ArgCatPrintLevel.ERROR, 1)
        else:
            ArgCatPrinter.print("Manifest file with path {} cannot be found.".format(manifest_file_path), 
            level=ArgCatPrintLevel.ERROR, indent=1)

    def _create_parsers(self):
        if self._manifest_data is None:
            return
        ArgCatPrinter.print("Creating parsers...")
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
            # Make meta dict
            parser_meta_dict = dict(parser_dict)
            if 'arguments' in parser_meta_dict:
                del parser_meta_dict['arguments']
            if 'argument_groups' in parser_meta_dict:
                del parser_meta_dict['argument_groups']

            # Add new parser
            if parser_name == 'main':
                new_parser = main_parser
            else:
                new_parser = argument_subparsers.add_parser(parser_name, **parser_meta_dict)
            
            # Add argument groups
            argument_groups_dict = parser_dict.get('argument_groups', None)
            if argument_groups_dict is not None:
                parser_argument_groups_dict = {}
                for group_name, group_meta_dict in argument_groups_dict.items():
                    is_mutually_exclusive = group_meta_dict['is_mutually_exclusive']
                    if is_mutually_exclusive is True:
                        parser_argument_groups_dict[group_name] = new_parser.add_mutually_exclusive_group()
                    else:
                        group_description = group_meta_dict['description']                        
                        parser_argument_groups_dict[group_name] = new_parser.add_argument_group(group_name, 
                        group_description)
            else:
                parser_argument_groups_dict = None

            # Add arguments into this new parser
            parser_arguments_list = parser_dict.get('arguments', [])   # might be None
            for argument_dict in parser_arguments_list:
                name_or_flags = argument_dict['name_or_flags']
                argument_meta_dict = dict(argument_dict)
                del argument_meta_dict['name_or_flags']
                # from lexcical type to real type
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                argument_meta_dict['type'] = locate(argument_meta_dict['type'])
                # Add arguments considering we now support group and mutually exclusive group.
                object_to_add_argument = new_parser
                if argument_groups_dict is not None:
                    argument_group = argument_meta_dict.get('group', None)
                    if argument_group is not None:
                        created_group = parser_argument_groups_dict.get(argument_group, None)
                        del argument_meta_dict['group']
                        if created_group is not None:
                            object_to_add_argument = created_group
                
                object_to_add_argument.add_argument(*name_or_flags, **argument_meta_dict)
            # Add a new ArgCatPartser with None handler_func    
            self._arg_parsers[parser_name] = ArgCatParser(new_parser, parser_name, parser_arguments_list, argument_groups_dict)

        # Handler
        self._parser_handlers = self._manifest_data['handlers']
        self._init_default_handler_funcs()
        # Except for 'default' handler, there are custom handlers.
        # These handlers need to be configured by set_handler() before parse() being called.     
            
        self._list_parser_handler_funcs()

    def _list_parser_handler_funcs(self):
        ArgCatPrinter.print("Handler functions: ")
        for parser_name, parser in self._arg_parsers.items():                
            if parser.handler_func is None:
                warning_msg = "- *WARNING* -"
            else:
                warning_msg = ""
            ArgCatPrinter.print("{} => {}  {}".format(parser_name, parser.handler_func, warning_msg), indent=1)

    def _init_default_handler_funcs(self):
        # Default handler is __main__
        default_handler_dict = self._parser_handlers['default']
        if default_handler_dict is not None:                
            # Find all funtions in __main__
            # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
            # https://stackoverflow.com/questions/18907712/python-get-list-of-all-functions-in-current-module-inspecting-current-module
            main_funcs = [{'name': name, 'func': obj} for name, obj in 
            inspect.getmembers(sys.modules['__main__']) 
            if (inspect.isfunction(obj))]
            # Find the valid function exists in __main__ of the handler.
            for handler_parser_name, handler_func_name in default_handler_dict.items():
                funcs = [item['func'] for item in main_funcs if item['name'] == handler_func_name]
                if len(funcs) > 0:
                    handler_func = funcs[0]
                else:
                    handler_func = None       
                self._arg_parsers[handler_parser_name].handler_func = handler_func

    def load(self, manifest_file_path):
        self._reset()
        self._load_manifest(manifest_file_path)
        self._create_parsers()

    def parse(self):
        # Call the main parser's parse_args() to parse the arguments input.
        sub_parser_name, parsed_arguments_dict = self._arg_parsers['main'].parse_args()
        parser = self._arg_parsers[sub_parser_name]
        handler_func = parser.handler_func
        if handler_func is not None:
            try:
                result = handler_func(**parsed_arguments_dict)               
            except TypeError:
                ArgCatPrinter.print("Handler function {} can not handle \'{}\' with args: {}"
                .format(handler_func, sub_parser_name, parsed_arguments_dict), level=ArgCatPrintLevel.ERROR, indent=1)
            else:
                return result
        else:
            ArgCatPrinter.print("{} does not have any handler function.".format(sub_parser_name), level=ArgCatPrintLevel.ERROR, indent=1)

    def set_handler(self, handler_name, handler):
        ArgCatPrinter.print("Setting handler: \'{}\' .".format(handler_name))
        handler_dict = self._parser_handlers.get(handler_name, None)
        if handler_dict is not None:
            for handler_parser_name, handler_func_name in handler_dict.items():
                self._arg_parsers[handler_parser_name].handler_func = getattr(handler, handler_func_name)
        else:
            ArgCatPrinter.print("Unknown handler {} to set. Check your manifest file.".format(handler_name), 
            level=ArgCatPrintLevel.ERROR, indent=1)
        self._list_parser_handler_funcs()