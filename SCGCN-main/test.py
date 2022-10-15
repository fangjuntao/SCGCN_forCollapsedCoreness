# encoding:utf-8
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os


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
        Edges.append((src, dst, {"weight": weight}))

    G = nx.Graph()
    # G = nx.DiGraph()
    G.add_edges_from(Edges)
    print('# nodes in core:', G.number_of_nodes())
    print('# edges in core:', G.number_of_edges())
    file.close()
    return G


def calFollower(gname, v):
    core = load_tmp_core(gname);
    # nx.draw(core)
    #
    # plt.show()
    coreness1 = nx.core_number(core);

    follower = 0
    core.remove_node(v)  # 删除节点v 以及边
    # nx.draw(core)
    #
    # plt.show()
    coreness2 = nx.core_number(core);
    for k in coreness2.items():
        nodeNum1 = k[0];
        nodeNum2 = k[0];
        if coreness1[nodeNum1] > coreness2[nodeNum2]:
                follower = follower + 1
        else:
                pass

    return follower


if __name__ == "__main__":
    gname = "/mnt/SCGCN/SCGCN-main/data/CollapsedCoreness/data2.txt"
    a = calFollower(gname, 2)
    print a ;