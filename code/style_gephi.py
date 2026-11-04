#!/usr/bin/env python3
"""Ensure canonical directed weighted GEXF files open with node positions, colors and sizes in Gephi."""
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]
PALETTE=['#2C699A','#BF623B','#588C62','#9467BD','#C49B35','#50A4AF','#9A5F78','#7F7F7F','#A6732C']
for year in (2017,2019,2020):
 path=ROOT/'networks'/f'oil_trade_{year}_directed_weighted.gexf'
 G=nx.read_gexf(path)
 for node,data in G.nodes(data=True):
  col=PALETTE[int(data.get('community',0))%len(PALETTE)]
  r,g,b=[int(col[k:k+2],16) for k in (1,3,5)]
  G.nodes[node]['viz']={
   'position':{'x':float(data.get('viz_x',0)),'y':float(data.get('viz_y',0)),'z':0.0},
   'color':{'r':r,'g':g,'b':b,'a':0.9},
   'size':float(7+1.7*(G.degree(node)**0.55)),
  }
 nx.write_gexf(G,path,version='1.2draft')
 check=nx.read_gexf(path)
 assert check.number_of_edges()==G.number_of_edges()
 assert check.nodes[next(iter(check.nodes))]['viz']['position']
 print(year,'styled',len(G),'nodes',G.number_of_edges(),'directed edges')
