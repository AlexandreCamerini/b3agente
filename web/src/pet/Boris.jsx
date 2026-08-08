/**
 * Boris.jsx — pet digital falante do Boris+ (coruja).
 * Drop-in React. Sem dependencias, sem build extra, sem rede.
 * Roda igual no PWA e no WKWebView (Capacitor).
 *
 * A FALA e DESACOPLADA da animacao (WKWebView iOS nao confia no speechSynthesis):
 *   - PWA / browser:  boris.speak(texto)               // usa Web Speech API
 *   - iOS Capacitor:  plugue um TTS nativo e dirija a boca:
 *        import { TextToSpeech } from '@capacitor-community/text-to-speech';
 *        boris.talk();                                  // abre o loop de boca
 *        await TextToSpeech.speak({ text, lang:'pt-BR' });
 *        boris.stop();                                  // fecha a boca
 *     (opcional) boris.setMouth(amp)  // 0..1 a cada frame se tiver amplitude
 *
 * API (via ref):
 *   speak(texto, {rate})   talk()   stop()   setMouth(0..1)
 *   setState('idle'|'thinking'|'speaking')   react('happy'|'bull')
 *   setVoice(SpeechSynthesisVoice|null)   setReduced(bool)
 *
 * Uso:
 *   const boris = useRef(null);
 *   <Boris ref={boris} size={300} />
 *   boris.current.setState('thinking');   // enquanto espera a resposta
 *   boris.current.speak(resposta);        // quando a resposta chega (PWA)
 *
 * Portado do original enviado pelo Alex (Downloads/Boris.jsx): a única
 * mudança é a origem da imagem — o PNG (490x655) saiu do data-URI embutido
 * (`OWL_SRC`, 132 KB de base64 numa linha só) e virou asset importado pelo
 * Vite, cacheável pelo service worker em vez de reparseado a cada boot.
 */
import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import owlSrc from '../assets/boris.png';

