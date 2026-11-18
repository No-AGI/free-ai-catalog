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
def compact(e):
 """Build a display-only summary; the source records remain untouched."""
 import re
 h=e.get('historical_summary') or {}; g=e.get('historical_124') or {}
 notes=e.get('historical_additional') or []
 # Group research belongs to several possible products and is never treated as
 # a confirmed condition of any individual card.
 individual=[n for n in notes if not any(f.get('label')=='Составная строка исследования 115' for f in n.get('fields',[]))]
 def note_values(*labels):
  return [str(f['value']).strip() for n in individual for f in n.get('fields',[]) if f.get('label') in labels and f.get('value')]
 def useful(v):
  return bool(v and str(v).strip() and not re.match(r'^(unknown|неизвестно|не установлено|n/a|нет данных|—)',str(v).strip(),re.I))
 def first(*values):
  return next((str(v).strip() for v in values if useful(v)),None)
 def translate_boolean(value):
  return {'no':'нет','yes':'да','true':'да','false':'нет'}.get(str(value).strip().lower(),value)
 def requirement(key,label):
  values=[g.get(key),h.get(key+'_required'),*note_values(label,'Исследование 115 — '+label)]
  states=set()
  for v in values:
   s=str(v or '').strip().lower()
   if re.match(r'^(нет|no|false)(?:\b|\s|\(|$)',s): states.add('no')
   elif re.match(r'^(да|yes|true)(?:\b|\s|\(|$)',s): states.add('yes')
  for n in notes:
   if any(f.get('label')=='Составная строка исследования 115' for f in n.get('fields',[])):
    for f in n.get('fields',[]):
     if 'no' in states and f.get('label')=='Группа — '+label and re.match(r'^(да|yes|true)(?:\b|\s|\(|$)',str(f.get('value','')).strip(),re.I):
      states.add('yes')
  if len(states)>1:return 'сведения расходятся'
  if len(states)==1:
   # Keep qualifications such as a deposit or a phone check.
   return translate_boolean(first(*values))
  return 'неизвестно'
 offer=first(e.get('offer'),(e.get('priority_research') or {}).get('offer'),g.get('free_quota'),h.get('free_quota'),*note_values('Условия бесплатного доступа','Бесплатный тариф','Бесплатные модели'))
 models=first(g.get('models'),h.get('models'),*note_values('Модели'))
 access=first(g.get('surfaces'),h.get('interfaces'),*note_values('Интерфейсы'))
 commercial=translate_boolean(first(g.get('commercial'),h.get('commercial'),*note_values('Коммерческое использование')))
 restrictions=first(e.get('restrictions'),(e.get('priority_research') or {}).get('limitations'))
 policy=first(e.get('data_policy'),g.get('data_collected'),h.get('data_collected'),*note_values('Обработка данных'))
 if policy and not re.search(r'обуч|переда|хран|логир|training|train|sharing|retain|logging',policy,re.I):policy=None
 dates=[str(n.get('research_date')) for n in individual if n.get('research_date')]
 date=first(e.get('verified_at'),(e.get('priority_research') or {}).get('research_date'),g.get('last_checked'),h.get('checked_at'),*(dates[-1:]))
 return {'offer':offer,'models':models,'access':access,'card':requirement('card','Карта'),'phone':requirement('phone','Телефон'),'commercial':commercial,'restrictions':restrictions,'policy':policy,'date':date}

