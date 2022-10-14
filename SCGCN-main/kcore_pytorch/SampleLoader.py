#encoding:utf-8
import numpy as np
import networkx as nx
import os
import torch
import random
import kcore
import itertools
from copy import deepcopy
from sets import Set
from math import log
import scipy.sparse as sp
from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader
from ctypes import *

import os

glist= cdll.LoadLibrary("/mnt/SCGCN/SCGCN-main/shared_forCollapsedCoreness/example2.so")


def generate_features(core, n_node):
	feat1 = np.zeros(shape = (n_node,))
	feat2 = np.zeros(shape = (n_node,))
	feat_cc = np.zeros(shape = (n_node,))
	core_num = nx.core_number(core)   # core_number: the largest k_core which is included the node
	core_deg = dict(core.degree())    # node degree
	core_cc = nx.clustering(core) # the local clustering coefficient
	feat_cc[list(core_cc.keys())] = list(core_cc.values()) # local cluster coefficient of each node 
	feat1[list(core_num.keys())] = list(core_num.values()) # core number of each node
	feat2[list(core_deg.keys())] = list(core_deg.values()) # degree of each node
	coremx = nx.adjacency_matrix(core).todense()
	all_core_num = coremx * np.diag(list(core_num.values()))
	feat3 = np.sort(all_core_num)[:, -5:] # top 5 largest core number of neighbors
	feats = np.vstack((feat1, feat2, feat_cc)).transpose()
	feats = np.hstack((feats, feat3))
	n_feats = feats.shape[1]
	return feats, n_feats

class SampleDataset(Dataset):
	def __init__(self, n_classes, n_node, non_dominated, X_norm, 
		extra_feats, ef, G, set_size, k, batch_size):
		'''
		n_clases: number of predict classes 
		n_node: number of nodes of graph
		non_dominated:  list (index: class id, value: non_dominated node id)
		X_norm: to compute sample probability
		extra_feats: extra features on nodes generated by 'generate_features'
		ef: whether or not extra_feats is available
		G: core (c++ object)
		set_size: b
		'''
		self.n_classes = n_classes
		self.n_node = n_node
		self.non_dominated = np.array(non_dominated)
		self.X_norm = X_norm
		self.extra_feats = extra_feats # numpy ndarray dim: n_node * n_feats
		self.ef = ef
		self.G = G
		self.set_size = set_size
		self.k = k
		self.batch_size = batch_size
		self.p = X_norm / float(np.sum(X_norm))


	def __getitem__(self, index):
		s_size = random.randint(3, self.set_size - 1)
		idx = np.random.choice(self.n_classes, size= s_size, replace = False, p=self.p) 
		x = np.zeros((self.n_node, 1), dtype = np.float32)
		g_idx = self.non_dominated[idx]
		x[g_idx] = 1  # remap to the graph id
		if self.ef > 0:
			x = np.hstack((x, self.extra_feats))
			x = torch.FloatTensor(x)
		y = np.array(self.G.KCoreLabelGeneration2(self.k, idx))
		weight = y
		w = np.min(y).reshape((1,))
		y = y - w + 1
		y = y.astype(np.float32) / np.sum(y)
		#print(x.shape, y.shape)
		return x, weight, y #  return (features, weight), label

	def __len__(self):
		return self.batch_size


def load_graph(fname):
	file = open(fname)
	Edges = []
	node_dict = {}
	node_cnt = 0
	for line in file:
		if line.strip().startswith("#"):
			continue
		src = int(line.strip().split()[0])
		if src not in node_dict:
			node_dict[src] = node_cnt
			node_cnt += 1
		dst = int(line.strip().split()[1])
		if dst not in node_dict:
			node_dict[dst] = node_cnt
			node_cnt += 1
		weight = np.random.random_sample()
		Edges.append((node_dict[src], node_dict[dst], {"weight": weight}))

	G = nx.Graph()
	G.add_edges_from(Edges)
	G.remove_edges_from(G.selfloop_edges())
	print('number of nodes in graph:', G.number_of_nodes())
	print('number of edges in graph:', G.number_of_edges())
	file.close()
	return G

