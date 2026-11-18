#!/usr/bin/env python3
import csv, json, pathlib, re, urllib.parse
root=pathlib.Path(__file__).resolve().parent.parent
data=json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
entries=data['entries']; ids=set()
for e in entries:
 assert e['id'] not in ids and e['name']; ids.add(e['id'])
 assert e['status'] in ('needs_review','official','community','ended')
 for link in e['links']:
  assert urllib.parse.urlsplit(link).scheme in ('http','https') and urllib.parse.urlsplit(link).netloc
 assert e['status']=='needs_review' or e.get('verified_at'), 'Verified statuses require a date and evidence'
 if e['status'] != 'needs_review': assert e.get('evidence'), 'Verified statuses require evidence'
# Embedded data makes the page usable from a local file and GitHub Pages.
payload=json.dumps(entries,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
template=(root/'site/template.html').read_text(encoding='utf-8')
(root/'index.html').write_text(template.replace('/* CATALOG_DATA */',payload),encoding='utf-8')
with (root/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['id','name','status','verified_at','links','provenance']);w.writerows((e['id'],e['name'],e['status'],e['verified_at'] or '', ' | '.join(e['links']),e['provenance']) for e in entries)
print(f'Built {len(entries)} entries')
