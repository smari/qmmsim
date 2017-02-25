from __future__ import division

import re
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral, \
                      Combine, Optional, nums, Or, Forward, ZeroOrMore, \
                      StringEnd, alphanums, cppStyleComment
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
        multop = mult | div
        expop = Literal("^")
        assign = Literal("=").suppress()
        declare = Literal(":").suppress()

        # NOTE(smari):
        # Identifiers in the model often contain periods. It is unclear if
        # the periods mean anything in particular.
        ident = Word(alphas,alphanums + '_' + '.')
        complexident = (ident + lpar + integer + rpar) #.setParseAction(self.complexident_handle)

        # NOTE(smari): It appears that mathematical operations can be done
        # on both sides of a definition expression, such as:
        #   CJ: CJ/GDPN = A.CJ + B.CJ*(CJ(-1)/GDPN(-1)) + C.CJ*GAPAV + Q1.CJ*Q1
        #                   + Q2.CJ*Q2 + Q3.CJ*Q3 + D091.CJ*D091 + R_CJ,
        # ... which explains the distinction between declaring and defining.
        atom = (
                (complexident | ident).setParseAction(self.add_ref) |
                (floatnumber | integer).setParseAction(self.add_const)
               )

        #factor = Forward()
        #factor << (atom + ZeroOrMore(
        #        (expop + factor)).setParseAction(self.add_factor))
        expr = Forward()
        term = Forward()

        term << (
                 atom |
                 (atom + multop + (expr|atom)).setParseAction(self.add_term)
                )

        expr << (
                 (term + addop + (expr|term)).setParseAction(self.add_expr) |
                 term |
                 (lpar + expr + rpar)
                ).setName("atom or addition")

        coefficient_set_value = ((ident + assign + expr)
            .setParseAction(self.define_coefficient)
            .setName("coefficient definition"))

        timeseries_define = (
                ident + declare + ident + assign + expr
            ).setParseAction(self.define_timeseries).setName("time series definition")

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
            ).setName("ignore").setParseAction(lambda x: None)

        self.pattern = (expression | declaration | ignore | cppStyleComment) + StringEnd()

    def parse(self, string):
        try:
            L = self.pattern.parseString(string)
        except ParseException,err:
            self.simulation.error = "Parse error: %s" % (string.strip())
            self.simulation.error_details = err
            return False

        return True

    #def add_factor(self, str, loc, toks):
    #    print "Found factor: ", toks
    #    return self.push_first(str, loc, toks)

    def add_term(self, str, loc, toks):
        right = toks[2]
        left = toks[0]
        if toks[1] == '*':
            op = Mul(left, right)
        else:
            op = Div(left, right)
        print "Found term: ", op
        return op

    def add_expr(self, str, loc, toks):
        right = toks[2]
        left = toks[0]
        if toks[1] == '+':
            op = Sum(left, right)
        else:
            op = Sub(left, right)
        return op

    def add_ref(self, str, loc, toks):
        # TODO(smari): This currently does not accept variable references to
        #              define time offset; perhaps it would be good to support.
        # TODO(smari): Currently we don't check if the identifier exists and
        #              is a time series type.
        ref = Reference(toks[0], int(toks[1]))
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
            res = self.parse(line)
            if not res:
                print "Error at %s:%d" % (filename, lineno)
                return False

if __name__ == '__main__':
    p = AbaqusParser(None)
    p.debug = True
    with open("sedlabanki/qmm_likan_desember_2015.inp") as stikur:
        p.parse_file(stikur)
