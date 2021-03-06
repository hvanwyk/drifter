import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import numbers

"""
Created on Jun 29, 2016
@author: hans-werner

"""
class Mesh(object):
    """
    Description: Mesh Class, consisting of a quadcell (background mesh), together with a tree, 
        from which a specific mesh instance can be constructed without deleting previous 
        mesh parameters.
    
    Attributes:
    
    Methods:
    """
    def __init__(self, quadcell=None, root_node=None):
        """
        Description: Constructor
        """
        if root_node.is_linked():
            Warning('Tree node is linked to a cell. Unlinking')    
        root_node.unlink()
        root_node.link(quadcell)
        self.__cell = quadcell
        self.__root_node = root_node
        self.__triangulated = False 
        self.__mesh_count = 0
        self.__dim = 2  # TODO: Change this in the case of 1D
        
    @classmethod 
    def copymesh(cls, mesh):
        """
        Copy existing mesh
        """
        quadcell = mesh.quadcell()
        root_node = mesh.root_node().copy()
        return cls(quadcell=quadcell, root_node=root_node)

        
    @classmethod
    def submesh(cls, mesh):
        """
        Construct new mesh from existing mesh 
        """
        quadcell = mesh.quadcell()
        root_node = mesh.root_node().copy()
        return cls(quadcell=quadcell, root_node=root_node) 
    
    
    @classmethod
    def newmesh(cls, box=[0.,1.,0.,1.], grid_size=None):
        """
        Construct new mesh from bounding box and initial grid
        """
        quadcell = QuadCell(box=box, grid_size=grid_size)
        root_node = Node(grid_size=grid_size)
        return cls(quadcell=quadcell, root_node=root_node)
    
     
    def box(self):
        """
        Return the dimensions of the rectangular domain
        """
        return self.root_node().quadcell().box()
    
    
    def dim(self):
        """
        Return the spatial dimension of the region
        """
        return self.__dim
    
            
    def grid_size(self):
        """
        Return grid size on coarsest level
        """
        return self.__cell.grid_size
    
    
    def depth(self):
        """
        Return the maximum refinement level
        """    
        return self.__root_node.tree_depth()
    
        
    def n_cells(self, flag=None):
        """
        Return the number of cells
        """
        if hasattr(self, '__n_quadcells'):
            return self.__n_quadcells
        else:
            self.__n_quadcells = len(self.__root_node.find_leaves(flag=flag))
            return self.__n_quadcells
    
            
    def root_node(self):
        """
        Return tree node used for mesh
        """
        return self.__root_node
     
        
    def boundary(self, entity, flag=None):
        """
        Returns a set of all boundary entities (vertices/edges)
        
        Input:
        
            entity: str, 'vertices', 'edges', or 'quadcells'
            
            flag: 
            
        TODO: Add support for tricells
        """
        boundary = set()
        print(entity)
        print(len(boundary))
        for node in self.root_node().find_leaves(flag=flag):
            cell = node.quadcell()
            for direction in ['W','E','S','N']:
                # 
                # Look in 4 direction
                # 
                if node.find_neighbor(direction) is None:
                    if entity=='quadcells':
                        boundary.add(cell)
                        break
                    
                    edge = cell.get_edges(direction)
                    if entity=='edges':
                        boundary.add(edge)
                        
                    if entity=='vertices':
                        for v in edge.vertices():
                            boundary.add(np.array(v.coordinate()))
            print(len(boundary))
        return boundary
                        

    def node_containing_points(self, x, flag=None):
        """
        Locate the node corresponding to the smallest cell that contains point
        x. If x has multiple points, return a list of nodes.
        
        Inputs:
        
            x: double, array of points
            
            flag: str, marker specifying subclass of nodes.
            
        Outputs: 
        
            nodes: Node, list of of Nodes
        """
        pass
    
        
        
    def unmark(self, nodes=False, quadcells=False, quadedges=False, quadvertices=False,
               tricells=False, triedges=False, trivertices=False, all_entities=False):
        """
        Unmark all nodes and/or quadcells, -edges, and -vertices 
        and/or tricells, -edges, and -vertices(recursively)
        
        TODO: This doesn't unmark specific flags
        """
        if all_entities:
            # 
            # Unmark everything
            # 
            nodes = True
            quadcells = True
            quadedges = True
            quadvertices = True
            tricells = True
            triedges = True
            trivertices = True
            
        node_list = self.root_node().traverse_tree()
        for node in node_list:
            if nodes:
                #
                # Unmark node
                #
                node.unmark(recursive=True)
            if quadcells:
                #
                # Unmark quad cell
                #
                node.quadcell().unmark()
            if quadedges:
                #
                # Unmark quad edges
                #
                for edge in node.quadcell().edges.values():
                    edge.unmark()
            if quadvertices:
                #
                # Unmark quad vertices
                #
                for vertex in node.quadcell().vertices.values():
                    vertex.unmark()
            if tricells or triedges or trivertices:
                if node.has_tricells():
                    for triangle in node.tricells():
                        if tricells:
                            #
                            # Unmark triangular cells
                            # 
                            triangle.unmark()
                        if triedges:
                            #
                            # Unmark triangle edges
                            # 
                            for edge in triangle.edges.values():
                                edge.unmark()
                        if trivertices:
                            #
                            # Unmark triangle vertices
                            #
                            for vertex in triangle.vertices.values():
                                vertex.unmark()
     
    def balance(self):
        """
        Balance the tree associated with the mesh
        """            
        self.root_node().balance()
        
        
    def is_balanced(self):
        """
        Returns true is the mesh's quadtree is balanced, false otherwise
        """ 
        return self.root_node().is_balanced()
        
    
    def is_triangulated(self):
        """
        Determine whether triangular mesh is present
        """
        return self.__triangulated
    
    
    def triangulate(self):
        """
        Generate a triangulation
        
        TODO: Incomplete 
        """
        node = self.root_node()
        if not(node.is_balanced()):
            self.balance()
            
        self.__triangulated = True
    
    
    def nodes(self, flag=None, nested=False):
        """
        Iterate over mesh nodes
        
        Inputs:
        
            flag: int/str, marker for the nodes to return
            
            nested: bool, nested traversal of tree (TRUE) 
                or only LEAF nodes (FALSE) 
                
                
        Outputs: 
            
            nodes: list, of (marked/unmarked) tree nodes.
        """
        return self.root_node().find_leaves(flag=flag, nested=nested)
         
    
    def iter_quadcells(self, flag=None, nested=False):
        """
        Iterate over active quad cells
        
        Output:
        
            quadcell_list, list of all active quadrilateral cells
        """ 
        quadcell_list = []
        node = self.root_node()
        for leaf in node.find_leaves(flag=flag, nested=nested):
            quadcell_list.append(leaf.quadcell())
        return quadcell_list
    
    
    def iter_quadedges(self, flag=None, nested=False):
        """
        Iterate over quadcell edges
        
        Output: 
        
            quadedge_list, list of all active quadcell edges
        """
        
        quadedge_list = []
        #
        # Unmark all edges
        # 
        self.unmark(quadedges=True)
        for cell in self.iter_quadcells(flag=flag, nested=nested):
            for edge_key in [('NW','SW'),('SE','NE'),('SW','SE'),('NE','NW')]:
                edge = cell.edges[edge_key]
                if not(edge.is_marked()):
                    #
                    # New edge: add it to the list
                    # 
                    quadedge_list.append(edge)
                    edge.mark()
        #
        # Unmark all edges again
        #             
        self.unmark(quadedges=True)
        return quadedge_list
        
                    
    def quadvertices(self, coordinate_array=True, flag=None, nested=False):
        """
        Iterate over quad cell vertices
        
        Inputs: 
        
            coordinate_array: bool, if true, return vertices as arrays 
            
            nested: bool, traverse tree depthwise
        
        Output: 
        
            quadvertex_list, list of all active quadcell vertices
        """
        quadvertex_list = []
        #
        # Unmark all vertices
        # 
        self.unmark(quadvertices=True)
        for cell in self.iter_quadcells(flag=flag, nested=nested):
            for direction in ['SW','SE','NW','NE']:
                vertex = cell.vertices[direction]
                if not(vertex.is_marked()):
                    #
                    # New vertex: add it to the list
                    #
                    quadvertex_list.append(vertex)
                    vertex.mark()
        self.unmark(quadvertices=True)
        if coordinate_array:
            return np.array([v.coordinate() for v in quadvertex_list])
        else:
            return quadvertex_list
    
    
    def iter_tricells(self):
        """
        Iterate over triangles
        
        Output: 
        
            tricell_list, list of all active triangular cells
        """
        tricell_list = []
        #
        # Unmark all triangle cells
        #
        self.unmark(tricells=True)
        for leaf in self.node().find_leaves():
            for triangle in leaf.tricells():
                tricell_list.append(triangle) 
        return tricell_list
    
    
    def iter_triedges(self):
        """
        Iterate over triangle edges
        
        Output: 
        
            triedge_list, list of all active edges
        """
        triedge_list = []
        self.unmark(triedges=True)
        for triangle in self.iter_tricells():
            for edge in triangle.edges():
                if not(edge.is_marked()):
                    triedge_list.append(edge)
                    edge.mark()
        return triedge_list
    
    
    def iter_trivertices(self):
        """
        Iterate over Triangle vertices
        
        Output: 
        
            trivertex_list, list of all active nodes
        """
        trivertex_list = []
        self.unmark(trivertices=True)
        for triangle in self.iter_tricells():
            for vertex in triangle.vertices():
                if not(vertex.is_marked()):
                    trivertex_list.append(vertex)
                    vertex.mark()
        return trivertex_list
    
        
    def refine(self, flag=None):
        """
        Refine mesh by splitting marked LEAF nodes
        """ 
        for leaf in self.root_node().find_leaves():
            if flag is None:
                # Non-selective refinement
                leaf.split()
            else:
                # Refine selectively according to flag
                if leaf.is_marked(flag=flag):
                    leaf.split()
                    #leaf.unmark(flag=flag)
    
    
    def coarsen(self):
        """
        Coarsen mesh by merging marked LEAF nodes
        
        TODO: FINISH
        """
        pass
    
    
    def record(self,flag=None):
        """
        Mark all mesh nodes with flag
        """
        count = self.__mesh_count
        for node in self.root_node().traverse_depthwise():
            if flag is None:
                node.mark(count)
            else:
                node.mark(flag)
        self.__mesh_count += 1
    
    
    def n_meshes(self):
        """
        Return the number of recorded meshes
        """
        return self.__mesh_count 
    
    
    def plot_quadmesh(self, ax, name=None, show=True, set_axis=True, 
                      vertex_numbers=False, edge_numbers=False,
                      cell_numbers=False):
        """
        Plot Mesh of QuadCells
        """
        node = self.root_node()
        if set_axis:
            x0, x1, y0, y1 = node.quadcell().box()          
            hx = x1 - x0
            hy = y1 - y0
            ax.set_xlim(x0-0.1*hx, x1+0.1*hx)
            ax.set_ylim(y0-0.1*hy, y1+0.1*hy)
            rect = plt.Polygon([[x0,y0],[x1,y0],[x1,y1],[x0,y1]],fc='b',alpha=0.5)
            ax.add_patch(rect)
        #
        # Plot QuadCells
        #                       
        for cell in self.iter_quadcells():
             
            x0, y0 = cell.vertices['SW'].coordinate()
            x1, y1 = cell.vertices['NE'].coordinate() 

            # Plot current cell
            # plt.plot([x0, x0, x1, x1],[y0, y1, y0, y1],'r.')
            points = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
            if cell.is_marked():
                rect = plt.Polygon(points, fc='r', edgecolor='k')
            else:
                rect = plt.Polygon(points, fc='w', edgecolor='k')
            ax.add_patch(rect)
        
        #
        # Plot Vertex Numbers
        #    
        if vertex_numbers:
            vertices = self.quadvertices()
            v_count = 0
            for v in vertices:
                x,y = v.coordinate()
                x += 0.01
                y += 0.01
                ax.text(x,y,str(v_count),size='smaller')
                v_count += 1
                
        #
        # Plot Edge Numbers
        #
        if edge_numbers:
            edges = self.iter_quadedges()
            e_count = 0
            for e in edges:
                if not(e.is_marked()):
                    v1, v2 = e.vertices()
                    x0,y0 = v1.coordinate()
                    x1,y1 = v2.coordinate()
                    x_pos, y_pos = 0.5*(x0+x1),0.5*(y0+y1)
                    if x0 == x1:
                        # vertical
                        ax.text(x_pos,y_pos,str(e_count),rotation=-90,
                                size='smaller',verticalalignment='center')
                    else:
                        # horizontal
                        y_offset = 0.05*np.abs((x1-x0))
                        ax.text(x_pos,y_pos+y_offset,str(e_count),size='smaller',
                                horizontalalignment='center')                 
                    e_count += 1
                e.mark()
        
        #
        # Plot Cell Numbers
        #
        if cell_numbers:
            cells = self.iter_quadcells()
            c_count = 0
            for c in cells:
                x0,x1,y0,y1 = c.box()
                x_pos, y_pos = 0.5*(x0+x1), 0.5*(y0+y1)
                ax.text(x_pos,y_pos,str(c_count),horizontalalignment='center',
                        verticalalignment='center',size='smaller')
                c_count += 1
        return ax
    
    
class Grid(object):
    """
    Description: Structure used for storing Nodes on coarsest refinement level
    """
    def __init__(self):
        """
        Constructor
        
        Inputs:
        
        """
        pass
    
    @classmethod 
    def from_gmsh(cls, file_name):
        """
        Constructor: Initialize quadrilateral grid from a .msh file. 
        """
        pass
    
    
    def dim(self):
        """
        Returns the underlying dimension of the grid
        """ 
        pass
    
    
    def get_neighbor(self, Node, direction):
        """
        Returns the neighbor of a Node in the Grid
        
        Inputs: 
        
            Node: Node, contained in the grid
            
            direction: str, ['L','R'] for a 1D grid or 
                ['N','S','E','W'] (or combinations) for a 2D grid
        """
        pass   
    
    
    def contains_node(self, node):
        """
        Determine whether a given Node is contained in the grid
        
        Inputs:
        
            Node: Node, 
        """
        pass
    
    
    
