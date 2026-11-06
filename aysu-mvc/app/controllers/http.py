"""Controller HTTP: entrada, autenticação, autorização e respostas JSON."""
import json,secrets,time,hmac,re
from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlsplit,parse_qs
from app.models import store
from app.services import postal, shipping, seo
import os

class Controller(BaseHTTPRequestHandler):
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_PUT(self): self.handle_request()
    def do_DELETE(self): self.handle_request()

    def send(self,status,data,mime='application/json; charset=utf-8'):
        body=json.dumps(data,ensure_ascii=False).encode() if mime.startswith('application/json') else data
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options','DENY')
        if os.environ.get('COOKIE_SECURE')=='1': self.send_header('Strict-Transport-Security','max-age=31536000')
        self.send_header('Cache-Control','no-store')
        if getattr(self,'new_token',None): self.send_header('Set-Cookie',f'aysu_session={self.new_token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800' + ('; Secure' if os.environ.get('COOKIE_SECURE')=='1' else ''))
        self.end_headers(); self.wfile.write(body)

    def handle_request(self):
        self.new_token=None
        path=urlsplit(self.path).path
        if self.command=='GET' and path=='/health': return self.send(200,{'ok':True})
        if self.command=='GET' and path=='/sitemap.xml': return self.send(200,seo.sitemap(),'application/xml; charset=utf-8')
        if self.command=='GET' and path=='/robots.txt': return self.send(200,('User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin.html\nDisallow: /conta.html\nDisallow: /carrinho.html\nDisallow: /login.html\nDisallow: /favoritos.html\nSitemap: '+seo.origin()+'/sitemap.xml\n').encode(),'text/plain; charset=utf-8')
        if not path.startswith('/api/'):
            if self.command!='GET': return self.send(405,{'error':'Método inválido.'})
            name='index.html' if path=='/' else path.lstrip('/')
            # Explicit allowlist; database and source code cannot be downloaded.
            folder='app/views' if name in ['index.html','loja.html','produto.html','carrinho.html','favoritos.html','login.html','sobre.html','admin.html','conta.html'] else 'public'
            if '/' in name or name not in [p.name for p in (store.ROOT/folder).iterdir() if p.is_file()]: return self.send(404,{'error':'Página não encontrada.'})
            import mimetypes
            body=(store.ROOT/folder/name).read_bytes()
            if folder=='app/views': body=seo.enrich(body.decode('utf-8-sig'),path,urlsplit(self.path).query).encode()
            return self.send(200,body,mimetypes.guess_type(name)[0] or 'application/octet-stream')
        try:
            with store.connect() as db:
                expired=db.execute('SELECT 1 FROM sessions WHERE expires<? LIMIT 1',(int(time.time()),)).fetchone()
                if expired: db.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),))
                db.commit()
                cookies=SimpleCookie(self.headers.get('Cookie',''))
                token=cookies['aysu_session'].value if 'aysu_session' in cookies else ''
                session=db.execute('SELECT * FROM sessions WHERE token=?',(token,)).fetchone()
                if not session:
                    token=secrets.token_urlsafe(32); self.new_token=token
                    db.execute('INSERT INTO sessions(token,expires) VALUES (?,?)',(token,int(time.time())+604800))
                db.commit()
                current=store.state(db,token)
                if self.command=='GET':
                    if path=='/api/state': return self.send(200,dict(current,csrf=token))
                    if path=='/api/cep': return self.send(200,postal.lookup(parse_qs(urlsplit(self.path).query).get('cep',[''])[0]))
                    if path=='/api/shipping': return self.send(200,shipping.quote(parse_qs(urlsplit(self.path).query).get('cep',[''])[0]))
                    if path in ['/api/orders','/api/profile']:
                        if not current['user']: raise PermissionError('Entre na sua conta.')
                        value=store.order_history(db,current['user']['id']) if path.endswith('orders') else store.profile(db,current['user']['id'])
                        return self.send(200,value)
                    return self.send(404,{'error':'Rota não encontrada.'})
                if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),token): return self.send(403,{'error':'Sessão inválida. Recarregue a página.'})
                length=int(self.headers.get('Content-Length',0))
                if length>100000: raise ValueError('Dados excedem o limite.')
                data=json.loads(self.rfile.read(length) or '{}')
                if not isinstance(data,dict): raise ValueError('Dados inválidos.')
                result={'ok':True}
                if path in ['/api/login','/api/register'] and self.command=='POST':
                    email=str(data.get('email','')).strip().lower(); password=str(data.get('password',''))
                    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(password)<6 or len(password)>200: raise ValueError('E-mail ou senha inválidos (mínimo 6 caracteres).')
                    if path.endswith('register'):
                        name=str(data.get('name','')).strip()
                        if not name or len(name)>150: raise ValueError('Informe seu nome.')
                        if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone(): raise ValueError('E-mail já cadastrado.')
                        uid=db.execute('INSERT INTO users(name,email,password) VALUES (?,?,?)',(name,email,store.password_hash(password))).lastrowid
                    else:
                        u=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                        if not u or not hmac.compare_digest(u['password'],store.password_hash(password,u['password'].split(':')[0])): raise ValueError('E-mail ou senha incorretos.')
                        uid=u['id']
                    # Rotate session to prevent fixation; transfer this browser's bag.
                    new=secrets.token_urlsafe(32)
                    db.execute('INSERT INTO sessions(token,user_id,expires) VALUES (?,?,?)',(new,uid,int(time.time())+604800))
                    for table in ['cart','favorites']: db.execute(f'UPDATE {table} SET owner=? WHERE owner=?',(new,token))
                    db.execute('DELETE FROM sessions WHERE token=?',(token,)); token=new; self.new_token=new
                elif path=='/api/logout' and self.command=='POST':
                    db.execute('DELETE FROM sessions WHERE token=?',(token,))
                    token=secrets.token_urlsafe(32); self.new_token=token
                    db.execute('INSERT INTO sessions(token,expires) VALUES (?,?)',(token,int(time.time())+604800))
                elif path=='/api/cart' and self.command=='PUT':
                    if not current['user']: raise PermissionError('Entre na sua conta para iniciar uma compra.')
                    items=data.get('cart',[])
                    if not isinstance(items,list) or len(items)>100: raise ValueError('Limite de 100 peças.')
                    catalog={p['id']:p for p in store.products(db)}
                    for item in items:
                        if item.get('id') not in catalog or item.get('size') not in catalog[item['id']]['sizes']: raise ValueError('Produto ou tamanho indisponível.')
                    db.execute('DELETE FROM cart WHERE owner=?',(token,))
                    db.executemany('INSERT INTO cart(owner,product_id,size) VALUES (?,?,?)',[(token,p['id'],p['size']) for p in items])
                elif path=='/api/favorites' and self.command=='PUT':
                    ids=data.get('favorites',[]); valid={p['id'] for p in store.products(db)}
                    if not isinstance(ids,list) or len(ids)>100 or any(i not in valid for i in ids): raise ValueError('Favoritos inválidos.')
                    db.execute('DELETE FROM favorites WHERE owner=?',(token,))
                    db.executemany('INSERT INTO favorites(owner,product_id) VALUES (?,?)',[(token,i) for i in set(ids)])
                elif path=='/api/profile' and self.command=='PUT':
                    if not current['user']: raise PermissionError('Entre na sua conta.')
                    result={'profile':store.save_profile(db,current['user']['id'],data)}
                elif path=='/api/orders' and self.command=='POST':
                    db.commit()
                    result=store.checkout(db,token,current['user'],data)
                elif path.startswith('/api/products'):
                    if not current['user'] or not current['user']['admin']: raise PermissionError('Acesso exclusivo de administrador.')
                    if path=='/api/products' and self.command=='POST':
                        p=store.validate_product(data)
                        pid=db.execute("INSERT INTO products(payload) VALUES ('{}')").lastrowid
                        p['id']=pid; db.execute('UPDATE products SET payload=? WHERE id=?',(json.dumps(p),pid))
                    elif re.fullmatch(r'/api/products/\d+',path) and self.command in ['PUT','DELETE']:
                        pid=int(path.rsplit('/',1)[1])
                        if not db.execute('SELECT 1 FROM products WHERE id=? AND active=1',(pid,)).fetchone(): return self.send(404,{'error':'Produto não encontrado.'})
                        if self.command=='DELETE':
                            db.execute('UPDATE products SET active=0 WHERE id=?',(pid,))
                            db.execute('DELETE FROM cart WHERE product_id=?',(pid,)); db.execute('DELETE FROM favorites WHERE product_id=?',(pid,))
                        else:
                            p=store.validate_product(data); p['id']=pid
                            db.execute('UPDATE products SET payload=? WHERE id=?',(json.dumps(p),pid))
                    else: return self.send(405,{'error':'Método inválido.'})
                else: return self.send(404,{'error':'Rota não encontrada.'})
                result=dict(result,state=dict(store.state(db,token),csrf=token))
            self.send(200,result)
        except PermissionError as exc: self.send(403,{'error':str(exc)})
        except (ValueError,KeyError,TypeError) as exc: self.send(400,{'error':str(exc)})
        except Exception:
            import traceback
            traceback.print_exc(); self.send(500,{'error':'Erro interno. Tente novamente.'})
