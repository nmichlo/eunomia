
class ParserError(Exception):
    pass


class MalformedPythonError(ParserError):
    pass


class NotExpressionError(ParserError):
    pass


class ExpressionSemicolonError(NotExpressionError):
    pass


class UnsupportedLanguageFeatureError(ParserError):
    pass


# ========================================================================= #
# Printing                                                                  #
# ========================================================================= #


def try_parse_expression(expr):
    import ast

    # get proper error message
    try:
        module = ast.parse(expr)
    except:
        raise MalformedPythonError(f'{expr=} is not a valid python.')

    # check that the body only has one statement/expression
    if len(module.body) > 1:
        raise NotExpressionError(f'{expr=} multiple statements are not supported.')

    # check that it is an expression
    statement = module.body[0]
    if isinstance(statement, ast.stmt):
        if not isinstance(statement, ast.Expr):
            raise NotExpressionError(f'{expr=} code is not an expression.')

        # semicolons convert expressions to statements
        if expr.rstrip()[-1] == ';':
            raise ExpressionSemicolonError(f'{expr=} semicolons convert statements into expressions.')

        # expr = statement.value
        # if isinstance(expr, ast.Lambda):
        #     raise UnsupportedLanguageFeatureError(f'{expr=} lambdas are not supported.')

    # final check using eval parsing mode
    # we may have missed something.
    try:
        ast.parse(expr, mode='eval')
    except Exception as e:
        raise NotExpressionError('An unknown error occured parsing the expression. Please report this.')


def asteval_interpret_expr(expr, usersyms=None):
    import asteval

    if usersyms is None:
        usersyms = {}

    # check that this is actually a proper expression
    # - fails for assignments, statements, functions, etc.
    try_parse_expression(expr)

    # we recreate the interpreter each time so that values we assign to are not
    interpreter = asteval.Interpreter(
        # symtable=None,
        usersyms=usersyms,
        # writer=None, err_writer=None, use_numpy=True, minimal=False,
        no_if=True, no_for=True, no_while=True, no_try=True, no_functiondef=True,
        # no_ifexp=False, no_listcomp=False,
        no_augassign=True, no_assert=True, no_delete=True, no_raise=True, no_print=True,
        # max_time=None,
        readonly_symbols=set(usersyms.keys()),
        builtins_readonly=True,
    )

    try:
        return interpreter.eval(expr, show_errors=False)
    except NotImplementedError as e:
        if isinstance(e.args[0], str):
            if e.args[0].endswith("'JoinedStr' not supported"):
                raise UnsupportedLanguageFeatureError(f'{expr=} f-strings are not supported')
        raise UnsupportedLanguageFeatureError(f'{expr=} has unsupported language features:\n{e}')
