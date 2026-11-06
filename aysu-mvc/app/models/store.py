"""Models: SQL parametrizado e regras transacionais do e-commerce."""
import sqlite3, json, hashlib, secrets, time, os, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get('DATABASE_PATH', str(ROOT / 'data/aysu.sqlite3')))

class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try: return super().__exit__(*args)
        finally: self.close()

def connect():
    db = sqlite3.connect(DB, factory=Connection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript((ROOT/'data/schema.sql').read_text(encoding='utf-8-sig'))
        columns={row[1] for row in db.execute('PRAGMA table_info(orders)')}
        for name,kind in [('shipping_cents','INTEGER NOT NULL DEFAULT 0'),('payment_method',"TEXT NOT NULL DEFAULT 'legado'"),('payment_status',"TEXT NOT NULL DEFAULT 'nao_processado'"),('payment_reference',"TEXT NOT NULL DEFAULT ''")]:
            if name not in columns: db.execute(f'ALTER TABLE orders ADD COLUMN {name} {kind}')
        db.execute('CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY REFERENCES users(id), payload TEXT NOT NULL)')
        # Seed only a newly created catalog; deleted products are never reinserted.
        if not db.execute('SELECT 1 FROM products LIMIT 1').fetchone():
            for p in json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8-sig')):
                db.execute('INSERT INTO products(id,payload) VALUES (?,?)',(p['id'],json.dumps(p,ensure_ascii=False)))

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()

def products(db):
    return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM products WHERE active=1')]

def state(db, token):
    user=db.execute('SELECT u.id,u.name,u.email,u.admin FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=?',(token,)).fetchone()
    return dict(products=products(db),cart=[dict(id=r['product_id'],size=r['size']) for r in db.execute('SELECT c.* FROM cart c JOIN products p ON p.id=c.product_id WHERE owner=? AND p.active=1 ORDER BY c.id',(token,))],favorites=[r[0] for r in db.execute('SELECT f.product_id FROM favorites f JOIN products p ON p.id=f.product_id WHERE owner=? AND p.active=1',(token,))],user=dict(user) if user else None)

def validate_product(p):
    allowed={'name','category','color','description','image','image2','tag','tagClass'}
    result={k:str(p.get(k,'' )).strip() for k in allowed}
    if not result['name'] or len(result['name'])>150: raise ValueError('Nome inválido.')
    if result['category'] not in ['vestidos','calcas','camisas','conjuntos']: raise ValueError('Categoria inválida.')
    if result['color'] not in ['verde','amarelo','azul','laranja']: raise ValueError('Cor inválida.')
    if result['tagClass'] not in ['tag-yellow','tag-blue','tag-orange']: raise ValueError('Etiqueta inválida.')
    for k in ['image','image2']:
        if not result[k].startswith('https://'): raise ValueError('Use URL HTTPS para as imagens.')
    sizes=p.get('sizes')
    if not isinstance(sizes,list) or not sizes or any(s not in ['P','M','G','GG','36','38','40','42','44'] for s in sizes): raise ValueError('Tamanhos inválidos.')
    from decimal import Decimal, InvalidOperation
    try:
        cents=Decimal(str(p.get('price')))*100
        if not cents.is_finite() or cents<=0 or cents>100000000 or cents!=cents.to_integral_value(): raise ValueError('Preço inválido.')
    except InvalidOperation: raise ValueError('Preço inválido.')
    return dict(result,sizes=sizes,price=int(cents)/100)


def validate_cpf(value):
    cpf=re.sub(r'[^0-9]','',str(value))
    if len(cpf)!=11 or len(set(cpf))==1: raise ValueError('CPF inválido.')
    for length in (9,10):
        digit=(sum(int(cpf[i])*(length+1-i) for i in range(length))*10)%11
        if int(cpf[length])!=(0 if digit==10 else digit): raise ValueError('CPF inválido.')
    return cpf

def validate_profile(data):
    keys=['name','cpf','phone','cep','street','number','district','city','state','complement']
    p={k:str(data.get(k,'')).strip() for k in keys}
    if any(len(v)>150 for v in p.values()): raise ValueError('Dados muito longos.')
    if any(not p[k] for k in keys if k!='complement'): raise ValueError('Preencha os dados pessoais e de entrega.')
    p['cpf']=validate_cpf(p['cpf'])
    p['cep']=re.sub(r'[^0-9]','',p['cep']);p['phone']=re.sub(r'[^0-9]','',p['phone'])
    if len(p['cep'])!=8 or not 10<=len(p['phone'])<=11: raise ValueError('CEP ou telefone inválido.')
    p['state']=p['state'].upper()
    if p['state'] not in 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(): raise ValueError('UF inválida.')
    return p

def profile(db,uid):
    row=db.execute('SELECT payload FROM profiles WHERE user_id=?',(uid,)).fetchone()
    return json.loads(row[0]) if row else {}

def save_profile(db,uid,data):
    p=validate_profile(data)
    db.execute('INSERT INTO profiles(user_id,payload) VALUES (?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload',(uid,json.dumps(p,ensure_ascii=False)))
    db.execute('UPDATE users SET name=? WHERE id=?',(p['name'],uid))
    return p

def order_history(db,uid):
    orders=[dict(r) for r in db.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(uid,))]
    for o in orders:
        o['address']=json.loads(o['address'])
        o['items']=[dict(r) for r in db.execute('SELECT name,size,price_cents FROM order_items WHERE order_id=?',(o['id'],))]
    return orders

def checkout(db,token,user,data):
    from app.services.shipping import quote
    if not user: raise PermissionError('Entre na sua conta para finalizar.')
    address=validate_profile(data)
    method=data.get('payment_method')
    if method not in ['pix','boleto','credito']: raise ValueError('Selecione Pix, boleto ou cartão de crédito de teste.')
    # Lock the transaction before reading the bag: prevents duplicate concurrent orders.
    db.execute('BEGIN IMMEDIATE')
    items=db.execute('SELECT c.size,p.id,p.payload,p.active FROM cart c JOIN products p ON p.id=c.product_id WHERE owner=? ORDER BY c.id',(token,)).fetchall()
    if not items: raise ValueError('Sua sacola está vazia.')
    from decimal import Decimal
    snapshots=[]
    for item in items:
        p=json.loads(item['payload'])
        if not item['active'] or item['size'] not in p['sizes']: raise ValueError('Um item não está mais disponível. Revise sua sacola.')
        snapshots.append((p,item['size'],int(Decimal(str(p['price']))*100)))
    subtotal=sum(p[2] for p in snapshots)
    shipping=quote(address['cep'])
    total=subtotal+shipping['cents']
    reference='TESTE-'+secrets.token_hex(6).upper()
    status='aprovado_simulado' if method=='credito' else 'pendente_simulado'
    cursor=db.execute('INSERT INTO orders(user_id,address,total_cents,shipping_cents,payment_method,payment_status,payment_reference) VALUES (?,?,?,?,?,?,?)',(user['id'],json.dumps(address),total,shipping['cents'],method,status,reference))
    order_id=cursor.lastrowid
    db.executemany('INSERT INTO order_items(order_id,product_id,name,size,price_cents) VALUES (?,?,?,?,?)',[(order_id,p['id'],p['name'],size,price) for p,size,price in snapshots])
    save_profile(db,user['id'],address)
    db.execute('DELETE FROM cart WHERE owner=?',(token,))
    return dict(id=order_id,total=total/100,shipping=shipping['cents']/100,status='recebido',payment_status=status,payment_reference=reference)
