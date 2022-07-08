from openpnm.utils import Docorator
import numpy as np
import scipy.constants as const


docstr = Docorator()


__all__ = [
    "fuller",
    "tyn_calus",
    "chapman_enskog",
    "wilke_fuller_mixture",
    "fuller_mixture",
    "gas_mixture_LJ_collision_integral",
    "gas_mixture_LJ_epsilon",
    "gas_mixture_LJ_sigma",
    "gas_mixture_diffusivity",
]


@docstr.get_sections(base='models.phase.diffusivity', sections=['Returns'])
@docstr.dedent
def fuller(target, MA, MB, vA, vB, temperature='pore.temperature',
           pressure='pore.pressure'):
    r"""
    Uses Fuller model to estimate diffusion coefficient for gases from first
    principles at conditions of interest

    Parameters
    ----------
    %(models.target.parameters)s
    MA : float
        Molecular weight of component A [kg/mol]
    MB : float
        Molecular weight of component B [kg/mol]
    vA:  float
        Sum of atomic diffusion volumes for component A
    vB:  float, array_like
        Sum of atomic diffusion volumes for component B
    %(models.phase.T)s
    %(models.phase.P)s

    Returns
    -------
    diffusivities : ndarray
        A numpy ndarray containing diffusion coefficient values [m2/s].
    """
    T = target[temperature]
    P = target[pressure]
    MAB = 2*(1.0/MA+1.0/MB)**(-1)
    MAB = MAB*1e3
    P = P*1e-5
    value = 0.00143*T**1.75/(P*(MAB**0.5)*(vA**(1./3)+vB**(1./3))**2)*1e-4
    return value


@docstr.dedent
def tyn_calus(target, VA, VB, sigma_A, sigma_B, temperature='pore.temperature',
              viscosity='pore.viscosity'):
    r"""
    Uses Tyn-Calus model to estimate diffusion coefficient in a dilute liquid
    solution of A in B from first principles at conditions of interest

    Parameters
    ----------
    %(models.target.parameters)s
    VA : float
        Molar volume of component A at boiling temperature (m3/mol)
    VB : float
        Molar volume of component B at boiling temperature (m3/mol)
    sigmaA : float
        Surface tension of component A at boiling temperature (N/m)
    sigmaB : float
        Surface tension of component B at boiling temperature (N/m)
    %(models.phase.T)s
    %(models.phase.P)s

    Returns
    -------
    %(models.phase.diffusivity.returns)s
    """
    T = target[temperature]
    mu = target[viscosity]
    A = 8.93e-8*(VB*1e6)**0.267/(VA*1e6)**0.433*T
    B = (sigma_B/sigma_A)**0.15/(mu*1e3)
    value = A*B
    return value


@docstr.dedent
def chapman_enskog(target, MA, MB, sigma_AB, omega_AB,
                   temperature='pore.temperature',
                   pressure='pore.pressure'):
    r"""
    Calculate gas phase diffusion coefficient using Chapman-Enskog equation.

    Parameters
    ----------
    %(models.target.parameters)s
    MA, MB : scalar
        The molecular mass of species A and B in units of kg/mol
    sigma_AB : scalar
        The collision diameter in units of Angstroms
    omega_AB : scalar
        The collision integral
    %(models.phase.T)s
    %(models.phase.P)s

    Returns
    -------
    %(models.phase.diffusivity.returns)s
    """
    T = target[temperature]
    P = target[pressure]
    DAB = 1.858e-3*(T**3*(0.001/MA + 0.001/MB))**0.5/(P*101325*sigma_AB**2*omega_AB)
    return DAB


def gas_mixture_LJ_collision_integral(
    target,
    temperature='pore.temperature',
    epsilon='pore.LJ_epsilon',
):
    r"""
    Calculates the collision integral for a single species

    Parameters
    ----------
    %(models.target.parameters)s
    %(models.phase.T)s
    """
    T = target[temperature]
    eAB = target[epsilon]
    A = 1.06036
    B = 0.15610
    C = 0.19300
    D = 0.47635
    E = 1.03587
    F = 1.52996
    G = 1.76474
    H = 3.89411
    Ts = const.Boltzmann*T/eAB
    Omega = A/Ts**B + C/np.exp(D*Ts) + E/np.exp(F*Ts) + G/np.exp(H*Ts)
    return Omega


def gas_mixture_LJ_epsilon(target):
    r"""
    Calculates the effective molecular diameter for a binary mixture
    """
    es = [c['param.lennard_jones_epsilon'] for c in target.components.values()]
    assert len(es) == 2
    eAB = np.sqrt(np.prod(es))
    return eAB


def gas_mixture_LJ_sigma(target):
    r"""
    Calculates the effective collision integral for a binary mixture
    """
    ss = [c['param.lennard_jones_sigma'] for c in target.components.values()]
    assert len(ss) == 2
    sAB = np.mean(ss)
    return sAB


