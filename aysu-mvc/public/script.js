/*
============================================================
AYSÚ - JAVASCRIPT GERAL
============================================================

Este arquivo é compartilhado pelas páginas do site.

Funções principais:
1. Menu mobile
2. Carrinho salvo no navegador
3. Favoritos salvos no navegador
4. Filtros da loja
5. Página de produto
6. Login e cadastro de demonstração
============================================================
*/

/* ============================================================
   BANCO DE PRODUTOS DE DEMONSTRAÇÃO

   Em um sistema real, esses dados viriam de um banco de dados.
   Aqui usamos um array para facilitar o projeto escolar.
   ============================================================ */
// Estado carregado do banco; estas variáveis são apenas cache de apresentação.
let PRODUCTS = [], cartCache = [], favoriteCache = [], currentUser = null, csrf = '';
function acceptState(s) {
  PRODUCTS = s.products; cartCache = s.cart; favoriteCache = s.favorites;
  currentUser = s.user; csrf = s.csrf;
}
async function api(path, method='GET', body) {
  const response = await fetch('/api/' + path, {method, headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Falha na comunicação.');
  if(data.state) acceptState(data.state);
  return data;
}
function getCart() { return cartCache.map(p=>({...p})); }
function getFavorites() { return [...favoriteCache]; }
async function saveCart(cart) { await api('cart','PUT',{cart}); updateHeaderCounts(); }
async function saveFavorites(favorites) { await api('favorites','PUT',{favorites}); updateHeaderCounts(); }
function escapeHtml(text) { return String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;'); }
// Escape all catalog text before interpolation into HTML, keeping numeric values intact.
function safeProduct(p) { return Object.fromEntries(Object.entries(p).map(([k,v])=>[k,typeof v==='string'?escapeHtml(v):Array.isArray(v)?v.map(escapeHtml):v])); }

/* ============================================================
   CONTADORES DO CABEÇALHO
   ============================================================ */
function updateHeaderCounts() {
  const cart = getCart();
  const favorites = getFavorites();

  document.querySelectorAll('[data-cart-count]').forEach(el => {
    el.textContent = cart.length;
  });

  document.querySelectorAll('[data-favorite-count]').forEach(el => {
    el.textContent = favorites.length;
  });
}

/* ============================================================
   MENU MOBILE
   ============================================================ */
const menuButton = document.getElementById('menuButton');
const iconNav = document.getElementById('iconNav');

if (menuButton && iconNav) {
  menuButton.addEventListener('click', () => {
    iconNav.classList.toggle('open');
    menuButton.textContent = iconNav.classList.contains('open') ? '✕' : '☰';
  });
}

/* ============================================================
   AVISO FLUTUANTE
   ============================================================ */
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 2200);
}

/* ============================================================
   CARRINHO
   ============================================================ */
async function addToCart(productId, size = null) {
  if(!currentUser) { location.href='login.html'; return; }
  const product = PRODUCTS.find(item => item.id === Number(productId));
  if (!product) return;

  const cart = getCart();

  cart.push({
    id: product.id,
    size: size || product.sizes[0]
  });

  await saveCart(cart);
  showToast(`${product.name} foi adicionado à sacola!`);
}

async function removeFromCart(index) {
  const cart = getCart();
  cart.splice(index, 1);
  await saveCart(cart);
  renderCartPage();
}

/* ============================================================
   FAVORITOS
   ============================================================ */
async function toggleFavorite(productId) {
  const id = Number(productId);
  let favorites = getFavorites();

  if (favorites.includes(id)) {
    favorites = favorites.filter(item => item !== id);
    showToast('Produto removido dos favoritos.');
  } else {
    favorites.push(id);
    showToast('Produto salvo nos favoritos!');
  }

  await saveFavorites(favorites);
  refreshFavoriteButtons();
  renderFavoritesPage();
}

function refreshFavoriteButtons() {
  const favorites = getFavorites();

  document.querySelectorAll('[data-favorite-id]').forEach(button => {
    const id = Number(button.dataset.favoriteId);
    const isFavorite = favorites.includes(id);

    button.classList.toggle('active', isFavorite);
    button.textContent = isFavorite ? '♥' : '♡';
  });
}

/* ============================================================
   CRIAÇÃO DO HTML DE UM CARD DE PRODUTO
   ============================================================ */
function createProductCard(product) {
  product = safeProduct(product);
  return `
    <article class="product-card" data-category="${product.category}" data-color="${product.color}" data-price="${product.price}">
      <div class="product-image">
        <span class="tag ${product.tagClass}">${product.tag}</span>

        <button
          class="favorite-button"
          data-favorite-id="${product.id}"
          aria-label="Favoritar ${product.name}"
          onclick="toggleFavorite(${product.id})"
        >♡</button>

        <a class="product-link" href="produto.html?id=${product.id}">
          <img src="${product.image}" alt="${product.name}">
        </a>

        <button class="quick-add" onclick="addToCart(${product.id})">
          adicionar à sacola
        </button>
      </div>

      <div class="product-info">
        <div>
          <a href="produto.html?id=${product.id}">
            <h3>${product.name}</h3>
          </a>
          <p>${product.category} • moda brasileira</p>
        </div>
        <strong>${formatPrice(product.price)}</strong>
      </div>
    </article>
  `;
}

function formatPrice(value) {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

/* ============================================================
   HOME
   Exibe alguns produtos automaticamente.
   ============================================================ */
function renderHomeProducts() {
  const homeProducts = document.getElementById('homeProducts');
  const bestSellers = document.getElementById('bestSellers');

  if (homeProducts) {
    homeProducts.innerHTML = PRODUCTS.slice(0, 4).map(createProductCard).join('');
  }

  if (bestSellers) {
    bestSellers.innerHTML = PRODUCTS.slice(2, 6).map(createProductCard).join('');
  }

  refreshFavoriteButtons();
}

/* ============================================================
   LOJA E FILTROS
   ============================================================ */
function renderShop() {
  const shopGrid = document.getElementById('shopGrid');
  if (!shopGrid) return;

  const category = document.getElementById('filterCategory')?.value || 'todos';
  const color = document.getElementById('filterColor')?.value || 'todos';
  const min = Number(document.getElementById('filterMin')?.value || 0);
  const max = Number(document.getElementById('filterMax')?.value || 99999);

  const filtered = PRODUCTS.filter(product => {
    const matchCategory = category === 'todos' || product.category === category;
    const matchColor = color === 'todos' || product.color === color;
    const matchPrice = product.price >= min && product.price <= max;

    return matchCategory && matchColor && matchPrice;
  });

  if (filtered.length === 0) {
    shopGrid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <h2>Nenhuma peça encontrada</h2>
        <p>Tente mudar os filtros.</p>
      </div>
    `;
    return;
  }

  shopGrid.innerHTML = filtered.map(createProductCard).join('');
  refreshFavoriteButtons();
}

['filterCategory', 'filterColor', 'filterMin', 'filterMax'].forEach(id => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener('input', renderShop);
    element.addEventListener('change', renderShop);
  }
});

/* ============================================================
   PÁGINA DE PRODUTO
   ============================================================ */
function renderProductPage() {
  const area = document.getElementById('productDetail');
  if (!area) return;

  const params = new URLSearchParams(window.location.search);
  const id = Number(params.get('id') || 1);
  const rawProduct = PRODUCTS.find(item => item.id === id);
  if (!rawProduct) { area.textContent = 'Produto não encontrado.'; return; }
  const product = safeProduct(rawProduct);

  area.innerHTML = `
    <div class="product-gallery">
      <div class="thumbnails">
        <button class="thumbnail active" data-image="${product.image}">
          <img src="${product.image}" alt="${product.name}">
        </button>

        <button class="thumbnail" data-image="${product.image2}">
          <img src="${product.image2}" alt="${product.name} em outro ângulo">
        </button>
      </div>

      <div class="main-product-image">
        <img id="mainProductImage" src="${product.image}" alt="${product.name}">
      </div>
    </div>

    <div class="product-detail-info">
      <span class="eyebrow">AYSÚ • ${product.category.toUpperCase()}</span>
      <h1>${product.name}</h1>
      <span class="product-price">${formatPrice(product.price)}</span>

      <p class="product-description">${product.description}</p>

      <span class="option-label">Escolha o tamanho</span>
      <div class="size-options" id="sizeOptions">
        ${product.sizes.map((size, index) => `
          <button class="size-button ${index === 0 ? 'selected' : ''}" data-size="${size}">
            ${size}
          </button>
        `).join('')}
      </div>

      <span class="option-label">Cor</span>
      <div class="color-options">
        <button class="color-button selected" style="background:${colorToHex(product.color)}"></button>
      </div>

      <div class="product-actions">
        <button class="btn btn-primary" id="productAddButton">
          adicionar à sacola
        </button>

        <button
          class="btn btn-outline"
          onclick="toggleFavorite(${product.id})"
        >
          salvar nos favoritos
        </button>
      </div>
    </div>
  `;

  let selectedSize = product.sizes[0];

  document.querySelectorAll('.size-button').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.size-button').forEach(item => item.classList.remove('selected'));
      button.classList.add('selected');
      selectedSize = button.dataset.size;
    });
  });

  document.querySelectorAll('.thumbnail').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.thumbnail').forEach(item => item.classList.remove('active'));
      button.classList.add('active');
      document.getElementById('mainProductImage').src = button.dataset.image;
    });
  });

  document.getElementById('productAddButton').addEventListener('click', () => {
    addToCart(product.id, selectedSize);
  });
}

function colorToHex(color) {
  const colors = {
    verde: '#286641',
    amarelo: '#f1c925',
    azul: '#007497',
    laranja: '#c55805'
  };

  return colors[color] || '#286641';
}

/* ============================================================
   PÁGINA DE CARRINHO
   ============================================================ */
function renderCartPage() {
  const cartList = document.getElementById('cartList');
  const subtotalEl = document.getElementById('cartSubtotal');
  const totalEl = document.getElementById('cartTotal');

  if (!cartList) return;

  const cart = getCart();

  if (cart.length === 0) {
    cartList.innerHTML = `
      <div class="empty-state">
        <h2>Sua sacola está vazia</h2>
        <p>Escolha uma peça bem brasileira para começar.</p>
        <a class="btn btn-primary" href="loja.html">ir para a loja</a>
      </div>
    `;

    if (subtotalEl) subtotalEl.textContent = formatPrice(0);
    if (totalEl) totalEl.textContent = formatPrice(0);
    return;
  }

  let total = 0;

  cartList.innerHTML = cart.map((cartItem, index) => {
    const raw = PRODUCTS.find(item => item.id === cartItem.id);
    if (!raw) return '';
    const product = safeProduct(raw);

    total += product.price;

    return `
      <article class="cart-item">
        <img src="${product.image}" alt="${product.name}">

        <div>
          <h3>${product.name}</h3>
          <p>Tamanho: ${escapeHtml(cartItem.size)}</p>
          <button class="cart-remove" onclick="removeFromCart(${index})">
            remover
          </button>
        </div>

        <strong>${formatPrice(product.price)}</strong>
      </article>
    `;
  }).join('');

  if (subtotalEl) subtotalEl.textContent = formatPrice(total);
  if (totalEl) totalEl.textContent = formatPrice(total);
}

/* ============================================================
   PÁGINA DE FAVORITOS
   ============================================================ */
function renderFavoritesPage() {
  const favoritesGrid = document.getElementById('favoritesGrid');
  if (!favoritesGrid) return;

  const favorites = getFavorites();
  const products = PRODUCTS.filter(product => favorites.includes(product.id));

  if (products.length === 0) {
    favoritesGrid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <h2>Você ainda não salvou nenhuma peça</h2>
        <p>Clique no coração dos produtos que você mais gostar.</p>
        <a href="loja.html" class="btn btn-primary">explorar loja</a>
      </div>
    `;
    return;
  }

  favoritesGrid.innerHTML = products.map(createProductCard).join('');
  refreshFavoriteButtons();
}


for (const kind of ['login','register']) {
 const form = document.getElementById(kind+'Form');
 if(form) form.addEventListener('submit', async event => {
  event.preventDefault();
  const message = document.getElementById(kind+'Message');
  const button=form.querySelector('button[type=submit]'); button.disabled=true;
  try {
   await api(kind,'POST',{email:document.getElementById(kind+'Email').value,password:document.getElementById(kind+'Password').value,name:document.getElementById('registerName')?.value});
   message.textContent='Conta conectada com sucesso.'; form.reset(); renderAccount();
  } catch(e) { message.textContent=e.message; } finally { button.disabled=false; }
 });
}
function renderAccount() {
 let el=document.getElementById('accountStatus');
 if(!el) { el=document.createElement('div'); el.id='accountStatus'; el.className='container'; document.querySelector('main')?.prepend(el); }
 el.replaceChildren();
 if(currentUser) {
  const text=document.createElement('p'); text.textContent='Olá, '+currentUser.name; el.append(text);
  const account=document.createElement('a'); account.href='conta.html'; account.textContent='Meus dados e pedidos '; el.append(account);
  const out=document.createElement('button'); out.className='btn btn-outline'; out.textContent='Sair';
  out.onclick=async()=>{await api('logout','POST',{}); location.reload();}; el.append(out);
  if(currentUser.admin) { const a=document.createElement('a'); a.href='admin.html'; a.textContent=' Administrar produtos'; el.append(a); }
 }
}
async function initialize() {
 acceptState(await api('state'));
 updateHeaderCounts(); renderHomeProducts(); renderShop(); renderProductPage(); renderCartPage(); renderFavoritesPage(); refreshFavoriteButtons(); renderAccount();
}
window.addEventListener('unhandledrejection', event=>{event.preventDefault(); showToast(event.reason?.message || 'Não foi possível salvar.');});
const appReady = initialize();
appReady.catch(e=>{showToast(e.message); const el=document.querySelector('main'); if(el) el.prepend(document.createTextNode('Não foi possível carregar a loja. Recarregue a página.'));});
