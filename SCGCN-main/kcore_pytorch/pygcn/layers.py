import math

import torch
import torch.nn.functional as F
from torch.nn.parameter import Parameter
from torch.nn.modules.module import Module


class GraphConvolution(Module):
    """
    Simple GCN layer, similar to https://arxiv.org/abs/1609.02907
    """

    def __init__(self, in_features, out_features, bias=True):
        super(GraphConvolution, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.weight.size(1))
        self.weight.data.uniform_(-stdv, stdv)
        if self.bias is not None:
            self.bias.data.uniform_(-stdv, stdv)

    def forward(self, input, adj):
        support = input.matmul(self.weight)
        output = adj.matmul(support)
        #support = torch.mm(input, self.weight)
        #output = torch.spmm(adj, support)
        if self.bias is not None:
            return output + self.bias
        else:
            return output

    def __repr__(self):
        return self.__class__.__name__ + ' (' \
               + str(self.in_features) + ' -> ' \
               + str(self.out_features) + ')'

class FC(Module):
    def __init__(self, in_ch, out_ch):
        super(FC, self).__init__()
        self.fc = torch.nn.Linear(in_ch, out_ch)

    def forward(self, x):
        return self.fc(x)


class Attention(Module):
    """
    Simple Attention layer
    """
    def __init__(self, n_expert, n_hidden, v_hidden):
        super(Attention, self).__init__()
        self.n_expert = n_expert
        self.n_hidden = n_hidden
        self.v_hidden = v_hidden
        self.w1 = Parameter(torch.FloatTensor(n_hidden, v_hidden))
        self.w2 = Parameter(torch.FloatTensor(n_expert, n_hidden))
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1. / math.sqrt(self.w1.size(1))
        self.w1.data.uniform_(-stdv, stdv)
        stdv = 1. / math.sqrt(self.w2.size(1))
        self.w2.data.uniform_(-stdv, stdv)

    def forward(self, x):
        support = F.tanh(self.w1.matmul(x.permute(0,2,1)))
        output = F.softmax(self.w2.matmul(support), dim = 2)
        return output
