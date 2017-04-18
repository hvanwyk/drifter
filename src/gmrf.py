'''
Created on Feb 8, 2017

@author: hans-werner
'''
from finite_element import System, QuadFE
from mesh import Mesh
import scipy.sparse as sp
from sksparse.cholmod import cholesky  # @UnresolvedImport
from scipy.special import kv, gamma
import numpy as np

# =============================================================================
# Covariance Functions
# =============================================================================
"""
Commonly used covariance functions

For each function, we assume the input is given by two d-dimensional
vectors of length n. 
"""
def constant_cov(x,y,c):
    """
    Constant covariance kernel
    
        C(x,y) = c
    
    """
    return c*np.ones(x.shape[0])
    

def linear_cov(x,y):
    """
    Linear covariance
    
        C(x,y) = <x,y>  (Euclidean inner product)
     
    """
    return np.sum(x*y, axis=1)

    
def sqr_exponential_cov(x,y,l):
    """
    Squared exponential covariance function
    
        C(x,y) = exp(-|x-y|^2/(2l^2))
    
    """
    d = distance(x,y)
    return np.exp(-d**2/(2*l**2))

    
def ornstein_uhlenbeck_cov(x,y,l):
    """
    Ornstein-Uhlenbeck covariance function
    
        C(x,y) = exp(-|x-y|/l)
        
    """
    d = distance(x,y)
    return np.exp(-d/l)

    
def matern_cov(x,y,sgm,nu,l):
    """
    Matern covariance function
    """
    d = distance(x,y)
    K = sgm**2*2**(1-nu)/gamma(nu)*(np.sqrt(2*nu)*d/l)**nu*\
        kv(nu,np.sqrt(2*nu)*d/l)
    #
    # Modified Bessel function undefined at d=0, covariance should be 1
    #
    K[np.isnan(K)] = 1
    return K
    
    
def rational_cov(x,y,a):
    """
    Rational covariance
    
        C(x,y) = 1/(1 + |x-y|^2)^a
         
    """
    d = distance(x,y)
    return (1/(1+d**2))**a


def distance(x,y):
    """
    Compute the Euclidean distance vector between rows in x and rows in y
    """
    #
    # Check wether x and y have the same dimensions
    # 
    assert x.shape == y.shape, 'Vectors x and y have incompatible shapes.'
    return np.sqrt(np.sum((x-y)**2,axis=1)) 
        
     
         
