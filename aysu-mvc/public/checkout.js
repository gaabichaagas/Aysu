appReady.then(async()=>{
 const button=document.getElementById('checkoutButton');
 if(!currentUser){button.disabled=true;button.insertAdjacentHTML('beforebegin','<p><a href="login.html">Entre na sua conta para iniciar a compra.</a></p>');return;}
 const form=document.createElement('form');form.className='auth-card checkout-form';
 form.innerHTML='<h2>Entrega e pagamento</h2><p>Ambiente acadêmico: use dados fictícios válidos. Nenhuma cobrança será realizada.</p>'+profileFormHTML()+'<button type="button" class="btn btn-outline" id="lookupCep">Consultar CEP</button> <button type="button" class="btn btn-outline" id="quoteShipping">Calcular frete</button><p id="shippingQuote" role="status">Calcule o frete antes de confirmar.</p><fieldset><legend>Pagamento de teste</legend><label><input type="radio" name="payment_method" value="credito" required> Cartão de crédito simulado — sem número de cartão</label><label><input type="radio" name="payment_method" value="boleto"> Boleto simulado — sem linha digitável real</label><label><input type="radio" name="payment_method" value="pix"> Pix simulado — sem chave ou QR Code real</label></fieldset><p id="checkoutMessage" role="status"></p>';
 button.before(form);
 const message=form.querySelector('#checkoutMessage'),quoteEl=form.querySelector('#shippingQuote');
 fillProfile(form,{name:currentUser.name,...await api('profile')});
 let quote=null;
 form.elements.cep.addEventListener('input',()=>{quote=null;quoteEl.textContent='CEP alterado: calcule o frete novamente.';});
 form.querySelector('#lookupCep').onclick=async()=>{quote=null;await lookupAddress(form,message);};
 form.querySelector('#quoteShipping').onclick=async()=>{
 try{quote=await api('shipping?cep='+encodeURIComponent(form.elements.cep.value));
 const subtotal=getCart().reduce((sum,item)=>sum+(PRODUCTS.find(p=>p.id===item.id)?.price||0),0);
 quoteEl.textContent=`Frete: ${formatPrice(quote.cents/100)} • Prazo: ${quote.days}. Total com frete: ${formatPrice(subtotal+quote.cents/100)}. ${quote.source}`;
 }catch(e){quote=null;quoteEl.textContent=e.message;}
 };
 button.onclick=async()=>{
 if(!form.reportValidity())return;
 if(!quote||quote.cep!==form.elements.cep.value.replace(/\D/g,'')){message.textContent='Calcule o frete para o CEP atual antes de confirmar.';return;}
 button.disabled=true;
 try{
 const order=await api('orders','POST',Object.fromEntries(new FormData(form)));
 message.textContent=`Pedido #${order.id} registrado. Total com frete: ${formatPrice(order.total)}. Pagamento: ${order.payment_status}. Referência: ${order.payment_reference}. Nenhuma cobrança realizada.`;
 const link=document.createElement('a');link.href='conta.html';link.textContent=' Ver meus pedidos';message.append(link);
 renderCartPage();updateHeaderCounts();quote=null;
 }catch(e){message.textContent=e.message;}finally{button.disabled=false;}
 };
}).catch(e=>showToast(e.message));
