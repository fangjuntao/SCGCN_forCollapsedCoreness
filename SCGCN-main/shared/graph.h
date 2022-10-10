//
//  graph.h
//  infSpread
//
//  Created by Kangfei Zhao on 1/12/2018.
//  Copyright © 2018 Kangfei Zhao. All rights reserved.
//

#pragma once
#ifndef _GRAPH_H
#define _GRAPH_H
#include <iostream>
#include <fstream>
#include <sstream>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <chrono>
#include <random>
#include <algorithm>
#include <string.h>
#include <vector>
#include <queue>
#include <map>
#include <set>
#include <unordered_set>
#include <unordered_map>

using namespace std;

typedef int NodeID;
typedef vector<NodeID> Adjlist;

class Graph {
public:
    map <NodeID, NodeID> node_dict;
    vector <Adjlist> G_IN ;
    vector <Adjlist> G_OUT;
    vector <int> un_dominated;
    vector <int> degree;
    
    long nodenum;
    long edgenum;
    
    Graph();
    ~Graph();
    void loadDirGraph(const string filename);
    void loadUndirGraph(const string filename);
    vector <int> ICSpread(vector <int> & S, float p);
    vector <int> LTSpread(vector <int> & S);
    vector <int> runIC(vector <int> & S, float p);
    vector <int> runLT(vector <int> & S);

    vector <int> greedyMVCFromStart(int k, int start);
    vector <int> DSLabelGeneration(vector <int> & res);
    vector <int> DSLabelGenerationFast(vector <int> & res);
    vector <int> MVCLabelGeneration(vector <int> & res);
    vector <int> MVCLabelGenerationFast(vector <int> & res);
    vector <int> KDSLabelGeneration(vector <int> & res);
    vector <int> KCoreRemoveNode(int k, vector <int> & idx);
    vector <int> KCoreLabelGeneration(int k, vector <int> & res);
    vector <int> KCoreLabelGeneration2(int k, vector <int> & idx);
    vector <int> KCoreCollapseDominate(int k);
    vector <int> KCoreXnormGeneration(int k);
    vector <int> getUnDominated();
    
};

struct pair_hash
{
    template <class T1, class T2>
    std::size_t operator () (std::pair<T1, T2> const &pair) const
    {
        std::size_t h1 = std::hash<T1>()(pair.first);
        std::size_t h2 = std::hash<T2>()(pair.second);
        
        return h1 ^ h2;
    }
};

#endif
