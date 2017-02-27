import csv


class Node:
    pass

class Sum(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def evaluate(self, time):
        print self.left, self.left.evaluate(time)
        print self.right, self.right.evaluate(time)
        return self.left.evaluate(time) + self.right.evaluate(time)

    def __repr__(self):
        # return "%s + %s" % (str(self.left), str(self.right))
        return "(+ %s %s)" % (str(self.left), str(self.right))

class Sub(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        #return "%s - %s" % (str(self.left), str(self.right))
        return "(- %s %s)" % (str(self.left), str(self.right))

class Mul(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        #return "%s * %s" % (str(self.left), str(self.right))
        return "(* %s %s)" % (str(self.left), str(self.right))

class Div(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        #return "%s / %s" % (str(self.left), str(self.right))
        return "(/ %s %s)" % (str(self.left), str(self.right))

class Reference(Node):
    def __init__(self, name, var, t):
        self.refer_to = name
        self.ref = var
        # print "Referring to", var
        self.time_offset = t

    def evaluate(self, time):
        if time < 0:
            return Constant(0)
        if time > 100:
            return Constant(0)
        t = self.time_offset+time
        return self.ref.evaluate(t)

    def __repr__(self):
        return "%s[%s]" % (self.refer_to, self.time_offset)

class Variable(Node):
    def __init__(self):
        pass

class Constant(Variable):
    def __init__(self, val=None):
        self.value = val

    def update(self, val):
        self.value = val

    def evaluate(self, time):
        return self.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

class Coefficient(Variable):
    def __init__(self):
        self.value = None

    def update(self, val):
        self.value = val

    def __str__(self):
        return str(self.value)

class TimeSeries(Variable):
    def __init__(self):
        pass


class ScalarTimeSeries(TimeSeries):
    def __init__(self):
        self.data = []
        self.period_names = []
        self.debug = False
        # How this compares to the other data sets:
        # The time series that starts at the earliest point in time should
        # be considered to start at 0.
        self.data_starts_at = 0

    def update(self, val):
        self.set_data(val)

    def set_data(self, data):
        self.data = data

    def load_data(self, filename):
        self.data = []
        self.period_names = []
        with open(filename) as fh:
            csv_reader = csv.reader(fh, dialect='excel')
            for row in csv_reader:
                self.period_names.append(row[0])
                self.data.append(row[1])

        if self.debug:
            print "Loaded %d data points ranging from %s to %s" % (
                len(EMP.data), EMP.period_names[0], EMP.period_names[-1])

    def evaluate(self, time):
        starttime = self.data_starts_at
        endtime = len(self.data)+self.data_starts_at
        if time > starttime and time < endtime:
            return self.data[time-starttime]
        else:
            return 0

    def __str__(self):
        if len(self.data) == 0:
            samples = "empty"
        elif len(self.data) < 10:
            samples = ", ".join(self.data)
        else:
            samples = ", ".join(self.data[:3]) + " ... " + ", ".join(self.data[-3:])
        return "[%d: %s]" % (len(self.data), samples)


class DerivedTimeSeries(TimeSeries):
    def __init__(self):
        self.equation = "UNDEFINED"

    def update(self, val):
        self.equation = val

    def evaluate(self, time):
        # TODO(smari): Actually evaluate
        return self.equation.evaluate(time)

    def __str__(self):
        return str(self.equation)

if __name__ == "__main__":
    EMP = ScalarTimeSeries("EMP")
    EMP.load_data('emp.csv')
