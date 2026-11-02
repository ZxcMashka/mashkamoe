const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
let checks=0;function check(v){assert(v);checks++}
for(const name of ['panel','battle','preview']){
 const file=path.join(__dirname,'../package/res/gui/gameface/mods/mashka_marks/',name+'.js');
 const text=fs.readFileSync(file,'utf8');new vm.Script(text);
 const start=text.indexOf('var mmStopped='),end=text.indexOf('window.MM_CLEANUP_'+name+'=mmCleanup;',start);
 check(start>0&&end>start);
 let jobs=new Map(),listeners=[],id=0;
 const window={addEventListener:(...x)=>listeners.push(x),removeEventListener:(...x)=>{listeners=listeners.filter(y=>y[0]!==x[0]||y[1]!==x[1])},cancelAnimationFrame:x=>jobs.delete(x)};
 const context={window,document:{createElement:()=>({style:{}})},setTimeout:fn=>{jobs.set(++id,fn);return id},setInterval:fn=>{jobs.set(++id,fn);return id},requestAnimationFrame:fn=>{jobs.set(++id,fn);return id},clearTimeout:x=>jobs.delete(x),clearInterval:x=>jobs.delete(x)};
 vm.createContext(context);vm.runInContext(text.slice(start,end),context);
 let called=0;context.mmTimeout(()=>called++,10);const late=[...jobs.values()][0];context.mmInterval(()=>called++,10);context.mmFrame(()=>called++);
 check(jobs.size===3);check(listeners.length===2);
 let badge;const root={querySelector:()=>badge,appendChild:x=>badge=x};
 context.mmNotice(root,{ok:true,lang:'en',region:'asia',regionalMissing:true});
 check(badge.textContent.includes('ASIA'));check(badge.textContent.includes('unavailable'));check(badge.textContent.includes('estimates'));
 context.mmNotice(root,{ok:true,lang:'ru',region:'eu',regionalMissing:false});check(badge.textContent.includes('оценки'));check(!badge.textContent.includes('Нет региональных'));
 context.mmCleanup();check(jobs.size===0);check(listeners.length===0);late();check(called===0);
 context.mmCleanup();context.mmInterval(()=>called++,1);check(jobs.size===0);
 check(!/(?<!function )\bsetInterval\(/.test(text.slice(end))); // all application timers use tracked wrappers
}
console.log(checks+' asset checks passed (timer, listener, animation cleanup; regional and estimate notices).');