class Node(object):
    """
    Description: Tree object for storing and manipulating adaptively
        refined quadtree meshes.
    
    Attributes:
    
        type: str, specifying node's relation to parents and/or children  
            'ROOT' (no parent node), 
            'BRANCH' (parent & children), or 
            'LEAF' (parent but no children)
        
        address: int, list allowing access to node's location within the tree
            General form [[i,j],k1,k2,k3,...kd] where d is the depth and
            [i,j] is the (x,y) position in the original mesh (if parent = MESH)
            kd = [0,1,2,3], where 0->SW, 1->SE, 2->NE, 3->NW
            address = [] if ROOT node. 
        
        depth: int, depth within the tree (ROOT nodes are at depth 0).
        
        parent: Node/Mesh whose child this is
        
        children: dictionary of child nodes. 
            If parent = MESH, keys are [i,j],
            Otherwise, keys are SW, SE, NE, NW. 
        
        marked: bool, flag used to refine or coarsen tree
        
        support: bool, indicates whether given node exists only to enforce the 
            2:1 rule. These nodes can be deleted when the mesh is coarsened.
    
    Methods:
    
        pos2id, id2pos
    """
    def __init__(self, parent=None, position=None, \
                 grid_size=None, quadcell=None):
        """
        Constructor
        
        Inputs:
                    
            parent: Node, parental node
            
            position: position within parent 
                ['SW','SE','NE','NW'] if parent = Node
                None if parent = None
                [i,j] if parent is a ROOT node with specified grid_size
                
            grid_size: int, tuple (nx,ny) specifying shape of a
                ROOT node's child array (optional).
                
            quadcell: QuadCell, physical Cell associated with tree
            
        """             
        #
        # Types
        # 
        if parent == None:
            #
            # ROOT node
            #
            node_type = 'ROOT'
            node_address = []
            node_depth = 0
            if grid_size != None:
                assert type(grid_size) is tuple \
                and all(type(i) is int for i in grid_size), \
                'Child grid size should be a tuple of integers'
                nx,ny = grid_size
                node_children = {}
                for i in range(nx):
                    for j in range(ny):
                        node_children[i,j] = None
            else:
                node_children = {'SW':None, 'SE':None, 'NW':None, 'NE':None}
            self.__grid_size = grid_size
        else:
            #
            # LEAF node
            # 
            node_type = 'LEAF'
            node_address = parent.address + [self.pos2id(position)]
            node_depth = parent.depth + 1
            node_children = {'SW': None, 'SE': None, 'NW': None, 'NE': None}
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'  # modify parent to branch
            
        #
        # Record Attributes
        # 
        self.type = node_type
        self.position = position
        self.address = node_address
        self.depth = node_depth
        self.parent = parent
        self.children = node_children
        self.__cell = quadcell
        self.__tricells = None
        self.__flags  = set()
        self.__support = False
    
    
    def info(self):
        """
        Display essential information about Node
        
        TODO: Delete
        """
        print('-'*11)
        print('Node Info')
        print('-'*11)
        print('{0:10}: {1}'.format('Address', self.address))
        print('{0:10}: {1}'.format('Type', self.type))
        if self.type != 'ROOT':
            print('{0:10}: {1}'.format('Parent', self.parent.address))
            print('{0:10}: {1}'.format('Position', self.position))
        print('{0:10}: {1}'.format('Flags', self.__flags))
        if self.has_children():
            if self.type == 'ROOT' and self.grid_size() != None:
                nx, ny = self.grid_size()
                for iy in range(ny):
                    str_row = ''
                    for ix in range(nx):
                        str_row += repr((ix,iy)) + ': ' 
                        if self.children[(ix,iy)] != None:
                            str_row += '1,  '
                        else:
                            str_row += '0,  '
                    if iy == 0:
                        print('{0:10}: {1}'.format('Children', str_row))
                    else:
                        print('{0:11} {1}'.format(' ', str_row))
            else:
                child_string = ''
                for key in ['SW','SE','NW','NE']:
                    child = self.children[key]
                    if child != None:
                        child_string += key + ': 1,  '
                    else:
                        child_string += key + ': 0,  '
                print('{0:10}: {1}'.format('Children',child_string))
        else:
            child_string = 'None'
            print('{0:10}: {1}'.format('Children',child_string))
            
            
    def copy(self, position=None, parent=None):
        """
        Copy existing Node without attached cell or parental node
        """
        if self.type == 'ROOT':
            #
            # As ROOT, only copy grid_size
            # 
            node_copy = Node(grid_size=self.grid_size())
        else:
            #
            # Copy parent node and position
            # 
            node_copy = Node(position=position, parent=parent)
            
        if self.has_children():
            for child in self.children.values():
                if child != None:
                    node_copy.children[position] = \
                        child.copy(position=child.position, parent=node_copy) 
        return node_copy
            
        
    def grid_size(self):
        """
        Return the grid size of root node
        """
        assert self.type == 'ROOT', 'Only ROOT nodes have children in grid.'
        return self.__grid_size
        
        
    def find_neighbor(self, direction):
        """
        Description: Returns the deepest neighboring cell, whose depth is at 
            most that of the given cell, or 'None' if there aren't any 
            neighbors.
         
        Inputs: 
         
            direction: char, 'N'(north), 'S'(south), 'E'(east), or 'W'(west)
             
        Output: 
         
            neighboring cell
         
        TODO: move to subclass   
        """
        if self.type == 'ROOT':
            #
            # ROOT Cells have no neighbors
            # 
            return None
        #
        # For a node in a grid, do a brute force search (comparing vertices)
        #
        elif self.in_grid():
            p = self.parent
            nx, ny = p.grid_size()

            i,j = self.address[0]
            if direction == 'N':
                if j < ny-1:
                    return p.children[i,j+1]
                else:
                    return None
            elif direction == 'S':
                if j > 0:
                    return p.children[i,j-1]
                else:
                    return None
            elif direction == 'E':
                if i < nx-1:
                    return p.children[i+1,j]
                else:
                    return None
            elif direction == 'W':
                if i > 0:
                    return p.children[i-1,j]
                else:
                    return None
            elif direction == 'SW':
                if i > 0 and j > 0:
                    return p.children[i-1,j-1]
                else:
                    return None
            elif direction == 'SE':
                if i < nx-1 and j > 0:
                    return p.children[i+1,j-1]
                else:
                    return None
            elif direction == 'NW':
                if i > 0 and j < ny-1:
                    return p.children[i-1,j+1]
                else: 
                    return None
            elif direction == 'NE':
                if i < nx-1 and j < ny-1:
                    return p.children[i+1,j+1]
                else:
                    return None 
        #
        # Non-ROOT cells 
        # 
        else:
            #
            # Check for neighbors interior to parent cell
            # 
            if direction == 'N':
                interior_neighbors_dict = {'SW': 'NW', 'SE': 'NE'}
            elif direction == 'S':
                interior_neighbors_dict = {'NW': 'SW', 'NE': 'SE'}
            elif direction == 'E':
                interior_neighbors_dict = {'SW': 'SE', 'NW': 'NE'}
            elif direction == 'W':
                interior_neighbors_dict = {'SE': 'SW', 'NE': 'NW'}
            elif direction == 'SW':
                interior_neighbors_dict = {'NE': 'SW'}
            elif direction == 'SE':
                interior_neighbors_dict = {'NW': 'SE'}
            elif direction == 'NW':
                interior_neighbors_dict = {'SE': 'NW'}
            elif direction == 'NE':
                interior_neighbors_dict = {'SW': 'NE'}
            else:
                print("Invalid direction. Use 'N', 'S', 'E', 'NE','SE','NW, 'SW', or 'W'.")
            
            if self.position in interior_neighbors_dict:
                neighbor_pos = interior_neighbors_dict[self.position]
                return self.parent.children[neighbor_pos]
            #
            # Check for (children of) parental neighbors
            #
            else:
                if direction in ['SW','SE','NW','NE'] and direction != self.position:
                    # Special case
                    for c1,c2 in zip(self.position,direction):
                        if c1 == c2:
                            here = c1
                    mu = self.parent.find_neighbor(here)
                    if mu != None and mu.depth == self.depth-1 and mu.has_children():
                        #
                        # Diagonal neighbors must share corner vertex
                        # 
                        opposite = {'N':'S', 'S':'N', 'W':'E', 'E':'W'}
                        nb_pos = direction
                        for i in range(len(direction)):
                            if direction[i] == here:
                                nb_pos = nb_pos.replace(here,opposite[here])
                        child = mu.children[nb_pos]
                        return child
                    else:
                        return None
                else:
                    mu = self.parent.find_neighbor(direction)
                    if mu == None or mu.type == 'LEAF':
                        return mu
                    else:
                        #
                        # Reverse dictionary to get exterior neighbors
                        # 
                        exterior_neighbors_dict = \
                           {v: k for k, v in interior_neighbors_dict.items()}
                            
                        if self.position in exterior_neighbors_dict:
                            neighbor_pos = exterior_neighbors_dict[self.position]
                            return mu.children[neighbor_pos] 
    
    
    def tree_depth(self, flag=None):
        """
        Return the maximum depth of sub-nodes 
        """
        depth = self.depth
        if self.has_children():
            for child in self.get_children(flag=flag):
                d = child.tree_depth()
                if d > depth:
                    depth = d 
        return depth
             
    
    def traverse(self, flag=None, mode='depth-first'):
        """
        Iterator: Return current node and all its flagged sub-nodes         
        
        Inputs: 
        
            flag [None]: node flag
            
            mode: str, type of traversal 
                'depth-first' [default]: Each cell's progeny is visited before 
                    proceeding to next cell.
                 
                'breadth-first': All cells at a given depth are returned before
                    proceeding to the next level.
        
        Output:
        
            all_nodes: list, of all nodes in tree (marked with flag).
        """
        queue = deque([self])
        while len(queue) != 0:
            if mode == 'depth-first':
                cell = queue.pop()
            elif mode == 'breadth-first':
                cell = queue.popleft()
            else:
                raise Exception('Input "mode" must be "depth-first"'+\
                                ' or "breadth-first".')
            if cell.has_children():
                for child in cell.get_children():
                    if child is not None:
                        queue.append(child)
            if flag is not None: 
                if cell.is_marked(flag):
                    yield cell
            else:
                yield cell        
                
                
    def traverse_tree(self, flag=None):
        """
        Return list of current node and ALL of its sub-nodes         
        
        Inputs: 
        
            flag [None]: node flag
        
        Output:
        
            all_nodes: list, of all nodes in tree (marked with flag).
        
        Note:
        
            Each node's progeny is visited before proceeding to next node 
            (compare traverse depthwise). 
            
        """
        all_nodes = []
        #
        # Add self to list
        #
        if flag is not None:
            if self.is_marked(flag):
                all_nodes.append(self)
        else:
            all_nodes.append(self)
            
        #
        # Add (flagged) children to list
        # 
        if self.has_children():
            for child in self.get_children():
                all_nodes.extend(child.traverse_tree(flag=flag))
                 
        return all_nodes
    
    
    def traverse_depthwise(self, flag=None):
        """
        Iterate node and all sub-nodes, ordered by depth
        
        TODO: Make slicker, like for cells!
        """
        queue = deque([self]) 
        while len(queue) != 0:
            node = queue.popleft()
            if node.has_children():
                for child in node.get_children():
                    if child is not None:
                        queue.append(child)
            if flag is not None:
                if node.is_marked(flag):
                    yield node
            else:
                yield node
        
    
    def find_leaves(self, flag=None, nested=False):
        """
        Return all LEAF sub-nodes (nodes with no children) of current node
        
        Inputs:
        
            flag: If flag is specified, return all leaf nodes within labeled
                submesh (or an empty list if there are none).
                
            nested: bool, indicates whether leaves should be searched for 
                in a nested way (one level at a time).
                
        Outputs:
        
            leaves: list, of LEAF nodes.
            
            
        Note: 
        
            For nested traversal of a node with flags, there is no simple way
            of determining whether any of the progeny are flagged. We therefore
            restrict ourselves to subtrees. If your children are not flagged, 
            then theirs will also not be. 
        """
        if nested:
            #
            # Nested traversal
            # 
            leaves = []
            for node in self.traverse_depthwise(flag=flag):
                if not node.has_children(flag=flag):
                    leaves.append(node)
            return leaves
        else:
            #
            # Non-nested (recursive algorithm)
            # 
            leaves = []
            if flag is None:
                if self.has_children():
                    for child in self.get_children():
                        leaves.extend(child.find_leaves(flag=flag))
                else:
                    leaves.append(self)
            else:
                if self.has_children(flag=flag):
                    for child in self.get_children(flag=flag):
                        leaves.extend(child.find_leaves(flag=flag))
                elif self.is_marked(flag):
                    leaves.append(self)
            return leaves
                              
            
            """
            if flag is None:
                #
                # No flag specified
                #
                if not self.has_children():
                    leaves.append(self)
                else:
                    for child in self.get_children():
                        leaves.extend(child.find_leaves(flag=flag))
            else:
                #
                # Flag specified
                # 
                if not any([child.is_marked(flag) for child in self.get_children()]):
                    if self.is_marked(flag=flag):
                        leaves.append(self)
                else:
                    for child in self.get_children():
                        leaves.extend(child.find_leaves(flag=flag))
            return leaves
            """
        
    '''    
    def find_leaves(self, flag=None):
        """
        Return all LEAF sub-nodes of current node
        
        Inputs:
        
            flag: If flag is specified, return all leaf nodes within labeled
                submesh (or an empty list if there are none).
        """
        leaves = []    
        if self.type == 'LEAF' or not(self.has_children()):
            # 
            # LEAF or childless ROOT
            # 
            if flag is not None:
                #
                # Extra condition imposed by flag
                # 
                if self.is_marked(flag):
                    leaves.append(self)
            else:
                leaves.append(self)
        else:
            if self.has_children():
                #
                # Iterate
                #
                if self.type == 'ROOT' and self.grid_size() is not None:
                    #
                    # Gridded root node: iterate from left to right, bottom to top
                    # 
                    nx, ny = self.grid_size()
                    for j in range(ny):
                        for i in range(nx):
                            child = self.children[(i,j)]
                            leaves.extend(child.find_leaves(flag=flag))
                else:
                    #
                    # Usual quadcell division: traverse in bottom-to-top mirror Z order
                    #
                    for child in self.get_children():
                        if child != None:
                            leaves.extend(child.find_leaves(flag=flag))
                    
        return leaves
    '''
    
    def get_root(self):
        """
        Return root node
        """
        if self.type == 'ROOT':
            return self
        else:
            return self.parent.get_root()
    
    
    def find_node(self, address):
        """
        Locate node by its address
        TODO: THIS DOESN'T LOOK LIKE IT WILL WORK
        """
        node = self.get_root()
        if address != []:
            #
            # Not the ROOT node
            # 
            for a in address:
                idx = self.id2pos(a)
                node = node.children[idx]
        return node
        
                
    def has_children(self, position=None, flag=None):
        """
        Determine whether node has children
        
        TODO: Move to subclass
        """
        if position is None:
            # Check for any children
            if flag is None:
                return any(child is not None for child in self.children.values())
            else:
                # Check for flagged children
                for child in self.children.values():
                    if child is not None and child.is_marked(flag):
                        return True
                return False
        else:
            #
            # Check for child in specific position
            # 
            # Ensure position is valid
            pos_error = 'Position should be one of: "SW", "SE", "NW", or "NE"'
            assert position in ['SW','SE','NW','NE'], pos_error
            if flag is None:
                #
                # No flag specified
                #  
                return self.children[position] is not None
            else:
                #
                # With flag
                # 
                return (self.children[position] is not None) and \
                        self.children[position].is_marked(flag) 
    
    def get_children(self, flag=None):
        """
        Returns a list of (flagged) children, ordered 
        
        Inputs: 
        
            flag: [None], optional marker
        
        Note: Only returns children that are not None 
        
        TODO: move to subclass
        """
        if self.has_children(flag=flag):
            if self.type=='ROOT' and self.grid_size() is not None:
                #
                # Gridded root node - traverse from bottom to top, left to right
                # 
                nx, ny = self.grid_size()
                for j in range(ny):
                    for i in range(nx):
                        child = self.children[(i,j)]
                        if child is not None:
                            if flag is None:
                                yield child
                            elif child.is_marked(flag):
                                yield child
            #
            # Usual quadcell division: traverse in bottom-to-top mirror Z order
            #  
            else:
                for pos in ['SW','SE','NW','NE']:
                    child = self.children[pos]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child
        

        
    def has_parent(self, flag=None):
        """
        Determine whether node has parents (with a given flag)
        """
        if flag is None:
            return self.type != 'ROOT'
        else:
            if self.type != 'ROOT':
                parent = self.parent
                if parent.is_marked(flag):
                    return True
                else:
                    return parent.has_parent(flag=flag)
            else:
                return False 
    
    
    def get_parent(self, flag=None):
        """
        Return node's parent, or first ancestor with given flag (None if there
        are none).
        """
        if flag is None:
            if self.has_parent():
                return self.parent
        else:
            if self.has_parent(flag):
                parent = self.parent
                if parent.is_marked(flag):
                    return parent
                else:
                    return parent.get_parent(flag=flag)
        
    
    def in_grid(self):
        """
        Determine whether node position is given by coordinates or directions
        
        TODO: move to subclass
        
        
        """
        return type(self.position) is tuple
    
    
    def mark(self, flag=None, recursive=False):
        """
        Mark node with keyword. 
        
        Recognized keys: 
                
            True, catchall 
            'split', split node
            'merge', delete children
            'support', mark as support node
            'count', mark for counting
        """
        if flag is None:
            self.__flags.add(True)
        else:
            self.__flags.add(flag)
        
        #
        # Mark children as well
        # 
        if recursive and self.has_children():
            for child in self.get_children():
                child.mark(flag, recursive=recursive)
                
    
    def unmark(self, flag=None, recursive=False):
        """
        Unmark node (and sub-nodes)
        
        Inputs: 
        
            flag: 
        
            recursive (False): boolean, unmark all progeny
            
        """
        # Remove tag
        if flag is None:
            self.__flags.clear()
        else:
            self.__flags.remove(flag)
        # Remove tag from children
        if recursive and self.has_children():
            for child in self.children.values():
                child.unmark(flag=flag, recursive=recursive)
     
    
    def is_marked(self,flag=None):
        """
        Check whether a node is marked.
        
        Input: 
        
            flag: str, int, double
        """
        if flag is None:
            # No flag specified check whether there is any mark
            if self.__flags:
                return True
            else:
                return False 
        else:
            # Check for the presence of given flag
            return flag in self.__flags           
    
    
    def is_linked(self):
        """
        Determine whether node is linked to a cell
        """
        return not self.__cell is None
    
        
    def link(self, cell,recursive=True):
        """
        Link node with QuadCell
        
        Inputs: 
        
            Quadcell: QuadCell object, rectangular cell linked to node
            
            recursive: bool, if True - link entire tree with cells
            
        """
        self.__cell = cell
        if recursive:
            #
            # Link child nodes to appropriate child cells
            #
            assert self.children.keys() == cell.children.keys(), \
            'Keys of tree and cell incompatible.'
            
            if self.has_children():
                if not(cell.has_children()):
                    #
                    # Cell must be split first
                    #
                    cell.split()
             
                for pos in self.children.keys():
                    tree_child = self.children[pos]
                    if tree_child.cell == None:
                        cell_child = cell.children[pos]
                        tree_child.link(cell_child,recursive=recursive) 
    
        
    def unlink(self, recursive=True):
        """
        Unlink node from cell
        """
        self.__cell = None
        if recursive and self.has_children():
            #
            # Unlink child nodes from cells
            # 
            for child in self.children.values():
                if child != None:
                    child.unlink()
        
    
    def quadcell(self):
        """
        Return associated quadcell
        
        TODO: change name
        """
        return self.__cell
       
    
    
    def add_tricells(self, tricells):
        """
        Associate a list of triangular cells with node
        """
        self.__tricells = tricells
        
        
    def tricells(self):
        """
        Return associated tricells 
        """
        return self.__tricells
    
    
    def has_tricells(self):
        """
        Return true if node is associated with list of tricells
        """
        return self.__tricells != None
  
    
    def merge(self):
        """
        Delete all sub-nodes of given node
        """
        for key in self.children.keys():
            self.children[key] = None
        self.type = 'LEAF'
    
    
    def remove(self):
        """
        Remove node from parent's list of children
        """
        assert self.type != 'ROOT', 'Cannot delete ROOT node.'
        self.parent.children[self.position] = None
        
        
    def split(self):
        """
        Add new child nodes to current node
        """
        #
        # If node is linked to cell, split cell and attach children
        #
        assert not(self.has_children()),'Node already has children.' 
        if self.__cell is not None: 
            cell = self.__cell
            #
            # Ensure cell has children
            # 
            if not(cell.has_children()):
                cell.split()
            for pos in self.children.keys():
                self.children[pos] = Node(parent=self, position=pos, \
                                          quadcell=cell.children[pos])
        else:
            for pos in self.children.keys():
                self.children[pos] = Node(parent=self, position=pos)
            
                    
    def is_balanced(self):
        """
        Check whether the tree is balanced
        
        TODO: move to subclass
        """
        children_to_check = {'N': ['SE', 'SW'], 'S': ['NE', 'NW'],
                             'E': ['NW', 'SW'], 'W': ['NE', 'SE']}        
        for leaf in self.find_leaves():
            for direction in ['N','S','E','W']:
                nb = leaf.find_neighbor(direction)
                if nb is not None and nb.has_children():
                    for pos in children_to_check[direction]:
                        child = nb.children[pos]
                        if child.type != 'LEAF':
                            return False
        return True
    
        
    def balance(self):
        """
        Ensure that subcells of current cell conform to the 2:1 rule
        
        TODO: move to subclass
        """
        leaves = set(self.find_leaves())  # set: no duplicates
        leaf_dict = {'N': ['SE', 'SW'], 'S': ['NE', 'NW'],
                     'E': ['NW', 'SW'], 'W': ['NE', 'SE']} 

        while len(leaves) > 0:            
            leaf = leaves.pop()
            flag = False
            #
            # Check if leaf needs to be split
            # 
            for direction1 in ['N', 'S', 'E', 'W']:
                nb = leaf.find_neighbor(direction1) 
                if nb == None:
                    pass
                elif nb.type == 'LEAF':
                    pass
                else:
                    for pos in leaf_dict[direction1]:
                        #
                        # If neighor's children nearest to you aren't LEAVES,
                        # then split and add children to list of leaves! 
                        #
                        if nb.children[pos].type != 'LEAF':
                            leaf.split()
                            for child in leaf.children.values():
                                child.mark('support')
                                leaves.add(child)
                                
                                    
                            #
                            # Check if there are any neighbors that should 
                            # now also be split.
                            #  
                            for direction2 in ['N', 'S', 'E', 'W']:
                                nb = leaf.find_neighbor(direction2)
                                if (nb != None) and \
                                   (nb.type == 'LEAF') and \
                                   (nb.depth < leaf.depth):
                                    leaves.add(nb)
                                
                            flag = True
                            break
                if flag:
                    break
        self.__balanced = True
        
    
    def remove_supports(self):
        """
        Remove the supporting nodes. This is useful after coarsening
        
        TODO: Move to subclass
        """    
        leaves = self.find_leaves()
        while len(leaves) > 0:
            leaf = leaves.pop()
            if leaf.is_marked('support'):
                #
                # Check whether its safe to delete the support cell
                # 
                safe_to_coarsen = True
                for direction in ['N', 'S', 'E', 'W']:
                    nb = leaf.find_neighbor(direction)
                    if nb!=None and nb.has_children():
                        safe_to_coarsen = False
                        break
                if safe_to_coarsen:
                    parent = leaf.parent
                    parent.merge()
                    leaves.append(parent)
        self.__balanced = False
                
                
    def pos2id(self, pos):
        """ 
        Convert position to index: 'SW' -> 0, 'SE' -> 1, 'NW' -> 2, 'NE' -> 3 
        
        TODO: move to subclass
        """
        if type(pos) is tuple:
            assert len(pos) == 2, 'Expecting a tuple of integers.'
            return pos 
        elif type(pos) is int and 0 <= pos and pos <= 3:
            return pos
        elif pos in ['SW','SE','NW','NE']:
            pos_to_id = {'SW': 0, 'SE': 1, 'NW': 2, 'NE': 3}
            return pos_to_id[pos]
        else:
            raise Exception('Unidentified format for position.')
    
    
    def id2pos(self, idx):
        """
        Convert index to position: 0 -> 'SW', 1 -> 'SE', 2 -> 'NW', 3 -> 'NE'
        
        TODO: move to subclass
        """
        if type(idx) is tuple:
            #
            # Grid index and positions coincide
            # 
            assert len(idx) == 2, 'Expecting a tuple of integers.'
            return idx
        
        elif idx in ['SW', 'SE', 'NW', 'NE']:
            #
            # Input is already a position
            # 
            return idx
        elif idx in [0,1,2,3]:
            #
            # Convert
            # 
            id_to_pos = {0: 'SW', 1: 'SE', 2: 'NW', 3: 'NE'}
            return id_to_pos[idx]
        else:
            raise Exception('Unrecognized format.')



