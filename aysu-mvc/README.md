# Aysú — Trabalho final de e-commerce

Versão revisada conforme o enunciado completo fornecido. Preserva o visual original e utiliza HTML, CSS, JavaScript, Python 3.12+ e SQLite. As tecnologias do curso não foram especificadas: confirme com o professor se Python e SQLite correspondem às técnicas estudadas. A arquitetura MVC não depende dessa escolha de linguagem.

## Executar localmente

1. Extraia o pacote e abra um terminal na pasta `aysu-mvc`.
2. Execute `python server.py --create-admin` para configurar e-mail e senha do administrador. Não existe senha padrão.
3. Execute `python server.py` e abra http://localhost:8000.
4. Crie uma conta de cliente na página de login. O catálogo é público; adicionar peças à sacola exige login.
5. Acesse “Meus dados e pedidos” para preencher os dados de teste e acompanhar suas compras.

Não abra os HTML diretamente. O servidor cria o banco em `data/aysu.sqlite3`, com seis produtos originais. Uma base anterior desta adaptação é migrada automaticamente, preservando usuários e pedidos existentes. Faça backup do banco antes de atualizar. Carrinho e favoritos persistem por sessão do navegador durante até sete dias; pedidos e perfil são vinculados à conta. Sair encerra a sessão e descarta carrinho e favoritos dela. O histórico permanece.

## Implementação

- `app/views`: nove páginas HTML, incluindo a nova área do cliente.
- `app/controllers/http.py`: rotas, autenticação, autorização e respostas HTTP/JSON.
- `app/models/store.py`: dados, regras, validações e transações SQL.
- `app/services/postal.py`: consulta real de endereço ao ViaCEP.
- `app/services/shipping.py`: frete acadêmico por faixa de CEP.
- `app/services/seo.py`: metadados, dados estruturados e sitemap.
- `public`: apresentação, interações, estilos e logotipo.
- `data/schema.sql`: esquema relacional; `seed.json`: catálogo inicial.
- `production.py`: adaptador WSGI para executar com Waitress.

Requisição → controller → model/serviço → banco/API → controller → apresentação. O navegador não é a fonte dos preços ou do frete. Produtos, contas, sessões, favoritos, carrinho, perfil, pedidos e itens são persistidos no SQLite. Consultas usam parâmetros. Exclusão de produto é lógica para preservar o histórico.

## Compra acadêmica

O perfil pede nome, CPF, telefone e endereço. O CPF é validado localmente por formato e dígitos verificadores; isso não comprova identidade nem consulta a Receita Federal. Use somente dados fictícios de teste. Não são utilizados serviços de autenticação de documentos.

Na sacola: consulte o endereço, confira e complete os campos, calcule o frete, selecione a forma de pagamento e confirme. O servidor recalcula valores, grava o pedido e limpa a sacola na mesma transação. O histórico apresenta itens, tamanhos, endereço, frete, total e situação do pagamento. O bloqueio transacional evita que duas confirmações simultâneas registrem a mesma sacola.

Pagamento implementado sem gateway, como simulação acadêmica explícita:

- Cartão de crédito: aprovação simulada, sem coletar número, CVV ou validade.
- Boleto: referência de teste e situação pendente simulada, sem boleto bancário real.
- Pix: referência de teste e situação pendente simulada, sem QR Code ou chave real.

Nenhuma cobrança ocorre. O enunciado prevê essas três opções e exige sandbox se houver integração com provedor; esta versão não integra um provedor financeiro. Não há estoque, emissão fiscal ou operação real de entrega.

## Frete e integração

ViaCEP preenche rua, bairro, cidade e UF, com timeout e preenchimento manual quando indisponível. Não valida CPF ou identidade.

Tabela própria de frete, calculada no servidor pelos dois primeiros dígitos do CEP:

| Faixa | Valor | Prazo acadêmico |
|---|---:|---|
| 00–19 | R$ 12,90 | 3 a 5 dias úteis |
| 20–39 | R$ 19,90 | 5 a 8 dias úteis |
| 40–79 | R$ 24,90 | 7 a 10 dias úteis |
| 80–99 | R$ 29,90 | 8 a 12 dias úteis |

CEP deve conter oito dígitos e não pode ser todo zero. A tabela não comprova existência ou entregabilidade do CEP e não é cotação dos Correios. O enunciado admite calcular ou consultar frete: esta versão calcula por tabela declarada.

## Segurança e administração

Senhas com PBKDF2-SHA256 e salt individual, cookie HttpOnly/SameSite, token CSRF, validação no servidor, escape de conteúdo e acesso de escrita exclusivo ao administrador. Perfis e pedidos são consultados apenas pelo próprio usuário. O banco e o código Python não são disponibilizados como arquivos públicos. Cadastros públicos nunca recebem acesso administrativo. Imagens de produtos usam URLs HTTPS; upload local foi desativado.

Em hospedagem HTTPS, defina `COOKIE_SECURE=1` para cookies Secure e HSTS. Use `python server.py --create-admin` no terminal da hospedagem para criar o administrador depois do deploy. Não salve senhas no repositório.

## Validação

Execute `python -m unittest discover -s tests -v`. Os quatro cenários automatizados passaram: fluxo de compra/CRUD, integração postal simulada, perfil/CPF/isolamento de contas/formas de pagamento/frete e adaptador WSGI/SEO/cookie seguro. Os testes usam banco temporário e o controller real em memória. A sintaxe JavaScript também foi verificada.

Limites da validação: navegação visual em navegador, construção do contêiner, conexão real com ViaCEP e deploy público não foram executados neste ambiente. Conexões locais estavam bloqueadas. Testes simulados do serviço postal não demonstram disponibilidade real da API.

## Publicação e entrega

Consulte `PUBLICACAO.md`, `REQUISITOS.md`, `SEO-SEM.md` e `ENTREGA.md`. O pacote está preparado para publicação, mas não contém URL pública: HTTPS só estará atendido após publicar e verificar o endereço real. Não há conta de hospedagem conectada nesta conversa.
