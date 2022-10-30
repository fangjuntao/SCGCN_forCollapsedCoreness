# encoding:utf-8

import networkx
import  numpy as np
import matplotlib.pyplot as plt
# df1 = open("test_edge.txt", "r")
# ncols1 = len(next(df1).split("\n"))
# g = networkx.Graph()
# edge_lable=[]
# for eline in df1:
#     eline = eline.strip("\n")
#     earray = eline.split(" ")
#     g.add_edge(earray[0], earray[1])
# df1.close()
#
#
# networkx.draw(g)
# plt.show()

weight = np.random.random_sample()
weight = np.around(weight, 4)
A = np.zeros((325729,325729), dtype=np.float32)
