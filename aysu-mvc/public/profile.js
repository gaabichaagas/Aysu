// Campos compartilhados entre área do cliente e checkout.
const profileFields=[['name','Nome completo'],['cpf','CPF (somente dados de teste)'],['phone','Telefone'],['cep','CEP'],['street','Rua'],['number','Número'],['district','Bairro'],['city','Cidade'],['state','UF'],['complement','Complemento (opcional)']];
function profileFormHTML() {
 return '<div class="profile-grid">'+profileFields.map(([id,label])=>`<div class="form-group"><label for="profile-${id}">${label}</label><input id="profile-${id}" name="${id}" ${id==='complement'?'':'required'} maxlength="${id==='state'?2:150}" ${['cpf','cep','phone'].includes(id)?'inputmode="numeric"':''} autocomplete="${({name:'name',phone:'tel',cep:'postal-code',street:'address-line1',city:'address-level2',state:'address-level1'})[id]||'off'}"></div>`).join('')+'</div>';
}
function fillProfile(form,data) {for(const [key] of profileFields) if(form.elements[key]) form.elements[key].value=data[key]||'';}
async function lookupAddress(form,message) {
 message.textContent='Consultando CEP…';
 try {const data=await api('cep?cep='+encodeURIComponent(form.elements.cep.value)); for(const key of ['cep','street','district','city','state']) form.elements[key].value=data[key]||'';message.textContent='Confira o endereço e preencha o número.';}
 catch(e){message.textContent=e.message;}
}