class BiNode(Node):
    """
    Binary tree Node
    
    Attributes:
    
        address:
        
        children:
        
        depth:
        
        parent: 
        
        position:
        
        type:
        
        __cell:
        
        __flags:
        
        __support:
        
    """
    def __init__(self, parent=None, position=None, 
                 grid_size=None, bicell=None):
        """
        Constructor
        
        Inputs:
                    
            parent: BiNode, parental node
            
            position: position within parent 
                ['L','R'] if parent = Node
                None if parent = None
                i if parent is a ROOT node with specified grid_size
                
            grid_size: int, number children of ROOT node (optional).
                
            bicell: BiCell, physical Cell associated with tree: 
        """
        #
        # Types
        # 
        if parent == None:
            #
            # ROOT node
            #
            node_type = 'ROOT'
            node_address = []
            node_depth = 0
            if grid_size is not None:
                assert type(grid_size) is int,\
                'Child grid size should be an integer.'
                nx = grid_size
                node_children = {}
                for i in range(nx):
                        node_children[i] = None
            else:
                node_children = {'L':None, 'R':None}
            self.__grid_size = grid_size
        else:
            #
            # LEAF node
            # 
            node_type = 'LEAF'
            node_address = parent.address + [self.pos2id(position)]
            node_depth = parent.depth + 1
            node_children = {'L': None, 'R': None}
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'  # modify parent to branch  
        #
        # Record Attributes
        # 
        self.type = node_type
        self.position = position
        self.address = node_address
        self.depth = node_depth
        self.parent = parent
        self.children = node_children
        self.__cell = bicell
        self.__flags  = set()
        self.__support = False
    
    
    def find_neighbor(self, direction):
        """
        Description: Returns the deepest neighboring cell, whose depth is at 
            most that of the given cell, or 'None' if there aren't any 
            neighbors.
         
        Inputs: 
         
            direction: char, 'L'(left), 'R'(right)
             
        Output: 
         
            neighboring Node
         
        """
        
        assert direction in ['L','R'], 'Invalid direction: use "L" or "R".'
        
        if self.type == 'ROOT':
            #
            # ROOT Cells have no neighbors
            # 
            return None
        #
        # For a node in a grid, do a brute force search (comparing vertices)
        #
        elif self.in_grid():
            p = self.parent
            nx = p.grid_size()

            i = self.address[0]
            if direction == 'L':
                if i > 0:
                    return p.children[i-1]
                else:
                    return None
            elif direction == 'R':
                if i < nx-1:
                    return p.children[i+1]
                else:
                    return None
        #
        # Non-ROOT cells 
        # 
        else:
            #
            # Check for neighbors interior to parent cell
            # 
            opposite = {'L': 'R', 'R': 'L'}
            if self.position == opposite[direction]:
                return self.parent.children[direction]
            else: 
                #
                # Children 
                # 
                mu = self.parent.find_neighbor(direction)
                if mu is None or mu.type == 'LEAF':
                    return mu
                else:
                    return mu.children[opposite[direction]]    
                                        
    
    
    def has_children(self, position=None, flag=None):
        """
        Determine whether node has children
        """
        if position is None:
            # Check for any children
            if flag is None:
                return any(child is not None for child in self.children.values())
            else:
                # Check for flagged children
                for child in self.children.values():
                    if child is not None and child.is_marked(flag):
                        return True
                return False
        else:
            #
            # Check for child in specific position
            # 
            # Ensure position is valid
            pos_error = 'Position should be one of: "L", or "R".'
            assert position in ['L','R'], pos_error
            if flag is None:
                #
                # No flag specified
                #  
                return self.children[position] is not None
            else:
                #
                # With flag
                # 
                return (self.children[position] is not None) and \
                        self.children[position].is_marked(flag) 
    
    
    
    def get_children(self, flag=None):
        """
        Returns a list of (flagged) children, ordered 
        
        Inputs: 
        
            flag: [None], optional marker
        
        Note: Only returns children that are not None 
        
        """
        if self.has_children(flag=flag):
            if self.type=='ROOT' and self.grid_size() is not None:
                #
                # Gridded root node - traverse from bottom to top, left to right
                # 
                nx = self.grid_size()
                for i in range(nx):
                    child = self.children[i]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child
            #
            # Traverse in left-to-right order
            #  
            else:
                for pos in ['L','R']:
                    child = self.children[pos]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child
                    
    def info(self):
        """
        Display essential information about Node
        """
        print('-'*11)
        print('Node Info')
        print('-'*11)
        print('{0:10}: {1}'.format('Address', self.address))
        print('{0:10}: {1}'.format('Type', self.type))
        if self.type != 'ROOT':
            print('{0:10}: {1}'.format('Parent', self.parent.address))
            print('{0:10}: {1}'.format('Position', self.position))
        print('{0:10}: {1}'.format('Flags', self.__flags))
        if self.has_children():
            if self.type == 'ROOT' and self.grid_size() is not None:
                str_row = ''
                nx = self.grid_size()
                for ix in range(nx):
                    str_row += repr(ix) + ': ' 
                    if self.children[ix] is not None:
                        str_row += '1,  '
                    else:
                        str_row += '0,  '
                print('{0:10}: {1}'.format('Children', str_row))
                
            else:
                child_string = ''
                for key in ['L','R']:
                    child = self.children[key]
                    if child is not None:
                        child_string += key + ': 1,  '
                    else:
                        child_string += key + ': 0,  '
                print('{0:10}: {1}'.format('Children',child_string))
        else:
            child_string = 'None'
            print('{0:10}: {1}'.format('Children',child_string))
    
    
