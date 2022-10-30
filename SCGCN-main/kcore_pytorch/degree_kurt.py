import numpy as np
import networkx as nx
from scipy.stats import kurtosis
from argparse import ArgumentParser, FileType, ArgumentDefaultsHelpFormatter

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
	print('number of nodes:', G.number_of_nodes())
	print('number of edges:', G.number_of_edges())
	file.close()
	return G

def main(fname):
	G = load_graph(fname)
	deg = list(G.degree().values())
	print("the kurtosis is:", kurtosis(deg, fisher = False))


if __name__ == "__main__":
	parser = ArgumentParser("dnn", formatter_class=ArgumentDefaultsHelpFormatter, conflict_handler="resolve")
	#Required 
	parser.add_argument("--fname", default="data.txt.txt/wv", help="Input data.txt.txt folder")
	args = parser.parse_args() 
	print(args)
	fname = args.fname
	main(fname)