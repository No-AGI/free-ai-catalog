#!/usr/bin/env python3
import csv,json,pathlib,urllib.parse
root=pathlib.Path(__file__).resolve().parent.parent
data=json.loads((root/'data/catalog.json').read_text(encoding='utf-8'));entries=data['entries'];ids=set()
for e in entries:
 assert e['id'] not in ids and e['name'];ids.add(e['id'])
 assert e['status'] in ('needs_review','official','community','ended')
 for link in e['links']:
  u=urllib.parse.urlsplit(link);assert u.scheme in ('http','https') and u.netloc
 assert e['status']=='needs_review' or (e.get('verified_at') and e.get('evidence'))
payload=json.dumps(entries,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
(root/'index.html').write_text((root/'site/template.html').read_text().replace('/* CATALOG_DATA */',payload),encoding='utf-8')
with (root/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['id','name','status','verified_at','offer','historical_111','historical_124','links']);w.writerows((e['id'],e['name'],e['status'],e.get('verified_at') or '',e.get('offer') or '',json.dumps(e.get('historical_summary',{}),ensure_ascii=False),json.dumps(e.get('historical_124',{}),ensure_ascii=False),' | '.join(e['links'])) for e in entries)
with (root/'CATALOG.md').open('w',encoding='utf-8') as f:
 f.write('# Каталог: исследовательские данные\n\nУсловия из исследований 17 ноября 2026 года требуют актуализации. API и регистрация не тестировались.\n\n')
 for e in entries:
  h=e.get('historical_summary',{});g=e.get('historical_124',{});f.write('## '+e['name'].replace('\n',' ')+'\n\n');f.write('**Статус:** '+e['status']+'  \n');
  if e.get('offer'):f.write('**Проверено '+str(e.get('verified_at'))+':** '+e['offer']+'  \n')
  for name,val in [('Исследование 111',h),('Исследование 124',g)]:
   if val:f.write('**'+name+' (17.11.2026):** '+ '; '.join(k+': '+str(v).replace('\n',' ') for k,v in val.items())+'  \n')
  f.write('**Ссылки:** '+ ' · '.join('<'+u+'>' for u in e['links'])+'\n\n')
print('Built',len(entries),'entries')
