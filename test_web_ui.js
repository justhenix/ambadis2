const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

async function main() {
  const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
  const script = [...html.matchAll(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/g)].at(-1)[1];
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, {value:'',innerText:'',innerHTML:'',
        classList:{add(...names){names.forEach(n=>classes.add(n))},remove(...names){names.forEach(n=>classes.delete(n))},contains(n){return classes.has(n)},toggle(){}},
        appendChild(){},scrollIntoView(){}});
    }
    return elements.get(id);
  };
  const requests = [];
  const context = vm.createContext({console,TextEncoder,setTimeout(){},clearTimeout(){},
    window:{addEventListener(){}}, navigator:{},
    document:{getElementById:element,querySelectorAll(){return []},createElement(){return element('row')}},
    fetch:async (url, options) => {
      requests.push({url,payload:options.body ? JSON.parse(options.body) : {}});
      const payload = requests.at(-1).payload;
      const data = url === '/api/test-suite'
        ? {status:'ok',summary:{total:1,pass:0,fail:1},cases:[{id:'CANARY',tipe:'CLI Tidak Valid',input:'43',ekspektasi:'error',status:'FAIL',keterangan:'expected error not observed'}]}
        : url === '/api/simulasi'
        ? {status:'ok',m:payload.message,n:'1000000016000000063',phi:'1000000014000000048',
           m_rsa:payload.message,m_crt:payload.message,q:payload.q,c:'123',d:'123',dP:'1',dQ:'1',qInv:'1',m1:'1',m2:'1',h:'0'}
        : {status:'ok',rsa_time_ms:1,crt_time_ms:2,speedup:0.5,text_original:payload.text,
           text_decrypted:payload.text,total_bytes:new TextEncoder().encode(payload.text).length,
           is_valid:true,ciphertext_hex:'41',ciphertext_base64:'NDE=',total_blocks:1,blocks:[]};
      return {json:async()=>data};
    }});
  vm.runInContext(script,context);
  element('param-p').value='1000000007';
  element('param-q').value='1000000009';
  element('param-e').value='65537';
  element('param-m').value='9007199254740993';
  assert.equal(vm.runInContext("readInteger('param-m')",context),9007199254740993n);
  vm.runInContext("stepVal('param-m',10)",context);
  assert.equal(element('param-m').value,'9007199254741003');
  element('param-m').value='9007199254740993';
  await vm.runInContext('runSimulasi()',context);
  assert.equal(requests.at(-1).payload.message,'9007199254740993');
  assert.equal(element('out-n').innerText,'1000000016000000063');

  const regularFetch = context.fetch;
  const pending = [];
  const simulationData = message => ({status:'ok',m:message,m_rsa:message,m_crt:message,
    n:'2537',phi:'2436',q:'59',c:'2081',d:'937',dP:'13',dQ:'9',qInv:'35',m1:'13',m2:'49',h:'30'});
  context.fetch = () => new Promise(resolve => pending.push(resolve));
  element('param-m').value='1819';
  const older = vm.runInContext('runSimulasi()',context);
  element('param-m').value='42';
  const newer = vm.runInContext('runSimulasi()',context);
  pending[1]({json:async()=>simulationData('42')}); await newer;
  pending[0]({json:async()=>simulationData('1819')}); await older;
  assert.equal(element('out-m-rsa').innerText,'42','older response must not replace latest results');
  context.fetch = async () => ({json:async()=>({status:'error',message:'invalid prime'})});
  await vm.runInContext('runSimulasi()',context);
  assert(element('simulasi-results').classList.contains('hidden'),'invalid input must hide previous results');
  assert(!element('simulasi-error').classList.contains('hidden'));
  context.fetch = regularFetch;

  assert.equal(vm.runInContext('gcd(17n,3120n)',context),1n);
  assert.equal(vm.runInContext('nextPrime(43n)',context),47n);
  assert.equal(vm.runInContext('prevPrime(43n)',context),41n);
  assert.match(vm.runInContext('speedupLabel(0.92)',context),/lebih lambat/);
  vm.runInContext("stepPrime('param-p',1)",context);
  element('param-p').value='';
  element('param-m').value='1e3';
  vm.runInContext('checkInputsLive()',context);
  assert.equal(vm.runInContext("readInteger('param-m')",context),null);
  assert(!html.includes('99.9999') && !html.includes('fermat-error-rate'));
  assert(!/fermat/i.test(html));
  await vm.runInContext('runTestSuite()',context);
  assert.equal(element('test-summary-badge').innerText,'FAIL');
  assert.equal(element('test-summary-title').innerText,'Ada Kasus Uji Gagal');
  assert.match(element('row').innerHTML,/tabindex="0"/);
  assert.match(element('row').innerHTML,/PASS berarti program berhasil menolaknya/);
  assert.match(element('row').innerHTML,/title="FAIL berarti keluaran program tidak sesuai ekspektasi/);
  assert(!html.includes('CRT ~3x-4x Lebih Cepat'));
  assert(!html.includes('setMeasuredSpeedup'));
  assert.equal(vm.runInContext('isPrimeCandidate(1373653n)',context),false);
  assert.equal(vm.runInContext('isPrimeCandidate(252601n)',context),false);
  if (html.includes('text-input-msg')) {
    element('param-p').value='43';element('param-q').value='59';element('param-e').value='13';
    element('text-input-msg').value='  Ã©ðŸ˜€\n';
    await vm.runInContext('runTextEncrypt()',context);
    assert.equal(requests.at(-1).payload.text,'  Ã©ðŸ˜€\n');
    assert.equal(requests.at(-1).payload.p,'43');
    assert.equal(element('res-dec-text').innerText,'  Ã©ðŸ˜€\n');
    assert.match(element('text-speedup-badge').innerText,/lebih lambat/);
  }
  console.log('PASS: exact integers, steppers, request serialization, Miller-Rabin labels, speedup labels'+(html.includes('text-input-msg')?', exact text.':'.'));
}
main().catch(error=>{console.error(error);process.exitCode=1});