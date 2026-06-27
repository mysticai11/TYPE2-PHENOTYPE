import pytest
import torch
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src_code.counterfactual.geodesic import RiemannianManifold, compute_geodesic

class MockDecoder(torch.nn.Module):
    def forward(self, z):
        # f(z1, z2) = [z1, z2, z1^2 + z2^2]
        out = torch.zeros(z.shape[0], 3)
        out[:, 0] = z[:, 0]
        out[:, 1] = z[:, 1]
        out[:, 2] = z[:, 0]**2 + z[:, 1]**2
        return out

def test_riemannian_metric():
    decoder = MockDecoder()
    manifold = RiemannianManifold(decoder, input_dim=2, output_dim=3)
    
    # At z = (0,0), J = [[1, 0], [0, 1], [0, 0]]. G = J^T J = [[1, 0], [0, 1]]
    z0 = np.array([0.0, 0.0])
    G = manifold.metric(z0)
    np.testing.assert_array_almost_equal(G, np.eye(2), decimal=4)
    
    # At z = (1, 1), J = [[1, 0], [0, 1], [2, 2]]. G = [[5, 4], [4, 5]]
    z1 = np.array([1.0, 1.0])
    G1 = manifold.metric(z1)
    expected_G1 = np.array([[5.0, 4.0], [4.0, 5.0]])
    np.testing.assert_array_almost_equal(G1, expected_G1, decimal=4)

def test_christoffel_symbols():
    decoder = MockDecoder()
    manifold = RiemannianManifold(decoder, input_dim=2, output_dim=3)
    
    # At z = (0,0), metric is constant (identity), so derivatives of G are 0 -> Christoffel symbols should be 0
    z0 = np.array([0.0, 0.0])
    Gamma = manifold.christoffel_symbols(z0)
    np.testing.assert_array_almost_equal(Gamma, np.zeros((2, 2, 2)), decimal=4)

class LinearMockDecoder(torch.nn.Module):
    def forward(self, z):
        out = torch.zeros(z.shape[0], 3)
        out[:, 0] = z[:, 0]
        out[:, 1] = z[:, 1]
        return out

def test_compute_geodesic():
    decoder = LinearMockDecoder()
    
    # Path from (1, 1) to (0, 0)
    z_start = np.array([1.0, 1.0])
    z_end = np.array([0.0, 0.0])
    
    geo_path = compute_geodesic(decoder, z_start, z_end, n_steps=10)
    
    assert geo_path.shape == (10, 2)
    
    euc_dist = np.linalg.norm(z_start - z_end)
    diffs = np.diff(geo_path, axis=0)
    geo_dist = np.sum(np.linalg.norm(diffs, axis=1))
    
    # On flat manifold, geodesic distance should equal Euclidean distance
    np.testing.assert_allclose(geo_dist, euc_dist, rtol=1e-4)
    np.testing.assert_array_almost_equal(geo_path[0], z_start)
    np.testing.assert_array_almost_equal(geo_path[-1], z_end)
