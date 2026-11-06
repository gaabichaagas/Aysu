/*
============================================================
ADMINISTRADOR AYSÚ
============================================================
Salva os produtos em:
localStorage -> aysuAdminProducts
============================================================
*/

const STORAGE_KEY = 'aysuAdminProducts';

const productForm = document.getElementById('productForm');
const productId = document.getElementById('productId');
const productName = document.getElementById('productName');
const productCategory = document.getElementById('productCategory');
const productPrice = document.getElementById('productPrice');
const productDescription = document.getElementById('productDescription');
const productTag = document.getElementById('productTag');
const productTagColor = document.getElementById('productTagColor');
const productImageFile = document.getElementById('productImageFile');
const productImageUrl = document.getElementById('productImageUrl');
const imagePreview = document.getElementById('imagePreview');
const previewEmpty = document.getElementById('previewEmpty');
const productList = document.getElementById('productList');
const productCount = document.getElementById('productCount');
const adminMessage = document.getElementById('adminMessage');
const saveButton = document.getElementById('saveButton');
const cancelButton = document.getElementById('cancelButton');
const formTitle = document.getElementById('formTitle');

let uploadedImage = '';

let adminProducts = [], csrf = '';
function getProducts() { return adminProducts; }
async function adminApi(path,method='GET',body) {
 const res=await fetch('/api/'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await res.json(); if(!res.ok) throw new Error(data.error);
 if(data.state) {adminProducts=data.state.products;csrf=data.state.csrf;}
 return data;
}
function showPreview(image) {
  if (!image) {
    imagePreview.style.display = 'none';
    imagePreview.removeAttribute('src');
    previewEmpty.style.display = 'block';
    return;
  }

  imagePreview.src = image;
  imagePreview.style.display = 'block';
  previewEmpty.style.display = 'none';
}

productImageFile.disabled=true;
productImageFile.title='Use uma URL HTTPS para a imagem.';
productImageFile.addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;

  const reader = new FileReader();

  reader.onload = function (event) {
    uploadedImage = event.target.result;
    productImageUrl.value = '';
    showPreview(uploadedImage);
  };

  reader.readAsDataURL(file);
});

productImageUrl.addEventListener('input', function () {
  const url = this.value.trim();

  if (url) {
    uploadedImage = '';
    showPreview(url);
  }
});

function getSelectedColor() {
  return document.querySelector('input[name="productColor"]:checked')?.value || 'verde';
}

function getSelectedSizes() {
  return Array.from(
    document.querySelectorAll('input[name="productSize"]:checked')
  ).map(input => input.value);
}

productForm.addEventListener('submit', async function (event) {
  event.preventDefault();

  const products = getProducts();
  const editingId = Number(productId.value || 0);
  const sizes = getSelectedSizes();

  if (!sizes.length) {
    adminMessage.textContent = 'Selecione pelo menos um tamanho.';
    return;
  }

  let image = uploadedImage || productImageUrl.value.trim();

  if (editingId && !image) {
    const existing = products.find(product => product.id === editingId);
    if (existing) image = existing.image;
  }

  if (!image) {
    adminMessage.textContent = 'Escolha uma imagem ou cole uma URL.';
    return;
  }

  const newProduct = {
    id: editingId || Date.now(),
    name: productName.value.trim(),
    category: productCategory.value,
    color: getSelectedColor(),
    sizes,
    price: Number(productPrice.value),
    description: productDescription.value.trim(),
    image,
    image2: image,
    tag: productTag.value,
    tagClass: productTagColor.value,
    adminCreated: true
  };

  try {
    await adminApi('products'+(editingId?'/'+editingId:''),editingId?'PUT':'POST',newProduct);
    adminMessage.textContent = 'Produto salvo no banco.';
  } catch(e) { adminMessage.textContent=e.message; return; }

  resetForm();
  renderProducts();
});

function renderProducts() {
  const products = getProducts();

  productCount.textContent =
    products.length === 1
      ? '1 produto'
      : `${products.length} produtos`;

  if (!products.length) {
    productList.innerHTML = `
      <div class="admin-empty">
        <strong>Nenhuma peça cadastrada ainda.</strong>
        <p>Preencha o formulário para adicionar a primeira.</p>
      </div>
    `;
    return;
  }

  productList.innerHTML = products.map(product => `
    <article class="admin-product">

      <img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}">

      <div class="admin-product-info">
        <h3>${escapeHtml(product.name)}</h3>
        <p>${escapeHtml(product.description)}</p>
        <strong>${formatPrice(product.price)}</strong>
        <small>${escapeHtml(product.category)} • ${product.sizes.map(escapeHtml).join(', ')}</small>
      </div>

      <div class="admin-product-actions">
        <button class="admin-edit" onclick="editProduct(${product.id})">
          editar
        </button>

        <button class="admin-delete" onclick="deleteProduct(${product.id})">
          excluir
        </button>
      </div>

    </article>
  `).join('');
}

function editProduct(id) {
  const product = getProducts().find(product => product.id === id);
  if (!product) return;

  productId.value = product.id;
  productName.value = product.name;
  productCategory.value = product.category;
  productPrice.value = product.price;
  productDescription.value = product.description;
  productTag.value = product.tag || 'novo';
  productTagColor.value = product.tagClass || 'tag-yellow';

  document.querySelectorAll('input[name="productColor"]').forEach(input => {
    input.checked = input.value === product.color;
  });

  document.querySelectorAll('input[name="productSize"]').forEach(input => {
    input.checked = product.sizes.includes(input.value);
  });

  uploadedImage = product.image;
  productImageUrl.value = product.image.startsWith('data:') ? '' : product.image;
  showPreview(product.image);

  saveButton.textContent = 'salvar alterações';
  cancelButton.hidden = false;
  formTitle.textContent = 'Editar peça';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function deleteProduct(id) {
  const products = getProducts();
  const product = products.find(product => product.id === id);

  if (!product) return;

  const confirmed = confirm(`Deseja excluir "${product.name}"?`);
  if (!confirmed) return;

  try { await adminApi('products/'+id,'DELETE'); }
  catch(e) { adminMessage.textContent=e.message; return; }

  renderProducts();
}

cancelButton.addEventListener('click', function () {
  resetForm();
  adminMessage.textContent = '';
});

function resetForm() {
  productForm.reset();

  productId.value = '';
  uploadedImage = '';
  showPreview('');

  const green = document.querySelector(
    'input[name="productColor"][value="verde"]'
  );

  if (green) green.checked = true;

  ['P', 'M', 'G'].forEach(size => {
    const input = document.querySelector(
      `input[name="productSize"][value="${size}"]`
    );

    if (input) input.checked = true;
  });

  saveButton.textContent = 'salvar produto';
  cancelButton.hidden = true;
  formTitle.textContent = 'Adicionar nova peça';
}

function formatPrice(value) {
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

adminApi('state').then(s=>{
 csrf=s.csrf; adminProducts=s.products;
 if(!s.user?.admin) { productForm.querySelectorAll('input,button,select,textarea').forEach(e=>e.disabled=true); adminMessage.innerHTML='Entre com uma conta administrativa na <a href="login.html">página de login</a>.'; return; }
 renderProducts();
}).catch(e=>adminMessage.textContent=e.message);
