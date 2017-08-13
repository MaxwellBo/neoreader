from ast import parse, walk, iter_fields, dump, NodeVisitor, get_docstring
import sys


def interpret_async(is_async):
    return "an async" if is_async else "a"


class PrettyReader(NodeVisitor):
    """
    stmt = FunctionDef(identifier name, arguments args,
                    stmt* body, expr* decorator_list, expr? returns)
        | AsyncFunctionDef(identifier name, arguments args,
                            stmt* body, expr* decorator_list, expr? returns)

        | ClassDef(identifier name,
            expr* bases,
            keyword* keywords,
            stmt* body,
            expr* decorator_list)
        | Return(expr? value)

        | Delete(expr* targets)
        | Assign(expr* targets, expr value)
        | AugAssign(expr target, operator op, expr value)
        -- 'simple' indicates that we annotate simple name without parens
        | AnnAssign(expr target, expr annotation, expr? value, int simple)

        -- use 'orelse' because else is a keyword in target languages
        | For(expr target, expr iter, stmt* body, stmt* orelse)
        | AsyncFor(expr target, expr iter, stmt* body, stmt* orelse)
        | While(expr test, stmt* body, stmt* orelse)
        | If(expr test, stmt* body, stmt* orelse)
        | With(withitem* items, stmt* body)
        | AsyncWith(withitem* items, stmt* body)

        | Raise(expr? exc, expr? cause)
        | Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
        | Assert(expr test, expr? msg)

        | Import(alias* names)
        | ImportFrom(identifier? module, alias* names, int? level)

        | Global(identifier* names)
        | Nonlocal(identifier* names)
        | Expr(expr value)
        | Pass | Break | Continue

        -- XXX Jython will be different
        -- col_offset is the byte offset in the utf8 string the parser uses
        attributes (int lineno, int col_offset)

        -- BoolOp() can use left & right?
    """

    def visit_Module(self, node):
        return self.visit_list(node.body)

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_list(self, xs):
        if len(xs) <= 1:
            return ", ".join([self.visit(i) for i in xs ])
        else:
            return ", ".join([self.visit(i) for i in xs[:-1]]) + f" and {self.visit(xs[-1])}"


    def visit_FunctionDef(self, node, is_async=False):
        docstring = get_docstring(node, True)
        body = node.body
        if docstring:
            body = body[1:]  # Don't mention it
        summary = ""\
            + f"{interpret_async(is_async)} function called {node.name}"\
            + f", which has {self.visit(node.args)}"\
            + (f", and returns a value of {self.visit(node.returns)}" if node.returns else "")\
            + (f", with the docstring of {docstring}" if docstring else "")\
            + f", with a body of {self.visit(node.body)}"

        return summary

    def visit_AsyncFunctionDef(self, node):
        return visit_FunctionDef(self, node, is_async=True)

    def visit_ClassDef(self, node):
        summary = (
            f"a class called {node.name}"
            f", which extends {self.visit_list(node.bases)}"
            f", and defines {self.visit_list(node.body)}"
        )
        return summary

    def visit_Return(self, node):
        if node.value:
            return f"a return statement returning {self.visit(node.value)}"
        else:
            return "a return statement"

    def visit_Delete(self, node):
        return f"a delete statement, deleting {self.visit_list(node.targets)}"

    def visit_Assign(self, node):
        return f"ellvalue {self.visit_list(node.targets)} assigned {self.visit(node.value)}"

    def visit_AugAssign(self, node):
        return f"ellvalue {self.visit(node.target)} augmented with {self.visit(node.operator)} and the value {self.visit(node.value)}"

    def visit_AnnAssign(self, node):
        return "TODO"

    def visit_For(self, node, is_async=False):
        summary = (
            f"{interpret_async(is_async)} for loop"
            f", using {self.visit(node.target)} as an iterator"
            f", looping through {self.visit(node.iter)}"
            f", with a body of {self.visit_list(node.body)}"
            # TODO: orelse
        )
        return summary

    def visit_AsyncFor(self, node):
        return visit_For(self, node, is_async=True)

    def visit_While(self, node):
        summary = (
            "a while loop"
            f", using {self.visit(node.test)} as the test"
            f", with a body of {self.visit_list(node.body)}"
            # TODO: orelse
        )
        return summary

    def visit_If(self, node):
        false_branch = self.visit_list(node.orelse)

        summary = "an if block"\
            + f", using {self.visit(node.test)} as the test"\
            + f", with a true branch of {self.visit_list(node.body)}"\
            + (f", and an false branch of {false_branch}" if len(false_branch) != 0 else "")
        return summary

    def visit_With(self, node, is_async=False):
        summary = (
            f"{interpret_async(is_async)} with block"
            f", using {self.visit_list(node.withitem)}"
            f", with a body of {self.visit_list(node.body)}"
            # TODO: orelse
        )
        return summary
    
    def visit_AsyncWith(self, node):
        return visit_With(self, node, is_async=True)

    def visit_Raise(self, node):
        summary = ""\
            + "a raise statement"\
            + (f", raising an exception {self.visit(node.exc)}" if node.exc else "")\
            + (f", with a cause of {self.visit(node.cause)}" if node.cause else "")

        return summary
    
    def visit_Try(self, node):
        summary = (
            "a try block"
            f", using {self.visit_list(node.handlers)} as the exception handlers"
            f", with a body of {self.visit_list(node.body)}"
            f",and a final body of {self.visit_list(node.finalbody)}"
            # TODO: orelse
        )
        return summary

    def visit_Assert(self, node):
        return "TODO"

    def visit_Import(self, node):
        return "TODO"
    
    def visit_ImportFrom(self, node):
        return "TODO"

    def visit_Global(self, node):
        return "TODO"

    def visit_Nonlocal(self, node):
        return "TODO"

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Pass(self, node):
        return "Pass"

    def visit_Break(self, node):
        return "Break"

    def visit_Continue(self, node):
        return "Continue"

    """
    expr = BoolOp(boolop op, expr* values)
        | BinOp(expr left, operator op, expr right)
        | UnaryOp(unaryop op, expr operand)
        | Lambda(arguments args, expr body)
        | IfExp(expr test, expr body, expr orelse)
        | Dict(expr* keys, expr* values)
        | Set(expr* elts)
        | ListComp(expr elt, comprehension* generators)
        | SetComp(expr elt, comprehension* generators)
        | DictComp(expr key, expr value, comprehension* generators)
        | GeneratorExp(expr elt, comprehension* generators)
        -- the grammar constrains where yield expressions can occur
        | Await(expr value)
        | Yield(expr? value)
        | YieldFrom(expr value)
        -- need sequences for compare to distinguish between
        -- x < 4 < 3 and (x < 4) < 3
        | Compare(expr left, cmpop* ops, expr* comparators)
        | Call(expr func, expr* args, keyword* keywords)
        | Num(object n) -- a number as a PyObject.
        | Str(string s) -- need to specify raw, unicode, etc?
        | FormattedValue(expr value, int? conversion, expr? format_spec)
        | JoinedStr(expr* values)
        | Bytes(bytes s)
        | NameConstant(singleton value)
        | Ellipsis
        | Constant(constant value)

        -- the following expression can appear in assignment context
        | Attribute(expr value, identifier attr, expr_context ctx)
        | Subscript(expr value, slice slice, expr_context ctx)
        | Starred(expr value, expr_context ctx)
        | Name(identifier id, expr_context ctx)
        | List(expr* elts, expr_context ctx)
        | Tuple(expr* elts, expr_context ctx)
    """

    def visit_BinOp(self, node):
        return f"{self.visit(node.left)} {self.visit(node.op)} {self.visit(node.right)}"

    def visit_UnaryOp(self, node):
        return f"{self.visit(node.op)} {self.visit(node.operand)}"

    def visit_Lambda(self, node):
        return f"an anonymous function taking {self.visit(node.args)} and returning {self.visit(node.body)}"

    def visit_IfExpr(self, node):
        return f"if {self.visit(node.test)} then {self.visit(node.body)} else {self.visit(node.orelse)}"

    def visit_Dict(self, node):
        return f"a dict of keys {self.visit_list(node.keys)}, and values {self.visit_list(node.values)}"

    def visit_Set(self, node):
        return f"a set of keys {self.visit_list(node.elts)}"

    def visit_ListComp(self, node):
        summary = (
            f"a list comprehension of {self.visit(node.elt)}"
            f", from {self.visit_list(node.generators)}"
        )
        return summary

    def visit_SetComp(self, node):
        summary = (
            f"a set comprehension of {self.visit(node.elt)}"
            f", from {self.visit_list(node.generators)}"
        )
        return summary

    def visit_DictComp(self, node):
        summary = (
            f"a dict comprehension of the {self.visit(node.key)} {self.visit(node.value)} key-value pair"
            f", from {self.visit_list(node.generators)}"
        )
        return summary

    def visit_GeneratorExp(self, node):
        summary = (
            f"a generator expression of {self.visit(node.elt)}"
            f", from {self.visit_list(node.generators)}"
        )
        return summary

    def visit_Await(self, node):
        return f"await {self.visit(node.value)}"

    def visit_Yield(self, node):
        return f"yield {self.visit(node.value) if node.value else ''}"

    def visit_YieldFrom(self, node):
        return f"yield from {self.visit(node.value)}"

    def visit_Compare(self, node):
        left = self.visit(node.left)
        ops = map(self.visit, node.ops)
        comp = map(self.visit, node.comparators)

        return left + ' ' + ' '.join([f'{op} {val}' for op, val in zip(ops, comp)])

    def visit_Call(self, node):
        return f"{self.visit(node.func)} called with {self.visit_list(node.args)}" 
        # TODO: Optional keywords (node.keywords)

    def visit_Num(self, node):
        return str(node.n)

    def visit_Str(self, node):
        return node.s

    def visit_FormattedValue(self, node):
        return "TODO"

    def visit_JoinedStr(self, node):
        return "TODO"

    def visit_Bytes(self, node):
        return "TODO"

    def visit_NameConstant(self, node):
        return str(node.value)

    def visit_Ellipsis(self, node):
        return "ellipsis"

    def visit_Constant(self, node):
        return self.visit(node.value)
    
    def visit_Attribute(self, node):
        return f"{self.visit(node.value)} DOT, {node.attr}'"

    def visit_Subscript(self, node):
        return f"the slice {self.visit(node.slice)} of {self.visit(node.value)}"

    def visit_Starred(self, node):
        return f"splat {self.visit(node.value)}"

    def visit_Name(self, node):
        return node.id

    def visit_List(self, node):
        if len(node.elts) == 0:
            return "an empty list"
        else:
            return f"a list of {self.visit_list(node.elts)}"

    def visit_Tuple(self, node):
        return f"a tuple of {self.visit_list(node.elts)}"

    """
    slice = Slice(expr? lower, expr? upper, expr? step)
        | ExtSlice(slice* dims)
        | Index(expr value)
    """

    def visit_Slice(self, node):
        summary = "A slice"\
            + (f"from {self.visit(node.lower)}" if node.lower else "")\
            + (f"to {self.visit(node.upper)}" if node.upper else "")\
            + (f"with stepping {self.visit(node.step)}" if node.step else "")
        return summary

    def visit_ExtSlice(self, node):
        return "TODO"

    def visit_Index(self, node):
        return f"an index of {self.visit(node.value)}"

    def visit_And(self, node):
        return "and"

    def visit_Or(self, node):
        return "or"

    def visit_Add(self, node):
        return "plus"

    def visit_Sub(self, node):
        return "minus"

    def visit_Mult(self, node):
        return "times"

    def visit_MatMult(self, node):
        return "matrix times"

    def visit_Div(self, node):
        return "divided by"

    def visit_Mod(self, node):
        return "modulo"

    def visit_Pow(self, node):
        return "to the power of"

    def visit_LShift(self, node):
        return "left shifted by"

    def visit_RShift(self, node):
        return "right shifted by"

    def visit_BitOr(self, node):
        return "bitwise or"

    def visit_BitXor(self, node):
        return "bitwise exclusive or"

    def visit_BitAnd(self, node):
        return "and"

    def visit_FloorDiv(self, node):
        return "integer divided by"

    def visit_Invert(self, node):
        return "inverted"

    def visit_Not(self, node):
        return "not"

    def visit_UAdd(self, node):
        return "positive"

    def visit_USub(self, node):
        return "negative"

    def visit_Eq(self, node):
        return "is equal to"

    def visit_NotEq(self, node):
        return "is not equal to"

    def visit_Lt(self, node):
        return "is less than"

    def visit_LtE(self, node):
        return "is less than or equal to"

    def visit_Gt(self, node):
        return "is greater than"

    def visit_GtE(self, node):
        return "is greater than or equal to"

    def visit_Is(self, node):
        return "is"

    def visit_IsNot(self, node):
        return "is not"

    def visit_In(self, node):
        return "in"

    def visit_NotIn(self, node):
        return "not in"

    """
    comprehension = (expr target, expr iter, expr* ifs, int is_async)

    excepthandler = ExceptHandler(expr? type, identifier? name, stmt* body)
                    attributes (int lineno, int col_offset)

    arguments = (arg* args, arg? vararg, arg* kwonlyargs, expr* kw_defaults,
                 arg? kwarg, expr* defaults)

    arg = (identifier arg, expr? annotation)
           attributes (int lineno, int col_offset)

    -- keyword arguments supplied to call (NULL identifier for **kwargs)
    keyword = (identifier? arg, expr value)

    -- import name with optional 'as' alias.
    alias = (identifier name, identifier? asname)

    withitem = (expr context_expr, expr? optional_vars)
    """

    def visit_comprehension(self, node):
        summary = (
            f"{'an async' if node.is_async else 'a'}"
            f" generator using {self.visit(node.target)} as an iterator"
            f", looping through {self.visit(node.iter)}"
            f", with guards of {self.visit_list(node.ifs)}"
        )
        return summary

    def visit_excepthandler(self, node):
        return "TODO"

    def visit_arguments(self, node):
        return f"{len(node.args)} arguments: {self.visit_list(node.args)}"
    
    def visit_arg(self, node):
        return node.arg + (f" of type {self.visit(node.annotation)}" if node.annotation else "")

    def visit_excepthandler(self, node):
        return "TODO"
    
    def visit_keyword(self, node):
        return "TODO"

    def visit_alias(self, node):
        return "TODO"

    def visit_withitem(self, node):
        return "TODO"


if __name__ == "__main__":
    raw = """
class SomeClass(object):
    def add(x: int, y: int) -> int:
        x = [ i + 1 for i in range(1, 10) if i % 2 == 0 ]
        ("hello", True)

        if True:
            return False

        return x + y
    """

    if len(sys.argv) < 2:
        print("Need filename")
        code = raw
    else:
        file_name = sys.argv[1]
        with open(file_name, 'r') as f:
            code = f.read()
    t = parse(code)
    print(dump(t))
    print(PrettyReader().visit(t))

