#! usr/bin/python
# encoding:utf-8
import time

from argparse import ArgumentParser, FileType, ArgumentDefaultsHelpFormatter

import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import _utils
from pygcn import GCN, GCNAtt
from earlystopping import EarlyStopping
from SampleLoader import *
from ctypes import *

import os
import sys


os.environ["CUDA_VISIBLE_DEVICES"] = "1"

def get_lr(optimizer):
    for param_group in optimizer.param_groups:
        return param_group['lr']


def cross_entropy(labels, outputs, weights):
    '''
    cross entropy loss with soft labels
    '''
    loss = torch.mean(torch.sum(weights * (-labels * outputs), 1))
    return loss


def validate(args, model, adj, val_data):
    '''
    model validation
    criterion: validation loss function
    '''
    data, weights, labels = val_data[0], val_data[1], val_data[2]
    if args.cuda:
        model.cuda()
        adj = adj.cuda()
        data, weights, labels = data.cuda(), weights.cuda(), labels.cuda()
    model.eval()
    criterion = torch.nn.MSELoss()
    outputs = model(data, adj)
    outputs = outputs.squeeze()
    outputs = torch.tensor(outputs, dtype=torch.float32)
    labels =torch.tensor(labels, dtype=torch.float32)
    val_loss = criterion(outputs, labels)
    return val_loss


def train(args, model, dataloader, adj, criterion, optimizer, scheduler, val_data, ini_step=0):
    '''
    model: model to train
    feats: node features
    criterion: defined loss(unused)
    optimizer: defined optimizer
    ini_step: pretrained steps of the model
    '''
    # print("进入train")
    if args.cuda:
        adj = adj.cuda()
        model.cuda()
    t = time.time()

    if args.earlystopping > 0:
        early_stopping = EarlyStopping(patience=args.earlystopping, verbose=False)

    # for step in range(args.steps):
    step = 0
    # t_begin = time. clock ()
    for i, data_all in enumerate(dataloader):
        # t_end =time. clock ()
        # print("-1")
        # print ( '--------Running time: %s Seconds' %(t_end-t_begin))
        # sys.exit(1)

        if step == args.steps:
            break
        else:
            pass

        step = step+1
        model.train()
        # print("进入")
        # data.txt, weights, labels = next(iter(dataloader))
        data, weights, labels = data_all
        data, weights, labels = data.float(), weights.float(), labels.float()
        if args.cuda:
            data, weights, labels = data.cuda(), weights.cuda(), labels.cuda()

        optimizer.zero_grad()
        outputs = model(data, adj)
        outputs = outputs.squeeze()
        # crit = torch.nn.BCELoss(weight = weights)
        # loss = crit(outputs, labels)
        loss = cross_entropy(labels, outputs, weights)
        # loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        val_loss = validate(args, model, adj, val_data)
        scheduler.step(val_loss)  # learn rate decay
        if args.earlystopping > 0:
            early_stopping(val_loss, model)
        if args.earlystopping > 0 and early_stopping.early_stop:
            print("Early stopping.")
            break

        if args.verbose and step % 100 == 0:
            print('step: {:04d}'.format(step + ini_step),
                  'loss: {:^10}'.format(loss.item()),
                  'val loss: {:^10}'.format(val_loss.item()),
                  'cur_lr: {:^10}'.format(get_lr(optimizer)),
                  'time: {:.4f}s'.format(time.time() - t))

    print("the total traing time:{:.4f}s".format(time.time() - t))
    # save the checkpoint
    torch.save({
        'step': ini_step + args.steps,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss.item()}, args.model_dir)

    return model


def predict_one(args, model, data, adj):
    data = torch.FloatTensor(data)
    if args.cuda:
        adj = adj.cuda()
        data = data.cuda()
    output = model(data, adj)
    pred = output.cpu().data.numpy()
    pred = pred.squeeze()
    return pred


def predict_all(args, model, data, adj):
    pred_all = []
    data = torch.FloatTensor(data)
    if args.cuda:
        adj = adj.cuda()
        data = data.cuda()
    for i in range(data.shape[0]):
        input = data[i].reshape(1, data.shape[1], data.shape[2])
        pred = model(input, adj)
        pred = pred.cpu().data.numpy().squeeze()
        pred_all.append(pred)
    return pred_all



