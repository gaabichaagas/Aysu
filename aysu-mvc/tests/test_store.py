import unittest,tempfile,threading,json,http.client
from pathlib import Path
from app.models import store
from app.controllers.http import Controller
from http.server import ThreadingHTTPServer

class EcommerceTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=store.ROOT / "data"); self.original=store.DB; store.DB=Path(self.temp.name)/'test.sqlite3'; store.initialize()
  self.cookie=''; self.csrf=''
 def tearDown(self):
  store.DB=self.original;self.temp.cleanup()
 def req(self,path,method='GET',data=None):
  # Exercise the real HTTP controller without opening a network socket.
  from io import BytesIO
  from email.message import Message
  h=object.__new__(Controller);h.path=path;h.command=method
  h.headers=Message();h.headers['Cookie']=self.cookie;h.headers['X-CSRF-Token']=self.csrf
  body=json.dumps(data).encode() if data is not None else b''
  h.headers['Content-Length']=str(len(body));h.rfile=BytesIO(body);h.wfile=BytesIO()
  headers={}; statuses=[]
  h.send_response=lambda status:statuses.append(status)
  h.send_header=lambda key,val:headers.update({key:val})
  h.end_headers=lambda:None
  h.handle_request()
  cookie=headers.get('Set-Cookie')
  if cookie:self.cookie=cookie.split(';')[0]
  value=json.loads(h.wfile.getvalue() or b'{}')
  if 'csrf' in value:self.csrf=value['csrf']
  if isinstance(value,dict) and 'state' in value and isinstance(value['state'],dict):self.csrf=value['state']['csrf']
  return statuses[0],value
 def test_admin_access(self):
  status,state=self.req('/api/state');product=state['products'][0].copy()
  self.assertEqual(self.req('/admin.html')[0],302)
  self.assertEqual(self.req('/api/admin/login','POST',{'email':'missing@example.com','password':'segredo123'})[0],400)
  self.req('/api/register','POST',{'name':'Cliente','email':'cliente@example.com','password':'segredo123','admin':True})
  self.assertFalse(self.req('/api/state')[1]['user']['admin'])
  cookie=self.cookie
  self.assertEqual(self.req('/api/admin/login','POST',{'email':'cliente@example.com','password':'segredo123'})[0],403)
  self.assertEqual(self.cookie,cookie)
  self.assertEqual(self.req('/admin.html')[0],302)
  for path,method in [('/api/products','POST'),('/api/products/1','PUT'),('/api/products/1','DELETE')]:
   self.assertEqual(self.req(path,method,product)[0],403)
  with store.connect() as db:
   db.execute('INSERT INTO users(name,email,password,admin) VALUES (?,?,?,1)',('Admin','admin@example.com',store.password_hash('admin123')))
  self.assertEqual(self.req('/api/admin/login','POST',{'email':'admin@example.com','password':'errada123'})[0],400)
  self.assertFalse(self.req('/api/state')[1]['user']['admin'])
  self.assertEqual(self.req('/api/admin/login','POST',{'email':'admin@example.com','password':'admin123'})[0],200)
  self.assertNotEqual(self.cookie,cookie)
  self.assertTrue(self.req('/api/state')[1]['user']['admin'])
  from production import application
  from io import BytesIO
  statuses=[]
  body=b''.join(application({'REQUEST_METHOD':'GET','PATH_INFO':'/admin.html','HTTP_COOKIE':self.cookie,'wsgi.input':BytesIO()},lambda status,headers:statuses.append(status)))
  self.assertIn('200',statuses[0]);self.assertIn(b'id="productForm"',body)
  self.assertEqual(self.req('/api/products','POST',product)[0],200)
  self.req('/api/logout','POST',{})
  self.assertEqual(self.req('/admin.html')[0],302)
  self.assertEqual(self.req('/api/products','POST',product)[0],403)
 def test_full_flow(self):
  status,s=self.req('/api/state');self.assertEqual(status,200);self.assertEqual(len(s['products']),6)
  self.assertEqual(self.req('/api/products','POST',{})[0],403)
  self.assertEqual(self.req('/api/register','POST',{'name':'Ana','email':'ana@example.com','password':'segredo123'})[0],200)
  self.assertEqual(self.req('/api/cart','PUT',{'cart':[{'id':1,'size':'INVALIDO'}]})[0],400)
  self.assertEqual(self.req('/api/cart','PUT',{'cart':[{'id':1,'size':'P'},{'id':1,'size':'P'}]})[0],200)
  self.req('/api/favorites','PUT',{'favorites':[2]})
  self.assertEqual(self.req('/api/state')[1]['favorites'],[2])
  status,order=self.req('/api/orders','POST',dict(name='Ana',cpf='52998224725',phone='11999999999',cep='01001000',street='Praça',number='1',district='Sé',city='São Paulo',state='SP',payment_method='pix',total=1))
  self.assertEqual(status,200);self.assertEqual(order['total'],592.7);self.assertEqual(order['state']['cart'],[])
  self.assertEqual(len(self.req('/api/orders')[1]),1)
  self.req('/api/logout','POST',{})
  self.assertEqual(self.req('/api/login','POST',{'email':'ana@example.com','password':'errada'})[0],400)
  self.assertEqual(self.req('/api/login','POST',{'email':'ana@example.com','password':'segredo123'})[0],200)
  with store.connect() as db:db.execute('UPDATE users SET admin=1 WHERE email=?',('ana@example.com',))
  p=s['products'][0].copy();p['name']='Teste CRUD'
  status,result=self.req('/api/products','POST',p);self.assertEqual(status,200)
  pid=result['state']['products'][-1]['id'];p['name']='Atualizado'
  self.assertEqual(self.req('/api/products/'+str(pid),'PUT',p)[0],200)
  self.assertEqual(self.req('/api/products/'+str(pid),'DELETE',{})[0],200)
  self.assertEqual(len(self.req('/api/state')[1]['products']),6)
  self.assertEqual(self.req('/data/aysu.sqlite3')[0],404)
  self.csrf='bad';self.assertEqual(self.req('/api/logout','POST',{})[0],403)
 def test_profile_and_security(self):
  self.req('/api/state')
  self.assertEqual(self.req('/api/cart','PUT',{'cart':[{'id':1,'size':'P'}]})[0],403)
  self.assertEqual(self.req('/api/profile')[0],403)
  self.req('/api/register','POST',{'name':'Bia','email':'bia@example.com','password':'segredo123'})
  profile=dict(name='Bia',cpf='52998224725',phone='11999999999',cep='01001000',street='Rua',number='2',district='Centro',city='São Paulo',state='SP')
  self.assertEqual(self.req('/api/profile','PUT',dict(profile,cpf='11111111111'))[0],400)
  self.assertEqual(self.req('/api/profile','PUT',dict(profile,cpf='52998224724'))[0],400)
  self.assertEqual(self.req('/api/profile','PUT',profile)[0],200)
  self.assertEqual(self.req('/api/profile')[1]['cpf'],profile['cpf'])
  self.req('/api/cart','PUT',{'cart':[{'id':1,'size':'P'}]})
  self.assertEqual(self.req('/api/orders','POST',dict(profile,payment_method='dinheiro'))[0],400)
  self.assertEqual(len(self.req('/api/state')[1]['cart']),1)
  for method in ['credito','boleto','pix']:
   self.req('/api/cart','PUT',{'cart':[{'id':1,'size':'P'}]})
   status,order=self.req('/api/orders','POST',dict(profile,payment_method=method,shipping_cents=0,total=1))
   self.assertEqual(status,200);self.assertEqual(order['total'],302.8)
   self.assertTrue(order['payment_reference'].startswith('TESTE-'))
   self.assertEqual(self.req('/api/orders','POST',dict(profile,payment_method=method))[0],400)
  self.assertEqual(len(self.req('/api/orders')[1]),3)
  self.req('/api/logout','POST',{})
  self.req('/api/register','POST',{'name':'Outra','email':'outra@example.com','password':'segredo123'})
  self.assertEqual(self.req('/api/orders')[1],[])
  self.assertEqual(self.req('/api/profile')[1],{})
  self.assertEqual(self.req('/api/shipping?cep=01001000')[1]['cents'],1290)
  self.assertEqual(self.req('/api/shipping?cep=90000000')[1]['cents'],2990)
 def test_wsgi_and_seo(self):
  from production import application
  from io import BytesIO
  import os
  from unittest.mock import patch
  def get(path,query=''):
   status=[];headers=[]
   result=application({'REQUEST_METHOD':'GET','PATH_INFO':path,'QUERY_STRING':query,'wsgi.input':BytesIO()},lambda a,b:(status.append(a),headers.extend(b)))
   return status[0],dict(headers),b''.join(result).decode()
  self.assertIn('200',get('/')[0])
  self.assertIn('canonical',get('/')[2])
  self.assertIn('schema.org',get('/produto.html','id=1')[2])
  self.assertIn('Vestido Pitanga',get('/produto.html','id=1')[2])
  self.assertIn('urlset',get('/sitemap.xml')[2])
  self.assertIn('Disallow: /conta.html',get('/robots.txt')[2])
  for name in ['conta','carrinho','loja','login','sobre','admin-login','favoritos']:
   self.assertIn('200',get('/'+name+'.html')[0])
  status,headers,body=get('/admin.html')
  self.assertIn('302',status);self.assertEqual(headers['Location'],'/admin-login.html')
  self.assertNotIn('productForm',body)
  with patch.dict(os.environ,{'COOKIE_SECURE':'1'}):
   _,headers,_=get('/api/state')
   self.assertIn('Secure',headers['Set-Cookie'])
   self.assertIn('Strict-Transport-Security',headers)
 def test_postal(self):
  from unittest.mock import patch,MagicMock
  response=MagicMock();response.__enter__.return_value.read.return_value=b'{"cep":"01001-000","logradouro":"Praca","bairro":"Se","localidade":"Sao Paulo","uf":"SP"}'
  with patch('app.services.postal.urlopen',return_value=response):self.assertEqual(self.req('/api/cep?cep=01001000')[1]['state'],'SP')
  self.assertEqual(self.req('/api/cep?cep=123')[0],400)
  with patch('app.services.postal.urlopen',side_effect=TimeoutError):self.assertEqual(self.req('/api/cep?cep=01001000')[0],400)

if __name__=='__main__':unittest.main()

