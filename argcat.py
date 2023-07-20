#!/usr/bin/env python3

import argparse
import inspect
import sys
import functools
from copy import deepcopy
from pydoc import locate
from enum import Enum, unique
from argparse import ArgumentParser, Namespace, _ArgumentGroup, _MutuallyExclusiveGroup, _SubParsersAction, Action
from typing import ClassVar, List, Dict, Optional, Callable, Tuple, Any, Union


# May not be the best solution for the constants, but it's fine for now.
# And we don't need ClassVar[str] here because I think all constants' type are pretty clear.
class _ManifestConstants:
    META = "meta"
    METAVAR = "metavar"
    PROG = "prog"
    DESCRIPTION = "description"
    TITLE = "title"
    HELP = "help"
    NARGS = "nargs"
    SUBPARSER_NAME = 'subparser_name'
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
    REQUIRED = 'required'
    ACTION = 'action'
    CHOICES = 'choices'
    CONST = 'const'
    HELP = 'help'
    # Mainly used for main arguments. If this is set to True, the argument will be filtered out before being passed
    # into subparser's handler. Default value is False.
    IGNORED_BY_SUBPARSER = 'ignored_by_subparser'
    DEFAULT_HANDLER = 'default_handler'   


# Default manifest
class _ARGUMENT_DEFAULTS_:
    # NOTE : REMEMBER TO USE DEEP COPY WHEN SETTING THIS DICT AS A DEFAULT DICT
    META = {
        _ManifestConstants.PROG: "ArgCat GO~",
        _ManifestConstants.DESCRIPTION: "It's sooo freeesh~",
        # In build mode, we don't use these by default to make the help texts clean.
        # ManifestConstants.SUBPARSER: {
        #     ManifestConstants.TITLE: "The subparsers title",
        #     ManifestConstants.DESCRIPTION: "The subparsers description",
        #     ManifestConstants.HELP: "The subparsers help"
        # }
    }
    NARGS = "?"
    TYPE = "str"
    DEST = "dest"
    HELP = ""
    METAVAR = "metavar"
    # NOTE : REMEMBER TO USE DEEP COPY WHEN SETTING THIS DICT AS A DEFAULT DICT
    PARSERS = {
        # There is a `main` parser by default
        _ManifestConstants.MAIN: { _ManifestConstants.ARGUMENTS: [] }
    }
    
@unique
class _ArgCatPrintLevel(Enum):
    # Print needed by user, for example, in print_parser_handlers()
    VERBOSE = 0
    IF_NECESSARY = 1
    WARNING = 2
    ERROR = 3
    def __str__(self):
        if self.value in [0, 1]:
            return "[ LOG ]: "
        elif self.value == 2:
            return "[ *WARNING* ]: "
        elif self.value == 3:
            return "[ #ERROR# ]: "

class _ArgCatPrinter:
    filter_level: ClassVar[_ArgCatPrintLevel] = _ArgCatPrintLevel.VERBOSE
    log_prefix: ClassVar[str] = "<ArgCat>"
    indent_blank_str: ClassVar[str] = " " * 2
    
    @classmethod
    def print(cls, msg: str, *, level: _ArgCatPrintLevel = _ArgCatPrintLevel.VERBOSE, indent: int = 0) -> None:
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

