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
  context.csvRows = [{p:'9007199254740993',rsa_samples_ns:[101,203],note:'comma, quote"\nline'}];
  assert.equal(vm.runInContext('benchmarkCsv(csvRows)',context),
    '"p","rsa_samples_ns","note"\r\n"9007199254740993","[101,203]","comma, quote""\nline"\r\n');
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

    const runText = text => {
      element('text-input-msg').value = text;
      return vm.runInContext('runTextEncrypt()',context);
    };
    const textData = text => ({status:'ok',rsa_time_ms:1,crt_time_ms:2,speedup:0.5,
      text_original:text,text_decrypted:text,total_bytes:new TextEncoder().encode(text).length,
      is_valid:true,ciphertext_hex:'41',ciphertext_base64:'NDE=',total_blocks:1,blocks:[]});
    const textReply = text => ({json:async()=>textData(text)});
    const isHidden = id => element(id).classList.contains('hidden');
    const requestCount = requests.length;
    await runText('');
    assert(isHidden('text-results-section'),'empty input must hide previous results');
    assert(!isHidden('text-error-box'),'empty input must show its error');
    assert(isHidden('btn-text-spinner'),'empty input must reset loading state');
    assert.equal(requests.length,requestCount,'empty input must not send a request');

    for (const failure of ['api','network']) {
      context.fetch = async () => textReply('previous success');
      await runText('previous success');
      context.fetch = failure === 'api'
        ? async () => ({json:async()=>({status:'error',message:'invalid key'})})
        : async () => {throw Error('network unavailable')};
      await runText('invalid request');
      assert(isHidden('text-results-section'),failure+' failure must hide previous results');
      assert(!isHidden('text-error-box'),failure+' failure must show its error');
      assert(isHidden('btn-text-spinner'),failure+' failure must reset loading state');
      assert.equal(element('btn-text-label').innerText,'Enkripsi & Dekripsi Pesan Teks');
    }

    const waiting = [];
    const deferText = () => {
      waiting.length = 0;
      context.fetch = () => new Promise((resolve,reject)=>waiting.push({resolve,reject}));
    };
    deferText();
    const oldText = runText('older result');
    const newText = runText('newer result');
    assert(isHidden('text-results-section'),'pending request must hide previous results');
    waiting[1].resolve(textReply('newer result')); await newText;
    waiting[0].resolve(textReply('older result')); await oldText;
    assert.equal(element('res-dec-text').innerText,'newer result','late success must not replace latest result');
    assert(!isHidden('text-results-section'));
    assert(isHidden('text-error-box'));

    deferText();
    const earlyText = runText('first response');
    const pendingText = runText('latest response');
    waiting[0].resolve(textReply('first response')); await earlyText;
    assert(isHidden('text-results-section'),'old response must not reveal results while latest request is pending');
    assert(!isHidden('btn-text-spinner'),'old response must not stop latest loading state');
    assert.equal(element('btn-text-label').innerText,'Mengenkripsi & Mendekripsi...');
    waiting[1].resolve(textReply('latest response')); await pendingText;
    assert.equal(element('res-dec-text').innerText,'latest response');
    assert(isHidden('btn-text-spinner'));

    deferText();
    const oldFailure = runText('older failure');
    const latestSuccess = runText('latest success');
    waiting[1].resolve(textReply('latest success')); await latestSuccess;
    waiting[0].reject(Error('outdated error')); await oldFailure;
    assert.equal(element('res-dec-text').innerText,'latest success');
    assert(isHidden('text-error-box'),'late error must not replace latest success');
    assert(!isHidden('text-results-section'));

    deferText();
    const beforeEmpty = runText('pending before empty');
    await runText('');
    waiting[0].resolve(textReply('pending before empty')); await beforeEmpty;
    assert(isHidden('text-results-section'),'late success must not undo newer empty-input rejection');
    assert(!isHidden('text-error-box'));
    assert.match(element('text-error-msg').innerText,/tidak boleh kosong/);
    assert(isHidden('btn-text-spinner'));

    deferText();
    const beforeError = runText('pending before rejection');
    const rejectedText = runText('rejected request');
    waiting[1].resolve({json:async()=>({status:'error',message:'latest rejection'})}); await rejectedText;
    waiting[0].resolve(textReply('pending before rejection')); await beforeError;
    assert(isHidden('text-results-section'),'late success must not undo newer API rejection');
    assert(!isHidden('text-error-box'));
    assert.equal(element('text-error-msg').innerText,'latest rejection');
    context.fetch = regularFetch;
    await runText('recovered request');
    assert(!isHidden('text-results-section'),'valid retry must show results');
    assert(isHidden('text-error-box'),'valid retry must clear previous error');
    assert.equal(element('res-dec-text').innerText,'recovered request');
  }
  console.log('PASS: exact integers, steppers, request serialization, Miller-Rabin labels, speedup labels'+(html.includes('text-input-msg')?', exact text, text request ordering and error recovery.':'.'));
}
main().catch(error=>{console.error(error);process.exitCode=1});
