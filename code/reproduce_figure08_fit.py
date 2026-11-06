#!/usr/bin/env python3
"""Recreate Figure 8 of the crude-oil trade manuscript.
Run from repository root after `python code/reproduce_analysis.py`.
Dependencies: networkx numpy scipy matplotlib.
The plot displays observed positive degrees and independently fitted
shifted-geometric and Zipf probability masses. Model parameters/AIC are
recomputed from the supplied graphs, with no fabricated observations.
"""
from pathlib import Path
import csv,collections,math
import networkx as nx
import numpy as np
from scipy.special import zeta
from scipy.optimize import minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
GRAPHS=ROOT/'reproduced'/'networks'
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
SUP=ROOT/'supplementary';SUP.mkdir(exist_ok=True)
fig,axs=plt.subplots(2,3,figsize=(13.8,7.3))
rows=[]
for col,year in enumerate([2017,2019,2020]):
    path=GRAPHS/f'oil_trade_{year}.gexf'
    if not path.exists():raise SystemExit(f'Missing {path}. Run code/reproduce_analysis.py first.')
    G=nx.read_gexf(path)
    for row,side in enumerate(['in','out']):
        sample=np.asarray([v for _,v in (G.in_degree() if side=='in' else G.out_degree()) if v>0],dtype=float)
        n=len(sample);p=1/sample.mean()
        logL_g=np.sum(np.log(p)+(sample-1)*np.log1p(-p))
        fn=lambda a:n*np.log(zeta(a,1))+a*np.log(sample).sum()
        optimal=minimize_scalar(fn,bounds=(1.01,8),method='bounded')
        alpha=float(optimal.x)
        AICg=float(-2*logL_g+2);AICz=float(2*fn(alpha)+2)
        rows.extend([(year,side,'geometric',n,p,AICg),(year,side,'zipf',n,alpha,AICz)])
        cnt=collections.Counter(sample.astype(int));ks=sorted(cnt)
        grid=np.arange(1,max(ks)+1)
        ax=axs[row,col]
        ax.scatter(ks,[cnt[k]/n for k in ks],s=20,color='#1f4e79',label='Observed',zorder=4)
        ax.plot(grid,p*np.power(1-p,grid-1),color='#e0842b',lw=1.7,label='Geometric MLE')
        ax.plot(grid,1/(zeta(alpha,1)*np.power(grid,alpha)),color='#45856b',ls='--',lw=1.7,label='Zipf MLE')
        ax.set_xscale('log');ax.set_yscale('log');ax.set_ylim(1e-5,1.05)
        ax.set_title(f'{year} — {side}-degree (n={n})',fontsize=11)
        ax.set_xlabel('Positive degree (k)',fontsize=10)
        if col==0:ax.set_ylabel('Probability mass',fontsize=10)
        ax.grid(alpha=.15)
        best='Geometric' if AICg<AICz else 'Zipf'
        ax.text(.03,.05,f'AIC: geom. {AICg:.1f} | Zipf {AICz:.1f}\nLower AIC: {best}',transform=ax.transAxes,fontsize=8,va='bottom',bbox=dict(facecolor='white',edgecolor='#ccc',alpha=.9,pad=4))
handles,labels=axs[0,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',ncol=3,bbox_to_anchor=(.5,.995),frameon=False)
fig.suptitle('Observed positive-degree probabilities and fitted discrete distributions',fontsize=14,y=1.032)
fig.tight_layout(rect=[0,0,1,.975])
for fmt in ['png','svg']:
    fig.savefig(OUT/f'Figure_08_Positive_Degree_Fits.{fmt}',dpi=220,bbox_inches='tight',facecolor='white')
plt.close(fig)
with open(SUP/'Degree_Distribution_Fit_AIC_Parameters.csv','w',encoding='utf-8-sig',newline='') as file:
    w=csv.writer(file);w.writerow(['year','side','model','positive_degree_nodes','fitted_parameter','AIC']);w.writerows(rows)
print('Figure 8 and fit table written to figures/ and supplementary/')
