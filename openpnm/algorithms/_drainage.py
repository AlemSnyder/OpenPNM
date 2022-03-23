import numpy as np
from openpnm.algorithms import GenericAlgorithm
from openpnm._skgraph.simulations import bond_percolation
from openpnm._skgraph.simulations import find_connected_clusters
from openpnm._skgraph.simulations import find_trapped_clusters
from openpnm.topotools import remove_isolated_clusters, ispercolating
from openpnm.utils import logging, SettingsAttr, Docorator


__all__ = ['Drainage']


docstr = Docorator()
logger = logging.getLogger(__name__)


@docstr.get_sections(base='DrainageSettings',
                     sections=['Parameters'])
@docstr.dedent
class DrainageSettings:
    r"""
    Parameters
    ----------
    %(GenericAlgorithmSettings.parameters)s
    access_limited : bool
        If ``True`` then invading fluid must be connected to the specified
        inlets
    mode : str
        Controls whether pore or throat entry threshold values are used.
        Options are:

            ===========  =====================================================
            mode         meaning
            ===========  =====================================================
            'site'       the pore entry is considered
            'bond'       the throat values are considered.
            ===========  =====================================================

    pore_entry_threshold : str
        The dictionary key for the pore entry pressure array
    throat_entry_threshold : str
        The dictionary key for the pore entry pressure array
    pore_volume : str
        The dictionary key for the pore volume array
    throat_volume : str
        The dictionary key for the throat volume array

    """
    phase = ''
    throat_entry_threshold = 'throat.entry_pressure'
    pore_volume = 'pore.volume'
    throat_volume = 'throat.volume'


class Drainage(GenericAlgorithm):

    def __init__(self, phase, settings=None, **kwargs):
        self.settings = SettingsAttr(DrainageSettings, settings)
        super().__init__(settings=self.settings, **kwargs)
        self.settings['phase'] = phase.name
        self.reset()

    def reset(self):
        self['pore.inlets'] = False
        self['pore.outlets'] = False
        self['pore.invaded'] = False
        self['throat.invaded'] = False
        self['pore.residual'] = False
        self['throat.residual'] = False
        self['pore.trapped'] = False
        self['throat.trapped'] = False

    def set_inlets(self, pores, mode='add'):
        self['pore.inlets'][pores] = True

    def set_outlets(self, pores, mode='add'):
        self['pore.outlets'][pores] = True

    def set_residual(self, pores=None, throats=None, mode='add'):
        if pores is not None:
            self['pore.residual'][pores] = True
        if throats is not None:
            self['throat.residual'][throats] = True

    def set_trapped(self, pores=None, throats=None):
        if pores is not None:
            self['pore.trapped'][pores] = True
        if throats is not None:
            self['throat.trapped'][throats] = True

    def run(self, pressure):

        phase = self.project[self.settings.phase]
        Tinv = phase[self.settings.throat_entry_threshold] <= pressure
        # Update invaded locations with residual
        Tinv += self['throat.residual']
        s_labels, b_labels = bond_percolation(self.network.conns, Tinv)
        s_labels, b_labels = find_connected_clusters(b_labels, s_labels, self['pore.inlets'], asmask=False)
        # Add result to existing invaded locations
        self['pore.invaded'][s_labels >= 0] = True
        self['throat.invaded'][b_labels >= 0] = True
        if np.any(self['pore.outlets']):
            s, b = find_trapped_clusters(conns=self.network.conns,
                                         occupied_bonds=self['throat.invaded'],
                                         outlets=self['pore.outlets'])
            self['pore.trapped'][s >= 0] = True
            self['throat.trapped'][b >= 0] = True


if __name__ == "__main__":
    import openpnm as op
    pn = op.network.Cubic([40, 40, 1], spacing=1e-5)
    geo = op.geometry.SpheresAndCylinders(network=pn, pores=pn.Ps, throats=pn.Ts)
    nwp = op.phase.GenericPhase(network=pn)
    nwp['throat.surface_tension'] = 0.480
    nwp['throat.contact_angle'] = 180
    phys = op.physics.GenericPhysics(network=pn, phase=nwp, geometry=geo)
    phys.add_model(propname='throat.entry_pressure',
                   model=op.models.physics.capillary_pressure.washburn)

    pressure = 1e6
    drn = Drainage(network=pn, phase=nwp)
    drn.set_inlets(pores=pn.pores('left'))
    drn.set_outlets(pores=pn.pores('right'))
    drn.run(pressure=pressure)

    # %%
    ax = op.topotools.plot_coordinates(pn, pores=drn['pore.inlets'])
    ax = op.topotools.plot_coordinates(pn, pores=pn.pores('right'), c='black', ax=ax)
    ax = op.topotools.plot_connections(pn, throats=nwp['throat.entry_pressure'] <= pressure, c='grey', ax=ax)
    ax = op.topotools.plot_connections(pn, throats=drn['throat.invaded'], ax=ax)
    ax = op.topotools.plot_coordinates(pn, pores=drn['pore.invaded'], ax=ax)
    ax = op.topotools.plot_coordinates(pn, pores=drn['pore.outlets'], ax=ax)
    ax = op.topotools.plot_coordinates(pn, pores=drn['pore.trapped'], c='green', ax=ax)
    # ax = op.topotools.plot_coordinates(pn, pores=~drn['pore.invaded'], c='grey', ax=ax)


    # %%
    # ax = op.topotools.plot_connections(pn, throats=drn['throat.invaded'], c='grey', ax=ax)
    # ax = op.topotools.plot_coordinates(pn, pores=drn['pore.invaded'], c='blue', ax=ax)























