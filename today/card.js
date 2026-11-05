// Draws the Break of the Day card on a canvas, 1080x1350.
//
// Lifted VERBATIM from supabase/functions/approve/index.ts (the approval page's
// own canvas port of marketing/make-break-card.py). Three copies of this
// geometry now exist and they have to stay in step; this one is a straight copy
// rather than a re-derivation so a diff against the approve page shows drift.
//
// It is drawn in the page rather than on a server because the phone rendering it
// has SF Pro Rounded natively and a Linux runner does not -- a server-rendered
// card would be off-brand in the one way nobody would notice until it shipped.

const ICON = "data:image/png;base64,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";
const GRAD_TOP=[86,139,148], GRAD_BOT=[55,89,96];
const CREAM='#F7F5F0', MUTED='#B6C7CB';
const VCOL={fire:'#E8734A',fun:'#1F6F78',marginal:'#8A74BF',skip:'#6B7280'};
// Same amplitude encoding as the app's VerdictWaveIcon: shape carries the
// verdict where colour can't.
const VAMP={skip:.08,marginal:.34,fun:.66,fire:1.0};
const rnd=(f,d)=>Number(f).toFixed(d);
const ICON_IMG=new Image(); ICON_IMG.src=ICON;

function sizeWords(f){
  if(f<1)return'flat'; if(f<2)return'ankle to knee high'; if(f<3)return'knee to waist high';
  if(f<4)return'waist to chest high'; if(f<5)return'chest to shoulder high';
  if(f<7)return'shoulder to head high'; if(f<9)return'overhead';
  if(f<12)return'well overhead'; return'double overhead plus';}

function tracked(c,x,y,t,track){for(const ch of t){c.fillText(ch,x,y);x+=c.measureText(ch).width+track;}}
function trackedW(c,t,track){let w=0;for(const ch of t)w+=c.measureText(ch).width+track;return w-track;}
function wrap(c,t,maxW){const ws=t.split(' ');const out=[];let cur='';
  for(const w of ws){const n=cur?cur+' '+w:w;
    if(c.measureText(n).width<=maxW||!cur)cur=n;else{out.push(cur);cur=w;}}
  if(cur)out.push(cur);return out;}

function waveGlyph(c,x,y,w,h,amp,stroke,whitecap){
  c.save();c.strokeStyle='#fff';c.lineWidth=stroke;c.lineCap='round';c.lineJoin='round';
  c.beginPath();const mid=y+h/2, a=(h/2-stroke)*amp;
  for(let i=0;i<=w;i+=2){const px=x+i, py=mid-Math.sin(i/w*Math.PI*3)*a;
    i?c.lineTo(px,py):c.moveTo(px,py);}
  c.stroke();
  if(whitecap){c.fillStyle='#fff';c.beginPath();
    c.arc(x+w/6,mid-a,stroke*1.15,0,7);c.fill();}
  c.restore();}

