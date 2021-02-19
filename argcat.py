#!/usr/bin/env python3

import os
import sys
import argparse
import inspect
import yaml
from pathlib import Path
from pydoc import locate
from enum import Enum, unique
from argparse import ArgumentParser, Namespace, _ArgumentGroup, _MutuallyExclusiveGroup, _SubParsersAction
from typing import ClassVar, List, Dict, Optional, Callable, Tuple, Any, Union

# May not be the best solution for the constants, but it's fine for now.
# And we don't need ClassVar[str] here because I think all constants' type are pretty clear.
class ManifestConstants:
    SUB_PARSER_NAME = 'sub_parser_name'
    SUBPARSER = 'subparser'
    PARSERS = 'parsers'
    DEST = 'dest'
    META = 'meta'
    ARGUMENTS = 'arguments'
    ARGUMENT_GROUPS = 'argument_groups'
    MAIN = 'main'
    IS_MUTUALLY_EXCLUSIVE = 'is_mutually_exclusive'
    DESCRIPTION = 'description'
    NAME_OR_FLAGS= 'name_or_flags'
    TYPE = 'type'
    GROUP = 'group'
    HANDLERS = 'handlers'
    DEFAULT = 'default'

@unique
class ArgCatPrintLevel(Enum):
    NORMAL = 0
    WARNING = 1
    ERROR = 2
    def __str__(self):
        if self.value == 0:
            return ""
        elif self.value == 1:
            return "WARNING: "
        elif self.value == 2:
            return "ERROR: "

class ArgCatPrinter:
    filter_level: ClassVar[ArgCatPrintLevel] = ArgCatPrintLevel.NORMAL
    @staticmethod
    def print(msg: str, level: ArgCatPrintLevel = ArgCatPrintLevel.NORMAL, indent: int = 0) -> None:
        if level.value < ArgCatPrinter.filter_level.value:
            return
        level_str: str = str(level)
        indent_str: str
        if indent <= 0 and level is ArgCatPrintLevel.NORMAL:
            indent_str = "# "
        else:
            indent_str = "  " * indent
        final_msg: str = indent_str + level_str + msg
        print(final_msg)

class ArgCatParser:
    def __init__(self, parser: ArgumentParser, name: str, arguments: List[Dict], groups: Optional[Dict] = None, 
    handler_func: Optional[Callable] = None):
        self._parser: ArgumentParser = parser
        self._name: str = name
        self._arguments: List[Dict] = arguments
        self._groups: Optional[Dict] = groups
        self._handler_func: Optional[Callable] = handler_func
    
    def set_handler_func(self, handler_func: Callable) -> None:           
        self._handler_func = handler_func

    def parse_args(self) -> Tuple[str, Dict]:
        # Call the main parser's parse_args() to parse the arguments input.
        args: Namespace = self._parser.parse_args()
        ArgCatPrinter.print("Parsing args: {}".format(args))
        parsed_arguments_dict: Dict = dict(vars(args))
        sub_parser_name: str = parsed_arguments_dict[ManifestConstants.SUB_PARSER_NAME]
        del parsed_arguments_dict[ManifestConstants.SUB_PARSER_NAME]
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
                dest: str = argument_dict.get(ManifestConstants.DEST, None)
                # Remove the argument by key in the parsed_arguments_dict.
                if dest is not None:
                    del parsed_arguments_dict[dest]
        else:
            sub_parser_name = self._name
        return sub_parser_name, parsed_arguments_dict

    @property
    def name(self) -> str:
        return self._name

    @property
    def arguments(self) -> List[Dict]:
        return self._arguments

    @property
    def handler_func(self) -> Optional[Callable]:
        return self._handler_func
    
    @handler_func.setter
    def handler_func(self, value) -> None:         
        self._handler_func = value

    @property
    def groups(self) -> Optional[Dict]:
        return self._groups
        
