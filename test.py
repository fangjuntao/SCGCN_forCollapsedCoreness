# encoding:utf-8

import networkx
import matplotlib.pyplot as plt
df1 = open("test.txt","r")
ncols1 = len(next(df1).split("\n"))
g = networkx.Graph()
edge_lable=[]
for eline in df1:
    eline = eline.strip("\n")
    earray = eline.split(" ")
    g.add_edge(earray[0], earray[1])
df1.close()


networkx.draw(g)
plt.show()

