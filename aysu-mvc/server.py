from http.server import ThreadingHTTPServer
from app.controllers.http import Controller
from app.models import store
import argparse,getpass

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Loja Aysú MVC')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--create-admin',action='store_true')
    args=parser.parse_args(); store.initialize()
    if args.create_admin:
        email=input('E-mail do administrador: ').strip().lower()
        password=getpass.getpass('Senha (mínimo 6 caracteres): ')
        if '@' not in email or len(password)<6: raise SystemExit('E-mail ou senha inválidos.')
        with store.connect() as db:
            db.execute('INSERT INTO users(name,email,password,admin) VALUES (?,?,?,1) ON CONFLICT(email) DO UPDATE SET password=excluded.password,admin=1',('Administrador',email,store.password_hash(password)))
        print('Administrador configurado.')
    else:
        print(f'Aysú: http://localhost:{args.port} — Ctrl+C para encerrar')
        ThreadingHTTPServer(('127.0.0.1',args.port),Controller).serve_forever()
