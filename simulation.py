from timeseries import Coefficient, ScalarTimeSeries

class Simulation:
    def __init__(self, database):
        self.time_series = {}
        self.coefficients = {}
        self.error = None
        self.error_details = None
        self.input_files = []
        self.database = database

    def add_time_series(self, name, ts):
        self.time_series[name] = ts
        # TODO(smari): When we add a new time series, we need to determine
        #              the most extreme starting point and make sure the
        #              time series all line up properly.
        # self.adjust_time_series()
        return True

    def add_time_series_from_database(self, name):
        if name in self.database:
            ts = ScalarTimeSeries()
            ts.update(self.database[name])
            self.time_series[name] = ts

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

    def get_value(self, name, time):
        if name in self.coefficients:
            # Coefficients are timeless!
            return self.coefficients[name]

        if name in self.time_series:
            return self.time_series[name].evaluate(time)

        self.error = "Variable %s does not exist." % name
        return False

    def get_var(self, name):
        if name in self.coefficients:
            # Coefficients are timeless!
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
        print "Coefficients:"
        for k, v in self.coefficients.iteritems():
            print "%20s = %s" % (k, v)
        print "Time series:"
        for k, v in self.time_series.iteritems():
            print "%20s = %s" % (k, v)
