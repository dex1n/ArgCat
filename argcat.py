#!/usr/bin/env python3

import os
import argparse
import inspect
import re
import yaml
from pathlib import Path
from pydoc import locate
from enum import Enum, unique
from argparse import ArgumentParser, Namespace, _ArgumentGroup, _MutuallyExclusiveGroup, _SubParsersAction
from typing import ClassVar, Container, List, Dict, Optional, Callable, Tuple, Any, Union


# May not be the best solution for the constants, but it's fine for now.
# And we don't need ClassVar[str] here because I think all constants' type are pretty clear.
class ManifestConstants:
    META = "meta"
    METAVAR = "metavar"
    PROG = "prog"
    DESCRIPTION = "description"
    TITLE = "title"
    HELP = "help"
    NARGS = "nargs"
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
    REQUIRED = 'required'
    ACTION = 'action'
    CHOICES = 'choices'
    CONST = 'const'
    HELP = 'help'
    # Mainly used for main arguments. If this is set to True, the argument will be filtered out before being passed
    # into subparser's handler. Default value is False.
    IGNORED_BY_SUBPARSER = 'ignored_by_subparser'   


# Default manifest
class _ARGUMENT_DEFAULTS_:
    META = {
        ManifestConstants.PROG: "Cool program name",
        ManifestConstants.DESCRIPTION: "Awesome description",
        # In easy mode, we don't use these to make the help texts clean.
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
    PARSERS = {
        # There is main parser by default
        ManifestConstants.MAIN: { ManifestConstants.ARGUMENTS: [] }
    }
    
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
        sub_parser_name: str = parsed_arguments_dict.get(ManifestConstants.SUB_PARSER_NAME, None)
        # If the sub parser is needed, remove all arguments from the 
        # namspace belong to the main parser(parent parser) marked IGNORED_BY_SUBPARSER True. 
        # By default, all main parser's arguments will
        # stored in the args namespace even there is no the main arguments 
        # input. So, this step is to make sure the arguments input
        # into the handler correctly.
        if sub_parser_name is not None:
            del parsed_arguments_dict[ManifestConstants.SUB_PARSER_NAME]
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

    def __init__(self, chatter: bool=False):
        """
        If chatter is True, ArgCat will display verbose prints. Otherwise,
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
        self._manifest_data: Optional[Dict] = {}

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
        
        # Main parser created on data from _manifest_data
        main_parser_meta_dict: Dict = dict(meta_dict)
        # In easy mode, ManifestConstants.SUBPARSER does not exist.
        if ManifestConstants.SUBPARSER in main_parser_meta_dict:
            del main_parser_meta_dict[ManifestConstants.SUBPARSER]
        main_parser: ArgumentParser = argparse.ArgumentParser(**main_parser_meta_dict)
        
        parsers_dict: Dict = self._manifest_data[ManifestConstants.PARSERS]
        
        # Make meta dict for creating sub parsers by add_subparsers() 
        # In easy mode, ManifestConstants.SUBPARSER value is None and to make sure add_subparsers() work in this case,
        # we use an empty dict as sub_parser_meta_dict.
        sub_parser_meta_dict: Dict = meta_dict.get(ManifestConstants.SUBPARSER, {})
        sub_parser_meta_dict[ManifestConstants.DEST] = ManifestConstants.SUB_PARSER_NAME # reserved 
        
        argument_subparsers: Optional[_SubParsersAction] = None

        for parser_name, parser_dict in parsers_dict.items():
            if parser_dict is None or len(parser_dict) == 0:
                continue
            # Make a meta dict which can be unpacked and binded into main_parser.add_subparsers.add_parser()
            # Since ManifestConstants.ARGUMENTS and ManifestConstants.ARGUMENT_GROUPS are added for ArgCat and not known
            # by add_parser(), so we delete them here.
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
                    level=ArgCatPrintLevel.WARNING)
            else:
                ArgCatPrinter.print(f"Unknown parser '{parser_name}' to set with handler '{func_name}'.", 
                level=ArgCatPrintLevel.WARNING)

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
    # TODO: For default main handler: use this ArgumentParser.print_usage to print usage.            
                
class ArgCatD(ArgCat):
    def __init__(self, prog_name: Optional[str] = None, description: Optional[str] = None, chatter: bool = False):
        """
        TODO: UPDATE THIS ONCE ALL THE WORK IS DONE!!!
        """
        super().__init__(chatter)               
        self._initialize(prog_name, description)

    def _create_default_argument(self) -> Dict:
        return {
            ManifestConstants.NAME_OR_FLAGS: None,
            ManifestConstants.NARGS: _ARGUMENT_DEFAULTS_.NARGS, 
            ManifestConstants.DEST: _ARGUMENT_DEFAULTS_.DEST, 
            ManifestConstants.METAVAR: _ARGUMENT_DEFAULTS_.METAVAR,
            ManifestConstants.TYPE: _ARGUMENT_DEFAULTS_.TYPE,
            ManifestConstants.HELP: _ARGUMENT_DEFAULTS_.HELP
        }
    
    def _initialize(self, prog_name: Optional[str], description: Optional[str]) -> None:
        self._reset()
        self._prog_name = prog_name
        self._description = description
        
        # Load default data.
        self._manifest_data[ManifestConstants.META] = _ARGUMENT_DEFAULTS_.META
        self._manifest_data[ManifestConstants.PARSERS] = _ARGUMENT_DEFAULTS_.PARSERS
        
        # Use the setting ones if necessary.
        if self._prog_name is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.PROG] = self._prog_name
            
        if self._description is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.DESCRIPTION] = self._description
        
    
    def _load_arg_recipes(self, arg_recipes: List[str]) -> None:
        # Load default data.
        self._manifest_data[ManifestConstants.META] = _ARGUMENT_DEFAULTS_.META
        self._manifest_data[ManifestConstants.PARSERS] = _ARGUMENT_DEFAULTS_.PARSERS
        
        # Use the setting ones if necessary.
        if self._prog_name is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.PROG] = self._prog_name
            
        if self._description is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.DESCRIPTION] = self._description
        
        parsers: Dict = self._manifest_data[ManifestConstants.PARSERS]
        main_parser: Dict = self._manifest_data[ManifestConstants.PARSERS][ManifestConstants.MAIN]
        
        for arg_recipe in arg_recipes:
            
            # Find the possible sub parser name from the beginning of the string.
            # NOTE that re.match() is to find the pattern from the beginning no matter the pattern has "^" or not.
            sub_parser_name_regex = re.compile(r"^ *(?P<sub_parser_name>[a-zA-Z]\w*)?")
            sub_parser_name_match = sub_parser_name_regex.match(arg_recipe)
            
            # If there is a sub parser name, try to find it or create it in the manifest data.
            if sub_parser_name_match:
                sub_parser_name = sub_parser_name_match.group(ManifestConstants.SUB_PARSER_NAME)
                the_sub_parser = parsers.setdefault(sub_parser_name, { ManifestConstants.ARGUMENTS: [] })
            else:
            # if not, add arguments to the default main parser.
                the_sub_parser = main_parser
            
            arguments = the_sub_parser[ManifestConstants.ARGUMENTS]
            new_argument = self._create_default_argument()
            
            # 目前这个正则除了 choice, action 和 help 都覆盖到了
            # A recipe would be like:
            # sub_parser_name -a/--arg nargs>dest:type?=default
            # For example, for a recipe: " data_file -f/--file 1>filename?=\"./__init__.py\" ",
            # a match for argument part would be like the tuple below:
            # ('-f', '--file', '?', 'filename', ':str', '?',        '="./__init__.py"', './__init__.py', '')
            # NAME_OR_FLAGS,   NARGS,   DEST,      TYPE, REQUIRED,                          DEFAULT 
            arguments_regex = re.compile(" +(\-\D)\/(\-\-\D\w+) +([?*+]|\d+)>([a-zA-Z]+)(:\w+)?(\??)(\=\"([^\"]+)\"|([^\"]+))?")
            arguments_matches = arguments_regex.findall(arg_recipe)
            print(arguments_matches)
            
            for match in arguments_matches:
                new_argument[ManifestConstants.NAME_OR_FLAGS] = [match[0], match[1]]
                
                if match[2] in ['?','*','+']:
                    new_argument[ManifestConstants.NARGS] = match[2]
                else: # NARGS is a int number.
                    new_argument[ManifestConstants.NARGS] = int(match[2])
                
                new_argument[ManifestConstants.DEST] = match[3]
                new_argument[ManifestConstants.METAVAR] = new_argument[ManifestConstants.DEST].upper()
                # If there is a type, use it without the first charactor ":".
                if match[4]:
                   new_argument[ManifestConstants.TYPE] = match[4][1:] 
                new_argument[ManifestConstants.REQUIRED] = not (match[4] == "?")    
                new_argument[ManifestConstants.DEFAULT] = match[7]
                
            print(new_argument)
            arguments.append(new_argument)
        
        #print(self._manifest_data)

    def _select_parser_by_name(self, parser_name: str) -> None:
        parsers: Dict = self._manifest_data[ManifestConstants.PARSERS]
        # Select the parser by name.
        # It may be a 'main' parser or any other sub parser.
        the_parser = parsers.setdefault(parser_name, { ManifestConstants.ARGUMENTS: [] })
        return the_parser
    
    def easy_load(self, arg_recipes: List[str]) -> None:
        """Load args recipe
        TODO: UPDATE THIS!!!
        A arg recipe is a special string in required format represents what you want for the arg.
        The format is like `^[sub_parser_name]?( -a/--arg nargs>dest(:type)?[?]?(=default_value)?)*` .
        For example: `data_file -f/--file ?>filename:str?="./__init__.py"` .
        `data_file` is the sub parser name.
        `-f/--file` is the arg name.
        `filename` is the arg's dest.
        `?` means this arg is optional.
        `="./__init__.py"` is the default value of the arg.
        `?>` means nargs is `?`.
        :str means the type is `str`.
        The arg would be str type by default, as str is the most commonly using type.
        The metavar would be the upper case of the dest. If the dest is set from the recipe to be upper case, then
        they would be the same.
        The nargs would be `?` by default.
        The help would be the same as the dest.
        These attributes might be modifiable in the late stage of the 0.3 development I guess.
        
        Returns None
        """
        
        if not arg_recipes:
            ArgCatPrinter.print("No valid Arg Recipes are provided. Quit...")
            return
        
        self._reset()
        self._load_arg_recipes(arg_recipes)
        self._create_parsers()
        ArgCatPrinter.print("Loading DONE. Use print_xx functions for more information.")

    
    def add_group(self, name: str, parser_name: str = ManifestConstants.MAIN, description: Optional[str] = None, 
                  is_mutually_exclusive: bool = False) -> None:
        
        the_parser = self._select_parser_by_name(parser_name)
        
        the_groups = the_parser.setdefault(ManifestConstants.ARGUMENT_GROUPS, {})
        
        new_group = the_groups.get(name, {})
        
        if new_group:
            ArgCatPrinter.print(f"Failed to add argument group `{name}` because it has already been there.", 
                                level=ArgCatPrintLevel.WARNING)
            return
        
        new_group[ManifestConstants.DESCRIPTION] = description
        new_group[ManifestConstants.IS_MUTUALLY_EXCLUSIVE] = is_mutually_exclusive
        
        the_groups[name] = new_group
        
    
    def add_argument(self, recipe: str, parser_name: str = ManifestConstants.MAIN, help: Optional[str] = None, 
                     arg_type: str = _ARGUMENT_DEFAULTS_.TYPE, choices: Optional[Container] = None, 
                     action: Optional[str] = None, const: Optional[str] = None, 
                     group_name: Optional[str] = None) -> None:
        
        the_parser = self._select_parser_by_name(parser_name)
        
        arguments = the_parser[ManifestConstants.ARGUMENTS]
        new_argument = self._create_default_argument()

        # 目前这个正则除了 choice, action 和 help 都覆盖到了
        # A recipe would be like:
        # `-a/--arg nargs>dest:type?=default`
        # For example, for a recipe: " -f/--file 1>filename?=\"./__init__.py\" ",
        # a match for argument part would be like the tuple below:
        # ('-f', '--file', '?', 'filename', ':str', '?',        '="./__init__.py"', './__init__.py', '')
        # NAME_OR_FLAGS,   NARGS,   DEST,      TYPE, REQUIRED,                          DEFAULT 
        arguments_regex = \
        re.compile("(\-\D)\/(\-\-\D\w+) +([?*+]|\d+)>([a-zA-Z]+)(:\w+)?(\??)(\=\"([^\"]+)\"|([^\"]+))?")
        arguments_matches = arguments_regex.findall(recipe)
        #print(arguments_matches)
        
        for match in arguments_matches:
            new_argument[ManifestConstants.NAME_OR_FLAGS] = [match[0], match[1]]
            
            if match[2] in ['?','*','+']:
                new_argument[ManifestConstants.NARGS] = match[2]
            else: # NARGS is a int number.
                new_argument[ManifestConstants.NARGS] = int(match[2])
            
            new_argument[ManifestConstants.DEST] = match[3]
            new_argument[ManifestConstants.METAVAR] = new_argument[ManifestConstants.DEST].upper()
            
            # If a arg_type is passed, use it ignoring the possible one in recipe.
            if arg_type:
                new_argument[ManifestConstants.TYPE] = arg_type
            elif match[4]:
            # Otherwise, use the type string in the recipe without the first charactor ":".
                new_argument[ManifestConstants.TYPE] = match[4][1:] 
                
            new_argument[ManifestConstants.REQUIRED] = not (match[5] == "?")    
            new_argument[ManifestConstants.DEFAULT] = match[7]
            
            # Addtional settings.
            if help:
                new_argument[ManifestConstants.HELP] = help
            
            if choices:
                new_argument[ManifestConstants.CHOICES] = choices
                
            if action:
                new_argument[ManifestConstants.ACTION] = action
            
            if const:
                new_argument[ManifestConstants.CONST] = const
            
            if group_name:
                new_argument[ManifestConstants.GROUP] = group_name
            
        arguments.append(new_argument)


    def build(self, builder: Callable) -> None:
        self._reset()
        self._build_manager = ArgCatBuildManager(self._manifest_data)
        builder(self._build_manager)
        self._create_parsers()
    

class ArgCatBuildManager:
    def __init__(self, manifest_data: dict) -> None:
        self._manifest_data = manifest_data
        
        # Load default data.
        self._manifest_data[ManifestConstants.META] = _ARGUMENT_DEFAULTS_.META
        self._manifest_data[ManifestConstants.PARSERS] = _ARGUMENT_DEFAULTS_.PARSERS
        
    def _create_default_argument(self) -> Dict:
        return {
            ManifestConstants.NAME_OR_FLAGS: None,
            ManifestConstants.NARGS: _ARGUMENT_DEFAULTS_.NARGS, 
            ManifestConstants.DEST: _ARGUMENT_DEFAULTS_.DEST, 
            ManifestConstants.METAVAR: _ARGUMENT_DEFAULTS_.METAVAR,
            ManifestConstants.TYPE: _ARGUMENT_DEFAULTS_.TYPE,
            ManifestConstants.HELP: _ARGUMENT_DEFAULTS_.HELP
        }  
    
    def _select_parser_by_name(self, parser_name: str) -> None:
        parsers: Dict = self._manifest_data[ManifestConstants.PARSERS]
        # Select the parser by name.
        # It may be a 'main' parser or any other sub parser.
        the_parser = parsers.setdefault(parser_name, { ManifestConstants.ARGUMENTS: [] })
        return the_parser
    
    def set_prog_info(self, prog_name: Optional[str], description: Optional[str]) -> None:
        if prog_name is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.PROG] = prog_name
        if description is not None:
            self._manifest_data[ManifestConstants.META][ManifestConstants.DESCRIPTION] = description
    
    def add_group(self, name: str, parser_name: str = ManifestConstants.MAIN, description: Optional[str] = None, 
                  is_mutually_exclusive: bool = False) -> None:
        
        the_parser = self._select_parser_by_name(parser_name)
        
        the_groups = the_parser.setdefault(ManifestConstants.ARGUMENT_GROUPS, {})
        
        new_group = the_groups.get(name, {})
        
        if new_group:
            ArgCatPrinter.print(f"Failed to add argument group `{name}` because it has already been there.", 
                                level=ArgCatPrintLevel.WARNING)
            return
        
        new_group[ManifestConstants.DESCRIPTION] = description
        new_group[ManifestConstants.IS_MUTUALLY_EXCLUSIVE] = is_mutually_exclusive
        
        the_groups[name] = new_group
        
    
    def add_argument(self, recipe: str, parser_name: str = ManifestConstants.MAIN, help: Optional[str] = None, 
                     arg_type: str = _ARGUMENT_DEFAULTS_.TYPE, choices: Optional[Container] = None, 
                     action: Optional[str] = None, const: Optional[str] = None, 
                     group_name: Optional[str] = None) -> None:
        
        the_parser = self._select_parser_by_name(parser_name)
        
        arguments = the_parser[ManifestConstants.ARGUMENTS]
        new_argument = self._create_default_argument()

        # 目前这个正则除了 choice, action 和 help 都覆盖到了
        # A recipe would be like:
        # `-a/--arg nargs>dest:type?=default`
        # For example, for a recipe: " -f/--file 1>filename?=\"./__init__.py\" ",
        # a match for argument part would be like the tuple below:
        # ('-f', '--file', '?', 'filename', ':str', '?',        '="./__init__.py"', './__init__.py', '')
        # NAME_OR_FLAGS,   NARGS,   DEST,      TYPE, REQUIRED,                          DEFAULT 
        arguments_regex = \
        re.compile("(\-\D)\/(\-\-\D\w+) +([?*+]|\d+)>([a-zA-Z]+)(:\w+)?(\??)(\=\"([^\"]+)\"|([^\"]+))?")
        arguments_matches = arguments_regex.findall(recipe)
        #print(arguments_matches)
        
        for match in arguments_matches:
            new_argument[ManifestConstants.NAME_OR_FLAGS] = [match[0], match[1]]
            
            if match[2] in ['?','*','+']:
                new_argument[ManifestConstants.NARGS] = match[2]
            else: # NARGS is a int number.
                new_argument[ManifestConstants.NARGS] = int(match[2])
            
            new_argument[ManifestConstants.DEST] = match[3]
            new_argument[ManifestConstants.METAVAR] = new_argument[ManifestConstants.DEST].upper()
            
            # If a arg_type is passed, use it ignoring the possible one in recipe.
            if arg_type:
                new_argument[ManifestConstants.TYPE] = arg_type
            elif match[4]:
            # Otherwise, use the type string in the recipe without the first charactor ":".
                new_argument[ManifestConstants.TYPE] = match[4][1:] 
                
            new_argument[ManifestConstants.REQUIRED] = not (match[5] == "?")    
            new_argument[ManifestConstants.DEFAULT] = match[7]
            
            # Addtional settings.
            if help:
                new_argument[ManifestConstants.HELP] = help
            
            if choices:
                new_argument[ManifestConstants.CHOICES] = choices
                
            if action:
                new_argument[ManifestConstants.ACTION] = action
            
            if const:
                new_argument[ManifestConstants.CONST] = const
            
            if group_name:
                new_argument[ManifestConstants.GROUP] = group_name
            
        arguments.append(new_argument)