//
//  main.cpp
//  infSpread
//
//  Created by Kangfei Zhao on 1/12/2018.
//  Copyright © 2018 Kangfei Zhao. All rights reserved.
//
#include "graph.h"
#include <iostream>
#include <random>
#ifdef _OPENMP
#include <omp.h>
#endif
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#define thread_count 30

Graph::Graph() {
    nodenum = edgenum = 0;
}

Graph::~Graph() {
}

void Graph::loadDirGraph(const string filename) {
    ifstream infile;
    infile.open(filename);
    
    string line;
    string fid;
    string tid;
    
    string node_num;
    string edge_num;
    
    getline(infile, line);
    stringstream ss(line);
    ss >> node_num;
    nodenum = atol(node_num.c_str());
    ss >> edge_num;
    edgenum = atol(edge_num.c_str());
    
    G_IN.resize(nodenum);
    G_OUT.resize(nodenum);
    
    long node_count = 0;
    long edge_count = 0;
    while (getline(infile, line))
    {
        //        getline(infile, line);
        stringstream ss(line);
        ss >> fid;
        if (strcmp(fid.c_str(), "#") == 0) continue;
        ss >> tid;
        long from = atol(fid.c_str());
        long to = atol(tid.c_str());
        
        if (node_dict.find(from) == node_dict.end()) {
            node_dict[from] = node_count; node_count++;
        }
        if (node_dict.find(to) == node_dict.end()) {
            node_dict[to] = node_count; node_count++;
        }
        //create the in-neighbor adj list
        G_IN[node_dict[to]].push_back(node_dict[from]);
        //create the out-neighbor adj list
        G_OUT[node_dict[from]].push_back(node_dict[to]);
        // for undirected graph
        //    G_IN[node_dict[from]].push_back(node_dict[to]);
        //    G_OUT[node_dict[to]].push_back(node_dict[from]);
        edge_count++;
    }
    //sort the in and out Adj list
    for (vector<Adjlist>::iterator it = G_IN.begin(); it != G_IN.end(); it++)
        sort(it->begin(), it->end());
    for (vector<Adjlist>::iterator it = G_OUT.begin(); it != G_OUT.end(); it++)
        sort(it->begin(), it->end());
    
    cout << "the number of node:" << nodenum << endl;
    cout << "the number of edge:" << edgenum << endl;
    cout << "# nodes have in-neigs: " << G_IN.size() << endl;
    cout << "# nodes have out-neigs: " << G_OUT.size() << endl;
    
    infile.close();
}


void Graph::loadUndirGraph(const string filename) {
    ifstream infile;
    infile.open(filename);
    
    string line;
    string fid;
    string tid;
    
    string node_num;
    string edge_num;
    
    getline(infile, line);
    stringstream ss(line);
    ss >> node_num;
    nodenum = atol(node_num.c_str());
    ss >> edge_num;
    edgenum = atol(edge_num.c_str());
    
    G_IN.resize(nodenum);
    G_OUT.resize(nodenum);
    
    long node_count = 0;
    long edge_count = 0;
    while (getline(infile, line))
    {
        //        getline(infile, line);
        stringstream ss(line);
        ss >> fid;
        if (strcmp(fid.c_str(), "#") == 0) continue;
        ss >> tid;
        long from = atol(fid.c_str());
        long to = atol(tid.c_str());
        
        if (node_dict.find(from) == node_dict.end()) {
            node_dict[from] = node_count; node_count++;
        }
        if (node_dict.find(to) == node_dict.end()) {
            node_dict[to] = node_count; node_count++;
        }
        //create the in-neighbor adj list
        G_IN[node_dict[to]].push_back(node_dict[from]);
        //create the out-neighbor adj list
        G_OUT[node_dict[from]].push_back(node_dict[to]);
        // for undirected graph
        G_IN[node_dict[from]].push_back(node_dict[to]);
        G_OUT[node_dict[to]].push_back(node_dict[from]);
        edge_count = edge_count + 2;
    }
    //sort the in and out Adj list
    for (vector<Adjlist>::iterator it = G_IN.begin(); it != G_IN.end(); it++)
        sort(it->begin(), it->end());
    for (vector<Adjlist>::iterator it = G_OUT.begin(); it != G_OUT.end(); it++)
        sort(it->begin(), it->end());
    
    cout << "the number of node:" << node_count << endl;
    cout << "the number of edge:" << edge_count << endl;
    cout << "# nodes have in-neigs: " << G_IN.size() << endl;
    cout << "# nodes have out-neigs: " << G_OUT.size() << endl;
    
    infile.close();
}