display=[dict(e, _summary=compact(e)) for e in entries]
payload=json.dumps(display,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
(root/'index.html').write_text((root/'site/template.html').read_text().replace('/* CATALOG_DATA */',payload),encoding='utf-8')
with (root/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['id','name','status','verified_at','offer','historical_111','historical_124','historical_additional','priority_research','links']);w.writerows((e['id'],e['name'],e['status'],e.get('verified_at') or '',e.get('offer') or '',json.dumps(e.get('historical_summary',{}),ensure_ascii=False),json.dumps(e.get('historical_124',{}),ensure_ascii=False),json.dumps(e.get('historical_additional',[]),ensure_ascii=False),json.dumps(e.get('priority_research',{}),ensure_ascii=False),' | '.join(e['links'])) for e in entries)
def cell(value):
 import re,html
 value=html.unescape(str(value)).replace('<br>','; ').replace('\n',' ')
 translations={'CONFIRMED':'Подтверждено в исследовании','COMMUNITY VERIFIED':'Подтверждено сообществом в исследовании','UNVERIFIED':'Не подтверждено в исследовании','EXPIRED':'Завершено по исследованию','FREE TRIAL':'Пробный период','FREE RECURRING':'Регулярная бесплатная квота','DATA EXCHANGE':'Доступ за передачу данных','COMMUNITY FUNDED':'Поддерживается сообществом','BETA ACCESS':'Бета-доступ','RESEARCH ACCESS':'Для исследований'}
 value=translations.get(value,value)
 value=value.replace('|','\\|')
 return re.sub(r'(https?://[^\s<>]+)',lambda m:'['+m.group(0)+']('+m.group(0)+')',value)
fields=[('Бесплатное предложение','free_quota','free_quota'),('Модели','models','models'),('Категория','category','category'),('Тип доступа','free_type','type'),('Регистрация','registration','signup_req'),('Банковская карта','card_required','card'),('Телефон','phone_required','phone'),('Использование данных','data_collected','data_collected'),('Ограничения','rate_limits','rate_limits'),('Обновление квоты','reset','refresh'),('Страны и регионы','russia','regions'),('Контекст','context','context'),('Использование tools','tool_calling','tool'),('Потоковая передача','streaming','stream'),('Коммерческое использование','commercial','commercial'),('Статус в исследовании','status','status'),('Объём проверки','verification_scope',None),('Дата исходной проверки','checked_at','last_checked'),('Источники','sources','sources'),('Запросы','requests','req_tokens'),('Токены','tokens',None),('Причина бесплатного доступа','why_free','why_free'),('Третьи стороны','third_party',None),('Отказ от обмена данными','opt_out','opt_out'),('Интерфейсы','interfaces','surfaces'),('Изображения','images','vision'),('Документы','documents',None),('Автоматизация','automation','automation'),('Устойчивость предложения','sustainability','durability'),('API протестирован','api_tested',None),('Регистрация протестирована','signup_tested',None)]
with (root/'CATALOG.md').open('w',encoding='utf-8') as f:
 f.write('# Каталог бесплатных AI-сервисов\n\n')
 f.write('Данные исследований относятся к ноябрю 2026 года и могут измениться. Информация собрана из нескольких исследований; расхождения сохранены в карточках. API и регистрация не тестировались. Для поиска по странице используйте Ctrl+F.\n\n')
 for e in entries:
  h=e.get('historical_summary',{});g=e.get('historical_124',{})
  name=e['name'].replace('\n',' ');f.write('## '+name+'\n\n')
  summary=compact(e)
  f.write('| Что важно | Сведения |\n|---|---|\n')
  for title,key in [('Бесплатно','offer'),('Модели','models'),('Доступ','access')]:
   if summary[key]:f.write('| '+title+' | '+cell(summary[key])+' |\n')
  if not summary['offer']:f.write('| Бесплатно | Условия неизвестны; требуется проверка. |\n')
  f.write('| Карта / телефон | '+cell(summary['card'])+' / '+cell(summary['phone'])+' |\n')
  if summary['commercial']:f.write('| Коммерческое использование | '+cell(summary['commercial'])+' |\n')
  if summary['restrictions']:f.write('| Важно | '+cell(summary['restrictions'])+' |\n')
  if summary['policy']:f.write('| Обработка данных | '+cell(summary['policy'])+' |\n')
  f.write('\n')
  if e['links']:f.write('[Открыть источник]('+e['links'][0]+') · ')
  f.write(('Официальное условие от ' if e.get('offer') else 'Исторические сведения · проверить актуальность')+(str(summary['date']) if e.get('offer') else ((' · '+str(summary['date'])) if summary['date'] else ''))+'\n\n')
  f.write('<details>\n<summary>Подробнее и сравнение источников</summary>\n\n')
  if e.get('offer'):
   f.write('**Условие по официальному источнику** · '+str(e.get('verified_at'))+': '+cell(e['offer'])+'\n\n')
  priority=e.get('priority_research',{})
  if priority:
   f.write('**Уточнение из исследования от '+priority['research_date']+'** · данные необходимо актуализировать.\n\n| Параметр | Сведения |\n|---|---|\n| Предложение | '+cell(priority['offer'])+' |\n| Ограничения и достоверность | '+cell(priority['limitations'])+' |\n\n')
   if priority.get('sources'):f.write('**Источники уточнения:** '+' · '.join('[Источник '+str(i)+']('+u+')' for i,u in enumerate(priority['sources'],1))+'\n\n')
  if h or g:
   f.write('> Исторические сведения: проверьте актуальность перед использованием.\n\n')
   f.write('| Параметр | Сведения |\n|---|---|\n')
   for label,k1,k2 in fields:
    v1=h.get(k1) if k1 else None;v2=g.get(k2) if k2 else None
    if v1 or v2:
     values=[]
     for v in (v1,v2):
      if v and str(v).strip().casefold() not in [str(t).strip().casefold() for t in values]:values.append(v)
     f.write('| '+label+' | '+'<br><br>'.join(cell(v) for v in values)+' |\n')
   f.write('\n')
  elif not e.get('historical_additional') and not priority:f.write('**Условия:** подробные сведения не перенесены; требуется проверка.\n\n')
  for note in e.get('historical_additional',[]):
   f.write('**Дополнительные сведения** · исследование от '+note['research_date']+':\n\n| Параметр | Сведения |\n|---|---|\n')
   for item in note['fields']:f.write('| '+cell(item['label'])+' | '+cell(item['value'])+' |\n')
   if note['sources']:f.write('\n**Источники дополнительного исследования:** '+ ' · '.join('[Источник '+str(i)+']('+u+')' for i,u in enumerate(note['sources'],1))+'\n')
   f.write('\n')
  if e.get('data_policy'):f.write('**Обработка данных:** '+cell(e['data_policy'])+'\n\n')
  if e['links']:
   f.write('**Ссылки:** '+ ' · '.join('[Источник '+str(i)+']('+u+')' for i,u in enumerate(e['links'],1))+'\n\n')
  f.write('</details>\n\n')
print('Built',len(entries),'entries')