def gen_kcore_union_coreness(args, model, adj):
    # Create the Estimator
    lr = args.learning_rate
    input_folder = args.input_data_folder
    verbose = args.verbose
    ef = args.extra_feats
    model_dir = args.model_dir
    b = args.b
    k = args.k
    # b = 25
    #
    # X_norm, n_classes, core, _ = build_testsetCoreness(input_folder, k)

    gname = os.path.join(input_folder, "temp_core_" + str(k) + ".txt")
    t_begin  = time.time()
    (X_norm, _, n_classes, core, G) = data_preprocessingCoreness(gname, k, True, False)
    orig_core = deepcopy(core)
    mask = np.zeros(shape=(n_classes,), dtype=int)
    n_node = core.number_of_nodes()
    extra_feats, n_feats = generate_features(core=core, n_node=n_node)
    res = []
    res_node = []
    seed = np.argmax(X_norm)
    # seed = 107
    # if verbose:
    #     print("seed: %d\t%d" % (seed, X_norm[seed]))

    mask[seed] = -10000000.0

    res.append(seed)
    res_node.append(seed)
    core.remove_node(seed)
    #graph = nx.k_core(core, k)  #这一步可以删除
    print("initial removed node:", seed)
    # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
    #removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
    #removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]

    #mask[removed_node] = -10000000.0
    #core = graph  # reset the core
    # if verbose:
    #     print("# removed node: %d" % (core.number_of_nodes() - orig_core.number_of_nodes()))
    cnt = len(res)

    while cnt < b:
        input = np.zeros(shape=(n_node,), dtype=int)
        input[res_node] = 1
        if ef > 0:
            input = np.hstack((input.reshape((n_node, 1)), extra_feats))
            input = torch.FloatTensor(input)  # must transfrom to torch tensor before reshape. don't know why.
            input = input.reshape((1, input.shape[0], input.shape[1]))  # (batch, node, feat)
        else:
            input = input.reshape((1, n_node, 1))

        pred = predict_one(args, model=model, data=input, adj=adj)
        t_pred = pred + mask
        oidx = np.argmax(t_pred)
        # print("max pred: %8f min pred: %8f"%(np.max(pred), np.min(pred)))
        # must not raise exception, if so, something wrong with data.txt.txt


        mask[oidx] = -1000000000.0
        res.append(oidx)
        res_node.append(oidx)
        core.remove_node(oidx)
        #graph = nx.k_core(core, k)
        # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
        #removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
        #removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
        mask[oidx] = -1000000000.0
        # core = graph

        if verbose:
            print("cnt: %d with: %d " %
                  (len(res), oidx))
        cnt += 1
        if core.number_of_nodes() == 0:
            break

    t_end  = time.time()
    print ("the total time of the predicting:{.4f}s".format(t_end-t_begin))

    if verbose:

        coreNew = copy.deepcopy(orig_core)

        # core 为networkX Graph()，idx为 ndrray(numpy)

        coreness1 = nx.core_number(coreNew)


        removeNodes = res
        coreNew.remove_nodes_from(removeNodes)  # 删除节点v 以及边

        coreness2 = nx.core_number(coreNew)

        for i in removeNodes:
            del coreness1[i]

        coreness1 = np.array(list(coreness1.values()))
        coreness2 = np.array(list(coreness2.values()))
        corenessLoss = np.sum(coreness1 - coreness2)
        #print("generate collesped k core (union): ")
        print("the selected node size: ", len(res))
        # print("the total coreness loss: ", corenessLoss )
    return corenessLoss






