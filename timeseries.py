import csv

class Variable:
    def __init__(self):
        pass

class Coefficient(Variable):
    def __init__(self):
        self.value = None

    def update(self, val):
        self.value = val

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

class DerivedTimeSeries(TimeSeries):
    def __init__(self):
        self.equation = ""

    def set_equation(self, equation):
        self.equation = ""



if __name__ == "__main__":
    EMP = ScalarTimeSeries("EMP")
    EMP.load_data('emp.csv')
