#!/usr/bin/env python3
"""Reproduce paper's numerical analysis from the published cleaned author edge lists.
Usage: python code/reproduce_analysis.py
Dependencies: networkx numpy scipy matplotlib
Deterministic seed values for community detection, attacks and null checks.
Does NOT reconstruct the original OEC scraping, which remains provenance-limited.
"""
from __future__ import annotations
import csv,json,random,math,collections
from pathlib import Path
import networkx as nx
import numpy as np
from scipy.stats import spearmanr
from scipy.optimize import minimize_scalar
from scipy.special import zeta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data'/'processed'
OUT=ROOT/'reproduced';OUT.mkdir(exist_ok=True)
(OUT/'figures').mkdir(exist_ok=True)
(OUT/'networks').mkdir(exist_ok=True)

def write(file,head,rows):
 with (OUT/file).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(head);w.writerows(rows)

def load(year):
 # Use the canonical GEXF to preserve the graph insertion order used when
 # calculating the published Louvain/seed-dependent partitions and attacks.
 # Equivalent sorted CSV edge lists are also provided and can be checked.
 G=nx.read_gexf(ROOT/'networks'/f'oil_trade_{year}_directed_weighted.gexf')
 with (SOURCE/f'edges_{year}_cleaned.csv').open(encoding='utf-8-sig',newline='') as f:
  edge_rows=list(csv.DictReader(f))
 assert len(edge_rows)==G.number_of_edges()
 assert all(G.has_edge(row['source'],row['target']) and abs(G[row['source']][row['target']]['weight']-float(row['weight_usd']))<1e-4 for row in edge_rows)
 return G

def weighted_projection(G):
 U=nx.Graph();U.add_nodes_from(G.nodes)
 for a,b,d in G.edges(data=True):
  if U.has_edge(a,b): U[a][b]['weight']+=float(d['weight'])
  else: U.add_edge(a,b,weight=float(d['weight']))
 return U

def efficiency(G):
 total=0.0
 for v in G:
  for dst,dist in nx.single_source_shortest_path_length(G,v).items():
   if dist>0:total+=1.0/dist
 return total/(len(G)*(len(G)-1))

def attack(G,mode):
 U=G.to_undirected();nodes=list(G);n=len(nodes)
 if mode=='targeted':orders=[sorted(nodes,key=lambda x:G.degree(x),reverse=True)]
 else:
  rng=random.Random(20261102);orders=[rng.sample(nodes,n) for _ in range(70)]
 rows=[]
 for pct in range(0,101,10):
  k=min(n,round(n*pct/100));vals=[]
  for order in orders:
   H=U.copy();H.remove_nodes_from(order[:k]);
   lcc=max((len(c) for c in nx.connected_components(H)),default=0)
   vals.append(lcc/max(1,n-k))
  rows.append((pct,float(np.mean(vals)),float(np.std(vals))))
 return rows

def fit_degree(G,year):
 rows=[]
 for side in ['in','out']:
  arr=np.array([d for _,d in (G.in_degree() if side=='in' else G.out_degree()) if d>0],dtype=float)
  mean=arr.mean();p=1/mean;n=len(arr)
  ll_geometric=(np.log(p)+(arr-1)*np.log(1-p)).sum()
  fn=lambda a:n*np.log(zeta(a,1))+a*np.log(arr).sum()
  best=minimize_scalar(fn,bounds=(1.01,8),method='bounded')
  rows += [(year,side,'geometric',n,float(p),float(-2*ll_geometric+2)),(year,side,'zipf',n,float(best.x),float(2*fn(best.x)+2))]
 return rows