class ArgCat:
    def __init__(self):
        self._reset()

    def _reset(self) -> None:
        # A little bit of my naming convensions:
        # Member variables' names don't need to contain the type information
        # string, such as, 'dict', 'path', 'list'
        # By contrast, all local variables' names must contain the type 
        # information.
        self._arg_parsers: Dict = {}
        self._parser_handlers: Dict = {}
        self._manifest_data: Optional[Dict] = None

    def _load_manifest(self, manifest_file_path: str) -> None:
        ArgCatPrinter.print("Loading manifest file: {}".format(manifest_file_path))
        resolved_file_path: str = str(Path(manifest_file_path).resolve())
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

    def _create_parsers(self) -> None:
        if self._manifest_data is None:
            return
        ArgCatPrinter.print("Creating parsers...")
        meta_dict: Dict = self._manifest_data[ManifestConstants.META]
        main_parser_meta_dict: Dict = dict(meta_dict)
        del main_parser_meta_dict[ManifestConstants.SUBPARSER]

        # Main parser
        main_parser: ArgumentParser = argparse.ArgumentParser(**main_parser_meta_dict)
        parsers_dict: Dict = self._manifest_data[ManifestConstants.PARSERS]

        # Sub parsers
        sub_parser_meta_dict: Dict = meta_dict[ManifestConstants.SUBPARSER]
        sub_parser_meta_dict[ManifestConstants.DEST] = ManifestConstants.SUB_PARSER_NAME # reserved 
        argument_subparsers: _SubParsersAction = main_parser.add_subparsers(**sub_parser_meta_dict)

        for parser_name, parser_dict in parsers_dict.items():
            # Make meta dict
            parser_meta_dict = dict(parser_dict)
            if ManifestConstants.ARGUMENTS in parser_meta_dict:
                del parser_meta_dict[ManifestConstants.ARGUMENTS]
            if ManifestConstants.ARGUMENT_GROUPS in parser_meta_dict:
                del parser_meta_dict[ManifestConstants.ARGUMENT_GROUPS]

            # Add new parser
            new_parser: ArgumentParser
            if parser_name == ManifestConstants.MAIN:
                new_parser = main_parser
            else:
                new_parser = argument_subparsers.add_parser(parser_name, **parser_meta_dict)
            
            # Add argument groups
            argument_groups_dict = parser_dict.get(ManifestConstants.ARGUMENT_GROUPS, None)
            parser_argument_groups_dict: Optional[Dict]
            if argument_groups_dict is not None:
                parser_argument_groups_dict = {}
                for group_name, group_meta_dict in argument_groups_dict.items():
                    is_mutually_exclusive = group_meta_dict[ManifestConstants.IS_MUTUALLY_EXCLUSIVE]
                    if is_mutually_exclusive is True:
                        parser_argument_groups_dict[group_name] = new_parser.add_mutually_exclusive_group()
                    else:
                        group_description = group_meta_dict[ManifestConstants.DESCRIPTION]                        
                        parser_argument_groups_dict[group_name] = new_parser.add_argument_group(group_name, 
                        group_description)
            else:
                parser_argument_groups_dict = None
            # Add arguments into this new parser
            parser_arguments_list = parser_dict.get(ManifestConstants.ARGUMENTS, [])   # might be None
            for argument_dict in parser_arguments_list:
                name_or_flags: List = argument_dict[ManifestConstants.NAME_OR_FLAGS]
                argument_meta_dict = dict(argument_dict)
                del argument_meta_dict[ManifestConstants.NAME_OR_FLAGS]
                # from lexcical type to real type
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                argument_meta_dict[ManifestConstants.TYPE] = locate(argument_meta_dict[ManifestConstants.TYPE])
                # Add arguments considering we now support group and mutually exclusive group.
                object_to_add_argument: Union[ArgumentParser, _ArgumentGroup, _MutuallyExclusiveGroup]
                object_to_add_argument = new_parser
                if parser_argument_groups_dict is not None:
                    argument_group = argument_meta_dict.get(ManifestConstants.GROUP, None)
                    if argument_group is not None:
                        created_group = parser_argument_groups_dict.get(argument_group, None)
                        del argument_meta_dict[ManifestConstants.GROUP]
                        if created_group is not None:
                            object_to_add_argument = created_group
                
                object_to_add_argument.add_argument(*name_or_flags, **argument_meta_dict)
            # Add a new ArgCatPartser with None handler_func    
            self._arg_parsers[parser_name] = ArgCatParser(new_parser, parser_name, parser_arguments_list, 
            argument_groups_dict)

        # Handler
        self._parser_handlers = self._manifest_data[ManifestConstants.HANDLERS]
        self._init_default_handler_funcs()
        # Except for 'default' handler, there are custom handlers.
        # These handlers need to be configured by set_handler() before parse() being called.     
            
        self._list_parser_handler_funcs()

    def _list_parser_handler_funcs(self) -> None:
        ArgCatPrinter.print("Handler functions: ")
        for parser_name, parser in self._arg_parsers.items():
            warning_msg: str                
            if parser.handler_func is None:
                warning_msg = "- *WARNING* -"
            else:
                warning_msg = ""
            ArgCatPrinter.print("{} => {}  {}".format(parser_name, parser.handler_func, warning_msg), indent=1)

    def _init_default_handler_funcs(self) -> None:
        # Default handler is __main__
        default_handler_dict: Dict = self._parser_handlers[ManifestConstants.DEFAULT]
        if default_handler_dict is not None:                
            # Find all funtions in __main__
            # https://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
            # https://stackoverflow.com/questions/18907712/python-get-list-of-all-functions-in-current-module-inspecting-current-module
            main_funcs: List[Dict] = [{'name': name, 'func': obj} for name, obj in 
            inspect.getmembers(sys.modules['__main__']) if (inspect.isfunction(obj))]
            # Find the valid function exists in __main__ of the handler.
            for handler_parser_name, handler_func_name in default_handler_dict.items():
                funcs = [item['func'] for item in main_funcs if item['name'] == handler_func_name]
                handler_func: Optional[Callable]
                if len(funcs) > 0:
                    handler_func = funcs[0]
                else:
                    handler_func = None       
                self._arg_parsers[handler_parser_name].handler_func = handler_func

    def load(self, manifest_file_path: str) -> None:
        self._reset()
        self._load_manifest(manifest_file_path)
        self._create_parsers()

    def parse(self) -> Any:
        # Call the main parser's parse_args() to parse the arguments input.
        sub_parser_name, parsed_arguments_dict = self._arg_parsers[ManifestConstants.MAIN].parse_args()
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
            ArgCatPrinter.print("{} does not have any handler function.".format(sub_parser_name), 
            level=ArgCatPrintLevel.ERROR, indent=1)
        return None

    def set_handler(self, handler_name: str, handler: Any) -> None:
        ArgCatPrinter.print("Setting handler: \'{}\' .".format(handler_name))
        handler_dict: Dict = self._parser_handlers.get(handler_name, None)
        if handler_dict is not None:
            for handler_parser_name, handler_func_name in handler_dict.items():
                self._arg_parsers[handler_parser_name].handler_func = getattr(handler, handler_func_name)
        else:
            ArgCatPrinter.print("Unknown handler {} to set. Check your manifest file.".format(handler_name), 
            level=ArgCatPrintLevel.ERROR, indent=1)
        self._list_parser_handler_funcs()