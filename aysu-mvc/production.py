"""Adaptador WSGI: reutiliza o controller MVC em servidor Waitress de produção."""
from io import BytesIO
from email.message import Message
from http import HTTPStatus
import os
from app.controllers.http import Controller
from app.models import store

def application(environ,start_response):
    handler=object.__new__(Controller)
    handler.command=environ['REQUEST_METHOD']
    handler.path=environ.get('PATH_INFO','/')+('?' + environ['QUERY_STRING'] if environ.get('QUERY_STRING') else '')
    handler.headers=Message()
    for key,value in environ.items():
        if key.startswith('HTTP_'): handler.headers[key[5:].replace('_','-')]=value
    handler.headers['Content-Length']=environ.get('CONTENT_LENGTH','0') or '0'
    handler.rfile=environ['wsgi.input'];handler.wfile=BytesIO()
    status=[];headers=[]
    handler.send_response=lambda code:status.append(code)
    handler.send_header=lambda key,value:headers.append((key,value))
    handler.end_headers=lambda:None
    handler.handle_request()
    start_response(str(status[0])+' '+HTTPStatus(status[0]).phrase,headers)
    return [handler.wfile.getvalue()]

if __name__=='__main__':
    from waitress import serve
    store.initialize()
    serve(application,host='0.0.0.0',port=int(os.environ.get('PORT','8000')),threads=4,max_request_body_size=100000)