# =============================================================================
# Gaussian Markov Random Field Class
# =============================================================================
class Gmrf(object):
    """
    Gaussian Markov Random Field
    """
 
    def __init__(self, mu=None, precision=None, covariance=None, 
                 mesh=None, element=None, discretization=None):
        """
        Constructor
        
        Inputs:
        
        
            mu: double, (n,) vector of expectations (default=0)
            
            precision: double, (n,n) sparse/full precision matrix
            
            covariance: double, (n,n) sparse/full covariance matrix
            
            mesh: Mesh, quadtree mesh
            
            element: QuadFE, finite element
            
            discretization: str, 'finite_elements' (default), or
                'finite_differences'.
                
            
        Attributes:
        
            __Q: double, precision matrix
            
            __Sigma: double, covariance matrix
            
            __mu: double, expected value
            
            __b: double, Q\mu (useful for sampling)
            
            __f_prec: double, lower triangular left cholesky factor of precision
                If Q is sparse, then use CHOLMOD.
                
            __f_cov: double, lower triangular left cholesky factor of covariance
                If Sigma is sparse, we use CHOLMOD.
                
            mesh: Mesh, Quadtree mesh
            
            element: QuadFE, finite element    
            
            discretization: str, 'finite_elements', or 'finite_differences' 
            
        """   
        n = None
        #
        # Need at least one
        #
        if precision is None and covariance is None:
            raise Exception('Specify precision or covariance (or both).')  
        #
        # Precision matrix
        # 
        self.__Q = precision
        if precision is not None:
            n = precision.shape[0]    
            if sp.isspmatrix(precision):
                self.__f_prec = cholesky(precision.tocsc())
            else:
                self.__f_prec = np.linalg.cholesky(precision)        
        #
        # Covariance matrix
        # 
        self.__Sigma = covariance
        if covariance is not None:
            n = covariance.shape[0]
            if sp.isspmatrix(covariance):
                self.__f_cov = cholesky(covariance.tocsc())
            else:
                # Most likely
                self.__f_cov  = np.linalg.cholesky(covariance)    
        #
        # Check compatibility
        # 
        if covariance is not None and precision is not None:
            n_cov = covariance.shape[0]
            n_prc = precision.shape[0]
            assert n_prc == n_cov, \
                'Incompatibly shaped precision and covariance.'
            isI = precision.dot(covariance)
            if sp.isspmatrix(isI):
                isI = isI.toarray()
                assert np.allclose(isI, np.eye(n_prc),rtol=1e-10),\
               'Covariance and precision are not inverses.' 
        #
        # Mean
        # 
        if mu is not None:
            assert len(mu) == n, 'Mean incompatible with precision/covariance.'
        else: 
            mu = np.zeros(n)
        self.__mu = mu
        # 
        # b = Q\mu
        # 
        if not np.allclose(mu, np.zeros(n), 1e-10):
            # mu is not zero
            b = self.Q_solve(mu)
        else:
            b = np.zeros(n)
        self.__b = b
        #
        # Store
        # 
        self.__n = n    
        #
        # Store mesh and elements if available
        #
        if mesh is not None:
            self.mesh = mesh
        if element is not None:
            self.element = element
        
    @classmethod
    def from_covariance_kernel(cls, kfn, mesh, element=None, 
                               discretization='finite_elements'):
        """
        Initialize Gmrf from covariance function
        """ 
        pass
    
    
    @classmethod
    def from_matern_pde(cls, alpha, kappa, mesh, element=None, tau=None):
        """
        Initialize finite element Gmrf from matern PDE
        
        Inputs: 
        
            alpha: double >0, smoothness parameter
            
            kappa: double >0, regularization parameter
            
            mesh: Mesh, computational mesh 
            
            *element: QuadFE, finite element (optional)
            
            *tau: double, matrix-valued function representing the structure
                tensor S = [uxx uxy; uxy uyy].
        """
        if element is not None: 
            discretization = 'finite_elements'
        else:
            discretization = 'finite_differences'
            
        pass
    
    
    def Q(self):
        """
        Return the precision matrix
        """
        return self.__Q
    
    
    def Sigma(self):
        """
        Return the covariance matrix
        """
        return self.__Sigma
        
    
    def L(self, b=None, mode='precision'):
        """
        Return lower triangular Cholesky factor L or compute L*b
        
            Inputs: 
            
                b: double, compatible vector
                
                mode: string, Specify the matrix for which to return the 
                    Cholesky factor: 'precision' (default) or 'covariance'
                    
                    
            Output:
            
                Lprec/Lcov: double, (sparse) lower triangular left Cholesky 
                    factor (if no b is specified) 
                    
                    or 
                
                y = Lprec*b / y = Lcov*b: double, vector.
                
        """
        #
        # Parse mode
        #
        assert self.mode_supported(mode), \
            'Mode "'+mode+'" not supported by this random field.' 
        if mode == 'precision':
            #
            # Precision Matrix
            # 
            assert self.__f_prec is not None, \
                'Precision matrix not specified.'
            if sp.isspmatrix(self.__Q):
                #
                # Sparse matrix, use CHOLMOD
                #  
                P = self.__f_prec.P()
                L = self.__f_prec.L()[P,:][:,P]
            else:
                #
                # Cholesky Factor stored as full matrix
                # 
                L = self.__f_prec

        elif mode == 'covariance':
            #
            # Covariance Matrix
            # 
            assert self.__f_cov is not None, \
                'Covariance matrix not specified.'
            if sp.isspmatrix(self.__Sigma):
                #
                # Sparse Covariance matrix, use CHOLMOD
                # 
                P = self.__f_cov.P()
                L = self.__f_cov.L()[P,:][:,P]
            else:
                #
                # Cholesky Factor stored as full matrix
                # 
                L = self.__f_cov
        else:
            raise Exception('Mode not recognized. Use either' + \
                            '"precision" or "covariance".')
        #
        # Parse b   
        # 
        if b is None:
            return L 
        else: 
            return L.dot(b) 
        
        
    def mu(self,n_copies=None):
        """
        Return the mean of the random vector
        
        Inputs:
        
            n_copies: int, number of copies of the mean
            
        Output: 
        
            mu: (n,n_copies) mean
        """
        if n_copies is not None:
            assert type(n_copies) is np.int, \
                'Number of copies should be an integer.'
            return np.tile(self.__mu, (n_copies,1)).transpose()
        else:
            return self.__mu
        
    
    def b(self):
        """
        Return Q\mu
        """
        return self.__b
    
    
    def n(self):
        """
        Return the dimension of the random vector 
        """
        return self.__n
    
    
    def Q_solve(self, b):
        """
        Return the solution x of Qx = b by successively solving 
        Ly = b for y and hence L^T x = y for x.
        
        """
        if sp.isspmatrix(self.__Q):
            return self.__f_prec(b)
        else:
            y = np.linalg.solve(self.__f_prec, b)
            return np.linalg.solve(self.__f_prec.transpose(),y)
    
    
    
    def L_solve(self, b, mode='precision'):
        """
        Return the solution x of Lx = b
        
        Note: CHOLMOD's solve_L assumes a factorization of the type LDL' = PQP'
        """
        assert self.mode_supported(mode),\
            'Mode "'+ mode + '" not supported for this random field.'
        if mode == 'precision':
            if sp.isspmatrix(self.__Q):
                # Sparse
                D = self.__f_prec.D()[self.__f_prec.P()] 
                return self.__f_prec.solve_L(b)/np.sqrt(D)
            else: 
                # Full
                return np.linalg.solve(self.__f_prec,b)
        elif mode == 'covariance':
            if sp.isspmatrix(self.__Sigma):
                # Sparse
                D = self.__f_cov.D()[self.__f_cov.P()]
                return self.__f_cov.solve_L(b)/np.sqrt(D)
            else:
                # Full
                return np.linalg.solve(self.__f_cov,b)
    
    
    def Lt_solve(self, b, mode='precision'):
        """
        Return the solution x, of L^T x = b
        
        Note: CHOLMOD's solve_Lt assumes a factorization of the type 
            LDL' = PQP'. To adjust, we solve P^T*sqrt(D)*L = b
        """
        assert self.mode_supported(mode), \
            'Mode "'+ mode + '" not supported for this random field.'
        if mode == 'precision':
            #
            # Precision matrix
            # 
            if sp.isspmatrix(self.__Q):
                # Sparse
                D = self.__f_prec.D()[self.__f_prec.P()]
                D1 = self.__f_prec.D()[self.__f_prec.P(),np.newaxis]
                print('D = {0}'.format(D))
                print('D1 = {0}'.format(D1))
                return self.__f_prec.solve_Lt(b/np.sqrt(D))
            else:
                # Full
                return np.linalg.solve(self.__f_prec.transpose(),b)
        elif mode == 'covariance':
            #
            # Covariance matrix
            # 
            if sp.isspmatrix(self.__Sigma):
                # Sparse
                D = self.__f_cov.D()[self.__f_cov.P()]
                return self.__f_cov.solve_Lt(b/np.sqrt(D))
            else:
                # Full
                return np.linalg.solve(self.__f_cov.transpose(),b)
        else:
            raise Exception('For mode, use "precision" or "covariance".')
    
    
    def kl_expansion(self, k=None):
        """
        Inputs:
        
        Outputs:
        
        """
        pass
    
    
    def sample(self, n_samples=None, z=None, mode='precision'):
        """
        Generate sample realizations from Gaussian random field.
        
        Inputs:
        
            n_samples: int, number of samples to generate
            
            z: (n,n_samples) random vector ~N(0,I).
            
            
        Outputs:
        
            x: (n,n_samples), samples paths of random field
        """
        assert self.mode_supported(mode), \
            'Mode "'+ mode + '" not supported for this random field.'
        #
        # Preprocess z   
        # 
        if z is None:
            assert n_samples is not None, \
                'Specify either random array or sample size.'
            z = np.random.normal(size=(self.n(), n_samples))
        else:
            assert n_samples is None or n_samples == z.shape[1], \
                'Sample size incompatible with given random array.'
            n_samples =  z.shape[1]
        #if n_samples == 1:
        #    z = z.ravel()
        #    print('z shape = {0}'.format(z.shape))
        
        if mode in ['precision','canonical']:
            v = self.Lt_solve(z, mode='precision')
            print("mu repeated ={0}".format(self.mu(n_samples)))
            x = v + self.mu(n_samples)
            print('add mu={0}'.format(x))
            return x
        elif mode == 'covariance':
            v = self.L(z,mode=mode)
            return v + self.mu(n_samples)
        
    
    def mode_supported(self, mode):
        """
        Determine whether enough information
        """
        if mode == 'precision':
            return self.__Q is not None
        elif mode == 'covariance':
            return self.__Sigma is not None
        elif mode == 'canonical':
            return self.__Q is not None
        else:
            raise Exception('For modes, use "precision", ' + \
                            '"covariance", or "canonical".')
            
    
    def condition(self, constraint=None, constraint_type='pointwise'):
        """
        
        Inputs:
        
            constraint: tuple, parameters specifying the constraint, determined
                by the constraint type:
                
                'pointwise': 
                
                'hard':
                
                'soft':
        
            constraint_type: str, 'pointwise' (default), 'hard', 'soft'.
        """
        pass
    
    
    def matern_precision(self, mesh, element, alpha, kappa, tau=None):
        """
        Return the precision matrix for the Matern random field defined on the 
        spatial mesh. The field X satisfies
        
            (k^2 - Delta)^{a/2} X = W
        
        Inputs: 
        
            mesh: Mesh, finite element mesh on which the field is defined
            
            element: QuadFE, finite element space of piecewise polynomials
            
            alpha: int, positive integer (doubles not yet implemented).
            
            kappa: double, positive regularization parameter.
            
            
        Outputs:
        
            Q: sparse matrix, in CSC format
            
        """
        system = System(mesh, element)
        
        #
        # Assemble (kappa * I + K)
        # 
        bf = [(kappa,'u','v'),(1,'ux','vx'),(1,'uy','vy')]
        G = system.assemble(bilinear_forms=bf)
        G = G.tocsr()
        
        #
        # Lumped mass matrix
        # 
        M = system.assemble(bilinear_forms=[(1,'u','v')]).tocsr()
        M_lumped_inv = sp.diags(1/np.array(M.sum(axis=1)).squeeze())
        
        
        #Ml = sp.diags(Ml)
        if np.mod(alpha,2) == 0:
            #
            # Even power alpha
            # 
            Q = G
            count = 1
        else:
            #
            # Odd power alpha
            # 
            Q = G.dot(M_lumped_inv.dot(G))
            count = 2
        while count < alpha:
            #
            # TODO: To keep Q symmetric positive definite, 
            #       perhaps compute cholesky earlier.
            # 
            Q = G.dot(M_lumped_inv.dot(Q.dot(M_lumped_inv.dot(G))))
            count += 2
        
        return Q