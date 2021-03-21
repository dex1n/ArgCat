#!/usr/bin/env python3

import os
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
    NAME_OR_FLAGS = 'name_or_flags'
    TYPE = 'type'
    GROUP = 'group'
    HANDLERS = 'handlers'
    DEFAULT = 'default'
    # Mainly used for main arguments. If this is set to True, the argument will be filtered out before being passed
    # into subparser's handler. Default value is False.
    IGNORED_BY_SUBPARSER = 'ignored_by_subparser'   

@unique
class ArgCatPrintLevel(Enum):
    # Print needed by user, for example, in print_parser_handlers()
    VERBOSE = 0
    IF_NECESSARY = 1
    WARNING = 2
    ERROR = 3
    def __str__(self):
        if self.value in [0, 1]:
            return ""
        elif self.value == 2:
            return "WARNING: "
        elif self.value == 3:
            return "ERROR: "

class ArgCatPrinter:
    filter_level: ClassVar[ArgCatPrintLevel] = ArgCatPrintLevel.VERBOSE
    log_prefix: ClassVar[str] = "<ArgCat>"
    indent_blank_str: ClassVar[str] = " " * 2
    
    @classmethod
    def print(cls, msg: str, *, level: ArgCatPrintLevel = ArgCatPrintLevel.VERBOSE, indent: int = 0) -> None:
        if level.value < cls.filter_level.value:
            return
        level_str: str = str(level)
        indent_str: str
        if indent <= 0:
            indent_str = cls.log_prefix + " "
        else:
            indent_str = cls.indent_blank_str * indent
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

    def parse_args(self, args: Optional[List[str]]=None, namespace: Optional[Namespace]=None) -> Tuple[str, Dict]:
        # Call the main parser's parse_args() to parse the arguments input.
        parsed_args: Namespace = self._parser.parse_args(args=args, namespace=namespace)
        ArgCatPrinter.print("Parsed args to: {}".format(parsed_args))
        parsed_arguments_dict: Dict = dict(vars(parsed_args))
        sub_parser_name: str = parsed_arguments_dict[ManifestConstants.SUB_PARSER_NAME]
        del parsed_arguments_dict[ManifestConstants.SUB_PARSER_NAME]
        # If the sub parser is needed, remove all arguments from the 
        # namspace belong to the main parser(parent parser) marked IGNORED_BY_SUBPARSER True. 
        # By default, all main parser's arguments will
        # stored in the args namespace even there is no the main arguments 
        # input. So, this step is to make sure the arguments input
        # into the handler correctly.
        if sub_parser_name is not None:
            for argument_dict in self._arguments:
                # 'dest' value is the key of the argument in the 
                # parsed_arguments_dict.
                dest: str = argument_dict.get(ManifestConstants.DEST, None)
                should_be_ignored: bool = argument_dict.get(ManifestConstants.IGNORED_BY_SUBPARSER, False)
                # Remove the argument by key in the parsed_arguments_dict.
                if dest is not None and should_be_ignored:
                    del parsed_arguments_dict[dest]
        else:
            sub_parser_name = self._name
        return sub_parser_name, parsed_arguments_dict

