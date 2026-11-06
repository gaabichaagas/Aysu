appReady.then(async()=>{
 const area=document.getElementById('accountArea');
 if(!currentUser) {area.innerHTML='<p>Entre para acessar seus dados e histórico.</p><a class="btn btn-primary" href="login.html">Entrar ou criar conta</a>';return;}
 area.innerHTML='<section class="auth-card"><h2>Dados pessoais e entrega</h2><form id="profileForm">'+profileFormHTML()+'<button type="button" id="lookupAddress" class="btn btn-outline">Consultar CEP</button> <button class="btn btn-primary" type="submit">Salvar dados</button><p id="profileMessage" role="status"></p></form></section><section class="section"><h2>Histórico de compras</h2><div id="orderHistory"></div></section>';
 const form=document.getElementById('profileForm'),message=document.getElementById('profileMessage');
 fillProfile(form,{name:currentUser.name,...await api('profile')});
 document.getElementById('lookupAddress').onclick=()=>lookupAddress(form,message);
 form.onsubmit=async e=>{e.preventDefault();try{await api('profile','PUT',Object.fromEntries(new FormData(form)));message.textContent='Dados atualizados.';renderAccount();}catch(err){message.textContent=err.message;}};
 const orders=await api('orders');
 document.getElementById('orderHistory').innerHTML=orders.length?orders.map(o=>`<article class="auth-card order-card"><h3>Pedido #${o.id}</h3><p>${escapeHtml(o.created)} UTC • ${escapeHtml(o.status)}</p><ul>${o.items.map(i=>`<li>${escapeHtml(i.name)} — ${escapeHtml(i.size)} — ${formatPrice(i.price_cents/100)}</li>`).join('')}</ul><p>Frete: ${formatPrice(o.shipping_cents/100)} • Total: <strong>${formatPrice(o.total_cents/100)}</strong></p><p>Pagamento: ${escapeHtml(o.payment_method)} — ${escapeHtml(o.payment_status)}<br>Referência de teste: ${escapeHtml(o.payment_reference)}</p><p>Entrega: ${escapeHtml(o.address.street)}, ${escapeHtml(o.address.number)} — ${escapeHtml(o.address.city)}/${escapeHtml(o.address.state)}</p><small>Simulação acadêmica. Nenhum valor foi cobrado.</small></article>`).join(''):'<p>Você ainda não tem pedidos. <a href="loja.html">Explorar coleção</a></p>';
}).catch(e=>{document.getElementById('accountArea').textContent=e.message;});
