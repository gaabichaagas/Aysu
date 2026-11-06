"""Integração ViaCEP com timeout e tratamento de indisponibilidade."""
import json, re
from urllib.request import urlopen

def lookup(cep):
    cep=re.sub(r'[^0-9]','',cep)
    if len(cep)!=8: raise ValueError('Informe um CEP de 8 dígitos.')
    try:
        with urlopen('https://viacep.com.br/ws/'+cep+'/json/',timeout=5) as response:
            data=json.load(response)
    except Exception as exc: raise ValueError('Consulta de CEP indisponível. Preencha o endereço manualmente.') from exc
    if data.get('erro'): raise ValueError('CEP não encontrado.')
    return dict(cep=data['cep'],street=data['logradouro'],district=data['bairro'],city=data['localidade'],state=data['uf'])