class QuadNode(Node):
    """
    Quadtree Node
    """
    def __init__(self, parent=None, position=None, \
                 grid_size=None, quadcell=None):
        """
        Constructor
        
        Inputs:
                    
            parent: Node, parental node
            
            position: position within parent 
                ['SW','SE','NE','NW'] if parent = Node
                None if parent = None
                [i,j] if parent is a ROOT node with specified grid_size
                
            grid_size: int, tuple (nx,ny) specifying shape of a
                ROOT node's child array (optional).
                
            quadcell: QuadCell, physical Cell associated with tree
            
        """             
        #
        # Types
        # 
        if parent == None:
            #
            # ROOT node
            #
            node_type = 'ROOT'
            node_address = []
            node_depth = 0
            if grid_size != None:
                assert type(grid_size) is tuple \
                and all(type(i) is int for i in grid_size), \
                'Child grid size should be a tuple of integers'
                nx,ny = grid_size
                node_children = {}
                for i in range(nx):
                    for j in range(ny):
                        node_children[i,j] = None
            else:
                node_children = {'SW':None, 'SE':None, 'NW':None, 'NE':None}
            self.__grid_size = grid_size
        else:
            #
            # LEAF node
            # 
            node_type = 'LEAF'
            node_address = parent.address + [self.pos2id(position)]
            node_depth = parent.depth + 1
            node_children = {'SW': None, 'SE': None, 'NW': None, 'NE': None}
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'  # modify parent to branch
            
        #
        # Record Attributes
        # 
        self.type = node_type
        self.position = position
        self.address = node_address
        self.depth = node_depth
        self.parent = parent
        self.children = node_children
        self.__cell = quadcell
        self.__tricells = None
        self.__flags  = set()
        self.__support = False
        
        
    def find_neighbor(self, direction):
        """
        Description: Returns the deepest neighboring cell, whose depth is at 
            most that of the given cell, or 'None' if there aren't any 
            neighbors.
         
        Inputs: 
         
            direction: char, 'N'(north), 'S'(south), 'E'(east), or 'W'(west)
             
        Output: 
         
            neighboring cell
                        
        """
        if self.type == 'ROOT':
            #
            # ROOT Cells have no neighbors
            # 
            return None
        #
        # For a node in a grid, do a brute force search (comparing vertices)
        #
        elif self.in_grid():
            p = self.parent
            nx, ny = p.grid_size()

            i,j = self.address[0]
            if direction == 'N':
                if j < ny-1:
                    return p.children[i,j+1]
                else:
                    return None
            elif direction == 'S':
                if j > 0:
                    return p.children[i,j-1]
                else:
                    return None
            elif direction == 'E':
                if i < nx-1:
                    return p.children[i+1,j]
                else:
                    return None
            elif direction == 'W':
                if i > 0:
                    return p.children[i-1,j]
                else:
                    return None
            elif direction == 'SW':
                if i > 0 and j > 0:
                    return p.children[i-1,j-1]
                else:
                    return None
            elif direction == 'SE':
                if i < nx-1 and j > 0:
                    return p.children[i+1,j-1]
                else:
                    return None
            elif direction == 'NW':
                if i > 0 and j < ny-1:
                    return p.children[i-1,j+1]
                else: 
                    return None
            elif direction == 'NE':
                if i < nx-1 and j < ny-1:
                    return p.children[i+1,j+1]
                else:
                    return None 
        #
        # Non-ROOT cells 
        # 
        else:
            #
            # Check for neighbors interior to parent cell
            # 
            if direction == 'N':
                interior_neighbors_dict = {'SW': 'NW', 'SE': 'NE'}
            elif direction == 'S':
                interior_neighbors_dict = {'NW': 'SW', 'NE': 'SE'}
            elif direction == 'E':
                interior_neighbors_dict = {'SW': 'SE', 'NW': 'NE'}
            elif direction == 'W':
                interior_neighbors_dict = {'SE': 'SW', 'NE': 'NW'}
            elif direction == 'SW':
                interior_neighbors_dict = {'NE': 'SW'}
            elif direction == 'SE':
                interior_neighbors_dict = {'NW': 'SE'}
            elif direction == 'NW':
                interior_neighbors_dict = {'SE': 'NW'}
            elif direction == 'NE':
                interior_neighbors_dict = {'SW': 'NE'}
            else:
                print("Invalid direction. Use 'N', 'S', 'E', 'NE','SE','NW, 'SW', or 'W'.")
            
            if self.position in interior_neighbors_dict:
                neighbor_pos = interior_neighbors_dict[self.position]
                return self.parent.children[neighbor_pos]
            #
            # Check for (children of) parental neighbors
            #
            else:
                if direction in ['SW','SE','NW','NE'] and direction != self.position:
                    # Special case
                    for c1,c2 in zip(self.position,direction):
                        if c1 == c2:
                            here = c1
                    mu = self.parent.find_neighbor(here)
                    if mu != None and mu.depth == self.depth-1 and mu.has_children():
                        #
                        # Diagonal neighbors must share corner vertex
                        # 
                        opposite = {'N':'S', 'S':'N', 'W':'E', 'E':'W'}
                        nb_pos = direction
                        for i in range(len(direction)):
                            if direction[i] == here:
                                nb_pos = nb_pos.replace(here,opposite[here])
                        child = mu.children[nb_pos]
                        return child
                    else:
                        return None
                else:
                    mu = self.parent.find_neighbor(direction)
                    if mu == None or mu.type == 'LEAF':
                        return mu
                    else:
                        #
                        # Reverse dictionary to get exterior neighbors
                        # 
                        exterior_neighbors_dict = \
                           {v: k for k, v in interior_neighbors_dict.items()}
                            
                        if self.position in exterior_neighbors_dict:
                            neighbor_pos = exterior_neighbors_dict[self.position]
                            return mu.children[neighbor_pos] 
                        


    def has_children(self, position=None, flag=None):
        """
        Determine whether node has children
        """
        if position is None:
            # Check for any children
            if flag is None:
                return any(child is not None for child in self.children.values())
            else:
                # Check for flagged children
                for child in self.children.values():
                    if child is not None and child.is_marked(flag):
                        return True
                return False
        else:
            #
            # Check for child in specific position
            # 
            # Ensure position is valid
            pos_error = 'Position should be one of: "SW", "SE", "NW", or "NE"'
            assert position in ['SW','SE','NW','NE'], pos_error
            if flag is None:
                #
                # No flag specified
                #  
                return self.children[position] is not None
            else:
                #
                # With flag
                # 
                return (self.children[position] is not None) and \
                        self.children[position].is_marked(flag) 
    
    
    
    def get_children(self, flag=None):
        """
        Returns a list of (flagged) children, ordered 
        
        Inputs: 
        
            flag: [None], optional marker
        
        Note: Only returns children that are not None 
        """
        if self.has_children(flag=flag):
            if self.type=='ROOT' and self.grid_size() is not None:
                #
                # Gridded root node - traverse from bottom to top, left to right
                # 
                nx, ny = self.grid_size()
                for j in range(ny):
                    for i in range(nx):
                        child = self.children[(i,j)]
                        if child is not None:
                            if flag is None:
                                yield child
                            elif child.is_marked(flag):
                                yield child
            #
            # Usual quadcell division: traverse in bottom-to-top mirror Z order
            #  
            else:
                for pos in ['SW','SE','NW','NE']:
                    child = self.children[pos]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child


    def info(self):
        """
        Displays relevant information about the QuadNode
        """
        print('-'*11)
        print('Node Info')
        print('-'*11)
        print('{0:10}: {1}'.format('Address', self.address))
        print('{0:10}: {1}'.format('Type', self.type))
        if self.type != 'ROOT':
            print('{0:10}: {1}'.format('Parent', self.parent.address))
            print('{0:10}: {1}'.format('Position', self.position))
        print('{0:10}: {1}'.format('Flags', self.__flags))
        if self.has_children():
            if self.type == 'ROOT' and self.grid_size() != None:
                nx, ny = self.grid_size()
                for iy in range(ny):
                    str_row = ''
                    for ix in range(nx):
                        str_row += repr((ix,iy)) + ': ' 
                        if self.children[(ix,iy)] != None:
                            str_row += '1,  '
                        else:
                            str_row += '0,  '
                    if iy == 0:
                        print('{0:10}: {1}'.format('Children', str_row))
                    else:
                        print('{0:11} {1}'.format(' ', str_row))
            else:
                child_string = ''
                for key in ['SW','SE','NW','NE']:
                    child = self.children[key]
                    if child != None:
                        child_string += key + ': 1,  '
                    else:
                        child_string += key + ': 0,  '
                print('{0:10}: {1}'.format('Children',child_string))
        else:
            child_string = 'None'
            print('{0:10}: {1}'.format('Children',child_string))
            
            
class Cell(object):
    """
    Cell object
    """
    def __init__(self):
        self._flags = set()
        self._vertex_positions = []
    
    
    def get_vertices(self, pos=None, as_array=True):
        """
        Returns the vertices of the current quadcell. 
        
        Inputs:
        
            pos: str, position of vertex within the cell: 
                SW, S, SE, E, NE, N, NW, or W. If pos is not specified, return
                all vertices.
                
            as_array: bool, if True, return vertices as a numpy array.
                Otherwise return a list of Vertex objects. 
             
                
        Outputs: 
        
            vertices: 
                    
        """            
        if pos is None: 
            #
            # Return all vertices
            # 
            vertices = [self.vertices[pos] for pos in self._vertex_positions]
            if as_array:
                #
                # Convert to array
                #  
                v = [vertex.coordinate() for vertex in vertices]
                return np.array(v)
            else:
                #
                # Return as list of Vertex objects
                #
                return vertices
        else:
            assert pos in self._vertex_positions, \
            'Valid inputs for pos are None, or %s' % self._vertex_positions
            #
            # Return specific vertex
            # 
            vertex = self.vertices[pos]
            if as_array:
                #
                # Convert to array
                # 
                v = vertex.coordinate()
                return np.array(v)
            else:
                #
                # Return vertex object
                # 
                return vertex

    '''
    def find_leaves(self, with_depth=False):
        """
        Returns a list of all 'LEAF' type sub-cells (and their depths) of a given cell 
        
        TODO: Make generic and delete special cases
        """
        leaves = []
        if self.type == 'LEAF':
            if with_depth:
                leaves.append((self,self.depth))
            else:
                leaves.append(self)
        elif self.has_children():
            for pos in self._child_positions:
                child = self.children[pos]
                leaves.extend(child.find_leaves(with_depth))    
        return leaves
    '''
            
    def traverse(self, flag=None, mode='depth-first'):
        """
        Iterator: Return current cell and all its flagged sub-cells         
        
        Inputs: 
        
            flag [None]: cell flag
            
            mode: str, type of traversal 
                'depth-first' [default]: Each cell's progeny is visited before 
                    proceeding to next cell.
                 
                'breadth-first': All cells at a given depth are returned before
                    proceeding to the next level.
        
        Output:
        
            all_nodes: list, of all nodes in tree (marked with flag).
        """
        queue = deque([self])
        while len(queue) != 0:
            if mode == 'depth-first':
                cell = queue.pop()
            elif mode == 'breadth-first':
                cell = queue.popleft()
            else:
                raise Exception('Input "mode" must be "depth-first"'+\
                                ' or "breadth-first".')
            if cell.has_children():
                reverse = True if mode=='depth-first' else False    
                for child in cell.get_children(reverse=reverse):
                    if child is not None:
                        queue.append(child)
            
            if flag is not None: 
                if cell.is_marked(flag):
                    yield cell
            else:
                yield cell             
                 
                
    def find_leaves(self, flag=None, nested=False):
        """
        Return all LEAF sub-nodes (nodes with no children) of current node
        
        Inputs:
        
            flag: If flag is specified, return all leaf nodes within labeled
                submesh (or an empty list if there are none).
                
            nested: bool, indicates whether leaves should be searched for 
                in a nested way (one level at a time).
                
        Outputs:
        
            leaves: list, of LEAF nodes.
            
            
        Note: 
        
            For nested traversal of a node with flags, there is no simple way
            of determining whether any of the progeny are flagged. We therefore
            restrict ourselves to subtrees. If your children are not flagged, 
            then theirs will also not be. 
        """
        if nested:
            #
            # Nested traversal
            # 
            leaves = []
            for cell in self.traverse(flag=flag, mode='breadth-first'):
                if not cell.has_children(flag=flag):
                    leaves.append(cell)
            return leaves
        else:
            #
            # Non-nested (recursive algorithm)
            # 
            leaves = []
            if flag is None:
                if self.has_children():
                    for child in self.get_children():
                        leaves.extend(child.find_leaves(flag=flag))
                else:
                    leaves.append(self)
            else:
                if self.has_children(flag=flag):
                    for child in self.get_children(flag=flag):
                        leaves.extend(child.find_leaves(flag=flag))
                elif self.is_marked(flag):
                    leaves.append(self)
            return leaves
    '''
    def find_cells_at_depth(self, depth):
        """
        Return a list of cells at a certain depth
        
        TODO: Is this necessary? 
        TODO: Make generic and delete special 
        """
        cells = []
        if self.depth == depth:
            cells.append(self)
        elif self.has_children():
            for child in self.children[self._children_positions]:
                cells.extend(child.find_cells_at_depth(depth))
        return cells
    '''
    
    def get_root(self):
        """
        Find the ROOT cell for a given cell
        """
        if self.type == 'ROOT' or self.type == 'MESH':
            return self
        else:
            return self.parent.get_root()
        
        
    def has_children(self, position=None, flag=None):
        """
        Determine whether node has children
        
        """
        if position is None:
            # Check for any children
            if flag is None:
                return any(child is not None for child in self.children.values())
            else:
                # Check for flagged children
                for child in self.children.values():
                    if child is not None and child.is_marked(flag):
                        return True
                return False
        else:
            #
            # Check for child in specific position
            # 
            # Ensure position is valid
            pos_error = 'Position should be one of: %s' %self._child_positions
            assert position in self._child_positions, pos_error
            if flag is None:
                #
                # No flag specified
                #  
                return self.children[position] is not None
            else:
                #
                # With flag
                # 
                return (self.children[position] is not None) and \
                        self.children[position].is_marked(flag) 
    
    
    def get_children(self, flag=None, reverse=False):
        """
        Returns (flagged) children, ordered 
        
        Inputs: 
        
            flag: [None], optional marker
            
            reverse: [False], option to list children in reverse order 
                (useful for the 'traverse' function).
        
        Note: Only returns children that are not None
              Use this to obtain a consistent iteration of children
        """
    
        if self.has_children(flag=flag):
            if not reverse:
                #
                # Go in usual order
                # 
                for pos in self._child_positions:
                    child = self.children[pos]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child
            else: 
                #
                # Go in reverse order
                # 
                for pos in reversed(self._child_positions):
                    child = self.children[pos]
                    if child is not None:
                        if flag is None:
                            yield child
                        elif child.is_marked(flag):
                            yield child
                            
    
    def has_parent(self):
        """
        Returns True if cell has a parent cell, False otherwise
        """
        return not self.parent == None
    
    
    def mark(self, flag=None):
        """
        Mark CEll
        
        Inputs:
        
            flag: int, optional label used to mark cell
        """  
        if flag is None:
            self._flags.add(True)
        else:
            self._flags.add(flag)
      
    
    def unmark(self, flag=None, recursive=False):
        """
        Unmark Cell
        
        Inputs: 
        
            flag: label to be removed
        
            recursive: bool, also unmark all subcells
        """
        #
        # Remove label from own list
        #
        if flag is None:
            # No flag specified -> delete all
            self._flags.clear()
        else:
            # Remove specified flag (if present)
            if flag in self._flags: self._flags.remove(flag)
        
        #
        # Remove label from children if applicable   
        # 
        if recursive and self.has_children():
            for child in self.children.values():
                child.unmark(flag=flag, recursive=recursive)
                
 
         
    def is_marked(self,flag=None):
        """
        Check whether quadcell is marked
        
        Input: flag, label for QuadCell: usually one of the following:
            True (catchall), 'split' (split cell), 'count' (counting)
            
        TODO: Move to cell class
        """ 
        if flag is None:
            # No flag -> check whether set is empty
            if self._flags:
                return True
            else:
                return False
        else:
            # Check wether given label is contained in quadcell's set
            return flag in self._flags
    
    
    def remove(self):
        """
        Remove node from parent's list of children
        """
        assert self.type != 'ROOT', 'Cannot delete ROOT node.'
        self.parent.children[self.position] = None    
           
           
