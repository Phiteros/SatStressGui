# Author: Travis Oliphant
# 2003

from numpy import asarray, zeros, place, nan, mod, pi, extract, log, sqrt, \
     exp, cos, sin, size, polyval, polyint, log10

def sawtooth(t,width=1):
    """Returns a periodic sawtooth waveform with period 2*pi
    which rises from -1 to 1 on the interval 0 to width*2*pi
    and drops from 1 to -1 on the interval width*2*pi to 2*pi
    width must be in the interval [0,1]
    """
    t,w = asarray(t), asarray(width)
    w = asarray(w + (t-t))
    t = asarray(t + (w-w))
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = zeros(t.shape,ytype)

    # width must be between 0 and 1 inclusive
    mask1 = (w > 1) | (w < 0)
    place(y,mask1,nan)

    # take t modulo 2*pi
    tmod = mod(t,2*pi)

    # on the interval 0 to width*2*pi function is
    #  tmod / (pi*w) - 1
    mask2 = (1-mask1) & (tmod < w*2*pi)
    tsub = extract(mask2,tmod)
    wsub = extract(mask2,w)
    place(y,mask2,tsub / (pi*wsub) - 1)

    # on the interval width*2*pi to 2*pi function is
    #  (pi*(w+1)-tmod) / (pi*(1-w))

    mask3 = (1-mask1) & (1-mask2)
    tsub = extract(mask3,tmod)
    wsub = extract(mask3,w)
    place(y,mask3, (pi*(wsub+1)-tsub)/(pi*(1-wsub)))
    return y


def square(t,duty=0.5):
    """Returns a periodic square-wave waveform with period 2*pi
    which is +1 from 0 to 2*pi*duty and -1 from 2*pi*duty to 2*pi
    duty must be in the interval [0,1]
    """
    t,w = asarray(t), asarray(duty)
    w = asarray(w + (t-t))
    t = asarray(t + (w-w))
    if t.dtype.char in ['fFdD']:
        ytype = t.dtype.char
    else:
        ytype = 'd'
    y = zeros(t.shape,ytype)

    # width must be between 0 and 1 inclusive
    mask1 = (w > 1) | (w < 0)
    place(y,mask1,nan)

    # take t modulo 2*pi
    tmod = mod(t,2*pi)

    # on the interval 0 to duty*2*pi function is
    #  1
    mask2 = (1-mask1) & (tmod < w*2*pi)
    tsub = extract(mask2,tmod)
    wsub = extract(mask2,w)
    place(y,mask2,1)

    # on the interval duty*2*pi to 2*pi function is
    #  (pi*(w+1)-tmod) / (pi*(1-w))

    mask3 = (1-mask1) & (1-mask2)
    tsub = extract(mask3,tmod)
    wsub = extract(mask3,w)
    place(y,mask3,-1)
    return y

