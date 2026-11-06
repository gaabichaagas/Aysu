# Correspondência com o enunciado

| Item do enunciado | Evidência/implementação | Situação |
|---|---|---|
| Grupo com até três alunos; entrega no Teams entre 16 e 20 de novembro | Roteiro em ENTREGA.md | Ação dos integrantes |
| Pelo menos cinco páginas | Home, loja, produto, sacola, favoritos, login, sobre, administração, conta | Implementado |
| Responsividade | CSS original com media queries; novos formulários em grade que vira coluna no celular | Implementado; inspeção visual pendente |
| Navegação pública | Catálogo e detalhes sem autenticação | Implementado |
| Cadastro, login e sessão para iniciar compra | Senha conferida; sessão no banco; PUT /api/cart bloqueado sem login | Testado |
| Área do usuário | Perfil editável, dados de compra/entrega e histórico com itens | Testado |
| Frete antes de confirmar | Cotação por CEP exibida no checkout; cálculo confiável no servidor | Testado; tabela acadêmica |
| Crédito, boleto e Pix | Escolha obrigatória; referências e estados de teste persistidos | Testado; simulação sem gateway |
| MVC | Views, controller, model, serviços e recursos públicos separados | Implementado |
| API externa pertinente | ViaCEP com timeout e tratamento de erro | Testado com mock; serviço real pendente |
| Banco e CRUD | SQLite, SQL parametrizado, CRUD administrativo de produtos | Testado |
| Tecnologias estudadas | HTML/CSS/JS/Python/SQL | Compatibilidade com o curso a confirmar |
| Validação e segurança | CPF com dígitos verificadores; autorização; PBKDF2; CSRF; escape; cookies | Testado nos cenários documentados |
| HTTPS e hospedagem | Docker, adaptador WSGI, COOKIE_SECURE e roteiro de deploy | Configurado; publicação pendente |
| SEO | Descrições, headings, canonical, sitemap, robots, metadados sociais e Product JSON-LD | Implementado; domínio final depende do deploy |
| SEM sem gastos reais | SEO-SEM.md com público, anúncios, palavras-chave e indicadores | Entregue |
| Evolução, organização e participação dos integrantes | Roteiro de evidências em ENTREGA.md | Registro pelos integrantes |

A configuração de hospedagem não equivale a uma publicação concluída. O projeto não pode ser declarado integralmente pronto para entrega até validar a URL HTTPS, as telas em diferentes tamanhos e a compatibilidade das tecnologias com o conteúdo do curso.