vector <int> Graph:: ICSpread(vector <int> & S, float p){
    vector <int> result(nodenum, 0);
    vector <int> T(S);
    srand((unsigned)time(NULL));
    int i = 0;
    while(i < T.size()){
        for (Adjlist:: iterator it = G_OUT[T[i]].begin(); it != G_OUT[T[i]].end() ; it ++){
            if (find(T.begin(), T.end(), *it) == T.end()){
                if ( ((double)rand())/RAND_MAX <= 1 - pow((1-p), 1.0/G_OUT[*it].size()))
                    T.push_back(*it);
            }
        }
        i ++;
    }
//    cout << "T size: " << T.size() << endl;
    # pragma omp parallel num_threads(thread_count)
    srand((unsigned)time(NULL));
    for(i = 0; i < nodenum; i++){
        if (find(T.begin(), T.end(), i) == T.end()){
            vector <int> tmp_T(T);
            int j = tmp_T.size();
            tmp_T.push_back(i);
            while (j < tmp_T.size()){
                for (Adjlist:: iterator it = G_OUT[tmp_T[j]].begin(); it!= G_OUT[tmp_T[j]].end(); it++){
                    if(find(tmp_T.begin(), tmp_T.end(), *it) == tmp_T.end()){
                        if ( ((double)rand())/RAND_MAX <= 1 - pow((1-p), 1.0/G_OUT[*it].size()))
                            tmp_T.push_back(*it);
                    }
                }
                j++;
            }
            result[i] = tmp_T.size();
        } //end if
        else result[i] = T.size();
    }
    return result;
}

vector <int> Graph:: LTSpread(vector <int> & S){
    vector <int> result(nodenum);
    vector <float> w(nodenum, 0.0);
    vector <float> threshold(nodenum, 0.0);
    default_random_engine generator;
    uniform_real_distribution<float> distribution(0.0, 1.0);
    for (int i = 0; i < nodenum; i++)
        threshold[i] = distribution(generator);
    vector <int> T(S);
    vector <int> Sj(S);
    while(Sj.size()){
        vector <int> Snew;
        for (Adjlist:: iterator u = Sj.begin(); u != Sj.end(); u++){
            for (Adjlist :: iterator v = G_OUT[*u].begin(); v != G_OUT[*u].end(); v++ ){
                if (find(T.begin(), T.end(), *v) == T.end()){
                    w[*v] += 1.0/G_OUT[*v].size();
                    if (w[*v] >= threshold[*v]){
                        Snew.push_back(*v);
                        T.push_back(*v);
                    }
                        
                }
            }
        }
        Sj.swap(Snew);
    }
//    cout << "T size: " << T.size() << endl;
    # pragma omp parallel num_threads(thread_count)
    for(int i = 0; i< nodenum; i++){
        if(find(T.begin(), T.end(), i)== T.end()){
            vector <int> tmp_T(T);
            vector <float> tmp_w(nodenum, 0);
            tmp_T.push_back(i);
            vector <int> tmp_Sj{i};
            while(tmp_Sj.size()){
                vector <int> tmp_Snew ;
                for (Adjlist ::iterator u = tmp_Sj.begin(); u != tmp_Sj.end(); u ++){
                    for (Adjlist :: iterator v = G_OUT[*u].begin(); v!= G_OUT[*u].end(); v++){
                        if (find(tmp_T.begin(), tmp_T.end(), *v)== tmp_T.end()){
                            tmp_w[*v] += 1.0 /G_OUT[*v].size();
                            if(w[*v] + tmp_w[*v] >= threshold[*v]){
                                tmp_Snew.push_back(*v);
                                tmp_T.push_back(*v);
                            }
                        }
                    }
                }
                tmp_Sj.swap(tmp_Snew);
            }
            result[i] = tmp_T.size();
        }
        else result[i] = T.size();
    }
    return result;
}