const CSS = `
@property --boris-blink { syntax:'<number>'; inherits:true; initial-value:0; }
@property --boris-mouth { syntax:'<number>'; inherits:true; initial-value:0; }
.boris-root{position:relative;user-select:none;-webkit-user-select:none;line-height:0}
.boris-stage{position:absolute;top:0;left:0;width:490px;height:655px;transform-origin:top left;
  --boris-ease:cubic-bezier(.2,0,0,1);--boris-emph:cubic-bezier(.3,0,0,1.25);--bob:1}
.boris-stage .platform{position:absolute;left:50%;bottom:64px;width:300px;height:58px;transform:translateX(-50%);
  background:radial-gradient(closest-side, rgba(0,0,0,.5), transparent 72%);filter:blur(2px)}
.boris-stage .owl-body{position:absolute;inset:0;will-change:transform;animation:boris-sway 6.4s var(--boris-ease) infinite}
.boris-stage .breath{position:absolute;inset:0;transform-origin:50% 78%;will-change:transform;animation:boris-breathe 3.6s var(--boris-ease) infinite}
.boris-stage .owl-img{position:absolute;inset:0;background-image:var(--owl);background-size:contain;background-repeat:no-repeat;background-position:center}
.boris-stage .gaze{position:absolute;inset:0;transform:translate(var(--gx,0px),var(--gy,0px)) rotate(var(--gr,0deg));transition:transform .22s var(--boris-ease);will-change:transform}
.boris-stage .emote{position:absolute;inset:0;transform-origin:50% 86%;will-change:transform}
.boris-stage .emote.talking{animation:boris-talknod .9s var(--boris-ease) infinite}
.boris-stage .emote.e-tilt{animation:boris-etilt 1.15s var(--boris-ease)}
.boris-stage .emote.e-peekL{animation:boris-epeekL 1.1s var(--boris-ease)}
.boris-stage .emote.e-peekR{animation:boris-epeekR 1.1s var(--boris-ease)}
.boris-stage .emote.e-hop{animation:boris-ehop .72s var(--boris-emph)}
.boris-stage .emote.e-wiggle{animation:boris-ewiggle .5s var(--boris-ease)}
.boris-stage .emote.e-pop{animation:boris-epop .5s var(--boris-emph)}
.boris-stage .confetti{position:absolute;width:9px;height:13px;border-radius:2px;pointer-events:none;will-change:transform}
.boris-stage .pling{position:absolute;left:300px;top:120px;min-width:26px;height:34px;padding:0 8px;background:#fff;color:#e0932c;font-weight:800;font-size:24px;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(0,0,0,.3);opacity:0;transform:scale(.5)}
.boris-stage .eye{position:absolute;width:84px;height:84px;border-radius:50%;overflow:hidden;pointer-events:none}
.boris-stage .eye.L{left:259px;top:167px}.boris-stage .eye.R{left:78px;top:172px}
.boris-stage .lid{position:absolute;inset:1px;border-radius:50% 50% 48% 48%;
  background:radial-gradient(120% 120% at 50% 30%, rgba(255,255,255,.28), transparent 46%),radial-gradient(closest-side, #d6c0b6 52%, #b99a91 82%, #937771 100%);
  box-shadow:inset 0 6px 9px rgba(255,255,255,.32), inset 0 -8px 11px rgba(96,64,60,.4);
  transform:translateY(calc((var(--boris-blink) - 1) * 114%))}
.boris-stage .lid:after{content:"";position:absolute;left:12%;right:12%;top:50%;height:5px;border-radius:50%;background:linear-gradient(180deg,rgba(66,40,38,.6),rgba(120,80,74,.12))}
.boris-stage .eye.R .lid{background:radial-gradient(120% 120% at 50% 30%, rgba(255,255,255,.26), transparent 46%),radial-gradient(closest-side, #d3bdb3 52%, #b6978e 82%, #90746e 100%)}
.boris-stage .mrig{position:absolute;inset:0;pointer-events:none}
.boris-stage .cav{position:absolute;left:187px;top:270px;width:40px;height:22px;
  background:radial-gradient(120% 100% at 50% 0%, #6b3a26 0%, #3d1e12 62%, #26120b 100%);
  clip-path:polygon(6% 0%,94% 0%,60% 100%,40% 100%);transform-origin:50% 0%;transform:scaleY(var(--boris-mouth));box-shadow:inset 0 2px 5px rgba(0,0,0,.5)}
.boris-stage .beak-jaw{position:absolute;inset:0;background:var(--owl) center/contain no-repeat;
  clip-path:polygon(184px 269px,228px 269px,206px 303px);transform-origin:206px 270px;
  transform:rotate(calc(var(--boris-mouth)*13deg)) translateY(calc(var(--boris-mouth)*4px));filter:drop-shadow(0 1px 2px rgba(0,0,0,.22))}
.boris-stage .fx{position:absolute;inset:0;pointer-events:none;overflow:visible}
.boris-stage .spark{position:absolute;width:16px;height:16px;opacity:0}
.boris-stage .arrow{position:absolute;left:340px;top:170px;width:70px;opacity:0}
.boris-stage .bubble{position:absolute;left:330px;top:70px;background:#fff;border-radius:16px;padding:9px 12px;box-shadow:0 8px 22px rgba(0,0,0,.35);opacity:0;transform:scale(.7) translateY(6px);transform-origin:0 100%}
.boris-stage .bubble:after{content:"";position:absolute;left:-6px;bottom:8px;border:7px solid transparent;border-right-color:#fff}
.boris-stage .bubble .d{display:inline-block;width:8px;height:8px;margin:0 2px;border-radius:50%;background:#8a93ad;animation:boris-think 1.1s var(--boris-ease) infinite}
.boris-stage .bubble .d:nth-child(2){animation-delay:.15s}.boris-stage .bubble .d:nth-child(3){animation-delay:.3s}
.boris-stage[data-state="speaking"] .breath{animation-duration:2.4s}
.boris-stage[data-state="thinking"] .owl-body{animation-duration:8s}
.boris-stage[data-state="thinking"] .breath{transform:rotate(-4deg)}
.boris-stage.boris-hop .owl-body{animation:boris-hop .62s var(--boris-emph)}
.boris-stage.boris-reduce .owl-body,.boris-stage.boris-reduce .breath{animation:none!important}
@keyframes boris-breathe{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(calc(-7px*var(--bob))) scale(1.014)}}
@keyframes boris-sway{0%,100%{transform:rotate(calc(-1.1deg*var(--bob)))}50%{transform:rotate(calc(1.1deg*var(--bob)))}}
@keyframes boris-hop{0%{transform:translateY(0) scale(1,1)}25%{transform:translateY(0) scale(1.06,.94)}55%{transform:translateY(-26px) scale(.96,1.06)}80%{transform:translateY(0) scale(1.05,.95)}100%{transform:translateY(0) scale(1,1)}}
@keyframes boris-think{0%,80%,100%{transform:translateY(0);opacity:.5}40%{transform:translateY(-5px);opacity:1}}
@keyframes boris-talknod{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-2.5px) rotate(-1.3deg)}}
@keyframes boris-etilt{0%{transform:rotate(0)}28%{transform:rotate(-8deg)}62%{transform:rotate(-8deg)}100%{transform:rotate(0)}}
@keyframes boris-epeekL{0%,100%{transform:translateX(0) rotate(0)}40%,60%{transform:translateX(-10px) rotate(-3deg)}}
@keyframes boris-epeekR{0%,100%{transform:translateX(0) rotate(0)}40%,60%{transform:translateX(10px) rotate(3deg)}}
@keyframes boris-ehop{0%{transform:translateY(0) scale(1,1)}30%{transform:translateY(0) scale(1.05,.95)}60%{transform:translateY(-16px) scale(.97,1.04)}100%{transform:translateY(0) scale(1,1)}}
@keyframes boris-ewiggle{0%,100%{transform:rotate(0)}25%{transform:rotate(4.5deg)}75%{transform:rotate(-4.5deg)}}
@keyframes boris-epop{0%{transform:scale(1)}42%{transform:scale(1.12)}100%{transform:scale(1)}}
@media (prefers-reduced-motion: reduce){.boris-stage .owl-body,.boris-stage .breath{animation:none!important}}
`;

