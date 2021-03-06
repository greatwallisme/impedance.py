from .circuit_elements import R, C, W, A, E, G, s, p  # noqa: F401
import numpy as np
from scipy.optimize import curve_fit


def rmse(a, b):
    """
    A function which calculates the root mean squared error
    between two vectors.

    Notes
    ---------
    .. math::

        RMSE = \\sqrt{\\frac{1}{n}(a-b)^2}
    """

    n = len(a)
    return np.linalg.norm(a - b) / np.sqrt(n)


def circuit_fit(frequencies, impedances, circuit, initial_guess,
                method='lm', bounds=None, bootstrap=False):

    """ Main function for fitting an equivalent circuit to data

    Parameters
    -----------------
    frequencies : numpy array
        Frequencies

    impedances : numpy array of dtype 'complex128'
        Impedances

    circuit : string
        string defining the equivalent circuit to be fit

    initial_guess : list of floats
        initial guesses for the fit parameters

    method : {‘lm’, ‘trf’, ‘dogbox’}, optional
        Name of method to pass to scipy.optimize.curve_fit

    bounds : 2-tuple of array_like, optional
        Lower and upper bounds on parameters. Defaults to bounds on all
        parameters of 0 and np.inf, except the CPE alpha
        which has an upper bound of 1

    Returns
    ------------
    p_values : list of floats
        best fit parameters for specified equivalent circuit

    p_errors : list of floats
        one standard deviation error estimates for fit parameters

    Notes
    ---------
    Need to do a better job of handling errors in fitting.
    Currently, an error of -1 is returned.

    """

    circuit = circuit.replace('_', '')

    f = frequencies
    Z = impedances

    if bounds is None:
        lb, ub = [], []
        p_string = [x for x in circuit if x not in 'ps(),-/']
        for i, (a, b) in enumerate(zip(p_string[::2], p_string[1::2])):
            lb.append(0)
            if str(a+b) == "E2":
                ub.append(1)
            else:
                ub.append(np.inf)

        bounds = ((lb), (ub))

    popt, pcov = curve_fit(wrapCircuit(circuit), f,
                           np.hstack([Z.real, Z.imag]), p0=initial_guess,
                           bounds=bounds, maxfev=100000, ftol=1E-13)

    perror = np.sqrt(np.diag(pcov))

    return popt, perror


def wrapCircuit(circuit):
    """ wraps function so we can pass the circuit string """
    def wrappedCircuit(frequencies, *parameters):
        """ returns a stacked

        Parameters
        ----------
        circuit : string
        parameters : list of floats
        frequencies : list of floats

        Returns
        -------
        array of floats

        """

        x = eval(buildCircuit(circuit, frequencies, *parameters))
        y_real = np.real(x)
        y_imag = np.imag(x)

        return np.hstack([y_real, y_imag])
    return wrappedCircuit


def computeCircuit(circuit, frequencies, *parameters):
    """ evaluates a circuit string for a given set of parameters and frequencies

    Parameters
    ----------
    circuit : string
    frequencies : list/tuple/array of floats
    parameters : list/tuple/array of floats

    Returns
    -------
    array of complex numbers
    """
    return eval(buildCircuit(circuit, frequencies, *parameters))


def buildCircuit(circuit, frequencies, *parameters):
    """ transforms a circuit, parameters, and frequencies into a string
    that can be evaluated

    Parameters
    ----------
    circuit : str
    parameters : list/tuple/array of floats
    frequencies : list/tuple/array of floats

    Returns
    -------
    eval_string : str
        Python expression for calculating the resulting fit
    """

    parameters = np.array(parameters).tolist()
    frequencies = np.array(frequencies).tolist()

    # remove spaces from circuit string
    circuit = circuit.replace(' ', '')

    series_string = "s(["
    for elem in circuit.split("-"):
        element_string = ""
        if "p" in elem:
            parallel_string = "p(("
            for par in elem.strip("p()").split(","):
                param_string = ""
                elem_type = par[0]
                elem_number = len(par.split("/"))

                param_string += str(parameters[0:elem_number])
                parameters = parameters[elem_number:]

                new_elem = (elem_type + "(" + param_string + "," +
                                        str(frequencies) + "),")
                parallel_string += new_elem

            element_string = parallel_string.strip(",") + "))"
        else:
            param_string = ""
            elem_type = elem[0]
            elem_number = len(elem.split("/"))

            param_string += str(parameters[0:elem_number])
            parameters = parameters[elem_number:]

            element_string = (elem_type + "(" + param_string + "," +
                                          str(frequencies) + ")")

        series_string += element_string + ","

    eval_string = series_string.strip(",") + "])"

    return eval_string


def calculateCircuitLength(circuit):
    l1 = ['R', 'E', 'W', 'C', 'A', 'G']
    length = 0
    for char in l1:
        length += circuit.count(char)
    return length
