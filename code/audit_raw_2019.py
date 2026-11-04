from pathlib import Path
import argparse
from zipfile import ZipFile
from io import BytesIO
from lxml import etree
import csv,collections,re,json
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Audit optional author-supplied OEC 2019 downloads against the consolidated 2019 edge list')
parser.add_argument('--raw-archive',required=True,help='Path to author-supplied OEC 2019 archive (.zip); not redistributed')
args=parser.parse_args()
OUT=ROOT/'reproduced'/'raw2019_audit'
OUT.mkdir(parents=True,exist_ok=True)
ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def parse(book):
 with ZipFile(BytesIO(book)) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   root=etree.fromstring(z.read('xl/sharedStrings.xml'))
   ss=[''.join(x.itertext()) for x in root]
  root=etree.fromstring(z.read('xl/worksheets/sheet1.xml'))
  data=[]
  for row in root.xpath('//x:sheetData/x:row',namespaces=ns):
   vals={}
   for c in row:
    r=re.match(r'([A-Z]+)',c.get('r')); v=c.find('{%s}v'%ns['x']); inline=c.find('{%s}is'%ns['x'])
    if v is not None:
     vals[r.group(1)]=ss[int(v.text)] if c.get('t')=='s' else v.text
    elif inline is not None:vals[r.group(1)]=''.join(inline.itertext())
   if vals:data.append(vals)
  return data
edge={(r['source'],r['target']):float(r['weight_usd']) for r in csv.DictReader(open(str(ROOT/'data'/'processed'/'edges_2019_cleaned.csv'),encoding='utf-8-sig'))}
allrows=[];compare=[];names=set();file_counts=[];mismatched=[]
with ZipFile(args.raw_archive) as z:
 for file in z.namelist():
  if not file.startswith('importers-of-crude-petroleum-in-2019-1') or not file.endswith('.xlsx'):continue
  name=file.replace('importers-of-crude-petroleum-in-2019-1','').replace('.xlsx','').replace(' - Copy','')
  rows=parse(z.read(file)); names.add(name)
  if not rows or rows[0].get('D')!='Imports (USD)':continue
  count=0
  for r in rows[1:]:
   if r.get('C')!='2019' or not r.get('D'):continue
   try:w=float(r['D'])
   except:continue
   partner=r.get('B','');key=(name,partner);v=edge.get(key)
   allrows.append([file,name,partner,r.get('A',''),w,v, '' if v is None else v-w])
   if v is not None:compare.append((name,partner,w,v))
   count+=1
  file_counts.append([file,name,count])
write=lambda filename,headers,rows:(lambda o:(o.writerow(headers),o.writerows(rows)))(csv.writer(open(str(OUT/filename),'w',newline='',encoding='utf-8-sig')))
write('raw_2019_crosswalk.csv',['source_file','reporter_as_source','partner_as_target','partner_iso3','raw_importers_usd','consolidated_edge_usd','consolidated_minus_raw'],allrows)
write('raw_2019_files.csv',['filename','reporter','rows_2019'],file_counts)
valid=[r for r in allrows if r[5] is not None]
ident=[r for r in valid if abs(r[5]-r[4])<1e-8]
close=[r for r in valid if abs(r[5]-r[4])/max(1,r[4])<=.01]
print(json.dumps({'n_files':len(file_counts),'raw_entries':len(allrows),'matched_directional_pairs':len(valid),'exact_value_match':len(ident),'within_1pct':len(close),'raw_no_edge_count':len(allrows)-len(valid),'raw_reporters_distinct':len(names),'raw_unmatched_names':sorted(names - set(x[0] for x in edge))[:30],'example_value_comparisons':[(a,b,x,y) for a,b,x,y in compare[:6]]},indent=2))
with open(str(OUT/'raw_2019_audit_summary.json'),'w') as f:json.dump({'n_files':len(file_counts),'raw_entries':len(allrows),'matched_directional_pairs':len(valid),'exact_value_match':len(ident),'within_1pct':len(close),'raw_no_edge_count':len(allrows)-len(valid),'example_values':compare[:8]},f,indent=2)
