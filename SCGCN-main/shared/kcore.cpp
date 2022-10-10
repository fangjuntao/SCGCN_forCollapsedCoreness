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
    degree.resize(nodenum);
    
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
    for(int i = 0; i < nodenum; i++)
        degree[i] = (int) G_IN[i].size();
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
    degree.resize(nodenum);
    
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
    for(int i = 0; i < nodenum; i++)
        degree[i] = (int) G_IN[i].size();
    cout << "the number of node:" << node_count << endl;
    cout << "the number of edge:" << edge_count << endl;
    cout << "# nodes have in-neigs: " << G_IN.size() << endl;
    cout << "# nodes have out-neigs: " << G_OUT.size() << endl;
    
    infile.close();
}

/*
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
    vector <int> deg(degree);

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
*/

vector <int> Graph:: KCoreLabelGeneration(int k, vector<int> &res){   
    vector <int> deg(degree);
    
    queue<int> Q;
    for (const int v : res){
        Q.push(v);
        deg[v] = 0;
    }
    int remove = 0;
    while(!Q.empty()){
        int v = Q.front();
        Q.pop();
        remove++;
        for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            deg[*it] --;
            if (deg[*it] == k-1){
                Q.push(*it);
            }
        }
    }//end while
     vector <int> label(nodenum, remove);
    # pragma omp parallel for num_threads(thread_count)
    for (int u = 0; u < nodenum; u++){  //compute the collapse of nodes of res + u
        if (deg[u] < k)  // u is already removed because of removing res
            continue;
        vector<int> tmp_deg(deg);
        queue <int> tmp_Q;
        
        tmp_Q.push(u);
        tmp_deg[u] = 0;
        int tmp_remove = 0;
        while(!tmp_Q.empty()){
            int v = tmp_Q.front();
            tmp_Q.pop();
            tmp_remove++;
            for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                }
            }
        }//end while
        label[u] += tmp_remove;
    }
    return label;
}

vector <int>  Graph:: KCoreXnormGeneration(int k){
    vector <int> X_norm(nodenum, 0);
    vector <int> deg(degree);

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
            tmp_remove++;
            for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                }
            }
        }
        X_norm[u] = tmp_remove;
    }
    return X_norm;
}


vector <int> Graph:: KCoreRemoveNode(int k, vector <int> & idx){
    vector <int> remove_node;
    vector <int> deg(degree);
    
    queue <int> Q;
    for (const int i: idx){
        Q.push(i);
        deg[i] = 0;
    }
    while(!Q.empty()){
        int v = Q.front();
        Q.pop();
        remove_node.push_back(v);
        for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            deg[*it] --;
            if (deg[*it] == k-1)
                Q.push(*it);
        }
    }
    return remove_node;
}

vector <int> Graph:: KCoreLabelGeneration2(int k, vector<int> &idx){
    int num_undomin = (int) un_dominated.size();
    vector <int> deg(degree);
    
    queue<int> Q;
    for (const int i : idx){
        int v = un_dominated[i];
        Q.push(v);
        deg[v] = 0;
    }
    int remove = 0;
    while(!Q.empty()){
        int v = Q.front();
        Q.pop();
        remove++;
        for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
            deg[*it] --;
            if (deg[*it] == k-1){
                Q.push(*it);
            }
        }
    }//end while
    vector <int> label(num_undomin, remove);
    # pragma omp parallel for num_threads(thread_count)
    for (int i = 0; i < num_undomin; i++){  //compute the collapse of nodes of res + u
        int u = un_dominated[i];
        if (deg[u] < k)  // u is already removed because of removing res
            continue;
        vector<int> tmp_deg(deg);
        queue <int> tmp_Q;
        
        tmp_Q.push(u);
        tmp_deg[u] = 0;
        int tmp_remove = 0;
        while(!tmp_Q.empty()){
            int v = tmp_Q.front();
            tmp_Q.pop();
            tmp_remove++;
            for (Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                }
            }
        }//end while
        label[i] += tmp_remove;
    }
    return label;
}


vector <int> Graph:: KCoreCollapseDominate(int k){
    vector <Adjlist> dominance;
    dominance.resize(nodenum);
    vector <int> deg(degree);
    
    # pragma omp parallel for num_threads(thread_count)
    for(int u = 0; u < nodenum; u++){
        vector <int> tmp_deg(deg);
        queue <int> tmp_Q;
        tmp_Q.push(u);
        tmp_deg[u] = 0;
        
        while(!tmp_Q.empty()){
            int v = tmp_Q.front();
            tmp_Q.pop();
            dominance[u].push_back(v); //save the deleted node
            for(Adjlist:: iterator it = G_IN[v].begin(); it != G_IN[v].end(); it++){
                tmp_deg[*it] --;
                if (tmp_deg[*it] == k-1){
                    tmp_Q.push(*it);
                }
            }
        }
        sort(dominance[u].begin(), dominance[u].end());
    }
    //find the dominated vertex
    unordered_set <int> dominated;
    for (int u = 0; u < nodenum; u++){
        for (int v: dominance[u]){
            if (dominance[v].size() < dominance[u].size() && //dom[v] is a true subset of dom[u]
                includes(dominance[u].begin(), dominance[u].end(), dominance[v].begin(), dominance[v].end()))
                dominated.insert(v);
        }
    }
    vector <int> X_norm;
    for (int u = 0; u < nodenum; u++)
        if (!dominated.count(u)){
            un_dominated.push_back(u);
            X_norm.push_back((int) dominance[u].size());
        }
    //cout << "# the un_dominated vertex: " << un_dominated.size() << endl;
    return X_norm;
}

vector <int> Graph:: getUnDominated(){
    return un_dominated;
}


PYBIND11_MODULE(kcore, m){
    pybind11::class_<Graph>(m, "Graph")
        .def(pybind11::init())
        .def("loadDirGraph", &Graph::loadDirGraph)
        .def("loadUndirGraph", &Graph::loadUndirGraph)
        .def("KCoreRemoveNode", &Graph::KCoreRemoveNode)
        .def("KCoreLabelGeneration", &Graph::KCoreLabelGeneration)
        .def("KCoreLabelGeneration2", &Graph::KCoreLabelGeneration2)
        .def("KCoreXnormGeneration", &Graph::KCoreXnormGeneration)
        .def("KCoreCollapseDominate", &Graph::KCoreCollapseDominate)
        .def("getUnDominated", &Graph::getUnDominated);
}