from __future__ import division

import re
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral, \
                      Combine, Optional, nums, Or, Forward, ZeroOrMore, \
                      StringEnd, alphanums, cppStyleComment, \
                      oneOf, Group
import math

from timeseries import Sum, Sub, Mul, Div, Reference, Coefficient, DerivedTimeSeries, ScalarTimeSeries, TimeSeries, Constant

class AbaqusParser:
    def __init__(self, simulation):
        #
        # NOTE(smari):
        # This is a really lousy parser, but it gets the job done.
        # In particular, we're ignoring a lot of Abaqus's actual
        # syntax and just parsing out the bits that seem meaningful.
        # This is bad form and will probably lead to me being put
        # against the wall when the revolution comes.
        #
        self.simulation = simulation
        self.debug = False

        self.expr_stack = []
        self.var_stack  = []

        # NOTE(smari): Floating point numbers. I have no idea if Abaqus
        #              actually supports 4.29E-12 format, but we might
        #              as well since it's easy.
        point = Literal('.')
        e = CaselessLiteral('E')
        plusorminus = Literal('+') | Literal('-')
        number = Word(nums)
        integer = Combine( Optional(plusorminus) + number )
        floatnumber = Combine( integer +
                               Optional( point + Optional(number) ) +
                               Optional( e + integer )
                             )

        plus  = Literal("+")
        minus = Literal("-")
        mult  = Literal("*")
        div   = Literal("/")
        lpar  = Literal("(").suppress()
        rpar  = Literal(")").suppress()
        addop  = plus | minus
        addop.setName("addop")
        mulop = mult | div
        mulop.setName("multop")
        op = addop | mulop
        expop = Literal("^")
        assign = Literal("=").suppress()
        declare = Literal(":").suppress()

        # NOTE(smari):
        # Identifiers in the model often contain periods. It is unclear if
        # the periods mean anything in particular.
        ident = Word(alphas, alphanums + '_' + '.')
        ident_subscript = (ident + lpar + integer + rpar) #.setParseAction(self.ident_subscript_handle)

        # NOTE(smari): It appears that mathematical operations can be done
        # on both sides of a definition expression, such as:
        #   CJ: CJ/GDPN = A.CJ + B.CJ*(CJ(-1)/GDPN(-1)) + C.CJ*GAPAV + Q1.CJ*Q1
        #                   + Q2.CJ*Q2 + Q3.CJ*Q3 + D091.CJ*D091 + R_CJ,
        # ... which explains the distinction between declaring and defining.
        expr = Forward()
        term = Forward()

        atom = (
                (ident_subscript | ident).setParseAction(self.add_ref) |
                (floatnumber | integer).setParseAction(self.add_const)
               )
        atom.setName("atom")

        #factor = Forward()
        #factor << (atom + ZeroOrMore(
        #        (expop + factor)).setParseAction(self.add_factor))

        def termfail(s, loc, expr, err):
            print "ERROR: %s / %s " % (expr, err)
            print "Failed on term '%s' at %s" % (s.strip(), loc)
            print '               ' + ' '*loc + '^'

        term = (
            (atom + ZeroOrMore(mulop + expr)) |
            atom |
            (lpar + expr + rpar)
        )
        term.setName("term")

        expr << (
                (term + ZeroOrMore(addop + expr)).setParseAction(self.add_expr) |
                (lpar + expr + rpar)
                )
        expr.setName("expr")
        expr.setFailAction(termfail)


        coefficient_set_value = ((ident + assign + expr)
            .setParseAction(self.define_coefficient)
            .setName("def(coefficient)"))

        timeseries_define = (
                ident + declare + ident + assign + expr
            ).setParseAction(self.define_timeseries).setName("def(time series)")

        expression = ((coefficient_set_value | timeseries_define) +
                      Literal(",").suppress())
        expression.setName("expression")

        #expression = ( Optional(ident + declare) +
        #               Optional((ident + assign).setParseAction(self.assign_var)) +
        #               expr
        #             )

        # TODO(smari): Use these declarations as initializers for coefficients
        #              or time series in the simulation.
        # NOTE(smari): "ENDROGENOUS", "EXOGENOUS" and "COEFFICIENT" tell us
        #              what kind of situation we're talking about.
        #              Coefficients will end up as scalars in the simulation,
        #              whereas the others are either derived time series or
        #              time series loaded from the "database" (read: Excel file)
        #
        declaration = (
            (
                Literal("ENDOGENOUS") |
                Literal("EXOGENOUS") |
                Literal("COEFFICIENT")
            )   + ZeroOrMore(ident)
                + Optional(Literal(",")).suppress()
            ).setParseAction(self.declare_variable).setName("declaration")

        # Junk that we're ignoring for now... it's probably super important!
        ignore = (
            Literal("Dofile") |
            Literal(";") |
            Literal("usemod;") |
            Literal("ADDSYM") |
            Literal("filemod cbiq;") |
            Literal("ADDEQ BOTTOM")
            ).setName("ignore").suppress()

        self.pattern = (expression | declaration | ignore | StringEnd())
        self.pattern.ignore(cppStyleComment)

    def parse(self, string):
        try:
            L = self.pattern.parseString(string)
        except ParseException,err:
            self.simulation.error = "Parse error: %s" % (string.strip())
            self.simulation.error_details = err
            # return False

        return True

    def add_expr(self, s, loc, toks):
        if len(toks) == 1:
            return toks[0]

        right = toks[2]
        left = toks[0]
        if toks[1] == '*':
            op = Mul(left, right)
        elif toks[1] == '/':
            op = Div(left, right)
        elif toks[1] == '+':
            op = Sum(left, right)
        else:
            op = Sub(left, right)

        return op


    def add_ref(self, str, loc, toks):
        # TODO(smari): This currently does not accept variable references to
        #              define time offset; perhaps it would be good to support.
        # TODO(smari): Currently we don't check if the identifier exists and
        #              is a time series type.
        varname = toks[0]
        var = self.simulation.get_var(varname)
        if len(toks) > 1:
            time_offset = toks[1]
        else:
            time_offset = 0
        ref = Reference(varname, var, int(time_offset))
        return ref

    def add_const(self, str, loc, toks):
        const = Constant(toks[0])
        return const


    def declare_variable(self, str, loc, toks):
        var_type = toks[0]
        if var_type == "EXOGENOUS":
            for tok in toks[1:]:
                res = self.simulation.add_time_series_from_database(tok)
                if not res:
                    return False
        elif var_type == "ENDOGENOUS":
            for tok in toks[1:]:
                ts = DerivedTimeSeries()
                res = self.simulation.add_time_series(tok, ts)
                if not res:
                    return False
        elif var_type == "COEFFICIENT":
            for tok in toks[1:]:
                res = self.simulation.add_coefficient(tok)
                if not res:
                    return False
        else:
            self.simulation.error = "Error: Unknown variable type '%s'" % var_type
            return False


    def push_first(self, str, loc, toks):
        print "Pushing %s of %s" % (toks[0], toks)
        self.expr_stack.append(toks[0])

    def assign_var(self, str, loc, toks):
        self.var_stack.append(toks[0])

    def define_timeseries(self, str, loc, toks):
        # TODO(smari): This is currently ignoring the left hand side!
        self.simulation.set_value(toks[0], toks[2])

    def define_coefficient(self, str, loc, toks):
        self.simulation.set_value(toks[0], toks[1])

    def parse_file(self, filename):
        self.simulation.input_files.append(filename)
        try:
            file_handle = open(filename, "r")
        except IOError, e:
            self.simulation.error = "Could not open %s: %s" % (filename, e)
            return False
        lineno = 0
        for line in file_handle:
            lineno += 1
            if line.strip() == "":
                continue
            res = self.parse(line.strip())
            if not res:
                print "Error at %s:%d" % (filename, lineno)
                return False

if __name__ == '__main__':
    p = AbaqusParser(None)
    p.debug = True
    with open("sedlabanki/qmm_likan_desember_2015.inp") as stikur:
        p.parse_file(stikur)