class _ArgCatParser:
    _parser: ArgumentParser
    _name: str
    _arguments: List[Dict]
    _dests: List[str]
    _groups: Optional[Dict]
    _handler_func: Optional[Callable]
    _additional_argument_info: Optional[dict]
    
    def __init__(self, parser: ArgumentParser, name: str, arguments: List[Action], additional_arguments_info: Dict, 
                 groups: Optional[Dict] = None, handler_func: Optional[Callable] = None):
        self._parser = parser
        self._name = name
        self._arguments = arguments
        self._dests = [arg.dest for arg in arguments]
        self._groups = groups
        self._handler_func = handler_func
        
        # {argument.dest: {_ManifestConstants.IGNORED_BY_SUBPARSER: None, _ManifestConstants.GROUP: None}}
        self._additional_argument_info = additional_arguments_info
    
    @property
    def name(self) -> str:
        return self._name

    @property
    def arguments(self) -> List[Action]:
        return self._arguments

    @property
    def dests(self) -> List[str]:
        return self._dests
    
    @property
    def handler_func(self) -> Optional[Callable]:
        return self._handler_func
    
    @handler_func.setter
    def handler_func(self, value: Optional[Callable]) -> None:         
        self._handler_func = value

    @property
    def groups(self) -> Optional[Dict]:
        return self._groups

    @property
    def parser(self) -> ArgumentParser:
        return self._parser
    
    @property
    def additional_arguments_info(self) -> Dict:
        return self._additional_argument_info
    
    def parse_args(self, args: Optional[List[str]]=None, namespace: Optional[Namespace]=None) -> Tuple[str, Dict, Dict]:
        # Call the main parser's parse_args() to parse the arguments input.
        parsed_args: Namespace = self._parser.parse_args(args=args, namespace=namespace)
        _ArgCatPrinter.print("Parsed args result: `{}`.".format(parsed_args))
        parsed_arguments_dict: Dict = dict(vars(parsed_args))
        subparser_name: str = parsed_arguments_dict.get(_ManifestConstants.SUBPARSER_NAME, None)
        
        # ManifestConstants.SUBPARSER_NAME is not needed for the handlers.
        # So, delete it from the argument dict if it exists.
        if _ManifestConstants.SUBPARSER_NAME in parsed_arguments_dict:
            del parsed_arguments_dict[_ManifestConstants.SUBPARSER_NAME]
        
        parsed_arguments_dict_for_cur_parser = {}
        # Firstly, pick all arguments parsed of the current parser.
        for k, v in parsed_arguments_dict.items():
            if k in self._dests:
                parsed_arguments_dict_for_cur_parser[k] = v
        
        # If the subparser is needed, remove all arguments from the 
        # namspace belong to the main parser(parent parser) marked IGNORED_BY_SUBPARSER True. 
        # By default, all main parser's arguments will
        # stored in the args namespace even there is no the main arguments 
        # input. So, this step is to make sure the arguments input
        # into the handler correctly.
        if subparser_name:
            for argument in self._arguments:
                # 'dest' value is the key of the argument in the parsed_arguments_dict.
                dest: str = argument.dest
                should_be_ignored: bool = \
                self._additional_argument_info[dest].get(_ManifestConstants.IGNORED_BY_SUBPARSER, True)
                # Remove the argument by key in the parsed_arguments_dict.
                if dest is not None and should_be_ignored:
                    del parsed_arguments_dict[dest]
        else:
            parsed_arguments_dict = None    # If subparser_name is None, clear this make sure it cannot be used.
        
        # parsed_arguments_dict now is a dict contains arguments only for the subparser.
        return subparser_name, parsed_arguments_dict, parsed_arguments_dict_for_cur_parser