vector <int> Graph:: runLT(vector <int> & S){
    vector <float> w(nodenum, 0.0);
    vector <float> threshold(nodenum, 0.0);
    default_random_engine generator(time(NULL));
    uniform_real_distribution<float> distribution(0.0, 1.0);
    for (int i = 0; i < nodenum; i++)
        threshold[i] = distribution(generator);
    vector <int> T(S);
    vector <int> Sj(S);
    while(Sj.size()){
        vector <int> Snew;
        for (Adjlist:: iterator u = Sj.begin(); u != Sj.end(); u++){
            for (Adjlist :: iterator v = G_OUT[*u].begin(); v != G_OUT[*u].end(); v++ ){
                if (find(T.begin(), T.end(), *v) == T.end()){
                    w[*v] += 1.0/G_OUT[*v].size();
                    if (w[*v] >= threshold[*v]){
                        Snew.push_back(*v);
                        T.push_back(*v);
                    }
                        
                }
            }
        }
        Sj.swap(Snew);
    }
    return T;
}

vector <int> Graph:: runIC(vector <int> & S, float p){
    vector <int> T(S);
    srand((unsigned)time(NULL));
    int i = 0;
    while(i < T.size()){
        for (Adjlist:: iterator it = G_OUT[T[i]].begin(); it != G_OUT[T[i]].end() ; it ++){
            if (find(T.begin(), T.end(), *it) == T.end()){
                if ( ((double)rand())/RAND_MAX <= 1 - pow((1-p), 1.0/G_OUT[*it].size()))
                    T.push_back(*it);
            }
        }
        i ++;
    }
    return T;
}

// greedy algorithm for maximum k cover from start
vector <int> Graph:: greedyMVCFromStart(int k, int start){
    vector <int> res;
    vector <int> deg(nodenum, 0);
    int uncovered_edge_num = edgenum;
    for(int i = 0; i < nodenum; i++)
        deg[i] = G_IN[i].size();
    res.push_back(start);
    for (Adjlist :: iterator it = G_IN[start].begin(); it != G_IN[start].end(); it++ ){
        deg[* it] --;
        uncovered_edge_num = uncovered_edge_num - 2;
    }
    deg[start] = -1;
    
    for (int i = 1; i < k; i++){
        if (uncovered_edge_num <= 0) break;
        int idx = distance(deg.begin(), max_element(deg.begin(), deg.end()));
        res.push_back(idx);
        for (Adjlist :: iterator it = G_IN[idx].begin(); it != G_IN[idx].end(); it++ ){
            deg[* it] --;
            uncovered_edge_num = uncovered_edge_num - 2;
        }
        deg[idx] = -1;
    }
    return res;
}

// generate the dominate set label for a given vertex
vector <int> Graph:: DSLabelGeneration(vector <int> & res){
    int k = res.size();
    vector <int> remove_loss (k, 0);
    unordered_set <int> res_set(res.begin(), res.end());
    
    // compute remove loss for each selected node
    for (int i = 0; i < k; i++){
        Adjlist :: iterator it = G_IN[res[i]].begin();
        //if no neighbors of selected node is in res, the selected node can dominate itself exclusively
        for (; it != G_IN[res[i]].end(); it++)
            if (res_set.count(*it)) break;
        if (it == G_IN[res[i]].end()){
            remove_loss[i]++;
            //cout << "haha" << endl;
        }
        
        it = G_IN[res[i]].begin();
        //cout << G_IN[res[i]].size() << endl;
        // the neighbor of selected node
        for (; it != G_IN[res[i]].end(); it++){
            
            if ( res_set.count(*it) ) continue; //the neighbor is in res: skip
            Adjlist:: iterator it2 = G_IN[*it].begin();
            //cout << "neig's neig size: " << G_IN[*it].size() << endl;
            //if no neighbor of the neighbor is in res, res[i] and dominate the neigbor exclusively.
            for (; it2!= G_IN[*it].end(); it2++)
                if (res_set.count(*it2) && *it2 != res[i]) break;
            if (it2 == G_IN[*it].end()){
                remove_loss[i]++;
                //cout << "hehe" << endl;
            }
        }
    }
    return remove_loss;
}

