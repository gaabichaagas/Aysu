# Publicação com HTTPS e banco persistente

## Estado

Configuração preparada, publicação não realizada. É necessário disponibilizar o projeto em uma conta/repositório de hospedagem. O serviço sugerido abaixo envolve plano pago para manter o SQLite em disco persistente; não foi contratado nem iniciado nenhum recurso.

## Render com Docker

1. Suba o conteúdo da pasta `aysu-mvc` para um repositório próprio. Não envie banco real nem dados de clientes.
2. No Render, crie um Blueprint a partir desse repositório usando o `render.yaml` incluído. Revise o plano e os custos antes de confirmar. Alternativamente, crie Web Service Docker e configure disco e variáveis manualmente.
3. Use disco persistente em `/var/data`; defina `DATABASE_PATH=/var/data/aysu.sqlite3` e `COOKIE_SECURE=1`.
4. Defina `PUBLIC_URL` com a URL HTTPS real do serviço, sem barra final. Ela define canonical e sitemap. Se o endereço só for conhecido depois do primeiro deploy, atualize a variável e reinicie o serviço.
5. O contêiner instala `requirements.txt` e executa `python production.py`. A porta vem da variável `PORT`; a rota de saúde é `/health`.
6. No terminal do serviço, execute `python server.py --create-admin` para configurar a conta administrativa no mesmo banco persistente.
7. Abra a URL HTTPS e realize cadastro, login, CRUD, compra e histórico. Reinicie o serviço e confira se os dados permanecem.
8. Verifique que HTTP redireciona para HTTPS e que o cookie de sessão apresenta Secure/HttpOnly/SameSite. Confira `/sitemap.xml` e `/robots.txt` com o domínio correto.

O Render fornece TLS e redirecionamento HTTPS no proxy. O SQLite precisa de disco persistente: o sistema de arquivos padrão do serviço é temporário. A documentação informa que discos persistentes são vinculados a serviços pagos. Não publique esta versão em plano sem armazenamento persistente supondo que os pedidos serão conservados.

Fontes oficiais consultadas:
- https://render.com/docs/web-services
- https://render.com/docs/disks
- https://render.com/docs/docker
- https://docs.pylonsproject.org/projects/waitress/en/latest/

## Outras hospedagens

Use Python 3.12+, instale `pip install -r requirements.txt`, monte volume persistente, configure as variáveis acima e execute `python production.py` atrás de proxy HTTPS. Mantenha uma instância do aplicativo com SQLite; não use múltiplas réplicas independentes com bancos locais diferentes. Faça backups com o aplicativo parado. O servidor `server.py` é voltado a testes locais.

## Execução local sem HTTPS

`python server.py` funciona sem instalar dependências adicionais e sem COOKIE_SECURE. Não configure cookies Secure no HTTP local, pois o navegador poderá não enviá-los. Essa execução é uma etapa de desenvolvimento, não cumpre a exigência de hospedagem HTTPS do enunciado.
