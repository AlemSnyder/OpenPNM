import pytest
import numpy as np
from numpy.testing import assert_allclose
from openpnm._skgraph import tools
from openpnm._skgraph.generators import cubic


class SKGRToolsTest:
    def setup_class(self):
        pass

    def teardown_class(self):
        pass

    def test_dict_to_am_undirected(self):
        g = cubic(shape=[3, 2, 1])
        am = tools.dict_to_am(g)
        # Make sure am is symmetrical but edges have the same order
        assert np.all(am.row == np.hstack((g['edge.conns'][:, 0], g['edge.conns'][:, 1])))
        assert np.all(am.col == np.hstack((g['edge.conns'][:, 1], g['edge.conns'][:, 0])))
        assert_allclose(np.linalg.norm(am.todense()), 3.7416573867739413)

    def test_dict_to_am_directed(self):
        g = cubic(shape=[3, 2, 1])
        g['edge.conns'][1, :] = [1, 0]
        am = tools.dict_to_am(g)
        # Make sure edges in am are untouched
        assert np.all(am.row == g['edge.conns'][:, 0])
        assert np.all(am.col == g['edge.conns'][:, 1])
        assert_allclose(np.linalg.norm(am.todense()), 2.6457513110645907)

    def test_dict_to_am_undirected_w_weights(self):
        g = cubic(shape=[3, 2, 1])
        Ts = np.arange(g['edge.conns'].shape[0])
        am = tools.dict_to_am(g, weights=Ts)
        assert np.all(am.data == np.hstack((Ts, Ts)))

    def test_dict_to_am_directed_w_weights(self):
        g = cubic(shape=[3, 2, 1])
        g['edge.conns'][1, :] = [1, 0]
        Ts = np.arange(g['edge.conns'].shape[0])
        am = tools.dict_to_am(g, weights=Ts)
        assert np.all(am.data == Ts)

    def test_dict_to_am_w_dupes(self):
        g = cubic(shape=[3, 2, 1])
        g['edge.conns'][1, :] = [0, 1]
        with pytest.raises(Exception):
            _ = tools.dict_to_am(g)
        g['edge.conns'][1, :] = [1, 0]
        with pytest.raises(Exception):
            _ = tools.dict_to_am(g)

    def test_dict_to_am_already_symmetrical(self):
        g = cubic(shape=[3, 2, 1])
        conns = g['edge.conns']
        g['edge.conns'] = np.vstack((conns, np.fliplr(conns)))
        with pytest.raises(Exception):
            _ = tools.dict_to_am(g)

    def test_cart2cyl_and_back(self):
        x, y, z = np.random.rand(10, 3).T
        r, q, z1 = tools.cart2cyl(x, y, z)
        x2, y2, z2 = tools.cyl2cart(r, q, z1)
        assert_allclose(x, x2)
        assert_allclose(y, y2)
        assert_allclose(z, z2)

    def test_cart2cyl_polar(self):
        x, y = np.random.rand(10, 2).T
        r, q, z = tools.cart2cyl(x, y)
        assert z.sum() == 0
        x, y, z = tools.cyl2cart(r, q)
        assert z.sum() == 0

    def test_cart2sph_and_back(self):
        x, y, z = np.random.rand(10, 3).T
        r, q, phi = tools.cart2sph(x, y, z)
        x2, y2, z2 = tools.sph2cart(r, q, phi)
        assert_allclose(x, x2)
        assert_allclose(y, y2)
        assert_allclose(z, z2)


if __name__ == '__main__':
    t = SKGRToolsTest()
    t.setup_class()
    self = t
    for item in t.__dir__():
        if item.startswith('test'):
            print(f'Running test: {item}')
            t.__getattribute__(item)()
