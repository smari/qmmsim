from __future__ import division

import re
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral, \
                      Combine, Optional, nums, Or, Forward, ZeroOrMore, \
                      StringEnd, alphanums, cppStyleComment
import math

from timeseries import Sum, Sub, Mul, Div, Reference, Coefficient, DerivedTimeSeries, ScalarTimeSeries, TimeSeries

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
        # NOTE(smari): We don't really want to suppress these though...
        lpar  = Literal("(").suppress()
        rpar  = Literal(")").suppress()
        addop  = plus | minus
        multop = mult | div
        expop = Literal("^")
        assign = Literal("=")
        declare = Literal(":")

        # NOTE(smari):
        # Identifiers in the model often contain periods. It is unclear if
        # the periods mean anything in particular.
        ident = Word(alphas,alphanums + '_' + '.')
        complexident = (ident + '(' + integer + ')').setParseAction(self.complexident_handle)

        # NOTE(smari): It appears that mathematical operations can be done
        # on both sides of a definition expression, such as:
        #   CJ: CJ/GDPN = A.CJ + B.CJ*(CJ(-1)/GDPN(-1)) + C.CJ*GAPAV + Q1.CJ*Q1
        #                   + Q2.CJ*Q2 + Q3.CJ*Q3 + D091.CJ*D091 + R_CJ,
        # ... which explains the distinction between declaring and defining.
        expr = Forward()
        atom = (
                (floatnumber | integer | complexident | ident).setParseAction(self.push_first) |
                (lpar + expr.suppress() + rpar)
               )

        factor = Forward()
        factor << atom + ZeroOrMore(
                (expop + factor).setParseAction(self.push_first))

        term = factor + ZeroOrMore(
                (multop + factor).setParseAction(self.push_first))

        expr << term + ZeroOrMore(
                (addop + term).setParseAction(self.push_first) ) + Literal(",").suppress()

        coefficient_set_value = (ident + assign + expr).setParseAction(self.define_coefficient)
        timeseries_define = (ident + declare + ident + assign + expr).setParseAction(self.define_timeseries)

        expression = timeseries_define | coefficient_set_value

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
            ).setParseAction(self.declare_variable)

        # Junk that we're ignoring for now... it's probably super important!
        ignore = (
            Literal("Dofile") |
            Literal(";") |
            Literal("usemod;") |
            Literal("ADDSYM") |
            Literal("filemod cbiq;") |
            Literal("ADDEQ BOTTOM")
            ).setParseAction(lambda x: None)

        self.pattern = (expression | declaration | ignore | cppStyleComment) + StringEnd()

    def parse(self, string):
        try:
            L = self.pattern.parseString(string)
        except ParseException,err:
            self.simulation.error = "Parse error: %s" % (string.strip())
            self.simulation.error_details = err
            return False

        # if self.debug: print "expr_stack=", self.expr_stack

        # calculate result , store a copy in ans , display the result to user
        result = self.evaluate_stack(self.expr_stack)

        # Assign result to a variable if required
        # if self.debug: print "var=",self.var_stack
        if len(self.var_stack)==1:
            res = self.simulation.set_value(self.var_stack[0], result)
            if not res:
                return False

        return True

    def complexident_handle(self, str, loc, toks):
        print "Complex identifier!!"
        print str, loc, toks


    def declare_variable(self, str, loc, toks):
        var_type = toks[0]
        if var_type == "EXOGENOUS":
            for tok in toks[1:]:
                ts = ScalarTimeSeries()
                res = self.simulation.add_time_series(tok, ts)
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
        print self.expr_stack
        self.expr_stack.append(toks[0])

    def assign_var(self, str, loc, toks):
        self.var_stack.append(toks[0])

    def define_timeseries(self, str, loc, toks):
        print "Defining timeseries %s" % toks

    def define_coefficient(self, str, loc, toks):
        print "Defining coefficient %s" % toks
        self.simulation.set_value(toks[0], toks[2])

    def evaluate_stack(self, stack):
        # NOTE(smari): This is stupid and should die.
        # Specifically, this was a nice testing function for initial parsing
        # but once we started to get good results, it didn't make much sense
        # any more.
        self.opn = { "+" : ( lambda a,b: a + b ),
                     "-" : ( lambda a,b: a - b ),
                     "*" : ( lambda a,b: a * b ),
                     "/" : ( lambda a,b: a / b ),
                     "^" : ( lambda a,b: a ** b ) }

        if (len(stack) == 0): return
        op = stack.pop()
        if op in "+-*/^":
            op2 = self.evaluate_stack(stack)
            op1 = self.evaluate_stack(stack)
            return self.opn[op](op1, op2)
        elif isinstance(op, TimeSeries):
            return "VAR" # op # TODO: Danger! Danger! This is infinite loop inducing!
        elif re.search('^[a-zA-Z][a-zA-Z0-9_]*$',op):
            if self.simulation.has_var(op):
                return str(self.simulation.get_var(op))
            else:
                return 0
        elif re.search('^[-+]?[0-9]+$',op):
            return long( op )
        else:
            return float( op )

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