vector <int> Graph:: DSLabelGenerationFast(vector <int> & res){
    vector <int> remove_loss(res.size(), 0);
    
    unordered_map <int, int> dominace;
    for (int v: res){
        if (dominace.find(v) == dominace.end())
            dominace[v] = 1;
        else dominace[v] += 1;
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            if(dominace.find(*it) == dominace.end())
                dominace[*it] = 1;
            else dominace[*it] += 1;
        }
    }
    
    for (int i = 0; i < res.size(); i++){
        remove_loss[i] = (int) G_IN[res[i]].size() + 1; //maximum loss: all neighbors and itself
        //if(dominace.find(res[i]) != dominace.end() && dominace[res[i]] == 1)
        if( dominace[res[i]] > 1)
            remove_loss[i] --;
        for (Adjlist:: iterator it = G_IN[res[i]].begin(); it!= G_IN[res[i]].end(); it++)
            if ( dominace[*it] > 1)
                remove_loss[i] --;
    }
    return remove_loss;
}

vector <int> Graph:: MVCLabelGeneration(vector <int> & res){
    vector <int> label(nodenum, 0);
    
    unordered_set <pair <int , int>, pair_hash> covered;
    unordered_set <int> S_res(res.begin(), res.end());
    for (int v : res){
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            pair <int, int> e = (*it > v) ? make_pair(*it, v): make_pair(v, *it);
            covered.insert(e);
        }
    }
    # pragma omp parallel for num_threads(thread_count)
    for (int u= 0; u < nodenum; u++){
        unordered_set <pair<int, int>, pair_hash> tmp_covered(covered);
        for (Adjlist:: iterator it = G_IN[u].begin(); it != G_IN[u].end(); it++){
            pair <int, int> e = (*it > u) ? make_pair(*it, u): make_pair(u, *it);
            tmp_covered.insert(e);
        }
        label[u] = (int) tmp_covered.size();
    }
    return label;
}


vector <int> Graph:: MVCLabelGenerationFast(vector <int> & res){
    vector <int> label(nodenum, 0);
    int covered_num = 0;
    unordered_set <int> S_res(res.begin(), res.end());
    for (int v : res){
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            if (!S_res.count(*it) || (S_res.count(*it) && *it < v))
                covered_num ++;
        }
    }
    //add the delta part for each vertex
    # pragma omp parallel for num_threads(thread_count)
    for (int u= 0; u < nodenum; u++){
        if (S_res.count(u)) {
            label[u] = covered_num;
            continue;
        }
        int tmp_covered = covered_num;
        for (Adjlist:: iterator it = G_IN[u].begin(); it != G_IN[u].end(); it++){
            if (!S_res.count(*it))
                tmp_covered ++;
        }
        label[u] = tmp_covered;
    }
    return label;
}

vector <int> Graph:: KDSLabelGeneration(vector <int> & res){
    
    unordered_set <int> S_res(res.begin(), res.end());
    int edge_num = 0;
    for (int v: res){
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            if (S_res.count(*it))
                edge_num ++;
        }
    }
    edge_num = edge_num / 2; // each undirected is counted double
    vector <int> label(nodenum, edge_num);
    //cout << edge_num << endl;
    # pragma omp parallel for num_threads(thread_count)
    for (int u = 0; u < nodenum; u++){
        if (S_res.count(u)) {
            continue;
        }
        for (Adjlist:: iterator it = G_IN[u].begin(); it != G_IN[u].end(); it++ )
            if (S_res.count(*it))
                label[u] ++;
    }
    return label;
}

