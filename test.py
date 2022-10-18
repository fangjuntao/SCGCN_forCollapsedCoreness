# encoding:utf-8
from multiprocessing import Pool
import numpy as np

# def f(x):
#     return x * x
#

if __name__ == '__main__':
    # p = Pool(5)  # 创建有5个进程的进程池
    # print(p.map(f, [1, 2, 3]))  # 将f函数的操作给进程池
    dict1 = {'name': 1,
            'age': 1,
            'sex': 2}
    dict2 = {'name': 1,
            'age': 2,
            'sex': 3}
    coreness1 = np.array(list(dict1.values()))
    coreness2 = np.array(list(dict2.values()))
    a  = np.sum(coreness1-coreness2)
    print  a