class BiCell(Cell):
    """
    Binary tree of sub-intervals in a 1d mesh
    
    Attributes:
    
        type: str, specifies cell's position in the binary tree
        
            ROOT - cell on coarsest level
            BRANCH - cell has a parent as well as children
            LEAF - cell on finest refinement level
            
        parent: BiCell, of which current cell is a child
        
        children: dict, of sub-cells of current cell
        
        flags: set, of flags (numbers/strings) associated with cell
        
        position: str, position within parent 'L' (left) or 'R' (right)
        
        address: list, specifying address within tree
        
        vertices: double, dictionary of left and right vertices
    
    
    Methods:
    
    
    Notes: 
    
        There are many similarities between BiCells (1d) and Edges (2d) 
        
        Once we're done with this, we have to modify 'Node'
    """
    
    
    
    
    def __init__(self, parent=None, position=None, grid_size=None, box=None):
        """
        Constructor
        
        Inputs:
        
            parent: BiCell, parental cell
            
            position: str, position within parental cell
            
            grid_size: int, number of elements in grid
            
            box: double, [x_min, x_max] interval endpoints
        """
        super().__init__()
        # =====================================================================
        # Tree Attributes
        # =====================================================================
        self.parent = parent
        if parent is None:
            #
            # ROOT Node
            # 
            self.type = 'ROOT'
            cell_depth = 0
            cell_address = []
            
            if grid_size == None:
                children = {'L': None, 'R': None}
                child_positions = ['L','R']
            else:
                n = grid_size
                children = {}
                for i in range(n):
                    children[i] = None
                child_positions = [i for i in range(n)]
            self.grid_size = grid_size
        else:
            #
            # LEAF Node
            #  
            position_missing = 'Position within parent cell must be specified.'
            assert position is not None, position_missing
        
            self.type = 'LEAF'
            # Change parent type (from LEAF)
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'
            
            cell_depth = parent.depth + 1
            cell_address = parent.address + [self.pos2id(position)]    
            children = {'L': None, 'R': None}
            child_positions = ['L','R']
        #
        # Set attributes
        # 
        
        self.children = children
        self.depth = cell_depth
        self.address = cell_address
        self.position = position
        self._vertex_positions = ['L','R','M']
        self._child_positions = child_positions
        
        
        # =====================================================================
        # Vertices
        # =====================================================================
        if parent == None:
            #
            # ROOT Cell
            # 
            if box == None:
                # Use default
                box = [0,1]                

            box_format = 'The box variable must be a list with 2 entries.'
            box_order  = 'The interval endpoints must be strictly increasing.'
            assert (type(box) is list) and (len(box)==2), box_format 
            assert box[0] < box[1], box_order 
            x0, x1 = box
            if grid_size == None:
                #
                # 2 subcells
                # 
                xm = 0.5*(x0+x1)
                vertices = {'L': Vertex((x0,)),
                            'M': Vertex((xm,)), 
                            'R': Vertex((x1,))}
                                                      
                edges = {('L','R') : Edge(vertices['L'],vertices['R']),
                         ('L','M') : Edge(vertices['L'],vertices['M']),
                         ('M','R') : Edge(vertices['M'],vertices['R'])}             
            else:
                #
                # Grid of sub-cells
                #
                # TODO: The root cell's edges (there are only 2) are not the 
                #       ones listed in the 'edges' attribute. However, they
                #       are inherited by the subcells.
                nx = grid_size                
                x = np.linspace(x0,x1,nx+1)
                vertices = {}
                edges = {}
                for i in range(nx+1):
                        # Vertices
                        vertices[i] = Vertex((x[i],))
                        
                        # Children
                        if i < nx: 
                            children[i] = None
                        
                        # Edges
                        if i>0:
                            # Horizontal edges
                            edges[i-1,i] = Edge(vertices[i-1],vertices[i])
                # Root Cell edges
                edges[('L','R')] = Edge(vertices[0],vertices[nx-1])
                
        else: 
            #
            # LEAF Node
            # 
            vertex_keys = ['L','M','R']
            vertices = dict.fromkeys(vertex_keys)
            edge_keys = [('L','R'),('L','M'), ('M','R')] 
            edges = dict.fromkeys(edge_keys)
            #
            # Inherited Vertices and Edges
            # 
            if parent.type == 'ROOT' and parent.grid_size is not None:
                #
                # Cell lies in grid
                #
                i = position
                vertices['L'] = parent.vertices[i]
                vertices['R'] = parent.vertices[i+1]
                
                x0, = vertices['L'].coordinate()
                x1, = vertices['R'].coordinate()
                xm = 0.5*(x0+x1)
                     
                vertices['M'] = Vertex((xm,))
                edges[('L','R')] = parent.edges[(i,i+1)] 
            else:
                
                #
                # Parent not gridded
                #
                           
                inherited_vertices = \
                    {'L': {'L':'L', 'R':'M'},
                     'R': {'L':'M', 'R':'R'}}
                
                for cv,pv in inherited_vertices[position].items():
                    vertices[cv] = parent.vertices[pv]
                
                inherited_edges = \
                    {'L': { ('L','R'):('L','M')}, 
                     'R': { ('L','R'):('M','R')}} 
                     
                for ce,pe in inherited_edges[position].items():
                    edges[ce] = parent.edges[pe]
            
            x0, = vertices['L'].coordinate()
            x1, = vertices['R'].coordinate()
            xm = 0.5*(x0+x1)
            
            vertices['M'] = Vertex((xm,))        
            
            #
            # New interior edges
            #             
            edges[('L','M')] = Edge(vertices['L'],vertices['M'])
            edges[('M','R')] = Edge(vertices['M'],vertices['R'])
            
        #
        # Store vertices and edges
        #  
        self.vertices = vertices
        self.edges = edges      
        
    
    def box(self):
        """
        Return the cell's interval endpoints
        """
        if self.type == 'ROOT' and self.grid_size is not None:
            nx = self.grid_size
            x0, = self.vertices[0].coordinate()
            x1, = self.vertices[nx].coordinate()
        else:
            x0, = self.vertices['L'].coordinate()
            x1, = self.vertices['R'].coordinate()
        return x0, x1
    
    
    
    
    def find_neighbor(self, direction):
        """
        Returns the deepest neighboring cell, whose depth is at most that of the
        given cell, or 'None' if there aren't any neighbors.
         
        Inputs: 
         
            direction: char, 'L', 'R'
             
        Output: 
         
            neighboring cell    
        """
        if self.parent == None:
            return None
        #
        # For cell in a MESH, do a brute force search (comparing vertices)
        #
        elif self.parent.type == 'ROOT' and self.parent.grid_size is not None:
            m = self.parent
            nx = m.grid_size
            i = self.position
            if direction == 'L':
                if i > 0:
                    return m.children[i-1]
                else:
                    return None
            elif direction == 'R':
                if i < nx-1:
                    return m.children[i+1]
                else:
                    return None     
        #
        # Non-ROOT cells 
        # 
        else:
            #
            # Check for neighbors interior to parent cell
            # 
            if direction == 'L':
                if self.position == 'R':
                    return self.parent.children['L']
            elif direction == 'R':
                if self.position == 'L':
                    return self.parent.children['R']
            else:
                raise Exception('Invalid direction. Use "L", or "R".')    
            #
            # Check for (children of) parental neighbors
            #
            mu = self.parent.find_neighbor(direction)
            if mu == None or mu.type == 'LEAF':
                return mu
            else:
                if direction == 'L':
                    return mu.children['R']
                elif direction == 'R':
                    return mu.children['L']
               
    '''
    TODO: Remove 
    def find_leaves(self, with_depth=False):
        """
        Returns a list of all 'LEAF' type sub-cells (and their depths) of a given cell 
        """
        leaves = []
        if self.type == 'LEAF':
            if with_depth:
                leaves.append((self,self.depth))
            else:
                leaves.append(self)
        elif self.has_children():
            for child in self.children.values():
                leaves.extend(child.find_leaves(with_depth))    
        return leaves
    
    
    def find_cells_at_depth(self, depth):
        """
        Return a list of cells at a certain depth
        """
        cells = []
        if self.depth == depth:
            cells.append(self)
        elif self.has_children():
            for child in self.children.values():
                cells.extend(child.find_cells_at_depth(depth))
        return cells
  
    
    def get_root(self):
        """
        Find the ROOT cell for a given cell
        """
        if self.type == 'ROOT' or self.type == 'MESH':
            return self
        else:
            return self.parent.get_root()
      
    def has_children(self):
        """
        Returns True if cell has any sub-cells, False otherwise
        """    
        return any([self.children[pos]!=None for pos in self.children.keys()])
    '''
    
        
    
    
    
    
    def contains_point(self, points):
        """
        Determine whether the given cell contains a point
        
        Input: 
        
            point: tuple (x,y), list of tuples, or (n,2) array
            
        Output: 
        
            contains_point: boolean array, True if cell contains point, 
            False otherwise
        
        
        Note: Points on the boundary between cells belong to both adjoining
            cells.
        """          
        x = np.array(points)
        x_min, x_max = self.box()
        
        in_box = (x_min <= x) & (x <= x_max)
        return in_box
            
               
    def locate_point(self, point):
        """
        Returns the smallest cell containing a given point or None if current 
        cell doesn't contain the point
        
        Input:
            
            point: double, x
            
        Output:
            
            cell: smallest cell that contains x
                
        """
        # TESTME: locate_point
        
        if self.contains_point(point):
            if self.type == 'LEAF': 
                return self
            else:
                #
                # If cell has children, find the child containing the point and continue looking from there
                # 
                for child in self.children.values():
                    if child.contains_point(point):
                        return child.locate_point(point)                     
        else:
            return None    
    
    
    def map_to_reference(self, x):
        """
        Map point to reference cell [0,1]^2
        
        Input:
        
            x: double, n_points array of points in the physical cell
            
        Output:
        
            x_ref: double, (n_points, dim) array of points in the reference 
                cell.
        """
        x = np.array(x)      
        x0,x1 = self.box()
        x_ref = (x-x0)/(x1-x0)
        return x_ref
    
    
    def map_from_reference(self, x_ref):
        """
        Map point from reference cell [0,1]^2 to physical cell
        
        Inputs: 
        
            x_ref: double, (n_points, dim) array of points in the reference
                cell. 
                
        Output:
        
            x: double, (n_points, dim) array of points in the physical cell
        """
        x_ref = np.array(x_ref)
        x0,x1 = self.box()
        x = np.array([x0 + (x1-x0)*x_ref])
        return x
    
    
    def derivative_multiplier(self, derivative):
        """
        Let y = l(x) be the mapping from the physical to the reference element.
        Then, if a (shape) function f(x) = g(l(x)), its derivative f'(x) = g'(x)l'(x)
        This method returns the constant l'(x) = 1/(b-a).   
        """
        c = 1
        if derivative[0] in {1,2}:
            # 
            # There's a map and we're taking derivatives
            #
            x0,x1 = self.box()
            for _ in range(derivative[0]):
                c *= 1/(x1-x0)
        return c
                    
                                
    def split(self):
        """
        Split cell into subcells
        """
        assert not self.has_children(), 'Cell is already split.'
        for pos in self._child_positions:
            self.children[pos] = BiCell(parent=self, position=pos) 
        
        
    def pos2id(self, position):
        """
        Convert 'L' and 'R' to 0 and 1 respectively
        
        Input:
        
            position: str, 'L', or 'R'
            
        Output:
        
            position: int, 0 (for 'L') or 1 (for 'R')
        """
        if type(position) is int:
            grid_size = self.get_root().grid_size
            if grid_size is None:
                assert position in [0,1],\
                'Input "position" passed as integer must be 0/1.'
            else:
                assert position < self.get_root().grid_size, \
                'Input "position"=%d exceeds grid_size=%d.' \
                %(position, grid_size)  
            return position 
        else:
            assert position in ['L','R'], \
            'Position is %s. Use "R" or "L" for position' % position
            if position == 'L':
                return 0
            else:
                return 1


class TriCell(object):
    """
    TriCell object
    
    Attributes:
        
    
    Methods:
    
    """
    def __init__(self, vertices, parent=None):
        """
        Inputs:
        
            vertices: Vertex, list of three vertices (ordered counter-clockwise)
            
            parent: QuadCell that contains triangle
            
        """
        v = []
        e = []
        assert len(vertices) == 3, 'Must have exactly 3 vertices.'
        for i in range(3):
            #
            # Define vertices and Half-Edges with minimun information
            # 
            v.append(Vertex(vertices[i],2))        
        #
        # Some edge on outerboundary
        # 
        self.outer_component = e[0]
        
        for i in range(3):
            #
            # Half edge originating from v[i]
            # 
            v[i].incident_edge = e[i]
            #
            # Edges preceding/following e[i]
            # 
            j = np.remainder(i+1,3)
            e[i].next = e[j]
            e[j].previous = e[i]
            #
            #  Incident face
            # 
            e[i].incident_face = self
            
        self.parent_node = parent
        self.__vertices = v
        self.__edges = [
                        Edge(vertices[0], vertices[1], parent=self), \
                        Edge(vertices[1], vertices[2], parent=self), \
                        Edge(vertices[2], vertices[0], parent=self)
                        ]
        self.__element_no = None
        self.__flags = set()
        
        
    def vertices(self,n):
        return self.__vertices[n]
    
    def edges(self):
        return self.__edges
    
        
    def area(self):
        """
        Compute the area of the triangle
        """
        v = self.__vertices
        a = [v[1].coordinate()[i] - v[0].coordinate()[i] for i in range(2)]
        b = [v[2].coordinate()[i] - v[0].coordinate()[i] for i in range(2)]
        return 0.5*abs(a[0]*b[1]-a[1]*b[0])
    
     
    def normal(self, edge):
        #p = ((y1-y0)/nnorm,(x0-x1)/nnorm)
        pass    
    
    
    def number(self, num, overwrite=False):
        """
        Assign a number to the triangle
        """
        if self.__element_no == None or overwrite:
            self.__element_no = num
        else:
            raise Warning('Element already numbered. Overwrite disabled.')
            return
        
    def find_neighbor(self, edge, tree):
        """
        Find neighboring triangle across edge wrt a given tree   
        """
        pass

    def mark(self, flag=None):
        """
        Mark TriCell
        
        Inputs:
        
            flag: optional label used to mark cell
        """  
        if flag is None:
            self.__flags.add(True)
        else:
            self.__flags.add(flag)
            
        
    def unmark(self, flag=None, recursive=False):
        """
        Remove label from TriCell
        
        Inputs: 
        
            flag: label to be removed
        
            recursive: bool, also unmark all subcells
        """
        #
        # Remove label from own list
        #
        if flag is None:
            # No flag specified -> delete all
            self.__flags.clear()
        else:
            # Remove specified flag (if present)
            if flag in self.__flags: self.__flags.remove(flag)
        
        #
        # Remove label from children if applicable   
        # 
        if recursive and self.has_children():
            for child in self.children.values():
                child.unmark(flag=flag, recursive=recursive)
                
 
         
    def is_marked(self,flag=None):
        """
        Check whether cell is marked
        
        Input: flag, label for QuadCell: usually one of the following:
            True (catchall), 'split' (split cell), 'count' (counting)
            
        TODO: Possible to add/remove set? Useful? 
        """ 
        if flag is None:
            # No flag -> check whether set is empty
            if self.__flags:
                return True
            else:
                return False
        else:
            # Check wether given label is contained in quadcell's set
            return flag in self.__flags
                    
        
