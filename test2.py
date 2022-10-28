# encoding:utf-8
import os
import networkx as nx
import numpy as np
# 处理数据文件使得其为不含重边以及不含自环的文件,以及删除没有存在的点的边

if __name__ == '__main__':

    edge_fname = "test_edge.txt"
    edgeFile = open(edge_fname)
    user_fname = "test_user.txt"
    userFile = open(user_fname)
    userSet ={"#"}
    gname ="edges_result.txt"
    for line in userFile:
        user_id = int(line.strip().split()[0])
        userSet.add(user_id)
    print len(userSet)

    edges = []
    for line in edgeFile:
        src_id = int(line.strip().split()[0])
        dst_id = int(line.strip().split()[1])
        edge= []
        if src_id in userSet and dst_id in userSet:
                edge.append(src_id)
                edge.append(dst_id)
        else:
            print "!!!!"
            pass

        edges.append(edge)
        A = np.array(edges)
    print A.shape

    dict_record ={}
    with open(gname, "w") as file:
        for edge in edges:
            src, dst = str(edge[0]), str(edge[1])
            if int(src) == int(dst):
                pass
            else:

                str1 = src+"_"+dst
                str2 = dst+"_"+src
                if dict_record.has_key(str1) or dict_record.has_key(str2):
                    pass
                else:
                    file.writelines(str(src) + '\t' + str(dst) + '\n')
                    dict_record[str1] = 1



