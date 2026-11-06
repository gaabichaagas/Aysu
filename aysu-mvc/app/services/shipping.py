"""Tabela própria de frete acadêmico por faixa de CEP; não é cotação dos Correios."""
import re

def quote(cep):
    cep=re.sub(r'[^0-9]','',str(cep))
    if len(cep)!=8 or cep=='00000000': raise ValueError('Informe um CEP válido com 8 dígitos.')
    prefix=int(cep[:2])
    if prefix<=19: cents,days=1290,'3 a 5 dias úteis'
    elif prefix<=39: cents,days=1990,'5 a 8 dias úteis'
    elif prefix<=79: cents,days=2490,'7 a 10 dias úteis'
    else: cents,days=2990,'8 a 12 dias úteis'
    return dict(cep=cep,cents=cents,days=days,source='Tabela acadêmica própria por faixa de CEP; não é cotação de transportadora.')