class QuadCell(Cell):
    """
    (Tree of) Rectangular cell(s) in mesh
        
    Attributes: 
    
        type - Cells can be one of the following types:
            
            ROOT   - cell on coarsest level
            BRANCH - cell has parent(s) as well as children
            LEAF   - cell on finest refinement level
         
        parent: cell/mesh of which current cell is a sub-cell
         
        children: list of sub-cells of current cell
        
        flag: boolean, used to mark cells
         
        neighbors: addresses of neighboring cells
         
        depth: int, current refinement level 0,1,2,...
        
        address: address within root cell/mesh.
         
        min_size: double, minimum possible mesh width
     
    
    Methods: 
       
    """ 
    
    
    '''
    ================
    OLD CONSTRUCTOR
    ================
    def __init__(self, vertices, parent=None, edges=None,
                 position=None, grid_size=None):
        """
        Description: Initializes the cell (sub-)tree
        
        Inputs: 
            
            vertices: corner points of cell in one of the following formats
                list             - [x0, x1, y0, y1]
                dict of tuples   - {'SW': (x0,y0), 'SE': (x1,y0), 
                                    'NE': (x1,y1), 'NW', (x0,y1) }
                dict of vertices - {'SW': Vertex((x0,y0)), 'SE': Vertex((x1,y0)), 
                                    'NE': Vertex((x1,y1)), 'NW': Vertex((x0,y1))}        
            parent: parental cell
                
            position: own position in parent cell. Formats:
                list - [i,j] i=0...nx, j=0...ny (when grid_size!=None). 
                    left bottom = (0,0) -> right top = (nx,ny).         
                str - NW, SW, NE, or SE
                
            grid_size: array size for children as integer tuple 
                (only for ROOT).
        """
        #
        # Vertices
        # 
        if type(vertices) is list:
            #
            # Vertices in the form [xmin, xmax, ymin, ymax]
            # 
            assert len(vertices) == 4, 'Vertex list must contain 4 entries.'
            x0, x1, y0, y1 = vertices
            cell_vertices = {'SW':Vertex((x0,y0)), 'SE': Vertex((x1,y0)), \
                             'NW':Vertex((x0,y1)), 'NE': Vertex((x1,y1)), \
                             'M': Vertex((0.5*(x0+x1),0.5*(y0+y1)))}
        else:
            #
            # Vertices in dictionary form
            cell_vertices = {}
            for k in ['SW', 'SE', 'NE', 'NW']:
                v = vertices[k]
                #
                # Convert tuple to Vertex if necessary
                #
                if type(v) is tuple:
                    v = Vertex(v)
                    cell_vertices[k] = v 
                elif type(v) is Vertex:
                    cell_vertices[k] = v
                else:
                    raise Exception('Only Vertex or tuple allowed.')
            x0, y0 = cell_vertices['SW'].coordinate()
            x1, y1 = cell_vertices['NE'].coordinate()
            cell_vertices['M'] = Vertex((0.5*(x0+x1),0.5*(y0+y1)))
        self.vertices = cell_vertices
        #
        # Edges
        #
        if edges == None:
            #
            # Edges not specified - define new ones using vertices
            # 
            e_we = Edge(self.vertices['SW'], self.vertices['SE'], parent=self)
            e_sn = Edge(self.vertices['SE'], self.vertices['NE'], parent=self) 
            e_ew = Edge(self.vertices['NE'], self.vertices['NW'], parent=self)
            e_ns = Edge(self.vertices['NW'], self.vertices['SW'], parent=self)
            self.edges = {'S': e_we, 'E': e_sn, 'N': e_ew, 'W': e_ns}
        else:
            #
            # Edges given: Incorporate after some checks
            # 
            assert type(edges) is dict,\
                'Type: %s - should be a dictionary' %(type(edges))
            
            assert all([direction in edges.keys() \
                        for direction in ['S','E','N','W']]), \
                   'Keys: %s- should be N, S, E, W.' %(repr(edges.keys()))
                   
            assert all([type(edge) is Edge for edge in edges.values() ]), \
                   'Values should be in class Edge.'
                   
            self.edges = edges
            
        if parent == None:
            #
            # ROOT cell
            #
            cell_type = 'ROOT'
            cell_depth = 0
            cell_address = []
            if grid_size != None:
                nx,ny = grid_size
                cell_children = {}
                for i in range(nx):
                    for j in range(ny):
                        cell_children[i,j] = None
            else:
                cell_children = {'SW':None, 'SE':None, 'NE':None, 'NW':None}
            self.grid_size = grid_size
        else:
            #
            # LEAF cell
            #
            cell_type = 'LEAF'
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'  # update parent's type
            cell_depth = parent.depth + 1
            cell_address = parent.address + [self.pos2id(position)]
            cell_children = {'SW':None, 'SE':None, 'NE':None, 'NW':None}
        #
        # Set attributes
        #     
        self.parent = parent
        self.children = cell_children
        self.type = cell_type
        self.position = position
        self.address = cell_address
        self.depth = cell_depth
        self.__flag = False
        self.support_cell = False   
        '''
        
    def __init__(self, parent=None, position=None, grid_size=None, box=None):
        """
        Constructor
        
        
        Inputs:
        
            parent: QuadCell, parental cell (must be specified for LEAF cells).
            
            position: str/tuple, position within parental cell (must be 
                specified for LEAF cells).
            
            grid_size: tuple, dimensions of ROOT cell's grid
            
            box: double, list [x0,x1,y0,y1] bnd of cell (default [0,1,0,1])
            
            
        Modified: 12/27/2016
        """
        super().__init__()
        
        # =====================================================================
        # Tree Attributes
        # =====================================================================
        if parent == None:
            #
            # ROOT Node
            # 
            cell_type = 'ROOT'
            cell_depth = 0
            cell_address = []
            
            if grid_size == None:
                children = {'SW': None, 'SE': None, 'NE':None, 'NW':None}
                child_positions = ['SW','SE','NW','NE']
            else:
                child_positions = []
                nx, ny = grid_size
                children = {}
                for j in range(ny):
                    for i in range(nx):
                        children[i,j] = None
                        child_positions.append((i,j))
            self.grid_size = grid_size
        else:
            #
            # LEAF Node
            #  
            position_missing = 'Position within parent cell must be specified.'
            assert position != None, position_missing
        
            cell_type = 'LEAF'
            # Change parent type (from LEAF)
            if parent.type == 'LEAF':
                parent.type = 'BRANCH'
            
            cell_depth = parent.depth + 1
            cell_address = parent.address + [self.pos2id(position)]    
            children = {'SW': None, 'SE': None, 'NW':None, 'NE':None}
            child_positions = ['SW','SE','NW','NE']
        #
        # Set attributes
        # 
        self.type = cell_type
        self.parent = parent
        self.children = children
        self.depth = cell_depth
        self.address = cell_address
        self.position = position
        self._child_positions = child_positions
        self._vertex_positions = ['SW', 'S', 'SE', 'E', 'NE', 'N', 'NW', 'W','M']
        
        
        # =====================================================================
        # Vertices and Edges
        # =====================================================================
        if parent == None:
            #
            # ROOT Cell
            # 
            if box == None:
                # Use default
                box = [0.,1.,0.,1.]                

            box_format = 'The box variable must be a list with 4 entries.'
            assert (type(box) is list) and (len(box)==4), box_format 
            
            x0, x1, y0, y1 = box
            if grid_size == None:
                #
                # 4 subcells
                # 
                xm = 0.5*(x0+x1)
                ym = 0.5*(y0+y1)
                vertices = {'SW': Vertex((x0,y0)),
                            'S' : Vertex((xm,y0)), 
                            'SE': Vertex((x1,y0)),
                            'E' : Vertex((x1,ym)),
                            'NE': Vertex((x1,y1)),
                            'N' : Vertex((xm,y1)),
                            'NW': Vertex((x0,y1)),
                            'W' : Vertex((x0,ym)),
                            'M' : Vertex((xm,ym))}
                                                      
                edges = {('M','SW') : Edge(vertices['M'],vertices['SW']),
                         ('M','S')  : Edge(vertices['M'],vertices['S']),
                         ('M','SE') : Edge(vertices['M'],vertices['SE']),
                         ('M','E')  : Edge(vertices['M'],vertices['E']),
                         ('M','NE') : Edge(vertices['M'],vertices['NE']),
                         ('M','N')  : Edge(vertices['M'],vertices['N']),
                         ('M','NW') : Edge(vertices['M'],vertices['NW']),
                         ('M','W')  : Edge(vertices['M'],vertices['W']),
                         ('SW','NE'): Edge(vertices['SW'],vertices['NE']),
                         ('NW','SE'): Edge(vertices['NW'],vertices['SE']),                         
                         ('SW','S') : Edge(vertices['SW'],vertices['S']),
                         ('S','SE') : Edge(vertices['S'],vertices['SE']), 
                         ('SE','E') : Edge(vertices['SE'],vertices['E']),
                         ('E','NE') : Edge(vertices['E'],vertices['NE']),
                         ('NE','N') : Edge(vertices['NE'],vertices['N']),
                         ('N','NW') : Edge(vertices['N'],vertices['NW']),
                         ('NW','W') : Edge(vertices['NW'],vertices['W']),
                         ('W','SW') : Edge(vertices['W'],vertices['SW']),
                         ('SW','SE'): Edge(vertices['SW'],vertices['SE']),
                         ('SE','NE'): Edge(vertices['SE'],vertices['NE']),
                         ('NE','NW'): Edge(vertices['NE'],vertices['NW']),
                         ('NW','SW'): Edge(vertices['NW'],vertices['SW'])}             
            else:
                #
                # Grid of sub-cells
                #
                # TODO: The root cell's edges (there are only 4) are not the 
                #       ones listed in the 'edges' attribute. However, they
                #       are inherited by the subcells.
                nx, ny = grid_size                
                x = np.linspace(x0,x1,nx+1)
                y = np.linspace(y0,y1,ny+1)
                vertices = {}
                edges = {}
                for i in range(nx+1):
                    for j in range(ny+1):
                        # Vertices
                        vertices[i,j] = Vertex((x[i],y[j]))
                        
                        # Children
                        if i<nx and j<ny:
                            children[i,j] = None
                        
                        # Edges
                        if i>0:
                            # Horizontal edges
                            edges[((i-1,j),(i,j))] = \
                                Edge(vertices[i-1,j],vertices[i,j])
                        
                        if j>0:
                            # Vertical edges
                            edges[((i,j-1),(i,j))] = \
                                Edge(vertices[i,j-1],vertices[i,j])
                edges[('SW','SE')] = Edge(vertices[0,0],vertices[nx-1,0])
                edges[('SE','NE')] = Edge(vertices[nx-1,0],vertices[nx-1,ny-1])
                edges[('NE','NW')] = Edge(vertices[nx-1,ny-1],vertices[0,ny-1])
                edges[('NW','SW')] = Edge(vertices[0,ny-1],vertices[0,0])
                
        else: 
            #
            # LEAF Node
            # 
            vertex_keys = ['SW','S','SE','E','NE','N','NW','W','M']
            vertices = dict.fromkeys(vertex_keys)
            edge_keys = [('M','SW'), ('M','S'), ('M','SE'), ('M','E'),
                         ('M','NE'), ('M','N'), ('M','NW'), ('M','W'),
                         ('SW','NE'), ('NW','SE'), ('SW','S'), ('S','SE'),
                         ('SE','E'), ('E','NE'), ('NE','N'), ('N','NW'),
                         ('NW','W'), ('W','SW'), ('SW','SE'), ('SE','NE'), 
                         ('NE','NW'), ('NW','SW')] 
            edges = dict.fromkeys(edge_keys)
            #
            # Inherited Vertices and Edges
            # 
            if parent.type == 'ROOT' and parent.grid_size is not None:
                #
                # Cell lies in grid
                #
                i,j = position
                vertices['SW'] = parent.vertices[i,j]
                vertices['SE'] = parent.vertices[i+1,j]
                vertices['NE'] = parent.vertices[i+1,j+1]
                vertices['NW'] = parent.vertices[i,j+1]
                
                x0,y0 = vertices['SW'].coordinate()
                x1,y1 = vertices['NE'].coordinate()
                
                xm = 0.5*(x0+x1)
                ym = 0.5*(y0+y1)     
                vertices['M'] = Vertex((xm,ym))
                
                edges[('SW','SE')] = parent.edges[((i,j),(i+1,j))] 
                edges[('SE','NE')] = parent.edges[((i+1,j),(i+1,j+1))]
                edges[('NE','NW')] = parent.edges[((i,j+1),(i+1,j+1))]
                edges[('NW','SW')] = parent.edges[((i,j),(i,j+1))]
                
            else:
                
                #
                # Parent not gridded
                #
                                                   
                inherited_vertices = \
                    {'SW': {'SW':'SW', 'SE':'S', 'NE':'M', 'NW':'W'},
                     'SE': {'SW':'S', 'SE':'SE', 'NE':'E', 'NW':'M'}, 
                     'NE': {'SW':'M', 'SE':'E', 'NE':'NE', 'NW':'N'}, 
                     'NW': {'SW':'W', 'SE':'M', 'NE':'N', 'NW':'NW'}}
                
                for cv,pv in inherited_vertices[position].items():
                    vertices[cv] = parent.vertices[pv]
                
                inherited_edges = \
                    {'SW': { ('SW','SE'):('SW','S'), ('SE','NE'):('M','S'), 
                             ('NE','NW'):('M','W'), ('NW','SW'):('W','SW'),
                             ('SW','NE'):('M','SW') }, 
                     'SE': { ('SW','SE'):('S','SE'), ('SE','NE'):('SE','E'),
                             ('NE','NW'):('M','E'), ('NW','SW'):('M','S'), 
                             ('NW','SE'):('M','SE') },
                     'NE': { ('SW','SE'):('M','E'), ('SE','NE'):('E','NE'), 
                             ('NE','NW'):('NE','N'), ('NW','SW'):('M','N'),
                             ('SW','NE'):('M','NE') }, 
                     'NW': { ('SW','SE'):('M','W'), ('SE','NE'):('M','N'), 
                             ('NE','NW'):('N','NW'), ('NW','SW'):('NW','W'),
                             ('NW','SE'):('M','NW') } }
                     
                for ce,pe in inherited_edges[position].items():
                    edges[ce] = parent.edges[pe]
            
            x0,y0 = vertices['SW'].coordinate()
            x1,y1 = vertices['NE'].coordinate()
            xm = 0.5*(x0+x1)
            ym = 0.5*(y0+y1)
            vertices['M'] = Vertex((xm,ym))        
            #
            # Neighboring Vertices and Edges 
            #
            opposite = {'N':'S', 'S':'N', 'W':'E', 'E':'W'}
            midv = {'N': (xm,y1), 'S':(xm,y0), 'W':(x0,ym), 'E':(x1,ym)}
            e_dir = {'N': [('NE','N'),('N','NW')], 
                     'S': [('SW','S'),('S','SE')],
                     'E': [('SE','E'),('E','NE')],
                     'W': [('NW','W'),('W','SW')] }                              
            for direction in ['N','S','E','W']:
                neighbor = self.find_neighbor(direction)
                if neighbor == None or neighbor.depth < self.depth:
                    #
                    # No/too big neighbor, specify vertices and edges
                    #
                    vertices[direction] = \
                        Vertex(midv[direction])
                    
                        
                    for edge_key in e_dir[direction]:
                        v1, v2 = edge_key
                        x0,y0 = vertices[v1].coordinate()
                        x1,y1 = vertices[v2].coordinate()
                        edges[edge_key] = Edge(vertices[v1],vertices[v2])
                            
                    if neighbor != None and neighbor.depth < self.depth-1:
                        #
                        # Enforce the 2-1 rule
                        # 
                        neighbor.split()
                            
                        
                elif neighbor.depth == self.depth:
                    #
                    # Neighbor on same level use neighboring vertices/edges
                    #            
                    vertices[direction] = \
                        neighbor.vertices[opposite[direction]]
                            
                    for edge_key in e_dir[direction]:
                        e0 = edge_key[0].replace(direction,opposite[direction])
                        e1 = edge_key[1].replace(direction,opposite[direction])
                        opp_edge_key = (e1,e0)
                        edges[edge_key] = neighbor.edges[opp_edge_key]
                else:
                    raise Exception('Cannot parse neighbor')
            #
            # New interior edges
            #             
            edges[('M','SW')] = Edge(vertices['M'],vertices['SW'])
            edges[('M','S')]  = Edge(vertices['M'],vertices['S'])
            edges[('M','SE')] = Edge(vertices['M'],vertices['SE'])
            edges[('M','E')]  = Edge(vertices['M'],vertices['E'])
            edges[('M','NE')] = Edge(vertices['M'],vertices['NE'])
            edges[('M','N')]  = Edge(vertices['M'],vertices['N'])
            edges[('M','NW')] = Edge(vertices['M'],vertices['NW'])
            edges[('M','W')]  = Edge(vertices['M'],vertices['W'])
            #
            # Possibly new diagonal edges
            #
            for edge_key in [('SW','NE'), ('NW','SE')]:
                if edges[edge_key] == None:
                    v1, v2 = edge_key
                    edges[edge_key] = Edge(vertices[v1],vertices[v2])
        #
        # Store vertices and edges
        #  
        self.vertices = vertices
        self.edges = edges
        
        
    def box(self):
        """
        Returns the coordinates of the cell's bounding box [x0,x1,y0,y1]
        """
        if self.type == 'ROOT' and self.grid_size is not None:
            nx, ny = self.grid_size
            x0, y0 = self.vertices[0,0].coordinate()
            x1, y1 = self.vertices[nx,ny].coordinate()
        else:
            x0, y0 = self.vertices['SW'].coordinate()
            x1, y1 = self.vertices['NE'].coordinate()
        return x0, x1, y0, y1
           
            
    def get_edges(self, pos=None):
        """
        Returns edge with a given position or all 
        """
        edge_dict = {'W':('NW','SW'),'E':('SE','NE'),'S':('SW','SE'),'N':('NE','NW')}   
        if pos == None:
            return [self.edges[edge_dict[key]] for key in ['W','E','S','N']]
        else:
            return self.edges[edge_dict[pos]] 
    
    
    def find_neighbor(self, direction):
        """
        Returns the deepest neighboring cell, whose depth is at most that of the
        given cell, or 'None' if there aren't any neighbors.
         
        Inputs: 
         
            direction: char, 'N'(north), 'S'(south), 'E'(east), or 'W'(west)
             
        Output: 
         
            neighboring cell
            
        """
        if self.parent == None:
            return None
        #
        # For cell in a MESH, do a brute force search (comparing vertices)
        #
        elif self.parent.type == 'ROOT' and self.parent.grid_size != None:
            m = self.parent
            nx, ny = m.grid_size
            i,j = self.position
            if direction == 'N':
                if j < ny-1:
                    return m.children[i,j+1]
                else:
                    return None
            elif direction == 'S':
                if j > 0:
                    return m.children[i,j-1]
                else:
                    return None
            elif direction == 'E':
                if i < nx-1:
                    return m.children[i+1,j]
                else:
                    return None
            elif direction == 'W':
                if i > 0:
                    return m.children[i-1,j]
                else:
                    return None 

        #
        # Non-ROOT cells 
        # 
        else:
            #
            # Check for neighbors interior to parent cell
            # 
            if direction == 'N':
                interior_neighbors_dict = {'SW': 'NW', 'SE': 'NE'}
            elif direction == 'S':
                interior_neighbors_dict = {'NW': 'SW', 'NE': 'SE'}
            elif direction == 'E':
                interior_neighbors_dict = {'SW': 'SE', 'NW': 'NE'}
            elif direction == 'W':
                interior_neighbors_dict = {'SE': 'SW', 'NE': 'NW'}
            else:
                print("Invalid direction. Use 'N', 'S', 'E', or 'W'.")
            
            if self.position in interior_neighbors_dict:
                neighbor_pos = interior_neighbors_dict[self.position]
                return self.parent.children[neighbor_pos]
            #
            # Check for (children of) parental neighbors
            #
            else:
                mu = self.parent.find_neighbor(direction)
                if mu == None or mu.type == 'LEAF':
                    return mu
                else:
                    #
                    # Reverse dictionary to get exterior neighbors
                    # 
                    exterior_neighbors_dict = \
                       {v: k for k, v in interior_neighbors_dict.items()}
                        
                    if self.position in exterior_neighbors_dict:
                        neighbor_pos = exterior_neighbors_dict[self.position]
                        return mu.children[neighbor_pos]                       

    '''
    def find_leaves(self, with_depth=False):
        """
        Returns a list of all 'LEAF' type sub-cells (and their depths) of a given cell 
        
        TODO: Move to Cell class
        """
        leaves = []
        if self.type == 'LEAF':
            if with_depth:
                leaves.append((self,self.depth))
            else:
                leaves.append(self)
        elif self.has_children():
            for child in self.children.values():
                leaves.extend(child.find_leaves(with_depth))    
        return leaves
=======
>>>>>>> branch 'branch1' of https://github.com/hvanwyk/quadmesh.git
    
   
    def find_cells_at_depth(self, depth):
        """
        Return a list of cells at a certain depth
        
        TODO: Is this necessary? 
        TODO: Move to Cell class
        """
        cells = []
        if self.depth == depth:
            cells.append(self)
        elif self.has_children():
            for child in self.children.values():
                cells.extend(child.find_cells_at_depth(depth))
        return cells
    '''       
        

    
    
    def contains_point(self, points):
        """
        Determine whether the given cell contains a point
        
        Input: 
        
            point: tuple (x,y), list of tuples, or (n,2) array
            
        Output: 
        
            contains_point: boolean array, True if cell contains point, 
            False otherwise
        
        
        Note: Points on the boundary between cells belong to both adjoining
            cells.
        """          
        xy = np.array(points)
        x_min, x_max, y_min, y_max = self.box()
        
        in_box = (x_min <= xy[:,0]) & (xy[:,0] <= x_max) & \
                 (y_min <= xy[:,1]) & (xy[:,1] <= y_max)
        return in_box
            

    
    def intersects_line_segment(self, line):
        """
        Determine whether cell intersects with a given line segment
        
        Input: 
        
            line: double, list of two tuples (x0,y0) and (x1,y1)
            
        Output:
        
            intersects: bool, true if line segment and quadcell intersect
            
        Modified: 06/04/2016
        """               
        #
        # Check whether line is contained in rectangle
        # 
        if self.contains_point(line[0]) and self.contains_point(line[1]):
            return True
        
        #
        # Check whether line intersects with any cell edge
        # 
        for edge in self.edges.values():
            if edge.intersects_line_segment(line):
                return True
            
        #
        # If function has not terminated yet, there is no intersection
        #     
        return False
    
               
    def locate_point(self, point):
        """
        Returns the smallest cell containing a given point or None if current 
        cell doesn't contain the point
        
        Input:
            
            point: tuple (x,y)
            
        Output:
            
            cell: smallest cell that contains (x,y)
                
        """
        # TESTME: locate_point
        
        if self.contains_point(point):
            if self.type == 'LEAF': 
                return self
            else:
                #
                # If cell has children, find the child containing the point and continue looking from there
                # 
                for child in self.children.values():
                    if child.contains_point(point):
                        return child.locate_point(point)                     
        else:
            return None    
    
    
    def normal(self, edge):
        """
        Return the cell's outward normal vector along edge
        """    
        xm,ym = self.vertices['M'].coordinate()
        v0,v1 = edge.vertices()
        x0,y0 = v0.coordinate(); x1 = v1.coordinate()[0]
        if np.abs(x0-x1) < 1e-12:
            #
            # Vertical 
            # 
            return np.sign(x0-xm)*np.array([1.,0.])
        else:
            #
            # Horizontal
            # 
            return np.sign(y0-ym)*np.array([0.,1.])
    
    
    def map_to_reference(self, x):
        """
        Map point to reference cell [0,1]^2
        
        Input:
        
            x: double, (n_points, dim) array of points in the physical cell
            
        Output:
        
            x_ref: double, (n_points, dim) array of points in the reference 
                cell.
        """            
        x0,x1,y0,y1 = self.box()
        x_ref = np.array([(x[:,0]-x0)/(x1-x0),
                          (x[:,1]-y0)/(y1-y0)]).T
        return x_ref
    
    
    def map_from_reference(self, x_ref):
        """
        Map point from reference cell [0,1]^2 to physical cell
        
        Inputs: 
        
            x_ref: double, (n_points, dim) array of points in the reference
                cell. 
                
        Output:
        
            x: double, (n_points, dim) array of points in the physical cell
        """
        x0,x1,y0,y1 = self.box()
        x = np.array([x0 + (x1-x0)*x_ref[:,0], 
                      y0 + (y1-y0)*x_ref[:,1]]).T
        return x
    
    
    def derivative_multiplier(self, derivative):
        """
        Deter
        """
        c = 1
        if derivative[0] in {1,2}:
            # 
            # There's a map and we're taking derivatives
            #
            x0,x1,y0,y1 = self.box()
            for i in derivative[1:]:
                if i==0:
                    c *= 1/(x1-x0)
                elif i==1:
                    c *= 1/(y1-y0)
        return c
     
    ''' 
    def mark(self, flag=None):
        """
        Mark QuadCell
        
        Inputs:
        
            flag: int, optional label used to mark cell
        """  
        if flag is None:
            self.__flags.add(True)
        else:
            self.__flags.add(flag)
           
        
    def unmark(self, flag=None, recursive=False):
        """
        Unmark QuadCell
        
        Inputs: 
        
            flag: label to be removed
        
            recursive: bool, also unmark all subcells
            
        TODO: Move to Cell class
        """
        #
        # Remove label from own list
        #
        if flag is None:
            # No flag specified -> delete all
            self.__flags.clear()
        else:
            # Remove specified flag (if present)
            if flag in self.__flags: self.__flags.remove(flag)
        
        #
        # Remove label from children if applicable   
        # 
        if recursive and self.has_children():
            for child in self.children.values():
                child.unmark(flag=flag, recursive=recursive)
                
 
         
    def is_marked(self,flag=None):
        """
        Check whether quadcell is marked
        
        Input: flag, label for QuadCell: usually one of the following:
            True (catchall), 'split' (split cell), 'count' (counting)
            
        TODO: Move to cell class
        """ 
        if flag is None:
            # No flag -> check whether set is empty
            if self.__flags:
                return True
            else:
                return False
        else:
            # Check wether given label is contained in quadcell's set
            return flag in self.__flags
    '''                 
                                
    def split(self):
        """
        Split cell into subcells
        """
        assert not self.has_children(), 'Cell is already split.'
        for pos in self.children.keys():
            self.children[pos] = QuadCell(parent=self, position=pos)        
    '''
    ============
    OLD VERSION
    ============    
    def split(self):
        """
        Split cell into subcells.

        """
        assert not self.has_children(), 'QuadCell has children and cannot be split.'
        if self.type == 'ROOT' and self.grid_size != None:
            #
            # ROOT cell's children may be stored in a grid 
            #
            nx, ny = self.grid_size
            cell_children = {}
            xmin, ymin = self.vertices['SW'].coordinate()
            xmax, ymax = self.vertices['NE'].coordinate()
            x = np.linspace(xmin, xmax, nx+1)
            y = np.linspace(ymin, ymax, ny+1)
            for i in range(nx):
                for j in range(ny):
                    if i == 0 and j == 0:
                        # Vertices
                        v_sw = Vertex((x[i]  ,y[j]  ))
                        v_se = Vertex((x[i+1],y[j]  ))
                        v_ne = Vertex((x[i+1],y[j+1]))
                        v_nw = Vertex((x[i]  ,y[j+1]))
                        
                        # Edges
                        e_w = Edge(v_sw, v_nw, parent=self)
                        e_e = Edge(v_se, v_ne, parent=self)
                        e_s = Edge(v_sw, v_se, parent=self)
                        e_n = Edge(v_nw, v_ne, parent=self)
                        
                    elif i > 0 and j == 0:
                        # Vertices
                        v_se = Vertex((x[i+1],y[j]  ))
                        v_ne = Vertex((x[i+1],y[j+1]))
                        v_sw = cell_children[i-1,j].vertices['SE']
                        v_nw = cell_children[i-1,j].vertices['NE']
                        
                        # Edges
                        e_w = cell_children[i-1,j].edges['E']
                        e_e = Edge(v_se, v_ne, parent=self)
                        e_s = Edge(v_sw, v_se, parent=self)
                        e_n = Edge(v_nw, v_ne, parent=self)
                        
                    elif i == 0 and j > 0:
                        # Vertices
                        v_ne = Vertex((x[i+1],y[j+1]))
                        v_nw = Vertex((x[i]  ,y[j+1]))
                        v_sw = cell_children[i,j-1].vertices['NW']
                        v_se = cell_children[i,j-1].vertices['NE']
                        
                        # Edges
                        e_w = Edge(v_sw, v_nw, parent=self)
                        e_e = Edge(v_se, v_ne, parent=self)
                        e_s = cell_children[i,j-1].edges['N']
                        e_n = Edge(v_nw, v_ne, parent=self)
                                            
                    elif i > 0 and j > 0:
                        # Vertices
                        v_ne = Vertex((x[i+1],y[j+1]))
                        v_nw = cell_children[i-1,j].vertices['NE']
                        v_sw = cell_children[i,j-1].vertices['NW']
                        v_se = cell_children[i,j-1].vertices['NE']
                        
                        # Edges
                        e_w = cell_children[i-1,j].edges['E']
                        e_e = Edge(v_se, v_ne, parent=self)
                        e_s = cell_children[i,j-1].edges['N']
                        e_n = Edge(v_nw, v_ne, parent=self)
                        
                    child_vertices = {'SW': v_sw, 'SE': v_se, \
                                      'NE': v_ne,'NW': v_nw}
                    child_edges = {'W':e_w, 'E':e_e, 'S':e_s, 'N':e_n}
                                        
                    child_position = (i,j)
                    cell_children[i,j] = QuadCell(vertices=child_vertices, \
                                              parent=self, edges=child_edges, \
                                              position=child_position)
            self.children = cell_children
        else: 
            if self.type == 'LEAF':    
                #
                # Reclassify LEAF cells to BRANCH (ROOTS remain as they are)
                #  
                self.type = 'BRANCH'
            #
            # Add cell vertices
            #
            x0, y0 = self.vertices['SW'].coordinate()
            x1, y1 = self.vertices['NE'].coordinate()
            hx = 0.5*(x1-x0)
            hy = 0.5*(y1-y0)
             
            if not 'M' in self.vertices:
                self.vertices['M'] = Vertex((x0 + hx, y0 + hy))        
            #
            # Add edge midpoints to parent
            # 
            mid_point = {'N': (x0 + hx, y1), 'S': (x0 + hx, y0), 
                         'W': (x0, y0 + hy), 'E': (x1, y0 + hy)}
            
            #
            # Add dictionary for edges
            #  
            directions = ['N', 'S', 'E', 'W']
            edge_dict = dict.fromkeys(directions)
            sub_edges = dict.fromkeys(['SW','SE','NE','NW'],edge_dict)
            
            opposite_direction = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}
            for direction in directions:
                #
                # Check wether we already have a record of this
                # MIDPOINT vertex
                #
                if not (direction in self.vertices):
                    neighbor = self.find_neighbor(direction)
                    opposite_dir = opposite_direction[direction]
                    if neighbor == None: 
                        #
                        # New vertex - add it only to self
                        # 
                        v_new =  Vertex(mid_point[direction])
                        self.vertices[direction] = v_new
                        
                        #
                        # New sub-edges - add them to dictionary
                        # 
                        for edge_key in sub_edges.keys():
                            if direction in list(edge_key):
                                sub_edges[edge_key][direction] = \
                                    Edge(self.vertices[direction], \
                                         self.vertices[edge_key])
                        
                    elif neighbor.type == 'LEAF':
                        #
                        # Neighbor has no children add new vertex to self and 
                        # neighbor.
                        #  
                        v_new =  Vertex(mid_point[direction])
                        self.vertices[direction] = v_new
                        neighbor.vertices[opposite_dir] = v_new 
                        
                        #
                        # Add new sub-edges to dictionary (same as above)
                        #
                        for edge_key in sub_edges.keys():
                            if direction in list(edge_key):
                                sub_edges[edge_key][direction] = \
                                    Edge(self.vertices[direction], \
                                         self.vertices[edge_key]) 
                    else:
                        #
                        # Vertex exists already - get it from neighoring Node
                        # 
                        self.vertices[direction] = \
                            neighbor.vertices[opposite_dir]
                        
                        #
                        # Edges exist already - get them from the neighbor    
                        # 
                        for edge_key in sub_edges.keys():
                            if direction in list(edge_key):
                                nb_ch_pos = edge_key.replace(direction,\
                                                 opposite_dir)
                                nb_child = neighbor.children[nb_ch_pos]
                                sub_edges[edge_key][direction] = \
                                    nb_child.edges[opposite_dir]
            #            
            # Add child cells
            # 
            sub_vertices = {'SW': ['SW', 'S', 'M', 'W'], 
                            'SE': ['S', 'SE', 'E', 'M'], 
                            'NE': ['M', 'E', 'NE', 'N'],
                            'NW': ['W', 'M', 'N', 'NW']}   
     
              
            for i in sub_vertices.keys():
                child_vertices = {}
                child_vertex_pos = ['SW', 'SE', 'NE', 'NW'] 
                for j in range(4):
                    child_vertices[child_vertex_pos[j]] = self.vertices[sub_vertices[i][j]] 
                child = QuadCell(child_vertices, parent=self, position=i)
                self.children[i] = child
    '''
                    
    '''  
    def merge(self):
        """
        Delete child nodes
        """
        #
        # Delete unnecessary vertices of neighbors
        # 
        opposite_direction = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}
        for direction in ['N','S','E','W']:
            neighbor = self.find_neighbor(direction)
            if neighbor==None:
                #
                # No neighbor on this side delete midpoint vertices
                # 
                del self.vertices[direction]
                
            elif not neighbor.has_children():
                #
                # Neighbouring cell has no children - delete edge midpoints of both
                # 
                del self.vertices[direction]
                op_direction = opposite_direction[direction]
                del neighbor.vertices[op_direction] 
        #
        # Delete all children
        # 
        self.children.clear()
        self.type = 'LEAF'
    '''

    '''
    =================================
    OBSOLETE: TREE IS ALwAYS BALANCED
    =================================
    def balance_tree(self):
        """
        Ensure that subcells of current cell conform to the 2:1 rule
        """
        leaves = self.find_leaves()
        leaf_dict = {'N': ['SE', 'SW'], 'S': ['NE', 'NW'],
                     'E': ['NW', 'SW'], 'W': ['NE', 'SE']} 

        while len(leaves) > 0:
            leaf = leaves.pop()
            flag = False
            #
            # Check if leaf needs to be split
            # 
            for direction in ['N', 'S', 'E', 'W']:
                nb = leaf.find_neighbor(direction) 
                if nb == None:
                    pass
                elif nb.type == 'LEAF':
                    pass
                else:
                    for pos in leaf_dict[direction]:
                        #
                        # If neighor's children nearest to you aren't LEAVES,
                        # then split and add children to list of leaves! 
                        #
                        if nb.children[pos].type != 'LEAF':
                            leaf.mark()
                            leaf.split()
                            for child in leaf.children.values():
                                child.mark_support_cell()
                                leaves.append(child)
                            
                            #
                            # Check if there are any neighbors that should 
                            # now also be split.
                            #  
                            for direction in ['N', 'S', 'E', 'W']:
                                nb = leaf.find_neighbor(direction)
                                if nb != None and nb.depth < leaf.depth:
                                    leaves.append(nb)
                                
                            flag = True
                            break
                if flag:
                    break
    '''
                
        
    def pos2id(self, pos):
        """ 
        Convert position to index: 'SW' -> 0, 'SE' -> 1, 'NW' -> 2, 'NE' -> 3 
        """
        if type(pos) is tuple:
            assert len(pos) == 2, 'Expecting a tuple of integers.'
            return pos 
        elif type(pos) is int and 0 <= pos and pos <= 3:
            return pos
        elif pos in ['SW','SE','NW','NE']:
            pos_to_id = {'SW': 0, 'SE': 1, 'NW': 2, 'NE': 3}
            return pos_to_id[pos]
        else:
            raise Exception('Unidentified format for position.')
    
    
    def id2pos(self, idx):
        """
        Convert index to position: 0 -> 'SW', 1 -> 'SE', 2 -> 'NW', 3 -> 'NE'
        """
        if type(idx) is tuple:
            #
            # Grid index and positions coincide
            # 
            assert len(idx) == 2, 'Expecting a tuple of integers.'
            return idx
        
        elif idx in ['SW', 'SE', 'NW', 'NE']:
            #
            # Input is already a position
            # 
            return idx
        elif idx in [0,1,2,3]:
            #
            # Convert
            # 
            id_to_pos = {0: 'SW', 1: 'SE', 2: 'NW', 3: 'NE'}
            return id_to_pos[idx]
        else:
            raise Exception('Unrecognized format.')
        
               
