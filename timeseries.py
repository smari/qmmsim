import csv


class Node:
    pass

class Sum(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s + %s" % (str(self.left), str(self.right))

class Sub(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s - %s" % (str(self.left), str(self.right))

class Mul(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s * %s" % (str(self.left), str(self.right))

class Div(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s * %s" % (str(self.left), str(self.right))

class Reference(Node):
    def __init__(self, name, t):
        self.refer_to = name
        self.time_offset = t

    def __repr__(self):
        return "%s[%s]" % (self.refer_to, self.time_offset)

class Variable(Node):
    def __init__(self):
        pass

    def get_value(self, t):
        return self.value

class Constant(Variable):
    def __init__(self, val=None):
        self.value = val

    def update(self, val):
        self.value = val

    def __str__(self):
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

    def extrema(self):
        return min(self.data), max(self.data)

    def update(self, val):
        print "Updating: %s" % (val)

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

    def eval(self, time):
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
        return "(scalar) [%d: %s]" % (len(self.data), samples)


class DerivedTimeSeries(TimeSeries):
    def __init__(self):
        self.equation = "UNDEFINED"

    def update(self, val):
        self.equation = val

    def __str__(self):
        return "(derived) " + str(self.equation)

if __name__ == "__main__":
    EMP = ScalarTimeSeries("EMP")
    EMP.load_data('emp.csv')