def gen_kcore_union(args, model, adj):
    # Create the Estimator
    lr = args.learning_rate
    input_folder = args.input_data_folder
    verbose = args.verbose
    ef = args.extra_feats
    model_dir = args.model_dir
    b = args.b
    k = args.k
    # b = 25
    X_norm, n_classes, non_dominated, nondomin_dict, core, _ = build_testset(input_folder, k)
    orig_core = deepcopy(core)
    mask = np.zeros(shape=(n_classes,), dtype=int)
    n_node = core.number_of_nodes()
    extra_feats, n_feats = generate_features(core=core, n_node=n_node)
    res = []
    res_node = []
    seed = np.argmax(X_norm)
    if verbose:
        print("seed: %d\t%d" % (seed, X_norm[seed]))
    g_id = non_dominated[seed]
    mask[seed] = -10000000.0

    res.append(seed)
    res_node.append(g_id)
    core.remove_node(g_id)
    graph = nx.k_core(core, k)
    print("initial removed node:", g_id)
    # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
    removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
    removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
    mask[removed] = -10000000.0
    core = graph  # reset the core
    if verbose:
        print("# removed node: %d" % (core.number_of_nodes() - orig_core.number_of_nodes()))
    cnt = len(res)

    while cnt < b:
        input = np.zeros(shape=(n_node,), dtype=int)
        input[res_node] = 1
        if ef > 0:
            input = np.hstack((input.reshape((n_node, 1)), extra_feats))
            input = torch.FloatTensor(input)  # must transfrom to torch tensor before reshape. don't know why.
            input = input.reshape((1, input.shape[0], input.shape[1]))  # (batch, node, feat)
        else:
            input = input.reshape((1, n_node, 1))

        pred = predict_one(args, model=model, data=input, adj=adj)
        t_pred = pred + mask
        oidx = np.argmax(t_pred)
        # print("max pred: %8f min pred: %8f"%(np.max(pred), np.min(pred)))
        # must not raise exception, if so, something wrong with data.txt.txt
        g_id = non_dominated[oidx]
        mask[oidx] = -1000000000.0
        res.append(oidx)
        res_node.append(g_id)
        core.remove_node(g_id)
        graph = nx.k_core(core, k)
        # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
        removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
        removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
        mask[removed] = -1000000000.0
        core = graph

        if verbose:
            print("cnt: %d with: %d without: %d graph id: %d all removed: %d" %
                  (len(res), oidx, np.argmax(pred), g_id, core.number_of_nodes() - orig_core.number_of_nodes()))
        cnt += 1
        if core.number_of_nodes() == 0:
            break
    if verbose:
        print("generate collesped k core (union): ")
        print ("the selected node size: ", len(res))
        print ("the collesped kcore size: ", len(core.nodes()))
    return orig_core.number_of_nodes() - core.number_of_nodes()


def count_remove_node(cur_core, gid, k):
    tmp_core = deepcopy(cur_core)
    tmp_core.remove_node(gid)
    tmp_core = nx.k_core(tmp_core, k)
    return cur_core.number_of_nodes() - tmp_core.number_of_nodes()


def ensenmble_predict(ml_pred, alg_pred, cur_core, non_dominated, k):
    ml_oid = np.argmax(ml_pred)
    alg_oid = np.argmax(alg_pred)

    ml_removed = count_remove_node(cur_core, non_dominated[ml_oid], k)
    alg_removed = count_remove_node(cur_core, non_dominated[alg_oid], k)

    oid = alg_oid if alg_removed > ml_removed else ml_oid
    return oid


