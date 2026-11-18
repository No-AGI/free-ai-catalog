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
  if e.get('offer'):
   f.write('**Условие по официальному источнику** · '+str(e.get('verified_at'))+': '+cell(e['offer'])+'\n\n')
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
  else:f.write('**Условия:** подробные сведения не перенесены; требуется проверка.\n\n')
  if e.get('data_policy'):f.write('**Обработка данных:** '+cell(e['data_policy'])+'\n\n')
  if e['links']:
   f.write('**Ссылки:** '+ ' · '.join('[Источник '+str(i)+']('+u+')' for i,u in enumerate(e['links'],1))+'\n\n')
print('Built',len(entries),'entries')