// Geometry is a port of marketing/make-break-card.py. Fractions of W/H, same names.
function drawCard(cv,p){
  const W=1080,H=1350; cv.width=W; cv.height=H;
  const c=cv.getContext('2d');
  const v=(p.verdict||'fun').toLowerCase(), vcol=VCOL[v]||VCOL.fun;
  const g=c.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'rgb('+GRAD_TOP+')'); g.addColorStop(1,'rgb('+GRAD_BOT+')');
  c.fillStyle=g; c.fillRect(0,0,W,H);
  // the icon's two wave bands
  [[.050,.88,'rgba(110,119,122,.69)'],[.038,.96,'rgba(128,136,139,.55)']].forEach(([amp,yo,col])=>{
    c.fillStyle=col; c.beginPath(); c.moveTo(0,H);
    for(let x=0;x<=W;x+=4)c.lineTo(x,H*yo-Math.sin(x/W*Math.PI*1.15+0.6)*H*amp);
    c.lineTo(W,H); c.closePath(); c.fill();});

  const M=Math.round(W*.093); const R='ui-rounded,-apple-system,system-ui,sans-serif';
  c.textBaseline='top';

  c.font='600 '+Math.round(W*.0296)+'px '+R; c.fillStyle=MUTED;
  let y=Math.round(H*.070);
  tracked(c,M,y,'BREAK OF THE DAY',W*.0083); y+=Math.round(H*.045);

  let ns=Math.round(W*.098); c.font='700 '+ns+'px '+R;
  let lines=wrap(c,p.name,W-M*2);
  if(lines.length>2){ns=Math.round(W*.070);c.font='700 '+ns+'px '+R;lines=wrap(c,p.name,W-M*2);}
  c.fillStyle=CREAM; for(const l of lines){c.fillText(l,M,y);y+=Math.round(ns*1.06);}
  y+=Math.round(H*.004);

  c.font='500 '+Math.round(W*.0361)+'px '+R; c.fillStyle=MUTED;
  c.fillText(p.region,M,y); y+=Math.round(H*.050);

  const fv=Math.round(W*.0546); c.font='700 '+fv+'px '+R;
  const word=v.toUpperCase(), tw=trackedW(c,word,W*.0046);
  const gw=Math.round(W*.089), gh=Math.round(W*.050);
  const padx=Math.round(W*.037), pady=Math.round(W*.024), gap=Math.round(W*.026);
  const capW=Math.round(padx*2+gw+gap+tw), capH=Math.round(fv+pady*2);
  c.fillStyle=vcol; c.beginPath(); c.roundRect(M,y,capW,capH,capH/2); c.fill();
  waveGlyph(c,M+padx,y+(capH-gh)/2,gw,gh,VAMP[v],Math.max(4,Math.round(W*.0065)),v==='fire');
  c.fillStyle='#fff'; c.font='700 '+fv+'px '+R;
  tracked(c,M+padx+gw+gap,y+(capH-fv)/2-Math.round(W*.004),word,W*.0046);
  y+=capH+Math.round(H*.052);

  const fh=Math.round(W*.0537); c.font='600 '+fh+'px '+R; c.fillStyle=CREAM;
  for(const l of wrap(c,p.read,W-M*2).slice(0,3)){c.fillText(l,M,y);y+=Math.round(fh*1.30);}

  const sy=H-Math.round(H*.255);
  c.strokeStyle='rgba(255,255,255,.18)'; c.lineWidth=2;
  c.beginPath(); c.moveTo(M,sy-Math.round(H*.038)); c.lineTo(W-M,sy-Math.round(H*.038)); c.stroke();
  const cw=Math.round((W-M*2)/3);
  const cols=[['SIZE',rnd(p.faceFt,1)+' ft',sizeWords(p.faceFt)],
              ['SWELL',Math.round(p.periodS)+' s',p.swellDir],
              ['WIND',Math.round(p.windKt)+' kt',p.windWords]];
  cols.forEach(([k,val,sub],i)=>{
    const x=M+cw*i;
    c.font='600 '+Math.round(W*.0250)+'px '+R; c.fillStyle=MUTED;
    tracked(c,x,sy,k,W*.0074);
    c.font='700 '+Math.round(W*.0472)+'px '+R; c.fillStyle=CREAM;
    c.fillText(val,x,sy+Math.round(H*.030));
    let ss=Math.round(W*.0287); c.font='500 '+ss+'px '+R;
    while(c.measureText(sub).width>cw-Math.round(W*.030)&&ss>16){ss-=2;c.font='500 '+ss+'px '+R;}
    c.fillStyle=MUTED; c.fillText(sub,x,sy+Math.round(H*.078));});
  c.font='500 '+Math.round(W*.0287)+'px '+R; c.fillStyle='rgba(255,255,255,.47)';
  c.fillText(p.hourLabel,M,sy+Math.round(H*.118));

  const fy=H-Math.round(H*.058), ih=Math.round(W*.052);
  if(ICON_IMG&&ICON_IMG.complete)c.drawImage(ICON_IMG,M,fy-ih/2,ih,ih);
  c.font='600 '+Math.round(ih*.86)+'px '+R; c.fillStyle=CREAM;
  c.fillText('Boardcall',M+ih+Math.round(ih*.34),fy-Math.round(ih*.46));
  c.font='500 '+Math.round(W*.0250)+'px '+R; c.fillStyle='rgba(255,255,255,.47)';
  const dt='Open-Meteo (CC BY 4.0)';
  c.fillText(dt,W-M-c.measureText(dt).width,fy-Math.round(W*.052*.20));
}