def gen_kcore_ensemble(args, model, adj):
    # Create the Estimator
    lr = args.learning_rate
    input_folder = args.input_data_folder
    verbose = args.verbose
    ef = args.extra_feats
    model_dir = args.model_dir
    b = args.b
    k = args.k
    # b = 25
    X_norm, n_classes, non_dominated, nondomin_dict, core, G = build_testset(input_folder, k)
    orig_core = deepcopy(core)
    mask = np.zeros(shape=(n_classes,), dtype=int)
    n_node = core.number_of_nodes()
    extra_feats, n_feats = generate_features(core=core, n_node=n_node)

    res = []
    res_node = []
    seed = np.argmax(X_norm)
    if verbose:
        print("seed: %d\t%d" % (seed, X_norm[seed]))
    g_id = non_dominated[seed]
    mask[seed] = -10000000.0

    res.append(seed)
    res_node.append(g_id)
    core.remove_node(g_id)
    graph = nx.k_core(core, k)
    print("initial removed node:", g_id)
    # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
    removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
    removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
    mask[removed] = -10000000.0
    core = graph  # reset the core
    if verbose:
        print("# removed node: %d" % (core.number_of_nodes() - orig_core.number_of_nodes()))
    cnt = len(res)

    while cnt < b:
        input = np.zeros(shape=(n_node,), dtype=int)
        input[res_node] = 1
        if ef > 0:
            input = np.hstack((input.reshape((n_node, 1)), extra_feats))
            input = torch.FloatTensor(input)  # must transfrom to torch tensor before reshape. don't know why.
            input = input.reshape((1, input.shape[0], input.shape[1]))  # (batch, node, feat)
        else:
            input = input.reshape((1, n_node, 1))

        pred = predict_one(args, model=model, data=input, adj=adj)
        t_pred = pred + mask

        y = np.array(G.KCoreLabelGeneration2(k, res))
        # print("max pred: %8f min pred: %8f"%(np.max(pred), np.min(pred)))
        # generate the ensemble result: choose the best of greedy and ml
        oidx = ensenmble_predict(ml_pred=t_pred, alg_pred=y,
                                 cur_core=core, non_dominated=non_dominated, k=k)
        g_id = non_dominated[oidx]
        mask[oidx] = -1000000000.0
        res.append(oidx)
        res_node.append(g_id)
        core.remove_node(g_id)
        graph = nx.k_core(core, k)
        # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
        removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
        removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
        mask[removed] = -1000000000.0
        core = graph

        if verbose:
            print("cnt: %d with: %d without: %d graph id: %d all removed: %d" %
                  (len(res), oidx, np.argmax(pred), g_id, core.number_of_nodes() - orig_core.number_of_nodes()))
        cnt += 1
        if core.number_of_nodes() == 0:
            break
    if verbose:
        print("generate collesped k core (ensemble): ")
        print ("the selected node size: ", len(res))
        print ("the collesped kcore size: ", len(core.nodes()))
    return orig_core.number_of_nodes() - core.number_of_nodes()


def gen_kcore_sep(args, model, adj):
    # Create the Estimator
    # N = args.n_classes
    lr = args.learning_rate
    input_folder = args.input_data_folder
    verbose = args.verbose
    ef = args.extra_feats
    model_dir = args.model_dir
    b = args.b
    k = args.k
    # b = 25
    X_norm, n_classes, non_dominated, nondomin_dict, core, _ = build_testset(input_folder,
                                                                             k)  # 这个是test的生成set的方式，跟前面的训练阶段不同
    orig_core = deepcopy(core)
    mask = np.zeros(shape=(n_classes,), dtype=int)
    n_node = core.number_of_nodes()
    extra_feats, n_feats = generate_features(core=core, n_node=n_node)
    extra_feats = np.tile(np.asarray(esxtra_feats), (n_node, 1)).reshape((n_node, n_node, n_feats))

    res = []
    res_node = []
    seed = np.argmax(X_norm)
    if verbose:
        print("seed: %d\t%d" % (seed, X_norm[seed]))
    g_id = non_dominated[seed]
    mask[seed] = -10000000.0

    res.append(seed)
    res_node.append(g_id)
    core.remove_node(g_id)
    graph = nx.k_core(core, k)
    # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
    removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
    removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
    mask[removed] = -10000000.0
    core = graph  # reset the core
    if verbose:
        print("# removed node: %d" % (core.number_of_nodes() - orig_core.number_of_nodes()))
    cnt = len(res)

    # Predict all labels
    data = np.identity(n_node).reshape((n_node, n_node, 1))
    if ef > 0:
        data = np.concatenate((data, extra_feats), axis=2)
    pred_all = predict_all(args, model=model, data=data, adj=adj)

    while cnt < b:
        # data.txt.txt = np.array(res[-w:])
        pred = np.zeros(shape=(1, n_classes), dtype=int)
        for r in res_node:
            pred = pred + pred_all[r]  # * X_norm[r]
        # print(X_norm[r])
        t_pred = pred + mask
        oidx = np.argmax(t_pred)

        g_id = non_dominated[oidx]
        mask[oidx] = -1000000000.0
        res.append(oidx)
        res_node.append(g_id)

        core.remove_node(g_id)
        graph = nx.k_core(core, k)
        # removed_node = list(Set(core.nodes()).difference(Set(graph.nodes())))
        removed_node = list(set(core.nodes()).difference(set(graph.nodes())))
        removed = [nondomin_dict[u] for u in removed_node if u in nondomin_dict.keys()]
        mask[removed] = -1000000000.0
        core = graph

        if verbose:
            print("cnt: %d with: %d without: %d graph id: %d all removed: %d" %
                  (len(res), oidx, np.argmax(pred), g_id, core.number_of_nodes() - orig_core.number_of_nodes()))
        cnt += 1
        if core.number_of_nodes() == 0:
            break
    if verbose:
        print("generate collesped k core (sep): ")
        print ("the selected node size: ", len(res))
        print ("the collesped kcore size: ", len(core.nodes()))
    return orig_core.number_of_nodes() - core.number_of_nodes()


