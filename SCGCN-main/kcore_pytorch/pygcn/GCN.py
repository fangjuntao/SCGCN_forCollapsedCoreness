import torch.nn as nn
import torch.nn.functional as F
from pygcn.layers import GraphConvolution, FC, Attention
# from pygcn.layers import FC, Attention
#
# from torch_geometric.nn import GCNConv

class GCN(nn.Module):
    def __init__(self, nfeat, nhid, nclass, dropout):
        super(GCN, self).__init__()
        #
        # self.gc1 = GCNConv(nfeat, nhid)
        # self.gc2 = GCNConv(nhid, nhid)
        # self.gc3 = GCNConv(nhid, nclass)



        self.gc1 = GraphConvolution(nfeat, nhid)
        self.gc2 = GraphConvolution(nhid, nhid)
        self.gc3 = GraphConvolution(nhid, nclass)
        self.dropout = dropout

    def forward(self, x, edge_index):
        x = F.relu(self.gc1(x, edge_index))
        x = F.dropout(x, self.dropout, training=self.training)
        x = F.relu(self.gc2(x, edge_index))
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.gc3(x, edge_index)
        return F.log_softmax(x, dim = 1)
        #return F.sigmoid(x) #F.log_softmax(x, dim=1)


"""
class GCNAtt(nn.Module):
    def __init__(self, nfeat, nhid, nclass, final_class, dropout):
        super(GCNAtt, self).__init__()

        self.nhid = nhid
        self.nclass = nclass
        self.gc1 = GraphConvolution(nfeat, nhid)
        self.gc2 = GraphConvolution(nhid, nclass)
        self.att_layer = Attention(n_expert = nhid, n_hidden = nhid, v_hidden = nclass)
        self.fc = FC(nhid * nclass, final_class)
        self.dropout = dropout

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.gc2(x, adj)
        att = self.att_layer(x)
        x = att.matmul(x)
        x = x.reshape(x.shape[0], self.nhid * self.nclass) # x = x.squeeze()
        x = self.fc(x)
        return F.log_softmax(x)
        #return F.sigmoid(x) #F.log_softmax(x, dim=1)
"""

class GCNAtt(nn.Module):
    def __init__(self, nfeat, n_hid1, n_hid2, n_expert, att_hid, final_class, dropout):
        super(GCNAtt, self).__init__()

        self.n_expert = n_expert
        self.n_hid2 = n_hid2
        self.gc1 = GraphConvolution(nfeat, n_hid1)
        self.gc2 = GraphConvolution(n_hid1, n_hid2)
        self.att_layer = Attention(n_expert = n_expert, n_hidden = att_hid, v_hidden = n_hid2)
        #self.fc = FC(n_expert * n_hid2, final_class)
        self.fc1 = FC(n_expert * n_hid2, att_hid)
        self.fc2 = FC(att_hid, final_class)
        self.dropout = dropout

    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.gc2(x, adj)
        att = self.att_layer(x)
        x = att.matmul(x)
        x = x.reshape(x.shape[0], self.n_expert * self.n_hid2) 
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim = 1)
        #return F.sigmoid(x) #F.log_softmax(x, dim=1)
