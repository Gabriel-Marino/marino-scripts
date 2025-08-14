import lmfit
import matplotlib.pyplot as plt
import numpy as np
import os
import re

def thermal_lens_light_intensity_shen_model_def(t: float, tc: float, m: float, V: float, th: float) -> float:
    """
    parameters:
    - t: time
    - tc: charcteristic time
    - m: geometric param given by the ratio of the probe-pump radiuses at the sample position
    - V: geometrica param
    - th: theta relates to the amplitude
    """
    return abs(1-(th/2)*np.arctan((2*m*V*2*t)/(tc*((1+2*m)**2+V**2)+2*t*(1+2*m+V**2))))**2

def tc_def(re0: float, D: float) -> float:
    """
    parameters:
    - re0: pump radius at it's focii, optimally the position of the sample
    - D: sample's thermal diffusivity
    """
    return (re0**2)/(4*D)

def D_def(k: float, rhoV: float, cp: float) -> float:
    """
    parameters:
    - k: thermal conductivity
    - rhoV: volumetric density
    - cp: specific heat at constant pressure
    """
    return k/(rhoV*cp)

def m_def(rp1: float, re0: float) -> float:
    """
    parameters:
    - rp1: probe radius at the sample postion
    - re0: pump radius at it's focii/sample position
    """
    return (rp1/re0)**2

def V_def(z1: float, z2: float, zcp: float) -> float:
    """
    parameters:
    - z1: the distance between the focii of the pump beam to the focii of the probe beam
    - z2: the distance between the sample to the detector
    - zcp: proba confocal distance
    """
    return z1/zcp + (zcp/z2)*(1+(z1/zcp)**2)

def gaussian_laser_beam_profile_def(z: float, z0: float, zc: float, r0: float) -> float:
    """
    parameters:
    - z: a position along the beam propagation
    - z0: an arbitrary position of reference
    - zc: confocal parameter of the beam
    - r0: the radius of the beam at it's focii
    """
    return r0*np.sqrt(1+((z-z0)/zc)**2)

def zc_def(r0: float, wl: float) -> float:
    """
    parameters:
    - r0: the radius of the beam at it's focii
    - wl: wavelength of the beam
    """
    return (np.pi*r0**2)/wl

def thermal_lens_light_intensity_shen_model(t: float, tc: float, z1: float, z2: float, re0: float, rp0: float, lp: float, th: float) -> float:
    """
    parameters:
    - t: time
    - tc: characteristic time
    - z1: distance between pump-probe focii
    - z2: distance to the sensor from the sampel
    - re0: pump beam radius at the focii
    - rp0: probe beam radius at the focii
    - lp: wavelength of the probe beam
    - th: theta
    """
    return thermal_lens_light_intensity_shen_model_def(t, tc, m_def(gaussian_laser_beam_profile_def(z1, 0, zc_def(rp0, lp), rp0), re0), V_def(z1, z2, zc_def(rp0, lp)), th)


def fitter(model_func: callable, params_to_fit: dict[str, dict[float, bool]], path_to_data: str, xname: str = 't', yname: str = 'y_label'):

    data = np.loadtxt(path_to_data)
    x_data = data[:,0]
    y_data = data[:,1]

    mod = lmfit.Model(model_func, independent_vars=[xname])
    params = mod.make_params()

    for name, settings in params_to_fit.items():
        params[name].set(**settings)

    res = mod.fit(y_data, params, **{xname: x_data})
    for name, settings in params_to_fit.items():
        if settings['vary']:
            val = res.params[name].value
            err = res.params[name].stderr
            print(f"{name} = {val:.2e} ± {err:.2e}")

    plt.scatter(x_data, y_data)
    plt.plot(x_data, res.best_fit, color='red', label='fitted curve')
    plt.legend()
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.title(re.sub(r'\.(dat|csv)$', '', os.path.basename(path_to_data)))
    plt.show()

    return res

def thermal_lens_test():

    params = {
        "tc": {"value": tc_def(53.5*10**-6, 0.598/(997048*4.18)), "vary": True},
        "m": {"value": 37.29, "vary": False},
        "V": {"value": 5.82, "vary": False},
        "th": {"value": 0.09, "vary": True}
    }

    datapath = r"dummy-thermal_lens-transient.dat"

    fitter(thermal_lens_light_intensity_shen_model_def, params, datapath, 't', 'Normalized light intensity')

def beam_profile_test():

    params = {
        "z0": {"value": 0., "vary": False},
        "zc": {"value": zc_def(42*10**-6, 532*10**-9), "vary": True},
        "r0": {"value": 42*10**-6, "vary": True}
    }

    datapath = r"dummy-beam-profile.dat"

    fitter(gaussian_laser_beam_profile_def, params, datapath, 'z', 'Beam radius')

if __name__ == '__main__':

    os.system('cls')

    thermal_lens_test()
    beam_profile_test()
