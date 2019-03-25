from gmrf import CovKernel
from gmrf import Covariance
from mesh import QuadMesh
from mesh import Mesh1D
from fem import QuadFE
from fem import DofHandler
from function import Nodal
from plot import Plot
import matplotlib.pyplot as plt

import numpy as np
from scipy import linalg as la

import unittest

class TestCovariance(unittest.TestCase):
    """
    Test class for covariance assembly
    """
    def test_constructor(self):
        pass
    
    
    def test_assembly(self):
        for mesh in [Mesh1D(resolution=(100,)), QuadMesh(resolution=(20,20))]:
            
            dim = mesh.dim()
            
            element = QuadFE(dim, 'DQ0')
            
            dofhandler = DofHandler(mesh, element)
            cov_kernel = CovKernel('gaussian', {'sgm': 1, 'l': 0.3, 'M': None}, dim)
            
            covariance = Covariance(cov_kernel, dofhandler, method='projection')
            M = covariance.mass()
            C = covariance.covariance_matrix()
            
            # Solve the generalized svd
            U, s, Vh = la.svd(la.solve(M.toarray(),C.toarray()))
            
            n = U.shape[0]
            n_sample = 1
            Z = np.random.normal(size=(n,n_sample))
            
            Y = U.dot(np.diag(np.sqrt(s)).dot(Z))
            
            y = Nodal(data=Y, dofhandler=dofhandler, dim=dim)
            print(Y.shape)
            plot = Plot()
            
            if dim==1:
                plot.line(y)
            elif dim==2:
                plot.wire(y)