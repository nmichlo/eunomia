import abc
import ast
from typing import Optional, Dict, Any, Union

from asteval.astutils import UNSAFE_ATTRS, make_symbol_table, safe_mult, safe_add, safe_pow, safe_lshift


# ========================================================================= #
# Errors                                                                    #
# ========================================================================= #


class InterpreterError(Exception):
    """
    A general interpreter error.
    """


class UnsupportedLanguageFeatureError(InterpreterError):
    """
    If the python language feature is not supported.
    """


class DisabledLanguageFeatureError(UnsupportedLanguageFeatureError):
    """
    If the python language feature has been disabled
    """

# ========================================================================= #
# Interpreter                                                               #
# ========================================================================= #


class BaseInterpreter(object):

    def copy(self) -> 'BaseInterpreter':
        return BaseInterpreter()

    def _get_visit_name(self, node):
        return 'visit_' + node.__class__.__name__

    def _visit(self, node, *args, **kwargs):
        attr = self._get_visit_name(node)
        visitor = getattr(self, attr, self._visit_unknown)
        if visitor is None:
            visitor = self._visit_disabled
        result = visitor(node, *args, **kwargs)
        return result

    def _visit_disabled(self, node, *args, **kwargs):
        attr = self._get_visit_name(node)
        raise DisabledLanguageFeatureError(f'Language feature has been disabled: {node=}\n method: {attr=} is None')

    def _visit_unknown(self, node, *args, **kwargs):
        attr = self._get_visit_name(node)
        raise UnsupportedLanguageFeatureError(f'Language feature not supported: {node=}\nCould not find method: {attr=}')

    def interpret(self, node_or_string, strip_whitespace=True):
        """
        Based on ast.literal_eval & ast.NodeTransformer

        - (Safely?) evaluate an expression node or a string containing
          a Python expression.
        """
        if isinstance(node_or_string, str):
            if strip_whitespace:
                # string.whitespace == ' \t\n\r\v\f'
                # we dont want to strip special characters
                node_or_string = node_or_string.strip(' \t')
            node_or_string = ast.parse(node_or_string, mode='eval')
        if isinstance(node_or_string, ast.Expression):
            node_or_string = node_or_string.body
        return self._visit(node_or_string)


# ========================================================================= #
# Basic Interpreter for expressions and literals                            #
# ========================================================================= #