class ArgCat:
    @staticmethod
    def handler(parser_name):
        """ArgCat handler decorator.
        
        This is to make regular function/method become handler for ArgCat. And
        parser_name must be exactly the same as the parser's name defined in 
        the YAML file.
        """
        def decorator_handler(func):
            # Add the attribute to the decorated func.
            # In set_handler_provider(), all func with a valid 
            # argcat_argument_parser_name attribute will be found and 
            # recorded by the ArgCat instance for handling the parsed
            # arguments.
            func.argcat_argument_parser_name = parser_name
            return func
        return decorator_handler

    def __init__(self, chatter=False):
        """If chatter is True, ArgCat will display verbose prints. Otherwise,
        it will keep silence until the print_* methods are called."""
        self.chatter = chatter
        ArgCatPrinter.print("Your cute argument parsing helper. >v<")
        self._reset()

    @property
    def chatter(self) -> bool:
        return ArgCatPrinter.filter_level is ArgCatPrintLevel.VERBOSE

    @chatter.setter
    def chatter(self, value: bool) -> None:
        if value is True:
            ArgCatPrinter.filter_level = ArgCatPrintLevel.VERBOSE
        else:
            ArgCatPrinter.filter_level = ArgCatPrintLevel.IF_NECESSARY

    def _reset(self) -> None:
        # A little bit of my naming convensions:
        # Member variables' names don't need to contain the type information
        # string, such as, 'dict', 'path', 'list'
        # By contrast, all local variables' names must contain the type 
        # information.
        self._arg_parsers: Dict = {}
        self._manifest_data: Optional[Dict] = None

    def _load_manifest(self, manifest_file_path: str) -> None:
        ArgCatPrinter.print("Loading manifest file: {} ...".format(manifest_file_path))
        resolved_file_path: str = str(Path(manifest_file_path).resolve())
        if os.path.exists(resolved_file_path):
            with open(resolved_file_path) as f:
                try:
                    self._manifest_data = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    self._manifest_data = None
                    ArgCatPrinter.print("Manifest file with path {} failed to load for exception: {}."
                    .format(resolved_file_path, exc), level=ArgCatPrintLevel.ERROR)
                finally:
                    if not self._manifest_data:
                        ArgCatPrinter \
                        .print(f"Load empty manifest data from the given manifest file {manifest_file_path}.", 
                        level=ArgCatPrintLevel.WARNING)
        else:
            ArgCatPrinter.print("Manifest file with path {} cannot be found.".format(manifest_file_path), 
            level=ArgCatPrintLevel.ERROR)

    def _create_parsers(self) -> None:
        if not self._manifest_data:
            return
        ArgCatPrinter.print("Creating parsers ...")
        meta_dict: Dict = self._manifest_data[ManifestConstants.META]
        main_parser_meta_dict: Dict = dict(meta_dict)
        del main_parser_meta_dict[ManifestConstants.SUBPARSER]

        # Main parser
        main_parser: ArgumentParser = argparse.ArgumentParser(**main_parser_meta_dict)
        parsers_dict: Dict = self._manifest_data[ManifestConstants.PARSERS]

        # Sub parsers
        sub_parser_meta_dict: Dict = meta_dict[ManifestConstants.SUBPARSER]
        sub_parser_meta_dict[ManifestConstants.DEST] = ManifestConstants.SUB_PARSER_NAME # reserved 
        argument_subparsers: Optional[_SubParsersAction] = None

        for parser_name, parser_dict in parsers_dict.items():
            if parser_dict is None or len(parser_dict) == 0:
                continue
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
                # Create the subparsers when need.
                # This is to make sure: if main arguments are declared in the yaml before the subparsers' arguments,
                # they will be added and parsed before the subparsers' arguments. This is very important and useful
                # when there is any positional argument before the subparsers' ones. 
                # More details can be found from:
                # https://stackoverflow.com/questions/8668519/python-argparse-positional-arguments-and-sub-commands?rq=1
                if argument_subparsers is None:
                    argument_subparsers: _SubParsersAction = main_parser.add_subparsers(**sub_parser_meta_dict)
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
                name_or_flags: Optional[List] = argument_dict.get(ManifestConstants.NAME_OR_FLAGS, None)
                argument_meta_dict = dict(argument_dict)
                if ManifestConstants.IGNORED_BY_SUBPARSER in argument_meta_dict:
                    del argument_meta_dict[ManifestConstants.IGNORED_BY_SUBPARSER]
                # from lexcical type to real type
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                lexical_type: str = argument_meta_dict.get(ManifestConstants.TYPE, None)
                if lexical_type is not None:
                    argument_meta_dict[ManifestConstants.TYPE] = locate(lexical_type)
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
                if name_or_flags:
                    del argument_meta_dict[ManifestConstants.NAME_OR_FLAGS]
                    object_to_add_argument.add_argument(*name_or_flags, **argument_meta_dict)
                else: # Suppose it's str by default. If it's not, let it crash.
                    object_to_add_argument.add_argument(**argument_meta_dict)
            # Add a new ArgCatPartser with None handler_func    
            self._arg_parsers[parser_name] = ArgCatParser(parser=new_parser, name=parser_name, arguments=parser_arguments_list, 
            groups=parser_argument_groups_dict)

        if ManifestConstants.MAIN not in self._arg_parsers:
            self._arg_parsers[ManifestConstants.MAIN] = ArgCatParser(parser=main_parser, name=ManifestConstants.MAIN, arguments=[])

    def load(self, manifest_file_path: str) -> None:
        """Load manifest from file at path.

        The manifest file must be a YAML file and have valid information for
        ArgCat to load. 

        Returns None
        """
        self._reset()
        self._load_manifest(manifest_file_path)
        self._create_parsers()
        ArgCatPrinter.print("Loading DONE. Use print_xx functions for more information.")

    def parse_args(self, args: Optional[List[str]]=None, namespace: Optional[Namespace]=None) -> Any:
        """Start to parse args.

        This method is pretty much the same as the original parse_args of ArgumentParser, which means
        you can use it the same way as you use ArgumentParser's before.

        Returns result from handler. This is the only difference from the ArgumentParser's parse_args.
        The latter one returns a Namespace, but ArgCat returns the result from handler since 
        ArgCat has taken care of parsing the raw Namespace from ArgumentParser.
        """
        # Call the main parser's parse_args() to parse the arguments input.
        sub_parser_name, parsed_arguments_dict = self._arg_parsers[ManifestConstants.MAIN].parse_args(args=args, 
        namespace=namespace)
        parser = self._arg_parsers[sub_parser_name]
        handler_func = parser.handler_func
        if handler_func is not None:
            try:
                ArgCatPrinter.print("Handler {} is handling \'{}\' with args: {}"
                .format(handler_func, sub_parser_name, parsed_arguments_dict))
                result = handler_func(**parsed_arguments_dict)
            # Catch all exception to print the actual exception raised in the handler besides
            # TypeError. If we are only capturing TypeError, the actual error would be "covered" by the TypeError, which
            # means all error would be raised as TypeError. This could be very confusing.
            except Exception as exc:
                func_sig = inspect.signature(parser.handler_func)
                input_sig = str(tuple(parsed_arguments_dict)).replace('\'','')
                error_msg = "Handling function Exception: \"{}\", with function sig: {} and received parameters: {}."\
                    .format(exc, func_sig, input_sig)
                ArgCatPrinter.print(error_msg, level=ArgCatPrintLevel.ERROR, indent=1)
            else:
                return result
        else:
            ArgCatPrinter.print("{} does not have any handler.".format(sub_parser_name), 
            level=ArgCatPrintLevel.ERROR, indent=1)
        return None

    def add_handler_provider(self, handler_provider: Any) -> None:
        """Set an object as the provider for ArgCat to find handlers.

        The provider can normally be a (meta) class (instance), namespace or 
        anything has @ArgCat.handler decorated method/function.

        Returns None.
        """
        ArgCatPrinter.print("Setting handlers from provider: \'{}\' ...".format(handler_provider))
        all_handler_func_dicts: List[Dict] = [{'name': name, 'func': obj} for name, obj in 
        inspect.getmembers(handler_provider) if ((inspect.ismethod(obj) or inspect.isfunction(obj)) and hasattr(obj, "argcat_argument_parser_name"))]
        # The functions retrieved will be in alphabet order. So, if there are method/functions with duplicate names, 
        # the first one in the sequence will be added and the other ones will be discarded.
        if not all_handler_func_dicts:
            ArgCatPrinter.print(f"The handler provider '{handler_provider}' does not have any handler. Skip ...", 
            level=ArgCatPrintLevel.VERBOSE, indent=1)
            return
        for func_dict in all_handler_func_dicts:
            func = func_dict['func']
            func_name = func_dict['name']
            parser_name = func.argcat_argument_parser_name
            parser = self._arg_parsers.get(parser_name, None)
            if parser:
                # If there are multiple parser handlers being set to one parser, only set the first one.
                if not parser.handler_func:
                    parser.handler_func = func
                else:
                    ArgCatPrinter.print(f"Multiple handlers for one parser '{parser_name}'.", 
                    level=ArgCatPrintLevel.WARNING, indent=2)
            else:
                ArgCatPrinter.print(f"Unknown parser '{parser_name}' to set with handler '{func_name}'.", 
                level=ArgCatPrintLevel.WARNING, indent=2)

    def print_parser_handlers(self) -> None:
        """Show information of all handlers."""
        if not self._arg_parsers:
            ArgCatPrinter.print("ArgCat does not have any parser.", level=ArgCatPrintLevel.IF_NECESSARY)
            return
        ArgCatPrinter.print("Handlers: ", level=ArgCatPrintLevel.IF_NECESSARY)
        for parser_name, parser in self._arg_parsers.items():
            func_sig: Optional[inspect.Signature] = None
            if parser.handler_func is not None:
                func_sig = inspect.signature(parser.handler_func)
            ArgCatPrinter.print("{} => {} : {}".format(parser_name, parser.handler_func, func_sig), indent=1, 
            level=ArgCatPrintLevel.IF_NECESSARY)
    
    def print_parsers(self) -> None:
        """Show information of all parsers."""
        if not self._arg_parsers:
            ArgCatPrinter.print("ArgCat does not have any parser.", level=ArgCatPrintLevel.IF_NECESSARY)
            return
        ArgCatPrinter.print("Parsers: ", level=ArgCatPrintLevel.IF_NECESSARY)
        for parser_name, parser in self._arg_parsers.items():
            ArgCatPrinter.print("{}:".format(parser_name), indent=1, level=ArgCatPrintLevel.IF_NECESSARY)
            for arg in parser.arguments:
                dest = arg.get(ManifestConstants.DEST, None)
                name = arg.get(ManifestConstants.NAME_OR_FLAGS, dest)
                ArgCatPrinter.print("{} -> {}".format(name, dest), indent=2, level=ArgCatPrintLevel.IF_NECESSARY)