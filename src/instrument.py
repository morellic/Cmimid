import sys
from clang.cindex import Index, Config, CursorKind

LIBCLANG_PATH = sys.argv[2]
Config.set_library_file(LIBCLANG_PATH)

counter = 0;
def create_cb_name():
    global counter
    counter += 1
    return "__fn%s" % counter

def compound_body_with_cb(node):
    stmts = (repr(to_ast(node))[2:-2]
             if node.kind == CursorKind.COMPOUND_STMT
             else repr(to_ast(node)))

    return "{\n%s() ;\n%s\n%s() ;\n}" % (create_cb_name(),
                                        stmts,
                                        create_cb_name())

class AstNode:
    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return " ".join([t.spelling for t in self.node.get_tokens()])

class IntegerLiteral(AstNode):
    def __repr__(self):
        return super().__repr__()
        #return "%s %s" % (self.node.type.spelling, self.node.spelling)

class ParmDecl(AstNode):
    def __repr__(self):
        return super().__repr__()
        assert not list(self.node.get_children())
        #return "%s %s" % (self.node.type.spelling, self.node.spelling)

class VarDecl(AstNode):
    def __repr__(self):
        return super().__repr__()
        #children = "\n".join([repr(to_ast(c)) for c in self.node.get_children()])
        #return "%s %s" % (self.node.type.spelling, children)

class DeclStmt(AstNode):
    def __repr__(self):
        return super().__repr__()
        #return "\n".join([repr(to_ast(c)) for c in self.node.get_children()])

class ReturnStmt(AstNode):
    def __repr__(self):
        return "%s ;" % super().__repr__()
        #return "\n".join([repr(to_ast(c)) for c in self.node.get_children()])

class WhileStmt(AstNode):
    def __repr__(self):
        before_cb = create_cb_name()
        after_cb = create_cb_name()

        children = list(self.node.get_children())
        assert(len(children) == 2)

        cond = repr(to_ast(children[0]))
        body = compound_body_with_cb(children[1]) 

        return "%s();\nwhile ( %s ) %s\n%s();" % (
                before_cb, cond, body, after_cb)



class IfStmt(AstNode):
    def __init__(self, node, with_cb=True):
        super().__init__(node)
        self.with_cb = with_cb

    def __repr__(self):
        if self.with_cb:
            before_cb = create_cb_name()
            after_cb = create_cb_name()

        cond =  ""
        if_body = ""
        else_body = ""

        for i, c in enumerate(self.node.get_children()):
            if i == 0:
                cond = "%s" % repr(to_ast(c))
            elif i == 1:
                if_body = compound_body_with_cb(c)
            elif i == 2:
                if c.kind == CursorKind.IF_STMT:
                    # else if -> no before/after if callbacks
                    else_body = "%s" % repr(IfStmt(c, with_cb=False))
                else:
                    else_body = compound_body_with_cb(c)

        block = "if ( %s ) %s" % (cond, if_body)
        if else_body != "":
            block += " else %s" % else_body

        if self.with_cb:
            return "%s() ;\n%s\n%s() ;" % (before_cb, block, after_cb)

        return block

class CompoundStmt(AstNode):
    def __repr__(self):
        stmts = [];
        for c in self.node.get_children():
            rep = repr(to_ast(c))
            if rep[-1] != "}" and rep[-1] != "\n" and rep[-1] != ";":
                rep += " ;"
            stmts.append(rep)
        body = "\n".join(stmts)
        return "{\n%s\n}" % body


class FunctionDecl(AstNode):
    def __repr__(self):
        children = list(self.node.get_children())
        return_type = self.node.result_type.spelling
        function_name = self.node.spelling
        params = ", ".join([repr(to_ast(c)) for c in children[:-1]])
        body = repr(to_ast(children[-1]))
        return "%s %s(%s) %s" % (return_type, function_name, params, body)


def to_ast(node):
    #print(node.kind, repr(AstNode(node)))

    # declarations
    if node.kind == CursorKind.FUNCTION_DECL:
        return FunctionDecl(node)
    elif node.kind == CursorKind.PARM_DECL:
        return ParmDecl(node)
    elif node.kind == CursorKind.VAR_DECL:
        return VarDecl(node)

    # literals
    elif node.kind == CursorKind.INTEGER_LITERAL:
        return IntegerLiteral(node)

    # statements
    elif node.kind == CursorKind.COMPOUND_STMT:
        return CompoundStmt(node)
    elif node.kind == CursorKind.DECL_STMT:
        return DeclStmt(node)
    elif node.kind == CursorKind.IF_STMT:
        return IfStmt(node)
    elif node.kind == CursorKind.WHILE_STMT:
        return WhileStmt(node)
    elif node.kind == CursorKind.RETURN_STMT:
        return ReturnStmt(node) # need the ;

    else:
        return AstNode(node)

def parse(arg):
    idx = Index.create()
    translation_unit = idx.parse(arg)
    for i in translation_unit.cursor.get_children():
        if i.location.file.name == sys.argv[1]:
            print(repr(to_ast(i)))


parse(sys.argv[1])
