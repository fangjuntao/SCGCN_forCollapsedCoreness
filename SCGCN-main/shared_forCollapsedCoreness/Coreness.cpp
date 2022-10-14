#include <bits/stdc++.h>
#include "glist.h"

#define PII pair<int,int>
#define inf 0x3fffffff
using namespace std;
const int maxn=10000,maxm=100000;
int n,m,ppp[maxn],pre[maxn],followers[maxn],collapsed[maxn],update[maxn],critical[maxn];
struct nodes{
    int coreness,degree,binpos,valid;
}node[maxn],tmp[maxn],save[maxn],tmp2[maxn];
struct Sort{
    int l,r;
}a[maxn];
vector<int> edge[maxn];
struct Edge{
    vector<int> More,Equal,Less;
}edges[maxn];
int budget;
vector<int> bin[maxn],hier,tid_;
int bb[maxn],cur_k;
int lowerbound[maxn],upperbound[maxn];
struct LCPSTreeVertex{
	vector<int> delta;
	vector<LCPSTreeVertex*> son;
	LCPSTreeVertex *p;
	int id;
	short k;
};
vector<LCPSTreeVertex*> t_;

extern "C"{ // 重要，因为使用g++编译时函数名会改变，比方print_msg(const char*)
            // 会编译成函数名 print_msg_char，这会导致python调用这个函数的时候
            // 找不到对应的函数名，这有加了 extern "C"，才会以C语言的方式进行
            // 编译，这样不会改变函数名字
void ReadEdgesS(int n, int m)
{
    srand(time(NULL));
    int v1,v2,k=0;
    for (int i=1;i<=m;i++)
    {
        scanf("%d%d", &v1, &v2);
        if (v1 > v2) swap(v1, v2);
        const auto e = make_pair(v1, v2);
        edge[v1].push_back(v2);
        edge[v2].push_back(v1);
        node[v1].degree++,node[v2].degree++;
    }
    for (int i=0;i<=n;i++)
        save[i]=node[i];
}

void __adjust_k(int target_k)
{
	if (cur_k < target_k) {
		int times = target_k - cur_k;
		hier.push_back(times * -2);
	}
	else if (cur_k > target_k) {
		int times = cur_k - target_k;
		hier.push_back(times * -2 + 1);
	}
	cur_k = target_k;
}

pair<char, int> decode_adjust(int mask)
{
	mask = -mask;
	if (mask & 1) {
		return make_pair(']', mask / 2 + 1);
	}
	else {
		return make_pair('[', mask / 2);
	}
}

void get_v(LCPSTreeVertex * rt, vector<int> & res)
{
	for (int v : rt->delta) {
		res.push_back(v);
	}
	for (auto p : rt->son) {
		get_v(p, res);
	}
}

vector<int> get_v(int v)
{
	vector<int> res;
	get_v(t_[tid_[v]], res);
	return res;
}

void __build_hier(vector<vector<int>> graph,vector<int> core,int n,int max_coreness)
{
	int kmax = max_coreness;
	vector<vector<int>*> R;
	R.resize(kmax + 1);
	for (int i = 0; i <= kmax; i++) {
		R[i] = new vector<int>;
	}
	vector<bool> vis(n, false);
	cur_k = -1;

	for (int i = 0; i < n; i++) {
		int cur_v = i;
		if (vis[cur_v]) continue;

		int cur_rmax = 0;
		R[0]->push_back(cur_v);
		while (true) {
			while (true) {
				if (cur_rmax < 0) break;
				if (R[cur_rmax]->empty()) {
					cur_rmax--;
					continue;
				}
				cur_v = R[cur_rmax]->back();
				R[cur_rmax]->pop_back();
				if (!vis[cur_v]) break;
			}
			if (cur_rmax < 0) break;

			if (cur_k > cur_rmax) __adjust_k(cur_rmax);
			int cv = core[cur_v];
			if (cv > cur_rmax) __adjust_k(cv);
			hier.push_back(cur_v);
			vis[cur_v] = true;
            for (auto nbr : graph[cur_v])
            {
				if (vis[nbr]) continue;
				int mn = min(core[cur_v], core[nbr]);
				cur_rmax = max(mn, cur_rmax);
				R[mn]->push_back(nbr);
			}
		}
		__adjust_k(-1);
	}
	for (int i = 0; i <= kmax; i++) {
		delete R[i];
	}
}

void __build_tree()
{
	LCPSTreeVertex *root = new LCPSTreeVertex;
	t_.push_back(root);
	LCPSTreeVertex *cur_tv = root;
	int cur_k = -1;
	for (int v : hier) {
		if (v < 0) {
			char op;
			int times;
			tie(op, times) = decode_adjust(v);
			if (op == '[') {
				while (times--) {
					LCPSTreeVertex *nxt_tv = new LCPSTreeVertex;
					nxt_tv->p = cur_tv;
					cur_tv->son.push_back(nxt_tv);
					cur_tv = nxt_tv;
					t_.push_back(nxt_tv);
				}
			}
			else if (op == ']') {
				while (times--) cur_tv = cur_tv->p;
			}
		}
		else {
			cur_tv->delta.push_back(v);
		}
	}
	hier.clear();
}

LCPSTreeVertex* dfs(LCPSTreeVertex* cur, vector<LCPSTreeVertex*> &store, LCPSTreeVertex* p)
{
	if (cur->delta.empty()) {
		auto pt = cur->son[0];
		delete cur;
		return dfs(pt, store, p);
	}
	else {
		cur->p = p;
		store.push_back(cur);
		for (int i = 0; i < cur->son.size(); i++) {
			cur->son[i] = dfs(cur->son[i], store, cur);
		}
		return cur;
	}
}

void __compress_tree(int n)
{
	vector<LCPSTreeVertex*> new_tv;
	LCPSTreeVertex *root = t_[0];
	for (int i = 0; i < root->son.size(); i++) {
		root->son[i] = dfs(root->son[i], new_tv, root);
		root->son[i]->p = NULL;
	}
	tid_ = vector<int>(n, 0);
	for (int i = 0; i < new_tv.size(); i++) {
		new_tv[i]->id = i;
		for (auto v : new_tv[i]->delta) {
			tid_[v] = i;
		}
	}
	t_ = new_tv;
	delete root;
}

void pre_LCPS(vector<vector<int>> graph,vector<int> core,int n,int max_coreness)
{
    hier.clear();cur_k=0;
    t_.clear();tid_.clear();
    __build_hier(graph,core,n,max_coreness);
	__build_tree();
	__compress_tree(n);
}


struct CCT{
    int id,layer;
}tree[maxn];
int nodeCCT,CCT_size[maxn],CCT_ance_size[maxn],CCT_child_size[maxn],CCT_fa[maxn];
vector<int> CCTchild[maxn];

void BuildCCT(int n,vector<int> G,vector<int> core,int fa,int Min_core)
{
    nodeCCT++;
    //cout<<nodeCCT<<endl;
    CCT_fa[nodeCCT]=fa;
    CCTchild[nodeCCT].clear();
    CCT_size[nodeCCT]=0;
    CCT_child_size[nodeCCT]=0;
    CCT_ance_size[nodeCCT]=CCT_ance_size[fa]+CCT_size[fa];
    for (auto x:G)
        if (Min_core==core[x])
            tree[x].id=nodeCCT,CCT_size[nodeCCT]++;
        else break;
    for (auto x:G)
        if (tree[x].id==0)
        {
            vector<vector<int> > bin(n+1);
            vector<int> nodes;
            nodes=get_v(x);
            int Min_coreness=core[x];
            for (auto y:nodes)
                bin[core[y]].push_back(y),
                Min_coreness=min(Min_coreness,core[y]);
            nodes.clear();
            for (int i=Min_coreness;i<=n;i++)
                    for (auto y:bin[i])
                        nodes.push_back(y);
            if (nodes.size()>0)
            {
                int id=nodeCCT,child=nodeCCT+1;
                CCTchild[id].push_back(child);
                BuildCCT(n,nodes,core,nodeCCT,Min_coreness);
                CCT_child_size[id]+=CCT_child_size[child]+CCT_size[child];
            }
        }
}
int ub(int x)
{
    x=tree[x].id;
    return CCT_ance_size[x]+CCT_size[x];
}
int upper_bound(int n,int x,vector<int> core)
{
    unordered_set<int> s;
    int sum=0;
    for (auto y:edges[x].Equal)
        if (!collapsed[y]&&critical[y])
        {
            if (s.find(tree[y].id)==s.end()) sum+=CCT_size[tree[y].id],s.insert(tree[y].id);
        }
    for (auto y:edges[x].Less)
        if (!collapsed[y]&&critical[y])
        {
            if (s.find(tree[y].id)==s.end()) sum+=CCT_size[tree[y].id],s.insert(tree[y].id);
        }
    return sum;
}
int lower_bound(int x)
{
    int sum=0;
    for (auto y:edges[x].Equal)
        if (!collapsed[y]&&critical[y]) sum++;
    for (auto y:edges[x].Less)
        if (!collapsed[y]&&critical[y]) sum++;
    return sum;
}


vector<int> getCoreness(string input_txt)
{

    int n, m;
    char input[100],output[100];
    // budget=atoi(argv[2]);
    sprintf(input,"%s.txt","data");
    // sprintf(output,"%s-%d-GCC.txt",argv[1],budget);
    freopen(input,"r",stdin);
    //freopen(output,"w",stdout);
    scanf("%d%d",&n,&m);
    // read the graph
    ReadEdgesS(n, m);
    // initialize the core component
    core::CoreMaintenance* cm = nullptr;  //函数指针
    cm = new core::GLIST(n);   //构造函数
    // create the adjacent list representation
    vector<vector<int>> graph(n);
    for (int i=0;i<n;i++)
        graph[i]=edge[i];
    vector<int> core(n);
    cm->ComputeCore(graph, true, core);
    return core ;
}




}