def run():
 Gs={y:load(y) for y in (2017,2019,2020)}
 summary=[];metric_by_year={};central_rows={};curves=[];seedrows=[];communityrows=[];thresholdrows=[];fitrows=[];nullrows=[];distrows=[]
 for year,G in Gs.items():
  U=weighted_projection(G);n=len(G);m=G.number_of_edges()
  i=dict(G.in_degree());o=dict(G.out_degree());si=dict(G.in_degree(weight='weight'));so=dict(G.out_degree(weight='weight'))
  h=nx.harmonic_centrality(G.reverse());h={k:v/(n-1) for k,v in h.items()}
  bet=nx.betweenness_centrality(G,normalized=True,weight=None)
  hub,authority=nx.hits(G,max_iter=300,normalized=True)
  communities=nx.community.louvain_communities(U,weight='weight',resolution=1,seed=46)
  community={node:j for j,c in enumerate(communities) for node in c}
  q=nx.community.modularity(U,communities,weight='weight')
  stats={'year':year,'nodes':n,'directed_edges':m,'density':nx.density(G),'mean_in_degree':m/n,'mean_total_degree':2*m/n,'weak_components':nx.number_weakly_connected_components(G),'strong_components':nx.number_strongly_connected_components(G),'lcc_weak_size':len(max(nx.weakly_connected_components(G),key=len)),'mean_undirected_clustering':nx.average_clustering(U),'weighted_clustering':nx.average_clustering(U,weight='weight'),'directed_global_efficiency':efficiency(G),'trade_total_usd':sum(d['weight'] for a,b,d in G.edges(data=True)),'weighted_modularity':q,'communities':len(communities)}
  summary.append(stats)
  central_rows[year]=[]
  metric_by_year[year]={'in_degree':i,'out_degree':o,'in_strength_usd':si,'out_strength_usd':so,'harmonic_out':h,'betweenness':bet,'hub_score':hub,'authority_score':authority}
  for node in sorted(G):
   central_rows[year].append([node,i[node],o[node],si[node],so[node],h[node],bet[node],hub[node],authority[node],community[node]])
   G.nodes[node].update(in_degree=i[node],out_degree=o[node],in_strength_usd=float(si[node]),out_strength_usd=float(so[node]),harmonic_out=float(h[node]),betweenness=float(bet[node]),hub_score=hub[node],authority_score=authority[node],community=community[node])
  write(f'centrality_{year}.csv',['country','in_degree','out_degree','in_strength_usd','out_strength_usd','harmonic_out','betweenness','hub_score','authority_score','community'],central_rows[year])
  nx.write_gexf(G,OUT/'networks'/f'oil_trade_{year}.gexf')
  for direction,ds in [('in_degree',i),('out_degree',o)]:
   for deg,count in collections.Counter(ds.values()).items():distrows.append((year,direction,deg,count))
  for j,c in enumerate(communities):
   top=sorted(c,key=lambda x:so[x]+si[x],reverse=True)[:8]
   communityrows.append((year,j,len(c),'; '.join(top)))
  for seed in range(20):
   comm=nx.community.louvain_communities(U,weight='weight',resolution=1,seed=1000+seed)
   seedrows.append((year,seed,nx.community.modularity(U,comm,weight='weight'),len(comm)))
  for mode in ['random','targeted']:
   for p,v,sd in attack(G,mode):curves.append((year,mode,p,v,sd))
  for cutoff in [0,1000,1000000,10000000]:
   H=nx.DiGraph((a,b,d) for a,b,d in G.edges(data=True) if d['weight']>=cutoff)
   H.add_nodes_from(G)
   thresholdrows.append((year,cutoff,H.number_of_edges(),nx.density(H),nx.number_weakly_connected_components(H),len(max(nx.weakly_connected_components(H),key=len))))
  fitrows.extend(fit_degree(G,year))
  obs=nx.average_clustering(U)
  for seed in range(25):
   H=U.copy()
   try:nx.double_edge_swap(H,nswap=3*H.number_of_edges(),max_tries=80*H.number_of_edges(),seed=random.Random(seed+year))
   except nx.NetworkXAlgorithmError:pass
   nullrows.append((year,seed,nx.average_clustering(H),obs))
  print(f'{year}: n={n}, edges={m}, density={stats["density"]:.5f}, efficiency={stats["directed_global_efficiency"]:.5f}, Q={q:.5f}')
 write('network_summary.csv',list(summary[0]),[[r[k] for k in summary[0]] for r in summary])
 write('degree_distribution.csv',['year','measure','degree','frequency'],sorted(distrows))
 write('degree_distribution_model_fit.csv',['year','side','model','positive_degree_nodes','fitted_parameter','AIC'],fitrows)
 write('communities.csv',['year','community_id','size','leading_trade_nodes'],communityrows)
 write('community_seed_stability.csv',['year','seed_index','modularity','number_communities'],seedrows)
 write('removal_curves.csv',['year','mode','percent_removed','lcc_fraction_surviving','sd'],curves)
 write('threshold_sensitivity.csv',['year','minimum_usd','edges','density','weak_components','largest_weak_component'],thresholdrows)
 write('degree_preserving_null.csv',['year','replicate','null_clustering','observed_clustering'],nullrows)
 rank=[]
 for a,b in [(2017,2019),(2019,2020),(2017,2020)]:
  same=sorted(set(Gs[a])&set(Gs[b]))
  for measure in ['in_degree','out_degree','in_strength_usd','out_strength_usd','harmonic_out','hub_score','authority_score']:
   va=[metric_by_year[a][measure][x] for x in same];vb=[metric_by_year[b][measure][x] for x in same]
   rank.append((a,b,measure,len(same),spearmanr(va,vb).statistic))
 write('rank_stability.csv',['year_start','year_end','metric','common_nodes','spearman_rho'],rank)
 # Regenerate empirical figure panels with transparent coding; conceptual diagrams are provided as editable SVG assets.
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
 def savefig(name):
  plt.tight_layout();plt.savefig(OUT/'figures'/(name+'.png'),dpi=240);plt.savefig(OUT/'figures'/(name+'.svg'));plt.close()
 fig,axs=plt.subplots(1,3,figsize=(15,5));pool=nx.Graph()
 for G in Gs.values():
  for u,v,d in G.edges(data=True):pool.add_edge(u,v,weight=pool.get_edge_data(u,v,default={}).get('weight',0)+np.log1p(d['weight']))
 pos=nx.spring_layout(pool,seed=46,weight='weight',iterations=170,k=.25)
 for ax,(year,G) in zip(axs,Gs.items()):
  nx.draw_networkx_edges(G,pos,ax=ax,edge_color='#86A3B6',alpha=.24,arrows=False,width=.35)
  nx.draw_networkx_nodes(G,pos,ax=ax,node_size=[12+15*np.sqrt(G.degree(x)) for x in G],node_color=[G.nodes[x]['community'] for x in G],cmap='tab20',vmin=0,vmax=12,edgecolors='white',linewidths=.2)
  ax.set_title(str(year));ax.axis('off')
 fig.suptitle('Directed crude-petroleum trade networks, with weighted Louvain groups');savefig('network_triptych')
 fig,ax=plt.subplots(figsize=(9,5))
 for name,label in [('density','Directed density'),('mean_undirected_clustering','Undirected clustering'),('directed_global_efficiency','Directed efficiency')]:
  ax.plot([str(x['year']) for x in summary],[x[name] for x in summary],marker='o',label=label)
 ax.legend();ax.grid(alpha=.2);ax.set_ylabel('Value');savefig('network_statistics')
 fig,axs=plt.subplots(1,2,figsize=(12,5))
 for ax,side in zip(axs,['in','out']):
  for y,G in Gs.items():
   vals=[d for _,d in (G.in_degree() if side=='in' else G.out_degree()) if d>0]
   counts=collections.Counter(vals)
   ax.scatter(sorted(counts),[counts[v] for v in sorted(counts)],s=14,label=str(y))
  ax.set_xscale('log');ax.set_yscale('log');ax.set_title(side.title()+'-degree');ax.set_xlabel('Degree');ax.set_ylabel('Count');ax.legend()
 savefig('degree_distribution')
 fig,axs=plt.subplots(1,3,figsize=(15,5))
 for ax,(year,G) in zip(axs,Gs.items()):
  top=sorted(G.nodes,key=lambda x:metric_by_year[year]['out_strength_usd'][x],reverse=True)[:8][::-1]
  ax.barh(top,[metric_by_year[year]['out_strength_usd'][x]/1e9 for x in top]);ax.set_title(str(year));ax.set_xlabel('US$ bn')
 savefig('out_strength')
 fig,ax=plt.subplots(figsize=(9,5))
 for year in Gs:
  for mode,style in [('random','-'),('targeted','--')]:
   subset=[r for r in curves if r[0]==year and r[1]==mode]
   ax.plot([r[2] for r in subset],[r[3] for r in subset],style,marker='o',label=f'{year} {mode}')
 ax.set(xlabel='Nodes removed (%)',ylabel='Largest weak component / survivors');ax.legend(ncol=2);ax.grid(alpha=.2)
 savefig('node_removal')
 fig,ax=plt.subplots(figsize=(9,5))
 for year in Gs:
  subset=[r for r in thresholdrows if r[0]==year]
  ax.plot([r[1] for r in subset],[r[5]/len(Gs[year]) for r in subset],marker='o',label=str(year))
 ax.set(xscale='symlog',xlabel='Minimum edge value (US$)',ylabel='Largest weak component / original nodes');ax.legend();ax.grid(alpha=.2)
 savefig('threshold_sensitivity')
 (OUT/'RUN_METADATA.json').write_text(json.dumps({'seed_layout':46,'seed_communities':46,'community_test_seeds':'1000–1019','removal_random_replicates':70,'null_rewires':25,'observations':[2017,2019,2020],'weight_units':'USD'},indent=2))
 print('Completed reproducible outputs in',OUT)

if __name__=='__main__':run()
