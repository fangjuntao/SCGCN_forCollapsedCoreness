# encoding:utf-8
import os
import networkx as nx
import numpy as np

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
    # print('number of nodes in graph:', G.number_of_nodes())
    # print('number of edges in graph:', G.number_of_edges())
    file.close()
    return G


if __name__ == '__main__':

    fname = "test.txt"

    graph = load_graph(fname)  # 读data，存为图（nx.Graph()）
    graph.remove_edges_from(graph.selfloop_edges())  # 去除自环（实际上 load_graph(fname)已经有这步操作了）
    core = nx.k_core(graph, 1)  # coreness问题让k=1即可
    # print("# nodes in %d core: %d" % (k, core.number_of_nodes()))
    # print("# edges in %d core: %d" % (k, core.number_of_edges()))
    gname ="test2.txt"
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



