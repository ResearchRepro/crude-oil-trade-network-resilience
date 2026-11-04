#!/usr/bin/env python3
"""Normalize original country-name typos in a three-column export of a supplied annual XLSX edge list.

For provenance verification, export columns source,target,weight from the original
spreadsheet to a CSV, then run e.g.:
  python code/normalize_exported_edge_csv.py --input original_2019.csv --output fixed_2019.csv
This operation does not infer unreported country identities, merge mirror trade
reports, or assert that the original OEC retrieval can be reconstructed.
"""
from __future__ import annotations
import argparse,csv,math,collections
from pathlib import Path
MAPPING={'CuraÃ§ao':'Curacao','Curaçao':'Curacao',"Cote d'lvoire":"Cote d'Ivoire",'Côte d’Ivoire':"Cote d'Ivoire",'Hungray':'Hungary','Saint BarthÃ©lemy':'Saint Barthelemy'}
parser=argparse.ArgumentParser()
parser.add_argument('--input',required=True)
parser.add_argument('--output',required=True)
args=parser.parse_args()
sums=collections.defaultdict(float);edits=[];excluded=[]
with Path(args.input).open(newline='',encoding='utf-8-sig') as f:
 reader=csv.DictReader(f)
 names={n.lower():n for n in (reader.fieldnames or [])}
 if not {'source','target'}.issubset(names):raise ValueError('Expected columns source,target and weight or weight_usd')
 valkey=names.get('weight') or names.get('weight_usd')
 if not valkey:raise ValueError('Missing weight column')
 for rownum,record in enumerate(reader,2):
  a=record[names['source']].strip();b=record[names['target']].strip()
  ca=MAPPING.get(a,a);cb=MAPPING.get(b,b)
  if ca!=a:edits.append((rownum,'source',a,ca))
  if cb!=b:edits.append((rownum,'target',b,cb))
  try:value=float(record[valkey])
  except (TypeError,ValueError):excluded.append((rownum,'invalid_number'));continue
  if not math.isfinite(value) or value<=0 or ca==cb:excluded.append((rownum,'nonpositive_selfloop_or_nonfinite'));continue
  sums[(ca,cb)]+=value
with Path(args.output).open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['source','target','weight_usd']);w.writerows((u,v,f'{value:.4f}') for (u,v),value in sorted(sums.items()))
print(f'Directed edges: {len(sums)}; normalized country labels: {len(edits)}; excluded records: {len(excluded)}')
print('Label edits:',edits[:30]);print('Exclusions:',excluded[:30])