vector <int> Graph:: KCoreLabelGeneration(int k, vector<int> &res){
    unordered_set <int> res_set(res.begin(), res.end());
    vector <int> deg(nodenum, 0);
    for(int i = 0; i < nodenum; i++)
        deg[i] = (int) G_IN[i].size();
    queue<int> Q;
    for (const int v : res){
        Q.push(v);
        deg[v] = 0;
    }
    int remove = 0;
    while(!Q.empty()){
        int v = Q.front();
        Q.pop();
        for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            deg[*it] --;
            if (deg[*it] == k-1){
                Q.push(*it);
                remove++;
            }
        }
    }//end while
    //cout << "remove: " << remove << endl;
     vector <int> label(nodenum, remove);
    # pragma omp parallel for num_threads(thread_count)
    for (int u = 0; u < nodenum; u++){  //compute the collapse of nodes of res + u
        if (res_set.count(u))
            continue;
        vector<int> tmp_deg(deg);
        queue <int> tmp_Q;
        tmp_Q.push(u);
        tmp_deg[u] = 0;
        int tmp_remove = 0;
        while(!tmp_Q.empty()){
            int v = tmp_Q.front();
            tmp_Q.pop();
            for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                    tmp_remove++;
                }
            }
        }
        label[u] += tmp_remove;
    }
    return label;
}

vector <int>  Graph:: KCoreXnormGeneration(int k){
    vector <int> X_norm(nodenum, 0);
    vector <int> deg(nodenum, 0);
    for(int i = 0; i < nodenum; i++)
        deg[i] = (int) G_IN[i].size();
    # pragma omp parallel for num_threads(thread_count)
    for(int u = 0; u < nodenum; u++){
        vector <int> tmp_deg(deg);
        queue <int> tmp_Q;
        tmp_Q.push(u);
        tmp_deg[u] = 0;
        int tmp_remove = 0;
        while(!tmp_Q.empty()){
            int v = tmp_Q.front();
            tmp_Q.pop();
            for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                    tmp_remove++;
                }
            }
        }
        X_norm[u] = tmp_remove;
    }
    return X_norm;
}

/*
vector <int> Graph:: KDSLabelGeneration(vector <int> & res){
    unordered_set <int> S_res(res.begin(), res.end());
    int edge_num = 0;
    for (int v: res){
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            if (S_res.count(*it))
                edge_num ++;
        }
    }
    edge_num = edge_num / 2; // each undirected is counted double
    vector <int> label(nodenum, edge_num);
    for (int v: res){
        for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++ )
            if(!S_res.count(*it))
                label[*it] ++;
    }
    return label;
}
*/

/*
int main(int argc, const char * argv[]) {
    string G_file;
    G_file = "/home/kfzhao/gorder/data/powergrid/powergrid.txt";
    Graph G;
    G.loadGraph(G_file);
    vector <int> S{10, 20, 30, 40, 50};
    //vector <int> res(G.ICSpread(S, 0.01));
    vector <int> res(G.LTSpread(S));
    for (int i = 0; i < 10; i++)
        cout << res[i] << endl;
    return 0;
}
*/
PYBIND11_MODULE(infSpread, m){
    pybind11::class_<Graph>(m, "Graph")
        .def(pybind11::init())
        .def("loadDirGraph", &Graph::loadDirGraph)
        .def("loadUndirGraph", &Graph::loadUndirGraph)
        .def("ICSpread", &Graph::ICSpread)
        .def("LTSpread", &Graph::LTSpread)
        .def("runIC", &Graph::runIC)
        .def("runLT", &Graph::runLT)
        .def("greedyMVCFromStart", &Graph::greedyMVCFromStart)
        .def("DSLabelGeneration", &Graph::DSLabelGeneration)
        .def("DSLabelGenerationFast", &Graph::DSLabelGenerationFast)
        .def("MVCLabelGeneration", &Graph::MVCLabelGeneration)
        .def("MVCLabelGenerationFast", &Graph::MVCLabelGenerationFast)
        .def("KDSLabelGeneration", &Graph::KDSLabelGeneration)
        .def("KCoreLabelGeneration", &Graph::KCoreLabelGeneration)
        .def("KCoreXnormGeneration", &Graph::KCoreXnormGeneration);
}