def load_tmp_core(fname):
	file = open(fname)
	Edges = []
	node_dict = {}
	node_cnt = 0
	line_cnt = 0
	for line in file:
		line_cnt += 1
		if line_cnt == 1:
			continue
		src = int(line.strip().split()[0])
		if src not in node_dict:
			node_dict[src] = node_cnt
			node_cnt += 1
		dst = int(line.strip().split()[1])
		if dst not in node_dict:
			node_dict[dst] = node_cnt
			node_cnt += 1
		weight = np.random.random_sample()
		Edges.append((node_dict[src], node_dict[dst], {"weight": weight}))

	G = nx.Graph()
	G.add_edges_from(Edges)
	print('# nodes in core:', G.number_of_nodes())
	print('# edges in core:', G.number_of_edges())
	file.close()
	return G

def extract_kcore(input_folder, k):
	fname = os.path.join(input_folder, "graph.txt")
	graph = load_graph(fname)  #读data，存为图（nx.Graph()）
	graph.remove_edges_from(graph.selfloop_edges())  #去除自环（实际上 load_graph(fname)已经有这步操作了）
	core = nx.k_core(graph, k)   
	print("# nodes in %d core: %d"%(k, core.number_of_nodes()))
	print("# edges in %d core: %d"%(k, core.number_of_edges()))
	gname = os.path.join(input_folder, "temp_core_" + str(k) + ".txt")
	node_dict = {}
	node_cnt = 0
	
	with open(gname, "w") as file:
		file.writelines(str(core.number_of_nodes()) + '\t' + str(core.number_of_edges()) + '\n')
		for edge in core.edges():
			src, dst = str(edge[0]), str(edge[1])
			if src not in node_dict:
				node_dict[src] = node_cnt
				node_cnt += 1
			if dst not in node_dict:
				node_dict[dst] = node_cnt
				node_cnt += 1
			file.writelines(str(node_dict[src]) + '\t' + str(node_dict[dst]) + '\n')

def data_preprocessing(gname, k, load_traindata=True):
	core = load_tmp_core(gname)
	
	A = nx.adjacency_matrix(core).todense()
	A = np.array(A)
	B = A.tolist()
	GLIST = glist.GLIST(core.number_of_nodes())
	GLIST.ComputeCore(B,True,)
	Y_train = A.astype(np.float32)
	deg_norm = np.sum(Y_train, axis = 0)
	G = kcore.Graph()
	G.loadUndirGraph(gname) # load the c++ graph object ,将core用C++存储
	

	X_norm = np.array(G.KCoreCollapseDominate(k)) # list
	non_dominated = G.getUnDominated() # list
	n_classes = len(non_dominated)
	def to_nondomin_dict(non_dominated): # create dict: graph node id --> class idx
		nondomin_dict = {}
		cnt = 0
		for u in non_dominated:
			nondomin_dict[u] = cnt
			cnt += 1
		return nondomin_dict
	nondomin_dict = to_nondomin_dict(non_dominated) 
	deg_norm = np.array(deg_norm[non_dominated])
	return (X_norm, deg_norm, n_classes, non_dominated, nondomin_dict, core, G)

def build_dataset(input_folder, k, load_traindata=True):
	gname = os.path.join(input_folder, "temp_core_" + str(k) + ".txt")
	core_exists = os.path.isfile(gname)
	if not core_exists: # if not have the core file, compute it on the fly
	  extract_kcore(input_folder, k)
	(X_norm, deg_norm, n_classes, non_dominated, nondomin_dict, core, G) = data_preprocessing(gname, k, load_traindata)
	
	return (deg_norm, n_classes, non_dominated, nondomin_dict, core, G) 

def build_testset(input_folder, k):
	gname = os.path.join(input_folder, "temp_core_" + str(k) + ".txt")
	(X_norm, _, n_classes, non_dominated, nondomin_dict, core, G) = data_preprocessing(gname, k, True)
	return (X_norm, n_classes, non_dominated, nondomin_dict, core, G)


def generate_adjmx(graph, normalization):
	adj_normalizer = fetch_normalization(normalization)
	adj = nx.to_scipy_sparse_matrix(graph) 
	adj = adj_normalizer(adj).todense()
	return adj