class _ArgCatBuilder:
    # NOTE: Try not to initialize a collection here, otherwise all instances of _ArgCatBuilder will have a member 
    # variable _manifest_data points to the SAME dict. This is a very subtle issue can cause serious bugs.
    _manifest_data: Dict # = {} 
    _on_build_done: Callable[[Dict], None]
    
    def __init__(self, on_build_done: Callable):
        self._manifest_data = {}
        self._on_build_done = on_build_done
    
    # For with statement: enter is before `with` body.
    def __enter__(self):
        # Init data with default values.
        # NOTE: DEEP COPY IS A MUST! Otherwise, all _manifest_data of _ArgCatBuilder instances will have and operate on
        # the same META and PARSERS dict, which is a epic serious bug.
        self._manifest_data[_ManifestConstants.META] = deepcopy(_ARGUMENT_DEFAULTS_.META)
        self._manifest_data[_ManifestConstants.PARSERS] = deepcopy(_ARGUMENT_DEFAULTS_.PARSERS)
        
        return self
    
    # For with statement: exit is after `with` body.
    def __exit__(self, type, value, traceback):
        self._on_build_done(self._manifest_data)
    
    def _select_parser_by_name(self, parser_name: str) -> Dict:
        parsers: Dict = self._manifest_data[_ManifestConstants.PARSERS]
        # Select the parser by name.
        # It may be a 'main' parser or any other subparser.
        the_parser = parsers.setdefault(parser_name, None)
        return the_parser
    
    def _add_parser_with_name(self, parser_name: str) -> Dict:
        parsers: Dict = self._manifest_data[_ManifestConstants.PARSERS]
        new_parser = { _ManifestConstants.ARGUMENTS: [] }
        parsers[parser_name] = new_parser
        return new_parser
    
    def set_prog_info(self, **kwargs) -> Dict:
        """Set basic information of program.
        
        `**kwargs` will be used to initialize the main parser of this program by `argparse.ArgumentParser()` without any
        modification from ArgCat. So, it is exactly the same as the one for `argparse.ArgumentParser()`. More details 
        about all the acceptable keys and values in `**kwargs` can be found in `argparse.ArgumentParser()`.
        
        This function can be omitted. If so, the "prog" and "description" will be set to default values.
        
        Returns a dict contains kwargs.
        """
        for k,v in kwargs.items():
            self._manifest_data[_ManifestConstants.META][k] = v
        return deepcopy(kwargs)
    
    def set_subparsers_info(self, **kwargs) -> Dict:
        """Set basic information of subparsers.
        
        `**kwargs` will be used to initialize the subparsers of the main parser by 
        `argparse.ArgumentParser.add_subparsers()` without any modification from ArgCat. So, `**kwargs` here is exactly 
        the same as the one for `argparse.ArgumentParser.add_subparsers()`.
        
        This function can be omitted. If so, an empty `**kwargs` will be used for the initialization.
        
        Returns a dict contains kwargs.
        """
        subparsers_data = self._manifest_data[_ManifestConstants.META].get(_ManifestConstants.SUBPARSER, {})
        for k,v in kwargs.items():
            subparsers_data[k] = v
        return deepcopy(kwargs)
    
    def add_subparser(self, parser_name: str, **kwargs: str) -> Optional[Dict]:
        """Add a new subparser
        
        `parser_name` is the name of the new subparser to add. If there has already been a parser with the same name
        added, this method will fail and None will be returned.
        
        `**kwargs` is exactly the same as the one passed into `argparse.ArgumentParser.add_parser()`. ArgCat does not 
        modify any elements of it.
        
        Returns a dict contains the parser's information from `*args, **kwargs` and ArgCat, or 
        None if a parser with the same name has already existed.
        """
        the_parser = self._select_parser_by_name(parser_name)
        if the_parser:
            _ArgCatPrinter.print(f"`{parser_name}` parser has already existed so cannot be added again.", 
                                 level=_ArgCatPrintLevel.ERROR)
            return None
        
        new_parser = self._add_parser_with_name(parser_name)
        for k,v in kwargs.items():
            new_parser[k] = v
        return deepcopy(new_parser)
    
    class __ArgCatParserArgumentBuilder:
        _parser: Dict # parser dict to add argumemt information
        
        def __init__(self, parser: Dict) -> None:
            self._parser = parser
        
        def _add_argument(self, ignored_by_subparser: bool, *args: str, **kwargs: str) -> Dict:
            new_argument = {} # An empty argument.
            if args:
                new_argument[_ManifestConstants.NAME_OR_FLAGS] = args
            new_argument[_ManifestConstants.IGNORED_BY_SUBPARSER] = ignored_by_subparser
            for k, v in kwargs.items():
                new_argument[k] = v
            arguments: List = self._parser[_ManifestConstants.ARGUMENTS]
            arguments.append(new_argument)
            # Make sure we don't return the actual dict of the argument information to prevent the internal dict from 
            # being modified outside the builder unexpectedly.
            return deepcopy(new_argument)
            
        def add_argument(self, *args: str, **kwargs: str) -> Dict:
            """Add a new argument
        
            `*args, **kwargs` is exactly the same as those for `argparse.ArgumentParser.add_argument()`. ArgCat just 
            uses these as they are without any further modification. So, if there is any complain/error due to your 
            input, don't blame the cat. LOL. (DOGE):P
        
            Returns a dict contains the argument information from `*args, **kwargs` and ArgCat.
            """
            return self._add_argument(False, *args, **kwargs)
        
        def add_group(self, group_name: str, description: Optional[str] = None, 
                      is_mutually_exclusive: bool = False) -> Optional[Dict]:
            """Add a new group for a parser.
            Returns a dict contains the group information or None if any errors.
            """
            the_groups = self._parser.setdefault(_ManifestConstants.ARGUMENT_GROUPS, {})
            new_group = the_groups.get(group_name, {})
        
            if new_group:
                _ArgCatPrinter.print(f"Failed to add the group `{group_name}`, as there has already been a group of" +
                                     " the same name.", 
                                    level=_ArgCatPrintLevel.WARNING)
                return None
        
            new_group[_ManifestConstants.DESCRIPTION] = description
            new_group[_ManifestConstants.IS_MUTUALLY_EXCLUSIVE] = is_mutually_exclusive
        
            the_groups[group_name] = new_group
            
            # Make sure we don't return the actual dict of the group information to prevent the internal dict from being 
            # modified outside the builder unexpectedly.
            return deepcopy(new_group)
    
    class __ArgCatMainParserArgumentBuilder(__ArgCatParserArgumentBuilder):
        
        def add_exclusive_argument(self, *args: str, **kwargs: str) -> Dict:
            """Add a new exclusive argument
            
            An exclusive argument for `main` parser is one argument whose `ignored_by_subparser` property is True,
            which means being ignored by any other subparsers.

            `ignored_by_subparser` is very important for arguments of `main` parsers.
            If `ignored_by_subparser` is True, any arguments created with this will only be passed to the handler for 
            `main` parser. Otherwise, the arguments will be also passed to all the subparser's handlers. This setting
            can decide the signature of the handlers directly. 
            For example, supposed `main` parser has an argument ['verbose'] and a subparser `load` has an argument 
            ['-f', '--file']. If ['verbose'] is `ignored_by_subparser`, the subparser's handler should be `func(file)`,
            which ignores ['verbose']. Instead, if ['verbose'] is not `ignored_by_subparser`, the subparser's handler 
            should be `func(verbose, file)`, which contains the main parser's argument ['verbose'].
        
            `*args, **kwargs` is exactly the same as those in `argparse.add_argument()`. ArgCat just passes these as
            they are into `argparse.add_argument()` without doing any further operation. So, if there is any 
            complain/error due to your input, don't blame the cat. (DOGE):P
        
            Returns a dict contains the argument information from `*args, **kwargs` and ArgCat.
            """
            return self._add_argument(True, *args, **kwargs)
    
    def main_parser(self) -> __ArgCatMainParserArgumentBuilder:
        """Start to create new arguments for the 'main' parser
        Returns an _ArgCatArgumentBuilder for add_argument() or add_exclusive_argument() arguments with configs.
        """
        the_parser = self._select_parser_by_name('main')
        # Theoretically, the_parser should never be None forever. 
        return self.__ArgCatMainParserArgumentBuilder(the_parser)
    
    def subparser(self, parser_name: str) -> Optional[__ArgCatParserArgumentBuilder]:
        """Start to create new arguments for a subparser.
        
        `parser_name` should be a valid name string other than `main`, which has already be used by the main parser by
        default. If the parser of the name does not exist, an error would be reported.
        
        Returns an __ArgCatParserArgumentBuilder for add_argument() arguments with configs, or
        None if the parser is not valid.
        """
        the_parser = self._select_parser_by_name(parser_name)
        if the_parser:
            return self.__ArgCatParserArgumentBuilder(the_parser)
        _ArgCatPrinter.print(f"`{parser_name}` parser is not valid.", level=_ArgCatPrintLevel.ERROR)
        return None
    