class BasicInterpreter(BaseInterpreter):
    """
    https://docs.python.org/3/reference/expressions.html
    https://docs.python.org/3/library/stdtypes.html
    """

    def __init__(
            self,
            # rules
            allow_nested_unary=False,
            allow_numerical_unary_on_bool=False,
            allow_chained_comparisons=False,
    ):
        # TODO: maybe convert to mixins?
        self._allow_nested_unary = allow_nested_unary
        self._allow_numerical_unary_on_bool = allow_numerical_unary_on_bool
        self._allow_chained_comparisons = allow_chained_comparisons

    def copy(self) -> 'BasicInterpreter':
        return BasicInterpreter(
            allow_nested_unary=self._allow_nested_unary,
            allow_numerical_unary_on_bool=self._allow_numerical_unary_on_bool,
            allow_chained_comparisons=self._allow_chained_comparisons,
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Atoms ::= identifier | literal | enclosure                            #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    # literals ::= stringliteral | bytesliteral | integer | floatnumber | imagnumber
    def visit_Constant(self, node): return node.value

    # enclosures ::= parenth_form | list_display | dict_display | set_display | generator_expression | yield_atom
    def visit_List (self, node): return [self._visit(n) for n in node.elts]
    def visit_Tuple(self, node): return tuple(self._visit(n) for n in node.elts)
    def visit_Set  (self, node): return {self._visit(n) for n in node.elts}
    def visit_Dict (self, node):
        if len(node.keys) != len(node.values):
            raise ValueError('Dict node is malformed, differing number of keys and values!')
        return {self._visit(k): self._visit(v) for k, v in zip(node.keys, node.values)}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Boolean Operations                                                    #
    # docs.python.org/3/library/stdtypes.html#boolean-operations-and-or-not #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def visit_BoolOp(self, node):
        return self._visit(node.op, node.values)

    # 1. This is a short-circuit operator, so it only evaluates the second argument if the first one is true.
    def visit_Or(self, node, values):
        result = False
        for value in values:
            result = result or self._visit(value)
            if result:
                return True
        return False

    # 2. This is a short-circuit operator, so it only evaluates the second argument if the first one is false.
    def visit_And(self, node, values):
        result = True
        for value in values:
            result = result and self._visit(value)
            if not result:
                return False
        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Comparisons                                                           #
    # docs.python.org/3/library/stdtypes.html#comparisons                   #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def visit_Compare(self, node):
        assert len(node.ops) == len(node.comparators)
        if self._allow_chained_comparisons:
            # Comparisons can be chained arbitrarily; for example, x < y <= z is
            # equivalent to x < y and y <= z, except that y is evaluated only once (but
            # in both cases z is not evaluated at all when x < y is found to be false)
            result = True
            vis_left = self._visit(node.left)
            for op, comp in zip(node.ops, node.comparators):
                vis_right = self._visit(comp)
                result = result and self._visit(op, vis_left, vis_right)
                if not result:
                    return False
                vis_left = vis_right
            return True
        else:
            if len(node.ops) > 1:
                raise DisabledLanguageFeatureError(f'Chained operators are not allowed, eg. (a <op> b <op> 3)\nConvert to ((a <op> b) and (b <op> c))')
            vis_left = self._visit(node.left)
            vis_right = self._visit(node.comparators[0])
            return self._visit(node.ops[0], vis_left, vis_right)

    def visit_Lt    (self, op, vis_left, vis_right): return vis_left < vis_right
    def visit_LtE   (self, op, vis_left, vis_right): return vis_left <= vis_right
    def visit_Gt    (self, op, vis_left, vis_right): return vis_left > vis_right
    def visit_GtE   (self, op, vis_left, vis_right): return vis_left >= vis_right
    def visit_Eq    (self, op, vis_left, vis_right): return vis_left == vis_right
    def visit_NotEq (self, op, vis_left, vis_right): return vis_left != vis_right
    def visit_Is    (self, op, vis_left, vis_right): return vis_left is vis_right
    def visit_IsNot (self, op, vis_left, vis_right): return vis_left is not vis_right

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Operators                                                             #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def visit_BinOp(self, node):
        return self._visit(node.op, self._visit(node.left), self._visit(node.right))

    def visit_Add     (self, node, vis_left, vis_right): return vis_left + vis_right
    def visit_Sub     (self, node, vis_left, vis_right): return vis_left - vis_right
    def visit_Mult    (self, node, vis_left, vis_right): return vis_left * vis_right
    def visit_MatMult (self, node, vis_left, vis_right): return vis_left @ vis_right
    def visit_Div     (self, node, vis_left, vis_right): return vis_left / vis_right
    def visit_FloorDiv(self, node, vis_left, vis_right): return vis_left // vis_right
    def visit_Mod     (self, node, vis_left, vis_right): return vis_left % vis_right
    def visit_Pow     (self, node, vis_left, vis_right): return vis_left ** vis_right

    def visit_BitAnd  (self, node, vis_left, vis_right): return vis_left & vis_right
    def visit_BitOr   (self, node, vis_left, vis_right): return vis_left | vis_right
    def visit_BitXor  (self, node, vis_left, vis_right): return vis_left ^ vis_right

    def visit_LShift  (self, node, vis_left, vis_right): return vis_left << vis_right
    def visit_RShift  (self, node, vis_left, vis_right): return vis_left >> vis_right

    def visit_In   (self, node, vis_left, vis_right): return vis_left in vis_right
    def visit_NotIn(self, node, vis_left, vis_right): return vis_left not in vis_right

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Unary Operators                                                       #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def visit_UnaryOp(self, node):
        if not self._allow_nested_unary:
            if isinstance(node.operand, ast.UnaryOp):
                raise DisabledLanguageFeatureError(f'Nested unary operators are not allowed, eg. ++1 or --1')
        if not self._allow_numerical_unary_on_bool:
            if not isinstance(node.op, ast.Not):
                if isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, bool):
                    raise DisabledLanguageFeatureError(f'Only the not unary operator is allowed on booleans, eg. not True')
        return self._visit(node.op, self._visit(node.operand))

    def visit_UAdd  (self, op, visited_value): return + visited_value
    def visit_USub  (self, op, visited_value): return - visited_value
    def visit_Invert(self, op, visited_value): return ~ visited_value
    def visit_Not   (self, op, visited_value): return not visited_value


# ========================================================================= #
# Interpreter for properties, getters and symtables                         #
# ========================================================================= #