function injectCSS(){
  if (typeof document === 'undefined' || document.getElementById('boris-css')) return;
  const s = document.createElement('style'); s.id = 'boris-css'; s.textContent = CSS; document.head.appendChild(s);
}

const Boris = forwardRef(function Boris({ size = 300, reduced = false, rate = 1, onReady }, ref){
  const rootRef = useRef(null);
  const stageRef = useRef(null);
  const eng = useRef({ speaking:false, manual:false, mouth:0, target:0, rate, mouthGain:1, blinkEvery:4, voice:null, reduced, raf:0, blinkT:0, fbT:0, fakeT:0 });

  const setVar = (k,v)=> stageRef.current && stageRef.current.style.setProperty(k, v);

  const setState = (st)=>{
    const stg = stageRef.current; if(!stg) return;
    stg.dataset.state = st;
    const on = st === 'thinking';
    const b = stg.querySelector('.bubble');
    if(b){ b.style.transition='transform .3s var(--boris-emph),opacity .3s'; b.style.opacity=on?1:0; b.style.transform=on?'scale(1) translateY(0)':'scale(.7) translateY(6px)'; }
  };

  const scheduleBlink = ()=>{
    const e = eng.current;
    const j = e.blinkEvery*(0.6+Math.random()*0.9);
    e.blinkT = setTimeout(()=>{ blink(); scheduleBlink(); }, j*1000);
  };
  const blink = ()=>{ const e=eng.current; if(e.reduced) return; setVar('--boris-blink','1'); setTimeout(()=>setVar('--boris-blink','0'), 92); };

  const osc = (t)=>{
    const s=t/1000;
    const base=0.5+0.5*Math.sin(s*15.0), mod=0.5+0.5*Math.sin(s*7.3+1.7), micro=0.5+0.5*Math.sin(s*23.0);
    const v=base*0.6+mod*0.3+micro*0.1;
    const gate=(Math.sin(s*3.1)+Math.sin(s*2.03))>1.2?0.15:1;
    return Math.max(0,Math.min(1,v*gate));
  };
  const loop = (t)=>{
    const e=eng.current;
    let desired = e.manual ? e.target : (e.speaking ? osc(t)*e.mouthGain : 0);
    const k = e.reduced?0.5:0.35;
    e.mouth += (desired-e.mouth)*k;
    setVar('--boris-mouth', e.mouth.toFixed(3));
    e.raf = requestAnimationFrame(loop);
  };

  const pickVoice = ()=>{
    if(typeof speechSynthesis==='undefined') return null;
    const vs=speechSynthesis.getVoices();
    const pt=vs.filter(v=>/pt(-|_)?BR/i.test(v.lang)||/^pt/i.test(v.lang)||/portugu/i.test(v.name));
    return eng.current.voice || pt[0] || vs[0] || null;
  };

  // --- speech (browser/PWA) ---
  const speak = (text, opts={})=>{
    if(!text) return; const e=eng.current;
    if(typeof window!=='undefined' && 'speechSynthesis' in window){
      window.speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(text);
      const v=pickVoice(); if(v){u.voice=v;u.lang=v.lang;} else {u.lang='pt-BR';}
      u.rate=opts.rate||e.rate; u.pitch=1.05;
      u.onstart=()=>{ clearTimeout(e.fbT); clearTimeout(e.fakeT); e.speaking=true; e.manual=false; setTalking(true); setState('speaking'); };
      u.onend=()=>{ endSpeak(); opts.then&&opts.then(); };
      u.onerror=()=>{ endSpeak(); opts.then&&opts.then(); };
      u.onboundary=()=>{ e.target=Math.min(1,0.9*e.mouthGain); };
      window.speechSynthesis.speak(u);
      clearTimeout(e.fbT); e.fbT=setTimeout(()=>{ if(!e.speaking) fakeSpeak(text,opts); }, 350);
    } else { fakeSpeak(text,opts); }
  };
  const fakeSpeak=(text,opts={})=>{ const e=eng.current; e.speaking=true; e.manual=false; setTalking(true); setState('speaking');
    const dur=Math.max(1200,Math.min(9000,(text?text.length:20)*62/e.rate));
    clearTimeout(e.fakeT); e.fakeT=setTimeout(()=>{ endSpeak(); opts.then&&opts.then(); },dur); };
  const endSpeak=()=>{ const e=eng.current; e.speaking=false; e.manual=false; e.target=0; setTalking(false); setState('idle'); };

  // --- native/manual talking (iOS Capacitor TTS) ---
  const talk = ()=>{ const e=eng.current; e.speaking=true; e.manual=false; setTalking(true); setState('speaking'); };
  const stop = ()=>{ endSpeak(); };
  const setMouth = (v)=>{ const e=eng.current; e.manual=true; e.speaking=true; setTalking(true); e.target=Math.max(0,Math.min(1,v)); setState('speaking'); };

  // --- reactions ---
  const sparkle=()=>{ const fx=stageRef.current&&stageRef.current.querySelector('.fx'); if(!fx)return;
    for(let i=0;i<7;i++){ const s=document.createElement('div'); s.className='spark';
      s.innerHTML='<svg viewBox="0 0 24 24" fill="#f2d34b"><path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4z"/></svg>';
      s.style.left=(190+Math.random()*130)+'px'; s.style.top=(150+Math.random()*120)+'px'; fx.appendChild(s);
      const ang=(Math.random()*2-1);
      s.animate([{opacity:0,transform:'translateY(0) scale(.3)'},{opacity:1,transform:`translateY(-30px) scale(1) rotate(${ang*60}deg)`,offset:.4},{opacity:0,transform:`translateY(-90px) scale(.5) rotate(${ang*120}deg)`}],{duration:900+Math.random()*400,easing:'cubic-bezier(.2,0,0,1)'}).onfinish=()=>s.remove();
    } };
  const emote=(cls,dur=1200)=>{ const el=stageRef.current&&stageRef.current.querySelector('.emote'); if(!el)return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); clearTimeout(eng.current['et_'+cls]); eng.current['et_'+cls]=setTimeout(()=>el.classList.remove(cls),dur); };
  const arrowFx=()=>{ const a=stageRef.current&&stageRef.current.querySelector('.arrow'); a&&a.animate([{opacity:0,transform:'translateY(30px) scale(.6)'},{opacity:1,transform:'translateY(-6px) scale(1.1)',offset:.35},{opacity:1,transform:'translateY(-14px) scale(1)',offset:.7},{opacity:0,transform:'translateY(-40px) scale(.9)'}],{duration:1400,easing:'cubic-bezier(.2,0,0,1)'}); };
  const confetti=()=>{ const fx=stageRef.current&&stageRef.current.querySelector('.fx'); if(!fx)return; const cols=['#f2a93b','#34d399','#5b8bf0','#ffffff','#f26d6d'];
    for(let i=0;i<26;i++){ const c=document.createElement('div'); c.className='confetti'; c.style.background=cols[i%cols.length]; c.style.left=(150+Math.random()*190)+'px'; c.style.top=(60+Math.random()*40)+'px'; fx.appendChild(c);
      const dx=(Math.random()*2-1)*150, dy=300+Math.random()*220, rot=(Math.random()*2-1)*720;
      c.animate([{opacity:1,transform:'translate(0,0) rotate(0)'},{opacity:1,transform:`translate(${dx*.5}px,${dy*.5}px) rotate(${rot*.5}deg)`,offset:.6},{opacity:0,transform:`translate(${dx}px,${dy}px) rotate(${rot}deg)`}],{duration:1400+Math.random()*700,easing:'cubic-bezier(.2,.6,.3,1)'}).onfinish=()=>c.remove(); } };
  const pling=(txt)=>{ const p=stageRef.current&&stageRef.current.querySelector('.pling'); if(!p)return; p.textContent=txt||'!'; p.animate([{opacity:0,transform:'scale(.5) translateY(6px)'},{opacity:1,transform:'scale(1) translateY(0)',offset:.3},{opacity:1,transform:'scale(1) translateY(-4px)',offset:.7},{opacity:0,transform:'scale(.8) translateY(-12px)'}],{duration:1100,easing:'cubic-bezier(.2,0,0,1)'}); };
  const squint=()=>{ setVar('--boris-blink','0.45'); clearTimeout(eng.current.sqT); eng.current.sqT=setTimeout(()=>setVar('--boris-blink','0'),430); };
  const react=(kind)=>{ const stg=stageRef.current; if(!stg)return;
    if(kind==='happy'){ emote('e-hop',720); sparkle(); squint(); }
    else if(kind==='bull'){ stg.classList.remove('boris-hop'); void stg.offsetWidth; stg.classList.add('boris-hop'); sparkle(); arrowFx(); confetti(); }
    else if(kind==='party'){ stg.classList.remove('boris-hop'); void stg.offsetWidth; stg.classList.add('boris-hop'); confetti(); sparkle(); squint(); }
    else if(kind==='surprise'){ emote('e-pop',520); pling('!'); }
  };
  const setTalking=(on)=>{ const el=stageRef.current&&stageRef.current.querySelector('.emote'); el&&el.classList.toggle('talking',on); };
  const gaze=()=>{ const set=(x,y)=>{ const g=stageRef.current&&stageRef.current.querySelector('.gaze'); if(!g||eng.current.reduced)return; g.style.setProperty('--gx',(x*11).toFixed(1)+'px'); g.style.setProperty('--gy',(y*7).toFixed(1)+'px'); g.style.setProperty('--gr',(x*3).toFixed(1)+'deg'); };
    const onMove=e=>{ if(!stageRef.current)return; const r=stageRef.current.getBoundingClientRect(); const x=Math.max(-1,Math.min(1,(e.clientX-(r.left+r.width/2))/(r.width/2))); const y=Math.max(-1,Math.min(1,(e.clientY-(r.top+r.height/2))/(r.height/2))); set(x*0.6,y*0.6); };
    window.addEventListener('pointermove',onMove); const leave=()=>set(0,0); rootRef.current&&rootRef.current.addEventListener('pointerleave',leave);
    eng.current.cleanupGaze=()=>{ window.removeEventListener('pointermove',onMove); rootRef.current&&rootRef.current.removeEventListener('pointerleave',leave); }; };
  const tap=()=>{ const body=stageRef.current&&stageRef.current.querySelector('.owl-body'); if(!body)return; body.style.cursor='pointer'; body.addEventListener('pointerdown',()=>{ if(eng.current.reduced)return; const r=['e-wiggle','e-pop','e-hop']; emote(r[Math.floor(Math.random()*r.length)],700); sparkle(); }); };
  const scheduleIdleBreak=()=>{ const t=5000+Math.random()*4500; eng.current.breakT=setTimeout(()=>{ idleBreak(); scheduleIdleBreak(); },t); };
  const idleBreak=()=>{ const e=eng.current; if(!stageRef.current||e.reduced||e.speaking||stageRef.current.dataset.state!=='idle')return; const acts=['tilt','peekL','peekR','hop','dblink','wiggle']; const a=acts[Math.floor(Math.random()*acts.length)]; if(a==='dblink'){ blink(); setTimeout(()=>blink(),240); return; } emote({tilt:'e-tilt',peekL:'e-peekL',peekR:'e-peekR',hop:'e-hop',wiggle:'e-wiggle'}[a]); };

  const setReduced=(on)=>{ eng.current.reduced=on; const stg=stageRef.current; stg&&stg.classList.toggle('boris-reduce',on); if(on)setVar('--boris-blink','0'); };
  const setVoice=(v)=>{ eng.current.voice=v; };

  useImperativeHandle(ref, ()=>({ speak, talk, stop, setMouth, setState, react, setVoice, setReduced,
    set rate(v){ eng.current.rate=v; }, set mouthGain(v){ eng.current.mouthGain=v; }, set blinkInterval(v){ eng.current.blinkEvery=v; clearTimeout(eng.current.blinkT); scheduleBlink(); } }));

  useEffect(()=>{
    injectCSS();
    const stg=stageRef.current;
    stg.style.setProperty('--owl', `url("${owlSrc}")`);
    if(typeof speechSynthesis!=='undefined'){ speechSynthesis.onvoiceschanged=()=>{}; }
    setReduced(reduced);
    eng.current.raf=requestAnimationFrame(loop);
    scheduleBlink(); gaze(); tap(); scheduleIdleBreak();
    onReady&&onReady();
    return ()=>{ cancelAnimationFrame(eng.current.raf); clearTimeout(eng.current.blinkT); clearTimeout(eng.current.fbT); clearTimeout(eng.current.fakeT); clearTimeout(eng.current.breakT); eng.current.cleanupGaze&&eng.current.cleanupGaze();
      if(typeof speechSynthesis!=='undefined') speechSynthesis.cancel(); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  useEffect(()=>{ eng.current.rate=rate; },[rate]);
  useEffect(()=>{ setReduced(reduced); // react to prop
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[reduced]);

  const scale = size/490;
  return (
    <div className="boris-root" ref={rootRef} style={{ width:size, height:Math.round(size*655/490) }} aria-hidden="false">
      <div className="boris-stage" ref={stageRef} data-state="idle" style={{ transform:`scale(${scale})` }}
           role="img" aria-label="Bóris, coruja mascote do Boris+">
        <div className="platform" />
        <div className="owl-body">
          <div className="breath">
            <div className="gaze"><div className="emote">
              <div className="owl-img" />
              <div className="eye L"><div className="lid" /></div>
              <div className="eye R"><div className="lid" /></div>
              <div className="mrig"><div className="cav" /><div className="beak-jaw" /></div>
            </div></div>
          </div>
        </div>
        <div className="fx">
          <div className="bubble" aria-hidden="true"><span className="d"/><span className="d"/><span className="d"/></div>
          <div className="pling" aria-hidden="true" />
          <svg className="arrow" viewBox="0 0 24 24" fill="none"><path d="M12 20V5M6 11l6-6 6 6" stroke="#34d399" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </div>
      </div>
    </div>
  );
});

export default Boris;