def gausspulse(t,fc=1000,bw=0.5,bwr=-6,tpr=-60,retquad=0,retenv=0):
    """Return a gaussian modulated sinusoid:  exp(-a t^2) exp(1j*2*pi*fc)

    If retquad is non-zero, then return the real and imaginary parts
       (inphase and quadrature)
    If retenv is non-zero, then return the envelope (unmodulated signal).
    Otherwise, return the real part of the modulated sinusoid.

    Inputs:

       t   --  Input array.
       fc  --  Center frequency (Hz).
       bw  --  Fractional bandwidth in frequency domain of pulse (Hz).
       bwr --  Reference level at which fractional bandwidth is calculated (dB).
       tpr --  If t is 'cutoff', then the function returns the cutoff time for when the
                  pulse amplitude falls below tpr (in dB).
       retquad -- Return the quadrature (imaginary) as well as the real part of the signal
       retenv  -- Return the envelope of th signal.
    """
    if fc < 0:
        raise ValueError, "Center frequency (fc=%.2f) must be >=0." % fc
    if bw <= 0:
        raise ValueError, "Fractional bandwidth (bw=%.2f) must be > 0." % bw
    if bwr >= 0:
        raise ValueError, "Reference level for bandwidth (bwr=%.2f) must " \
              "be < 0 dB" % bwr

    # exp(-a t^2) <->  sqrt(pi/a) exp(-pi^2/a * f^2)  = g(f)

    ref = pow(10, bwr/ 20)
    # fdel = fc*bw/2:  g(fdel) = ref --- solve this for a
    #
    # pi^2/a * fc^2 * bw^2 /4=-log(ref)
    a = -(pi*fc*bw)**2 / (4*log(ref))

    if t == 'cutoff': # compute cut_off point
        #  Solve exp(-a tc**2) = tref  for tc
        #   tc = sqrt(-log(tref) / a) where tref = 10^(tpr/20)
        if tpr >= 0:
            raise ValueError, "Reference level for time cutoff must be < 0 dB"
        tref = pow(10, tpr / 20)
        return sqrt(-log(tref)/a)

    yenv = exp(-a*t*t)
    yI = yenv * cos(2*pi*fc*t)
    yQ = yenv * sin(2*pi*fc*t)
    if not retquad and not retenv:
        return yI
    if not retquad and retenv:
        return yI, yenv
    if retquad and not retenv:
        return yI, yQ
    if retquad and retenv:
        return yI, yQ, yenv

def chirp(t, f0=0, t1=1, f1=100, method='linear', phi=0, qshape=None):
    """Frequency-swept cosine generator.

    Parameters
    ----------
    t : ndarray
        Times at which to evaluate the waveform.
    f0 : float or ndarray, optional
        Frequency (in Hz) of the waveform at time 0.  If `f0` is an
        ndarray, it specifies the frequency change as a polynomial in
        `t` (see Notes below).
    t1 : float, optional
        Time at which `f1` is specified.
    f1 : float, optional
        Frequency (in Hz) of the waveform at time `t1`.
    method : {'linear', 'quadratic', 'logarithmic'}, optional
        Kind of frequency sweep.
    phi : float
        Phase offset, in degrees.
    qshape : {'convex', 'concave'}
        If method is 'quadratic', `qshape` specifies its shape.

    Notes
    -----
    If `f0` is an array, it forms the coefficients of a polynomial in
    `t` (see `numpy.polval`). The polynomial determines the waveform
    frequency change in time.  In this case, the values of `f1`, `t1`,
    `method`, and `qshape` are ignored.

    """
    # Convert to radians.
    phi *= pi / 180
    if size(f0) > 1:
        # We were given a polynomial.
        return cos(2*pi*polyval(polyint(f0),t)+phi)
    if method in ['linear','lin','li']:
        beta = (f1-f0)/t1
        phase_angle = 2*pi * (f0*t + 0.5*beta*t*t)
    elif method in ['quadratic','quad','q']:
        if qshape == 'concave':
            mxf = max(f0,f1)
            mnf = min(f0,f1)
            f1,f0 = mxf, mnf
        elif qshape == 'convex':
            mxf = max(f0,f1)
            mnf = min(f0,f1)
            f1,f0 = mnf, mxf
        else:
            raise ValueError("qshape must be either 'concave' or 'convex' but "
                "a value of %r was given." % qshape)
        beta = (f1-f0)/t1/t1
        phase_angle = 2*pi * (f0*t + beta*t*t*t/3)
    elif method in ['logarithmic','log','lo']:
        if f1 <= f0:
            raise ValueError(
                "For a logarithmic sweep, f1=%f must be larger than f0=%f."
                % (f1, f0))
        beta = log10(f1-f0)/t1
        phase_angle = 2*pi * (f0*t + (pow(10,beta*t)-1)/(beta*log(10)))
    else:
        raise ValueError("method must be 'linear', 'quadratic', or "
            "'logarithmic' but a value of %r was given." % method)

    return cos(phase_angle + phi)