class Edge(object):
    '''
    Description: Edge object in quadtree
    
    
    Attributes:
    
    v_begin: Vertex, vertex where edge begins
    
    v_end: Vertex, vertex where edge ends
    
    children: Edge, list of Edge's between [v_begin,v_middle], and between 
              [v_middle,v_end].

    incident_face: Cell, lying to the left of the edge
    
    on_boundary: bool, True if edge lies on boundary 
    
    
    Methods:
    
    '''
    
    def __init__(self, v1, v2, parent=None):
        """
        Description: Constructor
        
        Inputs: 
        
            v1, v2: Vertex, two vertices that define the edge
            
            parent: One QuadCell/TriCell containing the edge (not necessary?)
            
            on_boundary: Either None (if not set) or Boolean (True if edge lies on boundary)
        """
        self.__vertices = set([v1,v2])
        
        dim = len(v1.coordinate())
        if dim == 1:
            x0, = v1.coordinate()
            x1, = v2.coordinate()
            nnorm = np.abs(x1-x0)
        elif dim == 2:
            x0,y0 = v1.coordinate()
            x1,y1 = v2.coordinate()
            nnorm = np.sqrt((y1-y0)**2+(x1-x0)**2)
        self.__length = nnorm
        self.__flags = set()
        self.__parent = parent 
     
     
    def info(self):
        """
        Display information about edge
        """
        v1, v2 = self.vertices()
        print('{0:10}: {1} --> {2}'.format('Vertices', v1.coordinate(), v2.coordinate()))
        #print('{0:10}: {1}'.format('Length', self.length()))
    
    
    def box(self):
        """
        Return the edge endpoint coordinates x0,y0,x1,y1, where 
        edge: (x0,y0) --> (x1,y1) 
        To ensure consistency, the points are sorted, first in the x-component
        then in the y-component.
        """    
        verts = self.vertex_coordinates()
        verts.sort()
        x0,y0 = verts[0]
        x1,y1 = verts[1]
        return x0,x1,y0,y1
        
        
    def mark(self, flag=None):
        """
        Mark Edge
        
        Inputs:
        
            flag: optional label used to mark edge
        """  
        if flag is None:
            self.__flags.add(True)
        else:
            self.__flags.add(flag)
            
        
    def unmark(self, flag=None):
        """
        Unmark Edge
        
        Inputs: 
        
            flag: label to be removed
            
        """
        if flag is None:
            # No flag specified -> delete all
            self.__flags.clear()
        else:
            # Remove specified flag (if present)
            if flag in self.__flags: self.__flags.remove(flag)         
 
         
    def is_marked(self,flag=None):
        """
        Check whether Edge is marked
        
        Input: flag, label for QuadCell: usually one of the following:
            True (catchall), 'split' (split cell), 'count' (counting)
        """ 
        if flag is None:
            # No flag -> check whether set is empty
            if self.__flags:
                return True
            else:
                return False
        else:
            # Check wether given label is contained in quadcell's set
            return flag in self.__flags     
      
       
    def vertices(self):
        """
        Returns the set of vertices
        """
        return self.__vertices

    
    def vertex_coordinates(self):
        """
        Returns the vertex coordinates as list of tuples
        """        
        v1,v2 = self.__vertices
        return [v1.coordinate(), v2.coordinate()]

        
    def length(self):
        """
        Returns the length of the edge
        """
        return self.__length
    
    
    def intersects_line_segment(self, line):
        """
        Determine whether the edge intersects with a given line segment
        
        Input: 
        
            line: double, list of two tuples
            
        Output:
        
            boolean, true if intersection, false otherwise.
        """        
        # Express edge as p + t*r, t in [0,1]
        v1,v2 = self.vertices()
        p = np.array(v1.coordinate())
        r = np.array(v2.coordinate()) - p
        
        # Express line as q + u*s, u in [0,1] 
        q = np.array(line[0]) 
        s = np.array(line[1]) - q
        
        if abs(np.cross(r,s)) < 1e-14:
            #
            # Lines are parallel
            # 
            if abs(np.cross(q-p,r)) < 1e-14:
                #
                # Lines are collinear
                # 
                t0 = np.dot(q-p,r)/np.dot(r,r)
                t1 = t0 + np.dot(s,r)/np.dot(r,r)
                
                if (max(t0,t1) >= 0) and (min(t0,t1) <= 1):
                    # 
                    # Line segments overlap
                    # 
                    return True
                else:
                    return False
            else:
                #
                # Lines not collinear
                # 
                return False 
        else:
            #
            # Lines not parallel
            #   
            t = np.cross(q-p,s)/np.cross(r,s)
            u = np.cross(p-q,r)/np.cross(s,r)
            
            if 0 <= t <= 1 and 0 <= u <= 1:
                #
                # Line segments meet
                # 
                return True
            else:
                return False 
         
            