# Only public class for use. #      
class ArgCat:
    @staticmethod
    def handler(parser_name):
        """ArgCat handler decorator.
        
        This is to make regular function/method become handler for ArgCat. And
        parser_name must be exactly the same as the parser's name. (Blah blah)
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

    def __init__(self, chatter: bool=False):
        """
        If chatter is True, ArgCat will display verbose prints. Otherwise,
        it will keep silence until the print_* methods are called.
        """
        self.chatter = chatter
        self._is_building = False
        _ArgCatPrinter.print("Your cute argument parsing helper. >v<")
        self._reset()

    @property
    def chatter(self) -> bool:
        return _ArgCatPrinter.filter_level is _ArgCatPrintLevel.VERBOSE

    @chatter.setter
    def chatter(self, value: bool) -> None:
        if value is True:
            _ArgCatPrinter.filter_level = _ArgCatPrintLevel.VERBOSE
        else:
            _ArgCatPrinter.filter_level = _ArgCatPrintLevel.IF_NECESSARY

    def _reset(self) -> None:
        # A little bit of my naming convensions:
        # Member variables' names don't need to contain the type information
        # string, such as, 'dict', 'path', 'list'
        # By contrast, all local variables' names must contain the type 
        # information.
        self._arg_parsers: Dict = {}
        self._manifest_data: Optional[Dict] = {}

    def _create_parsers(self) -> None:
        _ArgCatPrinter.print("Creating parsers ...")
        
        if not self._manifest_data:
            _ArgCatPrinter.print("Fatal error. No valid information found for parsers! Exit ...", 
                                 level=_ArgCatPrintLevel.ERROR)
            return
        
        meta_dict: Dict = self._manifest_data[_ManifestConstants.META]
        
        # Main parser created on data from _manifest_data
        main_parser_meta_dict: Dict = dict(meta_dict)
        # In easy mode, ManifestConstants.SUBPARSER does not exist.
        if _ManifestConstants.SUBPARSER in main_parser_meta_dict:
            del main_parser_meta_dict[_ManifestConstants.SUBPARSER]
        main_parser: ArgumentParser = argparse.ArgumentParser(**main_parser_meta_dict)
        
        parsers_dict: Dict = self._manifest_data[_ManifestConstants.PARSERS]
        
        # Make meta dict for creating subparsers by add_subparsers() 
        # In easy mode, ManifestConstants.SUBPARSER value is None and to make sure add_subparsers() work in this case,
        # we use an empty dict as subparser_meta_dict.
        subparser_meta_dict: Dict = meta_dict.get(_ManifestConstants.SUBPARSER, {})
        subparser_meta_dict[_ManifestConstants.DEST] = _ManifestConstants.SUBPARSER_NAME # reserved 
        
        argument_subparsers: Optional[_SubParsersAction] = None

        for parser_name, parser_dict in parsers_dict.items():
            if parser_dict is None or len(parser_dict) == 0:
                continue
            # Make a meta dict which can be unpacked and binded into main_parser.add_subparsers.add_parser()
            # Since ManifestConstants.ARGUMENTS and ManifestConstants.ARGUMENT_GROUPS are added for ArgCat and not known
            # by add_parser(), so we delete them here.
            parser_meta_dict = dict(parser_dict)
            if _ManifestConstants.ARGUMENTS in parser_meta_dict:
                del parser_meta_dict[_ManifestConstants.ARGUMENTS]
            if _ManifestConstants.ARGUMENT_GROUPS in parser_meta_dict:
                del parser_meta_dict[_ManifestConstants.ARGUMENT_GROUPS]

            # Add new parser
            new_parser: ArgumentParser
            if parser_name == _ManifestConstants.MAIN:
                new_parser = main_parser
            else:
                # Create the subparsers when need.
                if argument_subparsers is None:
                    argument_subparsers: _SubParsersAction = main_parser.add_subparsers(**subparser_meta_dict)
                new_parser = argument_subparsers.add_parser(parser_name, **parser_meta_dict)
                
            # Add argument groups
            argument_groups_dict = parser_dict.get(_ManifestConstants.ARGUMENT_GROUPS, None)
            parser_argument_groups_dict: Optional[Dict]
            if argument_groups_dict is not None:
                parser_argument_groups_dict = {}
                for group_name, group_meta_dict in argument_groups_dict.items():
                    is_mutually_exclusive = group_meta_dict[_ManifestConstants.IS_MUTUALLY_EXCLUSIVE]
                    if is_mutually_exclusive is True:
                        parser_argument_groups_dict[group_name] = new_parser.add_mutually_exclusive_group()
                    else:
                        group_description = group_meta_dict[_ManifestConstants.DESCRIPTION]                        
                        parser_argument_groups_dict[group_name] = new_parser.add_argument_group(group_name, 
                        group_description)
            else:
                parser_argument_groups_dict = None
            # Add arguments into this new parser
            parser_arguments_list = parser_dict.get(_ManifestConstants.ARGUMENTS, [])   # might be None
            added_arguments = []  # For collecting added arguments
            # Collect addtional argument information which cannot be provided by created argument instance, which is 
            # just a Action object.
            additional_arguments_info = {}
            for argument_dict in parser_arguments_list:
                name_or_flags: Optional[List] = argument_dict.get(_ManifestConstants.NAME_OR_FLAGS, None)
                argument_meta_dict = dict(argument_dict)
                ignored_by_subparser = True # This is true by default 
                if _ManifestConstants.IGNORED_BY_SUBPARSER in argument_meta_dict:
                    ignored_by_subparser = argument_meta_dict[_ManifestConstants.IGNORED_BY_SUBPARSER]
                    del argument_meta_dict[_ManifestConstants.IGNORED_BY_SUBPARSER]
                # from lexcical type to real type
                # https://stackoverflow.com/questions/11775460/lexical-cast-from-string-to-type
                lexical_type = argument_meta_dict.get(_ManifestConstants.TYPE, None)
                if lexical_type and isinstance(lexical_type, str):
                    argument_meta_dict[_ManifestConstants.TYPE] = locate(lexical_type)
                # Add arguments considering we now support group and mutually exclusive group.
                object_to_add_argument: Union[ArgumentParser, _ArgumentGroup, _MutuallyExclusiveGroup]
                object_to_add_argument = new_parser # By default, the argument should be added into a ArgumentParser.
                # However, if there is a specific `group` set, we add it into an accordingly group.
                if parser_argument_groups_dict is not None:
                    argument_group_name = argument_meta_dict.get(_ManifestConstants.GROUP, None)
                    if argument_group_name is not None:
                        created_group = parser_argument_groups_dict.get(argument_group_name, None)
                        del argument_meta_dict[_ManifestConstants.GROUP]
                        if created_group is not None:
                            object_to_add_argument = created_group
                            
                if name_or_flags:
                    if _ManifestConstants.NAME_OR_FLAGS in argument_meta_dict:
                        del argument_meta_dict[_ManifestConstants.NAME_OR_FLAGS]
                    added_arg = object_to_add_argument.add_argument(*name_or_flags, **argument_meta_dict)
                else: 
                    added_arg = object_to_add_argument.add_argument(**argument_meta_dict)
                
                added_arguments.append(added_arg) # Collect and later save them into _ArgCatParser()
                new_additional_argument_info = {} 
                if object_to_add_argument is not new_parser:
                    new_additional_argument_info[_ManifestConstants.GROUP] = argument_group_name
                new_additional_argument_info[_ManifestConstants.IGNORED_BY_SUBPARSER] = ignored_by_subparser
                additional_arguments_info[added_arg.dest] = new_additional_argument_info
            # Add a new ArgCatPartser with None handler_func    
            self._arg_parsers[parser_name] = _ArgCatParser(parser=new_parser, name=parser_name,
                                                           arguments=added_arguments,
                                                           additional_arguments_info=additional_arguments_info,
                                                           groups=parser_argument_groups_dict)

        if _ManifestConstants.MAIN not in self._arg_parsers:
            self._arg_parsers[_ManifestConstants.MAIN] = _ArgCatParser(parser=main_parser, 
                                                                       name=_ManifestConstants.MAIN, 
                                                                       arguments=[])
        
        # A very private way to set a default main handler in case user does not provide any handler.
        self._arg_parsers[_ManifestConstants.MAIN].handler_func = self._default_main_handler
    
    # The return value for this is mainly for unittest.
    def _default_main_handler(self, **kwargs: str) -> Dict:
        _ArgCatPrinter.print("The default `main` handler is triggered to print simple usage only. " + 
                            "Please set your `main` handler if necessary.", level=_ArgCatPrintLevel.VERBOSE)
        main_parser = self._arg_parsers.get(_ManifestConstants.MAIN, None)
        if main_parser:
            main_parser.parser.print_usage()
        else:
            _ArgCatPrinter.print("The default `main` handler is triggered but the main parser is not valid!", 
                                 level=_ArgCatPrintLevel.ERROR)
        return kwargs
    
    def _call_parser_handler(self, parser: _ArgCatParser, parameters: Dict) -> Any:
        if parser.handler_func:
            try:
                _ArgCatPrinter.print("Handler `{}` is handling `{}` with args: {} ..."
                .format(parser.handler_func, parser.name, parameters))
                result = parser.handler_func(**parameters)
            # Catch all exception to print the actual exception raised in the handler besides
            # TypeError. If we are only capturing TypeError, the actual error would be "covered" by the TypeError, which
            # means all error would be raised as TypeError. This could be very confusing.
            except Exception as exc:
                func_sig = inspect.signature(parser.handler_func)
                input_sig = str(tuple(parameters)).replace('\'','')
                error_msg = "Handling function Exception: \"{}\", with function sig: {} and received parameters: {}."\
                    .format(exc, func_sig, input_sig)
                _ArgCatPrinter.print(error_msg, level=_ArgCatPrintLevel.ERROR, indent=1)
            else:
                return result
        else:
            _ArgCatPrinter.print("Parser `{}` does not have any handler.".format(parser.name), 
            level=_ArgCatPrintLevel.ERROR, indent=1)
        return None
        
    def build(self) -> _ArgCatBuilder:
        """Build arguments by an ArgCatBuilder.

        Use `with ArgCat.build() as builder:` and ArgCatBuilder's methods for setting parsers and arguments.

        This `with` statement is freaking crazy. Wow, I LOVE Python! 

        Returns an ArgCatBuilder.
        """
        self._reset()
        self._is_building = True
        _ArgCatPrinter.print(f"Building ...")
        # Create the parsers once the build is done.
        def on_build_done(manifest_data):
            self._manifest_data = manifest_data
            self._create_parsers()
            self._is_building = False
            _ArgCatPrinter.print("Building DONE. Use print_xx functions for more information.")
        
        return _ArgCatBuilder(on_build_done)
        
    def parse_args(self, args: Optional[List[str]]=None, namespace: Optional[Namespace]=None) -> Dict:
        """Start to parse args.

        This method is pretty much the same as the original `parse_args()` of ArgumentParser, which means
        you can use it the same way as you use ArgumentParser's before.

        Returns result from handler. This is the only difference from the ArgumentParser's parse_args.
        The latter one returns a Namespace, but ArgCat returns the result from handler since 
        ArgCat has taken care of parsing the raw Namespace from ArgumentParser.
        """
        _ArgCatPrinter.print("Parsing args ...")
        # Call the main parser's parse_args() to parse the arguments input.
        subparser_name, subparser_parsed_arguments_dict, main_parser_parsed_arguments_dict = \
        self._arg_parsers[_ManifestConstants.MAIN].parse_args(args=args, namespace=namespace)
        
        ret_result = {}
        
        # The main parser's handler should be called for two cases: 
        # 1. no subparser called or 
        # 2. subparser called but main parser has arguments.
        if subparser_name is None or main_parser_parsed_arguments_dict:
            ret_result['main'] = self._call_parser_handler(parser=self._arg_parsers[_ManifestConstants.MAIN], 
                                                           parameters=main_parser_parsed_arguments_dict)
        
        # Only need to check subparser_name because subparser_parsed_arguments_dict can be None when a subparser 
        # is called without any arguments.
        if subparser_name:
            subparser = self._arg_parsers[subparser_name]
            ret_result[subparser_name] = self._call_parser_handler(parser=subparser, 
                                                                    parameters=subparser_parsed_arguments_dict)
            
        return ret_result
    
    def add_handler_provider(self, handler_provider: Any) -> bool:
        """Set an object as the provider for ArgCat to find handlers.

        The provider can normally be a (meta) class (instance), namespace or 
        anything has @ArgCat.handler decorated method/function.

        Returns a bool value which is whether all the handlers are set successfully.
        """
        _ArgCatPrinter.print(f"Setting handlers from provider: `{handler_provider}` ...")
        all_handler_func_dicts: List[Dict] = [{'name': name, 'func': obj} 
                                              for name, obj in inspect.getmembers(handler_provider) 
                                              if ((inspect.ismethod(obj) or inspect.isfunction(obj)) and 
                                                  hasattr(obj, "argcat_argument_parser_name"))]
        # The functions retrieved will be in alphabet order. So, if there are method/functions with duplicate names, 
        # the first one in the sequence will be added and the other ones will be discarded.
        if not all_handler_func_dicts:
            _ArgCatPrinter.print(f"The handler provider '{handler_provider}' does not have any handler. Skip ...", 
            level=_ArgCatPrintLevel.WARNING)
            return False
        all_done = True
        for func_dict in all_handler_func_dicts:
            func = func_dict['func']
            func_name = func_dict['name']
            parser_name = func.argcat_argument_parser_name
            done = self.set_parser_handler(parser_name=parser_name, handler=func, handler_name=func_name)
            if done == False:
                all_done = False
        return all_done

    def add_main_module_as_handler_provider(self) -> bool:
        """ A convenient method to add main module as a handler provider. 
        Returns a bool value which is whether the handler provider is set successfully.
        """
        return self.add_handler_provider(sys.modules['__main__'])
    
    def set_parser_handler(self, parser_name: str, handler: Callable, handler_name: Optional[str] = None) -> bool:
        """ A flexible way to add handler for a specific parser. 
        Returns a bool value which is whether the handler is set successfully.
        """
        if handler_name is None:
            handler_name = handler.__name__
        parser = self._arg_parsers.get(parser_name, None)
        if parser:
            # If there is no handler or the handler is a default one provided by ArgCat.
            if not parser.handler_func or parser.handler_func == self._default_main_handler:
                # Check the signature of the handler to make sure it can work.
                func_sig = inspect.signature(handler)
                handler_parameters = set(func_sig.parameters.keys())
                # Find all arguments for `main` parser which are not ignored by subparser.
                if parser_name == 'main':
                    # If it's adding handler for 'main' parser, parser.dests is what we need.
                    parser_required_parameters = parser.dests
                else:
                    # Otherwise, we should not only consider parser.dests but also considering all arguments are not 
                    # ignored by subparsers for `main` parser.
                    dests_in_main_parser_should_not_be_ignored = [k for k, v in 
                                                                  self._arg_parsers['main'].additional_arguments_info
                                                                  .items() 
                                                                  if v[_ManifestConstants.IGNORED_BY_SUBPARSER] 
                                                                  == False]
                    # Add this parser's dests.
                    dests_in_main_parser_should_not_be_ignored.extend(parser.dests)
                    parser_required_parameters = dests_in_main_parser_should_not_be_ignored
                    
                # Compare two by putting them into sets and finding difference.
                if set(handler_parameters) == set(parser_required_parameters):
                    parser.handler_func = handler
                    _ArgCatPrinter.print(f"Added handler `{handler_name}{func_sig}` for the parser `{parser_name}`.",
                                         level=_ArgCatPrintLevel.VERBOSE)
                    return True
                else:
                    if parser_required_parameters:
                        parser_require_parameters_str = functools.reduce(lambda a, b: f"{a}, {b}", 
                                                                         parser_required_parameters)
                    else:
                        parser_require_parameters_str = ''
                    _ArgCatPrinter.print(f"Provided handler `{handler_name}{func_sig}` does not meet the " + 
                                         f"requirement of the parser `{parser_name}`, which requires a handler with " +
                                         "parameters " + f"`({parser_require_parameters_str})`.", 
                                         level=_ArgCatPrintLevel.WARNING)
                    return False
            else:
                _ArgCatPrinter.print(f"Multiple handlers for one parser `{parser_name}`.", 
                level=_ArgCatPrintLevel.WARNING)
        else:
            _ArgCatPrinter.print(f"Unknown parser `{parser_name}` to set with handler `{handler_name}`.", 
            level=_ArgCatPrintLevel.WARNING)
            
        return False
    
    def print_parser_handlers(self) -> None:
        """Show information of all handlers."""
        if not self._arg_parsers:
            _ArgCatPrinter.print("ArgCat does not have any parser.", level=_ArgCatPrintLevel.IF_NECESSARY)
            return
        _ArgCatPrinter.print("Handlers: ", level=_ArgCatPrintLevel.IF_NECESSARY)
        for parser_name, parser in self._arg_parsers.items():
            func_sig: Optional[inspect.Signature] = None
            if parser.handler_func is not None:
                func_sig = inspect.signature(parser.handler_func)
            _ArgCatPrinter.print("{} => {} : {}".format(parser_name, parser.handler_func, func_sig), indent=1, 
            level=_ArgCatPrintLevel.IF_NECESSARY)
    
    def print_parsers(self) -> None:
        """Show information of all parsers."""
        if not self._arg_parsers:
            _ArgCatPrinter.print("ArgCat does not have any parser.", level=_ArgCatPrintLevel.IF_NECESSARY)
            return
        _ArgCatPrinter.print("Parsers: ", level=_ArgCatPrintLevel.IF_NECESSARY)
        for parser_name, parser in self._arg_parsers.items():
            _ArgCatPrinter.print("{}:".format(parser_name), indent=1, level=_ArgCatPrintLevel.IF_NECESSARY)
            for arg in parser.arguments:
                dest = arg.dest
                if arg.option_strings:
                    name = arg.option_strings
                else:
                    name = dest
                _ArgCatPrinter.print("{} -> {}".format(name, dest), indent=2, level=_ArgCatPrintLevel.IF_NECESSARY)