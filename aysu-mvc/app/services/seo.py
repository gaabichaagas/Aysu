"""Metadados e sitemap produzidos pelo servidor para páginas públicas."""
import os,json,html
from urllib.parse import urlsplit,parse_qs
from app.models import store

def origin():
    value=os.environ.get('PUBLIC_URL','http://localhost:8000').rstrip('/')
    parsed=urlsplit(value)
    if parsed.scheme not in ['http','https'] or not parsed.netloc: raise ValueError('PUBLIC_URL inválida.')
    return value

def sitemap():
    with store.connect() as db: catalog=store.products(db)
    paths=['/','/loja.html','/sobre.html']+['/produto.html?id='+str(p['id']) for p in catalog]
    return ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+html.escape(origin()+p)+'</loc></url>' for p in paths)+'</urlset>').encode()

def enrich(body,path,query):
    if path not in ['/','/index.html','/loja.html','/produto.html','/sobre.html']: return body
    url=origin()+('/' if path=='/index.html' else path)
    extra=''
    if path=='/produto.html':
        try: pid=int(parse_qs(query).get('id',['1'])[0])
        except ValueError: return body
        with store.connect() as db: product=next((p for p in store.products(db) if p['id']==pid),None)
        if product:
            url+='?id='+str(pid)
            data={'@context':'https://schema.org','@type':'Product','name':product['name'],'image':[product['image']],'description':product['description'],'brand':{'@type':'Brand','name':'Aysú'}}
            # Escape '<' so product text cannot terminate the JSON script element.
            extra='<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>'
            import re
            body=re.sub(r'<title>.*?</title>','<title>'+html.escape(product['name'])+' | Aysú</title>',body,flags=re.S)
    extra+='<link rel="canonical" href="'+html.escape(url,quote=True)+'"><meta property="og:url" content="'+html.escape(url,quote=True)+'">'
    return body.replace('</head>',extra+'</head>')