def sparse_mx_to_torch_sparse_tensor(sparse_mx):
	"""Convert a scipy sparse matrix to a torch sparse tensor."""
	sparse_mx = sparse_mx.tocoo().astype(np.float32)
	indices = torch.from_numpy(
		np.vstack((sparse_mx.row, sparse_mx.col)).astype(np.int64))
	values = torch.from_numpy(sparse_mx.data)
	shape = torch.Size(sparse_mx.shape)
	return torch.sparse.FloatTensor(indices, values, shape)



def normalized_laplacian(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv_sqrt = np.power(row_sum, -0.5).flatten()
   d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
   d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
   return (sp.eye(adj.shape[0]) - d_mat_inv_sqrt.dot(adj).dot(d_mat_inv_sqrt)).tocoo()


def laplacian(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1)).flatten()
   d_mat = sp.diags(row_sum)
   return (d_mat - adj).tocoo()


def gcn(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv_sqrt = np.power(row_sum, -0.5).flatten()
   d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
   d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
   return (sp.eye(adj.shape[0]) + d_mat_inv_sqrt.dot(adj).dot(d_mat_inv_sqrt)).tocoo()


def aug_normalized_adjacency(adj):
   adj = adj + sp.eye(adj.shape[0])
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv_sqrt = np.power(row_sum, -0.5).flatten()
   d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
   d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
   return d_mat_inv_sqrt.dot(adj).dot(d_mat_inv_sqrt).tocoo()

def bingge_norm_adjacency(adj):
   adj = adj + sp.eye(adj.shape[0])
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv_sqrt = np.power(row_sum, -0.5).flatten()
   d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
   d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
   return (d_mat_inv_sqrt.dot(adj).dot(d_mat_inv_sqrt) +  sp.eye(adj.shape[0])).tocoo()

def normalized_adjacency(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv_sqrt = np.power(row_sum, -0.5).flatten()
   d_inv_sqrt[np.isinf(d_inv_sqrt)] = 0.
   d_mat_inv_sqrt = sp.diags(d_inv_sqrt)
   return (d_mat_inv_sqrt.dot(adj).dot(d_mat_inv_sqrt)).tocoo()

def random_walk_laplacian(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv = np.power(row_sum, -1.0).flatten()
   d_mat = sp.diags(d_inv)
   return (sp.eye(adj.shape[0]) - d_mat.dot(adj)).tocoo()


def aug_random_walk(adj):
   adj = adj + sp.eye(adj.shape[0])
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv = np.power(row_sum, -1.0).flatten()
   d_mat = sp.diags(d_inv)
   return (d_mat.dot(adj)).tocoo()

def random_walk(adj):
   adj = sp.coo_matrix(adj)
   row_sum = np.array(adj.sum(1))
   d_inv = np.power(row_sum, -1.0).flatten()
   d_mat = sp.diags(d_inv)
   return d_mat.dot(adj).tocoo()

def no_norm(adj):
   adj = sp.coo_matrix(adj)
   return adj

def fetch_normalization(type):
   switcher = {
	   'NormLap': normalized_laplacian,  # A' = I - D^-1/2 * A * D^-1/2
	   'Lap': laplacian,  # A' = D - A
	   'RWalkLap': random_walk_laplacian,  # A' = I - D^-1 * A
	   'FirstOrderGCN': gcn,   # A' = I + D^-1/2 * A * D^-1/2
	   'AugNormAdj': aug_normalized_adjacency,  # A' = (D + I)^-1/2 * ( A + I ) * (D + I)^-1/2
	   'BingGeNormAdj': bingge_norm_adjacency, # A' = I + (D + I)^-1/2 * (A + I) * (D + I)^-1/2
	   'NormAdj': normalized_adjacency,  # D^-1/2 * A * D^-1/2
	   'RWalk': random_walk,  # A' = D^-1*A
	   'AugRWalk': aug_random_walk,  # A' = (D + I)^-1*(A + I)
	   'NoNorm': no_norm, # A' = A
   }
   func = switcher.get(type, lambda: "Invalid normalization technique.")
   return func

def row_normalize(mx):
	"""Row-normalize sparse matrix"""
	rowsum = np.array(mx.sum(1))
	r_inv = np.power(rowsum, -1).flatten()
	r_inv[np.isinf(r_inv)] = 0.
	r_mat_inv = sp.diags(r_inv)
	mx = r_mat_inv.dot(mx)
	return mx