def main(args):

    n_hid1 = args.n_hid1
    n_hid2 = args.n_hid2
    n_expert = args.n_expert
    att_hid = args.att_hid
    dropout = args.dropout

    input_folder = args.input_data_folder
    model_dir = args.model_dir
    steps = args.steps
    batch_size = args.batch_size
    weight_decay = args.weight_decay
    lr = args.learning_rate
    normalization = args.normalization

    ef = args.extra_feats
    verbose = args.verbose
    set_size = args.b
    k = args.k
    EveryNodeFollowers_filename = args.EveryNodeFollowers_filename
    args.cuda = not args.no_cuda and torch.cuda.is_available()

    train_norm, n_classes, graph = build_datasetCoreness(input_folder, k)
    # nodeFollowers_line = linecache.getline(EveryNodeFollowers_filename,1)
    # X_norm = [int(line.rstrip()) for line in nodeFollowers_line.split()]
    # train_norm = np.array(X_norm)
    if verbose:
        print("training data.txt. shape: ")
        print(train_norm.shape)

    # define the training dataset and dataloader
    n_node = graph.number_of_nodes()
    extra_feats, n_feats = generate_features(core=graph, n_node=n_node)


    dataset = SampleDatasetCoreness(input_filename=args.input_train_filename, label_name=args.train_label_filename,n_classes=n_classes, n_node=graph.number_of_nodes(),
                                    X_norm=train_norm,
                                    extra_feats=extra_feats, ef=ef,
                                    G=graph, set_size=set_size,
                                    k=k, batch_size=batch_size)  # 得到不同的训练 size
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                            shuffle=False, sampler=None)
    # define the validation dataset
    val_dataset = SampleDatasetCoreness(input_filename=args.input_val_filename, label_name=args.val_label_filename,n_classes=n_classes, n_node=graph.number_of_nodes(),
                                X_norm=train_norm,
                                extra_feats=extra_feats, ef=ef,
                                G=graph, set_size=set_size,
                                k=k, batch_size=100)

    val_dataloader = torch.utils.data.DataLoader(val_dataset, batch_size=100,
                                shuffle=False, sampler=None)

    val_data = next(iter(val_dataloader))

    # define the model
    nfeat = 1 + n_feats if ef > 0 else 1
    model = GCNAtt(nfeat=nfeat, n_hid1=n_hid1, n_hid2=n_hid2,
                   n_expert=n_expert, att_hid=att_hid, final_class=n_classes,
                   dropout=dropout)

    optimizer = optim.Adam(model.parameters(),
                           lr=lr, weight_decay=args.weight_decay)

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=100, factor=0.8)

    # build the adj matrix of graph
    adj = generate_adjmx(graph, normalization)
    adj = torch.FloatTensor(adj)   # FloatTensor 默认生成float32
    # criterion = torch.nn.MultiLabelMarginLoss()
    # criterion = torch.nn.MSELoss()
    edge_idx_device = torch.tensor(np.where(adj != 0), dtype=torch.long)
    criterion = torch.nn.BCELoss()

    ini_step = 0
    # if model exists, reload the model
    model_exists = os.path.isfile(model_dir)
    if model_exists:
        checkpoint = torch.load(model_dir)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        if args.cuda:
            for state in optimizer.state.values():
                for k, v in state.items():
                    if isinstance(v, torch.Tensor):
                        state[k] = v.cuda()  # move optmizer to cuda manually
            model.cuda()
        ini_step = checkpoint['step']
        loss = checkpoint['loss']
    if verbose:
        print("training...")
    train(args, model, dataloader, adj, criterion, optimizer, scheduler, val_data, ini_step)
    # predication

    union_result = gen_kcore_union_coreness(args, model, adj)

    # sep_result = gen_kcore_sep(args, model, adj)
    # ensemble_result = gen_kcore_ensemble(args, model, adj)
    # print("accuracy=%d" % (max(union_result, sep_result, ensemble_result)))
    print("coreness loss =%d" % union_result)



