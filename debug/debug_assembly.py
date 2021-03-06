import numpy as np
from mesh import Mesh
from finite_element import DofHandler, GaussRule, QuadFE
import matplotlib.pyplot as plt
import scipy.sparse as sp
# -------------------
# Helper functions
# -------------------


"""
Test solution of simple Dirichlet problem.

TODO: Plot Nodal Functions
TODO: Impose Boundary Conditions
TODO: Impose Hanging Node Restrictions
"""
#ue = lambda x,y: np.sin(np.pi*x)*(1.+np.cos(np.pi*y))
#fe = lambda x,y: np.pi**2*np.sin(np.pi*x)*(1.+2*np.cos(np.pi*y))
ue = lambda x,y: np.sin(np.pi*x)*np.sin(np.pi*y)
fe = lambda x,y: np.pi**2*np.sin(np.pi*x)*np.sin(np.pi*y)

mesh = Mesh.newmesh(box=[0.,1.,0.,1.], grid_size=(30,30))
mesh.root_node().mark()
mesh.refine()
V = QuadFE(2,'Q1')
n_dofs = V.n_dofs()
dh = DofHandler(mesh,V)
dh.distribute_dofs()
n_nodes = dh.n_dofs()
# 
# Quadrature Rule
# 
n_quad = 9
rule = GaussRule(n_quad,V)
r = rule.nodes()
w = rule.weights()

#
# Evaluate Shape Functions on Reference Domain
#
phi_ref = np.empty((n_quad,n_dofs))
phix_ref = np.empty((n_quad,n_dofs))
phiy_ref = np.empty((n_quad,n_dofs))
for i in range(n_dofs):
    phi_ref[:,i] = V.phi(i,r)
    phix_ref[:,i] = V.dphi(i,r,0)
    phiy_ref[:,i] = V.dphi(i,r,1)
x_ref = V.reference_nodes()
#
# Initialize system matrices 
# 
rows = []
cols = []
a_vals = []
ax_vals = []
f_rhs = np.empty(n_nodes,)
u_vec = np.empty(n_nodes,)
for node in mesh.root_node().find_leaves():
    #
    # Loop over mesh nodes
    # 
    node_dofs = dh.get_global_dofs(node)
    quadcell = node.quadcell()
    #
    # Local system matrices
    # 
    r_phys = rule.map(quadcell, r)
    x_phys = rule.map(quadcell, x_ref)
    w_phys = np.array(w)*rule.jacobian(quadcell)
    A_loc = np.dot(phi_ref.T,np.dot(np.diag(w_phys),phi_ref))
    Ax_loc = np.dot(phix_ref.T,np.dot(np.diag(w_phys),phix_ref))
    Ay_loc = np.dot(phiy_ref.T,np.dot(np.diag(w_phys),phiy_ref))
    f_loc = fe(r_phys[:,0],r_phys[:,1])
    
    for i in range(n_dofs):
        u_vec[node_dofs] = ue(x_phys[:,0],x_phys[:,1])
        f_rhs[node_dofs[i]] = np.sum(f_loc*phi_ref[:,i]*w_phys)
        for j in range(n_dofs):
            rows.append(node_dofs[i])
            cols.append(node_dofs[j])
            a_vals.append(A_loc[i,j])
            ax_vals.append(Ax_loc[i,j]+Ay_loc[i,j])
            
    A = sp.coo_matrix((a_vals,(rows,cols)))
    Ax = sp.coo_matrix((ax_vals,(rows,cols)))
 
Ax = Ax.tocsr()
f_app = Ax.dot(u_vec)
print(np.linalg.norm(np.abs(f_app-f_rhs)))
plt.spy(A,markersize=1)
plt.spy(Ax,markersize=.1)
plt.show()
Acheck_1 = 1/36.0*np.array([[4,2,2,1],[2,4,1,2],[2,1,4,2],[1,2,2,4]])
Acheck_2 = 1/36.0*np.array([[4,2,2,1,0,0],[2,8,1,4,2,1],[2,1,4,2,0,0],
                           [1,4,2,8,1,2],[0,2,0,1,4,2],[0,1,0,2,2,4]])
print(Acheck_2)
print(A.toarray())

"""
_,ax = plt.subplots()
mesh.plot_quadmesh(ax, set_axis=True, vertex_numbers=True)
plt.show()
"""