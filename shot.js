// Smoke test: for each model, screenshots a mid-animation frame, a spread of steps, the exploded view and a phone layout.
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1280,height:760}});const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>m.type()=='error'&&errs.push(m.text()));
await p.goto('file://'+__dirname+'/index.html');
await p.waitForTimeout(1800);await p.screenshot({path:'landing.png'});await p.setViewportSize({width:390,height:800});await p.waitForTimeout(500);await p.screenshot({path:'landing-phone.png'});await p.setViewportSize({width:1280,height:760});
await p.click('#l-build');await p.waitForTimeout(2200);await p.screenshot({path:'after-build.png'});
const ex=async v=>{await p.evaluate(v=>{const e=document.getElementById('explode');e.value=v;e.oninput({target:e})},v)};
for(const [m,tag,steps,mid] of [[0,'a',[0,1,2,3,4,5,6],4],[1,'b',[0,2,4,7,9,11,13,15,17,20,22,24],15]]){
  await p.evaluate(m=>window.__model(m),m);await p.waitForTimeout(600);
  await p.evaluate(i=>window.__go(i,true),mid);await p.waitForTimeout(700);await p.screenshot({path:`${tag}-anim.png`});
  for(const i of steps){await p.evaluate(i=>window.__go(i,false),i);await p.waitForTimeout(900);await p.screenshot({path:`${tag}${i}.png`});}
  await ex(0.6);await p.waitForTimeout(500);await p.screenshot({path:`${tag}-explode.png`});await ex(0);
  await p.setViewportSize({width:390,height:800});await p.waitForTimeout(600);await p.screenshot({path:`${tag}-phone.png`});await p.setViewportSize({width:1280,height:760});
}
console.log(errs);await b.close()})()
