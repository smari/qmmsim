from timeseries import Coefficient

class Simulation:
    def __init__(self):
        self.time_series = {}
        self.coefficients = {}
        self.error = None
        self.error_details = None
        self.input_files = []

    def add_time_series(self, name, ts):
        self.time_series[name] = ts
        # TODO(smari): When we add a new time series, we need to determine
        #              the most extreme starting point and make sure the
        #              time series all line up properly.
        # self.adjust_time_series()
        return True

    def add_coefficient(self, name):
        self.coefficients[name] = Coefficient()
        return True

    def set_value(self, name, value):
        if name in self.coefficients:
            self.coefficients[name] = value
        elif name in self.time_series:
            self.time_series[name].update(value)
        else:
            self.error = "Trying to set value of undeclared variable."
            return False
        return True

    def get_var(self, name):
        if name in self.coefficients:
            return self.coefficients[name]

        if name in self.time_series:
            return self.time_series[name]

        self.error = "Variable %s does not exist." % name
        return False

    def has_var(self, name):
        if name in self.coefficients: return True
        if name in self.time_series: return True
        return False

    def handle_errors(self):
        print "Error arose: %s" % (self.error)
        if self.error_details:
            print "                     ",
            print " "*(self.error_details.column-1) + "----^"
            print self.error_details

        print "Environment consisted of:"
        print "   %4d coefficients." % len(self.coefficients)
        print "   %4d time series." % len(self.time_series)
        print "   Parsed %d input files." % len(self.input_files)
        print self.coefficients.keys()
        print self.time_series.keys()
