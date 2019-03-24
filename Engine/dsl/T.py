import functools
import operator
import traces


# TEMPORAL SUBSTRATE


# Lays the foundation for time series processing
# Much of the heavy lifting is done by the "traces" Python module
# Most of the functions below serve as wrappers to that module


# Time-related constants
DawnOfTime = '1900-01-01'
AssessmentStart = '2018-01-01'
AssessmentEnd = '2020-12-31'


# Internal function: Detect whether an object is a time series
def is_timeseries(a):
    return type(a) is traces.timeseries.TimeSeries


# Apply a binary function to the values in two time series
def apply_binary_ts_fcn(f, ts1, ts2):
    return ts1.operation(ts2, lambda x, y: f(x, y))


# Apply a unary function to the values in a time series
def apply_unary_ts_fcn(f, ts):
    return ts.operation(ts, lambda x, y: f(x))


# Instantiate a new time series, given a list of date-value pairs
def TS(pairs):
    return T(traces.TimeSeries(pairs))


# T OBJECTS


class T:
    def __init__(self, value, cf=1):

        # Substantive content of the object
        self.value = value

        # Certainty factor
        self.cf = cf

        # Time series indicator
        if type(value) is traces.timeseries.TimeSeries:
            self.ts = True
        else:
            self.ts = False

    # &
    def __and__(self, o):
        return internal_and(self, o)

    def __rand__(self, o):
        return internal_and(self, o)

    # |
    def __or__(self, o):
        return internal_or(self, o)

    def __ror__(self, o):
        return internal_or(self, o)

    # ~
    def __invert__(self):
        if self.value is None:
            return T(None)
        else:
            return T(not self.value, self.cf)

    # Arithmetic...
    def __add__(self, o):
        return process_binary(operator.add, self, o)

    def __radd__(self, o):
        return process_binary(operator.add, self, o)

    def __mul__(self, o):
        return process_binary_mult(self, o)

    def __rmul__(self, o):
        return process_binary_mult(self, o)

    def __sub__(self, o):
        return process_binary(operator.sub, self, o)

    def __rsub__(self, o):
        return process_binary(operator.sub, o, self)

    def __truediv__(self, o):
        return process_binary(operator.truediv, self, o)

    def __rtruediv__(self, o):
        return process_binary(operator.truediv, o, self)

    # Comparison...
    def __lt__(self, o):
        return process_binary(operator.lt, self, o)

    def __le__(self, o):
        return process_binary(operator.le, self, o)

    def __eq__(self, o):
        # Hacking equality == playing with fire
        return process_binary(operator.eq, self, o)

    def __ne__(self, o):
        return ~ (self == o)

    def __gt__(self, o):
        return process_binary(operator.gt, self, o)

    def __rgt__(self, o):
        return process_binary(operator.gt, o, self)

    def __ge__(self, o):
        return process_binary(operator.ge, self, o)

    def __rge__(self, o):
        return process_binary(operator.ge, o, self)

    # TODO: Add list operators


# Internal processing of most binary operators
# TODO: Catch uncertainty within assessment range for time series
def process_binary(f, a, b):

    # Calculate certainty
    cf = cf_conj(get_cf(a), get_cf(b))

    # Compute the result, based on the object types
    if is_stub(a) or is_stub(b):
        return Stub(cf)
    elif is_none(a) or is_none(b):
        return T(None, cf)
    elif is_ts_T(a) or is_ts_T(b):
        return T(apply_binary_ts_fcn(f, get_val(a), get_val(b)), cf)
    else:
        return T(f(get_val(a), get_val(b)), cf)


# Special case for multiplication
# Short-circuits when one of the values is 0
def process_binary_mult(a, b):

    # Calculate certainty
    cf = cf_conj(get_cf(a), get_cf(b))

    # Compute the result, based on the object types
    if get_val(a) is 0 or get_val(b) is 0:
        return T(0, cf)
    elif is_stub(a) or is_stub(b):
        return Stub(cf)
    elif is_none(a) or is_none(b):
        return T(None, cf)
    elif is_ts_T(a) or is_ts_T(b):
        return T(apply_binary_ts_fcn(operator.mul, get_val(a), get_val(b)), cf)
    else:
        return T(get_val(a) * get_val(b), cf)


# Compute the CF of a conjunction
def cf_conj(a, b):
    return a * b


# Compute the CF of a disjunction
def cf_disj(a, b):
    return a + b - (a * b)


# Gets the certainty factor of a T object or scalar
def get_cf(a):
    if type(a) is T:
        return a.cf
    else:
        return 1


# Gets the value of a T object or scalar
def get_val(a):
    if type(a) is T:
        return a.value
    else:
        return a


# Object is a T whose contents is a time series
def is_ts_T(a):
    return type(a) is T and a.ts


# Determines whether an object is a T with a value of None
def is_none(a):
    return type(a) is T and a.value is None


# STUBS


# Global variable representing a rule stub
def Stub(cf=1):
    return T(StubVal, cf)


# Used internally to indicate that a T object is a stub
StubVal = "#stub#"


# Determines whether a T object is a stub
def is_stub(a):
    return not is_ts_T(a) and get_val(a) == StubVal


# LOGIC


def And(*args):
    return functools.reduce(internal_and, args)


def Or(*args):
    return functools.reduce(internal_or, args)


def Not(a):
    if is_none(a) or is_stub(a):
        return a
    elif is_ts_T(a):
        return T(apply_unary_ts_fcn(Not, a.value), get_cf(a))
    else:
        return T(not get_val(a), get_cf(a))


# TODO: Make the methods below private, if possible


def internal_and(a, b):
    return more_internal_and(get_val(a), get_val(b), get_cf(a) * get_cf(b))


def more_internal_and(a, b, cf):
    if a is False or b is False:
        return T(False, cf)
    elif a is None or b is None:
        return T(None, cf)
    elif is_stub(a) or is_stub(b):
        return Stub(cf)
    else:
        return T(True, cf)


def internal_or(a, b):
    cfa = get_cf(a)
    cfb = get_cf(b)
    return more_internal_or(get_val(a), get_val(b), cfa + cfb - (cfa * cfb))


def more_internal_or(a, b, cf):
    if a is True or b is True:
        return T(True, cf)
    elif a is None or b is None:
        return T(None, cf)
    elif is_stub(a) or is_stub(b):
        return Stub(cf)
    else:
        return T(False, cf)


# CONDITIONALS


# TODO: Implement lazy evaluation so args b and c are only invoked as needed
# TODO: Finish implementing certainty factors
def If(a, b, c):
    if is_none(a) or is_stub(a):
        return a
    #if get_val(a) is None:
    #    return T(None, get_cf(a))
    #elif is_stub(a):
    #    return a
    elif get_val(a):
        if type(b) is T:
            return b
        else:
            return T(b)
    else:
        if type(c) is T:
            return c
        else:
            return T(c)


# Display a T object as a comprehensible string
def Pretty(a):
    if is_ts_T(a):
        return apply_unary_ts_fcn(Pretty, a.value)
    else:
        return str("Stub" if is_stub(a) else get_val(a)) + " (" + str(round(get_cf(a) * 100)) + "% certain)"