def gas_mixture_diffusivity(
    target,
    temperature='pore.temperature',
    pressure='pore.pressure',
    sigma='pore.LJ_sigma',
    omega='pore.LJ_omega',
):
    r"""
    Estimates the diffusivity of A in binary mixture using the Lennard-Jones

    Parameters
    ----------
    %(models.target.parameters)s
    %(models.phase.T)s
    %(models.phase.P)s
    sigma : str
        Dictionary key pointing to the Lennard-Jones molecular diameter values
    omega : str
        Dictionary key pointing to the Lennard-Jones collision integral values
    """
    MW = np.array([c['param.molecular_weight'] for c in target.components.values()])
    assert len(MW) == 2
    MWAB = 2/np.sum(1/np.array(MW*1000))
    T = target[temperature]
    P = target[pressure] / 101325  # convert to bar
    sAB = target[sigma]
    Omega = target[omega]
    DAB = 0.00266 * (T**1.5) / (P * MWAB**0.5 * sAB**2 * Omega) * 1e-4
    return DAB


def fuller_mixture(target,
                   molecular_weight='param.molecular_weight',
                   molar_diffusion_volume='param.molar_diffusion_volume',
                   temperature='pore.temperature',
                   pressure='pore.pressure'):
    r"""
    Estimates the diffusion coefficient of both species in a binary gas
    mixture using the Fuller correlation

    Parameters
    ----------
    %(models.target.parameters)s
    molecular_weight : string
        Dictionary key containing the molecular weight of each species.  The
        default is 'pore.molecular_weight'
    molar_diffusion_volume : string
        Dictionary key containing the molar diffusion volume of each species.
        This is used by the Fuller correlation.  The default is
        'pore.molar_diffusion_volume'
    %(models.phase.T)s
    %(models.phase.P)s

    Returns
    -------
    Dij : dict containing ND-arrys
        The dict contains one array for each component, containing the
        diffusion coefficient of that component at each location.
    """
    species_A, species_B = target.components.values()
    T = target[temperature]
    P = target[pressure]
    MA = species_A[molecular_weight]
    MB = species_B[molecular_weight]
    vA = species_A[molar_diffusion_volume]
    vB = species_B[molar_diffusion_volume]
    MAB = 1e3*2*(1.0/MA + 1.0/MB)**(-1)
    P = P/101325
    value = 0.00143*T**1.75/(P*(MAB**0.5)*(vA**(1./3) + vB**(1./3))**2)*1e-4
    return value


@docstr.dedent
def wilke_fuller_mixture(
        target,
        molecular_weight='pore.molecular_weight',
        molar_diffusion_volume='pore.molar_diffusion_volume',
        temperature='pore.temperature',
        pressure='pore.pressure'):
    r"""
    Estimates the diffusion coeffient of each species in a gas mixture

    Uses the Fuller equation to estimate binary diffusivity between pairs,
    then uses the correction of Fairbanks and Wilke [1] to account for the
    composition of the gas mixture.

    Parameters
    ----------
    %(models.target.parameters)s
    molecular_weight : str
        Dictionary key containing the molecular weight of each species.  The
        default is 'pore.molecular_weight'
    molar_diffusion_volume : str
        Dictionary key containing the molar diffusion volume of each species.
        This is used by the Fuller correlation.  The default is
        'pore.molar_diffusion_volume'
    %(models.phase.T)s
    %(models.phase.P)s

    Returns
    -------
    Dij : dict containing ND-arrys
        The dict contains one array for each component, containing the
        diffusion coefficient of that component at each location.

    Reference
    ---------
    [1] Fairbanks DF and CR Wilke, Diffusion Coefficients in Multicomponent
    Gas Mixtures. Industrial & Engineering Chemistry, 42(3), p471–475 (1950).
    `DOI: 10.1021/ie50483a022 <http://doi.org/10.1021/ie50483a022>`_
    """

    class MixDict(dict):
        r"""
        This utility dict is used to create a temporary mixture object containing
        only two components of a mixture that has several.  This is necessary for
        use of the fuller model for calculating binary diffusivities.
        """

        def __init__(self, target, components):
            super().__init__(target)
            self.components = {}
            for item in components:
                self.components.update({item.name: item})

    comps = list(target.components.values())
    values = {}
    for i in range(len(comps)):
        A = comps[i]
        denom = 0.0
        for j in range(len(comps)):
            if i != j:
                B = comps[j]
                temp = MixDict(target=target, components=(A, B))
                D = fuller_mixture(target=temp,
                                   molecular_weight=molecular_weight,
                                   molar_diffusion_volume=molar_diffusion_volume,
                                   temperature=temperature,
                                   pressure=pressure)
                yB = target['pore.mole_fraction.' + B.name]
                denom += yB/D
        yA = target['pore.mole_fraction.' + A.name]
        values[A.name] = (1 - yA)/denom
    return values