if __name__ == "__main__":
    parser = ArgumentParser("gcn", formatter_class=ArgumentDefaultsHelpFormatter, conflict_handler="resolve")
    # Model settings
    parser.add_argument("--n_hid1", default=32, type=int,
                        help="first layer of GCN: number of hidden units")  # options [64, 128, 256]
    parser.add_argument("--n_hid2", default=32, type=int,
                        help="second layer of GCN: number of hidden units")  # options [64, 128, 256]
    parser.add_argument("--n_expert", default=32, type=int,
                        help="attention layer: number of experts")  # options [16, 32, 64, 128]
    parser.add_argument("--att_hid", default=32, type=int,
                        help="attention layer: hidden units")  # options [64, 128, 256]
    parser.add_argument("--model_dir", type=str, default="./GCNmodel_Arxiv_full_b.pt")
    parser.add_argument('--dropout', type=float, default=0.5,
                        help='Dropout rate (1 - keep probability).')
    parser.add_argument("--normalization", default="AugNormAdj",
                        help="The normalization on the adj matrix.")

    # Training settings
    parser.add_argument("--batch_size", default=64000, type=int)  # options: [32, 64, 128]
    parser.add_argument("--steps", default=20000000, type=int)  # options:  (1000, 2000, ... 40000)
    parser.add_argument("--learning_rate", default=0.001, type=float)  # options [1e-3, 1e-4]
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='Disables CUDA training.')
    parser.add_argument('--weight_decay', type=float, default=5e-4,
                        help='Weight decay (L2 loss on parameters).')
    parser.add_argument("--earlystopping", type=int, default=0,
                        help="The patience of earlystopping. Do not adopt the earlystopping when it equals 0.")

    # Others
    parser.add_argument("--extra_feats", default=0, type=int,
                        help="whether or not enable extra feats (e.g.,core num, etc.) 0 Disables/1 Enable")
    parser.add_argument("--input_data_folder", default="/mnt/SCGCN/SCGCN-main/data/socfb-Northeastern19/",
                        help="Input data.txt.txt folder")
    parser.add_argument("--verbose", default=False, type=bool)
    # parser.add_argument("--k", default=33, type=int, help = "the k core to be collesped") # options [20, 30, 40]
    parser.add_argument("--k", default=1, type=int, help="Collapsed Coreness,k ==1")  # options [20, 30, 40]
    parser.add_argument("--b", default=20, type=int, help="the result set size")
    parser.add_argument("--input_train_filename",default="/mnt/SCGCN/SCGCN-main/data/fb/fb/b20/train_input.txt", help="the path of the input data.txt file ")
    parser.add_argument("--train_label_filename",default="/mnt/SCGCN/SCGCN-main/data/fb/fb/b20/train_label.txt",help="the path of the label file of the data.txt sample")
    parser.add_argument("--input_val_filename",
                        default="/mnt/SCGCN/SCGCN-main/data/fb/fb/b20/val_input.txt",
                        help="the path of the input data.txt file ")
    parser.add_argument("--val_label_filename", default="/mnt/SCGCN/SCGCN-main/fb/fb/b20/val_label.txt",
                        help="the path of the label file of the data.txt sample")

    # unused parameters
    '''
    parser.add_argument("--dev_data_file", default = "")
    parser.add_argument("--n_eval_data", default = 1000, type = int) # number of eval data.txt.txt to generate/load
    parser.add_argument('--lradjust',action='store_true', default=False, 
        help = 'Enable leraning rate adjust.(ReduceLROnPlateau)')
    parser.add_argument("--debug_samplingpercent", type=float, default=1.0, 
        help="The percent of the preserve edges (debug only)")
    '''
    args = parser.parse_args()
    if args.verbose:
        print(args)
    main(args)