class Vertex(object):
    """
    Description:
    
    Attributes:
    
        coordinate: double, tuple (x,y)
        
        flag: boolean
    
    Methods: 
    """


    def __init__(self, coordinate):
        """
        Description: Constructor
        
        Inputs: 
        
            coordinate: double tuple, x- and y- coordinates of vertex
            
            on_boundary: boolean, true if on boundary
              
        """
        if isinstance(coordinate, numbers.Real):
            #
            # Coordinate passed as a real number 1D
            # 
            dim = 1
            coordinate = (coordinate,)  # recast coordinate as tuple
        elif type(coordinate) is tuple:
            #
            # Coordinate passed as a tuple
            # 
            dim = len(coordinate)
            assert dim <= 2, 'Only 1D and 2D meshes supported.'
        else:
            raise Exception('Enter coordinate as a number or a tuple.')
        self.__coordinate = coordinate
        self.__flags = set()
        self.__dim = dim
    
    def coordinate(self):
        """
        Return coordinate tuple
        """
        return self.__coordinate
    
    
    def dim(self):
        """
        Return the dimension of the vertex
        """
        return self.__dim
        
    
    def mark(self, flag=None):
        """
        Mark Vertex
        
        Inputs:
        
            flag: int, optional label
        """  
        if flag is None:
            self.__flags.add(True)
        else:
            self.__flags.add(flag)
            
        
    def unmark(self, flag=None):
        """
        Unmark Vertex
        
        Inputs: 
        
            flag: label to be removed

        """
        #
        # Remove label from own list
        #
        if flag is None:
            # No flag specified -> delete all
            self.__flags.clear()
        else:
            # Remove specified flag (if present)
            if flag in self.__flags: self.__flags.remove(flag)
        
         
    def is_marked(self,flag=None):
        """
        Check whether Vertex is marked
        
        Input: flag, label for QuadCell: usually one of the following:
            True (catchall), 'split' (split cell), 'count' (counting)
        """ 
        if flag is None:
            # No flag -> check whether set is empty
            if self.__flags:
                return True
            else:
                return False
        else:
            # Check wether given label is contained in quadcell's set
            return flag in self.__flags