class Interpreter(BasicInterpreter):

    def __init__(
            self,
            # symtable
            default_symtable: Optional[Dict[str, Any]] = None,
            extra_symtable: Optional[Dict[str, Any]] = None,
            # rules
            allow_nested_unary=False,
            allow_numerical_unary_on_bool=False,
            allow_chained_comparisons=False,
            allow_unpacking=False,
    ):
        super().__init__(
            allow_nested_unary=allow_nested_unary,
            allow_numerical_unary_on_bool=allow_numerical_unary_on_bool,
            allow_chained_comparisons=allow_chained_comparisons,
        )
        self._allow_unpacking = allow_unpacking
        # make default symtable
        self._symtable = make_symbol_table(use_numpy=False) if (default_symtable is None) else default_symtable
        # add extras to symtable
        self._symtable.update({} if (extra_symtable is None) else extra_symtable)

    def copy(self) -> 'Interpreter':
        # TODO: this is not safe, does not use a deep copy
        return Interpreter(
            default_symtable=dict(self._symtable),
            # rules
            allow_nested_unary=self._allow_nested_unary,
            allow_numerical_unary_on_bool=self._allow_numerical_unary_on_bool,
            allow_chained_comparisons=self._allow_chained_comparisons,
            allow_unpacking=self._allow_unpacking,
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Properties                                                            #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def visit_Name(self, node):
        try:
            return self._symtable[node.id]
        except KeyError:
            pass
        raise NameError(f"name {repr(node.id)} is not defined")

    def visit_Attribute(self, node):
        if node.attr in UNSAFE_ATTRS:
            raise KeyError(f'Tried to access unsafe attribute: {node.attr}')
        return getattr(self._visit(node.value), node.attr)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # List, Tuple, Set, Dict Unpacking                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _yield_visit_unpack_elts(self, elts) -> list:
        for n in elts:
            if isinstance(n, ast.Starred):
                if not self._allow_unpacking:
                    raise DisabledLanguageFeatureError('Starred unpacking is disabled.')
                yield from self._visit(n.value)
            else:
                yield self._visit(n)

    def _yield_visit_unpack_dict_pairs(self, keys, values, is_keywords=False) -> list:
        # same error as super().visit_Dict(...)
        if not is_keywords:
            if len(keys) != len(values):
                raise ValueError('Dict node is malformed, differing number of keys and values!')
        # actually unpack
        for k, v in zip(keys, values):
            if k is None:
                if not self._allow_unpacking:
                    raise DisabledLanguageFeatureError('Starred unpacking is disabled.')
                # get dictionary value
                unpack_dict = self._visit(v)
                # check that we are not malformed
                if not isinstance(unpack_dict, dict):
                    raise ValueError('Tried to unpack non dict.')
                # return all
                yield from unpack_dict.items()
            else:
                if not is_keywords:
                    yield self._visit(k), self._visit(v)
                else:
                    yield k, self._visit(v)

    def visit_List (self, node): return list(self._yield_visit_unpack_elts(node.elts))
    def visit_Tuple(self, node): return tuple(self._yield_visit_unpack_elts(node.elts))
    def visit_Set  (self, node): return set(self._yield_visit_unpack_elts(node.elts))
    def visit_Dict (self, node): return dict(self._yield_visit_unpack_dict_pairs(node.keys, node.values, is_keywords=False))

    def visit_Starred(self, node):
        raise RuntimeError('This should never happen.')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Call                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _build_kwargs(self, keywords: list):
        # unpack everything like a dictionary
        unpacked_keys_values = self._yield_visit_unpack_dict_pairs(
            keys=(kw.arg for kw in keywords),
            values=(kw.value for kw in keywords),
            is_keywords=True,
        )
        # check that kwargs are unique
        kwargs = {}
        for k, v in unpacked_keys_values:
            if k in kwargs:
                raise TypeError(f"got multiple values for keyword argument {repr(k)}")
            kwargs[k] = v
        # done!
        return kwargs

    def visit_Call(self, node):
        func = self._visit(node.func)
        # get args and kwargs
        args = self._yield_visit_unpack_elts(node.args) if node.args else []
        kwargs = self._build_kwargs(node.keywords) if node.keywords else {}
        # call the function
        return func(*args, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Get Item                                                              #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    # TODO: maybe names, subscripts and properties should be moved into basic
    #       but with limitations on which funcs are available
    def visit_Subscript(self, node):
        slice = self._visit(node.slice)
        value = self._visit(node.value)
        return value[slice]
