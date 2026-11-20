const canvas = document.querySelector('#game'), ctx = canvas.getContext('2d');
const menu = document.querySelector('#menu'), result = document.querySelector('#result'), hud = document.querySelector('#hud');
const keys = new Set(); let running = false, paused = false, last = 0, state, currentNight=1;
const lanternPos = [[0,25],[23.8,7.7],[14.7,-20.2],[-14.7,-20.2],[-23.8,7.7]];
const layouts={1:lanternPos,2:[[0,20],[17,-10],[-17,-10],[70,20],[87,-10],[53,-10]],3:[[0,6],[18,10],[-18,10],[35,-10],[-35,-10],[20,-35],[-20,-35]]};
const palette = { sky:'#0E1430', fog:'#1B2350', grass:'#2F5D50', sand:'#C9B48A', lit:'#FFB347', core:'#FFE9B0', off:'#5B5F6E', shade:'#120A1A', edge:'#7A3CFF' };
function reset(){
  state={player:{x:0,z:0,carried:0,flames:3}, lanterns:layouts[currentNight].map((p,i)=>({id:`L${i+1}`,x:p[0],z:p[1],lit:false,dep:0})), motes:[], shades:[], time:({1:300,2:330,3:360})[currentNight],score:0,pulse:0,dash:0,dashCd:0};paused=false;
  for(let i=0;i<20;i++){const r=i<8?12:33,a=i*(Math.PI*2/(i<8?8:16));state.motes.push({x:Math.cos(a)*r,z:Math.sin(a)*r});}
  state.shades=[{x:35,z:10,stun:0},{x:-30,z:-18,stun:0}]; result.hidden=true;
}
function project(x,y,z){ const dx=x-state.player.x,dz=z-state.player.z+9, depth=dz+24, scale=700/Math.max(5,depth); return [canvas.width/2+dx*scale,canvas.height*.55-y*scale,scale,depth]; }
function disk(x,z,r,color){const p=project(x,0,z); if(p[3]<1)return;ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(p[0],p[1],r*p[2],r*p[2]*.28,0,0,Math.PI*2);ctx.fill();}
function pillar(x,z,h,color){const p=project(x,0,z);if(p[3]<1)return;ctx.fillStyle=color;ctx.fillRect(p[0]-p[2]*.18,p[1]-h*p[2],p[2]*.36,h*p[2]);ctx.beginPath();ctx.arc(p[0],p[1]-h*p[2],p[2]*.45,0,Math.PI*2);ctx.fill();}
function draw(){
  ctx.fillStyle=palette.sky;ctx.fillRect(0,0,canvas.width,canvas.height);let g=ctx.createLinearGradient(0,0,0,canvas.height);g.addColorStop(.3,'#1B2350');g.addColorStop(1,'#12384A');ctx.fillStyle=g;ctx.fillRect(0,0,canvas.width,canvas.height);
  disk(0,0,currentNight===3?45:currentNight===2?28:40,palette.grass);if(currentNight===2){disk(70,0,28,palette.grass);ctx.fillStyle='#6B4A2F';let a=project(26,0,-2),b=project(44,0,2);ctx.fillRect(a[0],a[1]-8,b[0]-a[0],16)} state.motes.sort((a,b)=>b.z-a.z).forEach(m=>{disk(m.x,m.z,.28,palette.core)});
  state.lanterns.sort((a,b)=>b.z-a.z).forEach(l=>{if(l.lit)disk(l.x,l.z,6,'#ffb34722');pillar(l.x,l.z,2.4,l.lit?palette.lit:palette.off)});
  state.shades.sort((a,b)=>b.z-a.z).forEach(s=>{disk(s.x,s.z,.7,s.stun?'#3A3450':palette.edge);pillar(s.x,s.z,1.2,palette.shade)});
  pillar(state.player.x,state.player.z,1.6,'#E8E2D0'); disk(state.player.x,state.player.z,.35,palette.lit);
}
function update(dt){
  if(!running||paused)return; let x=(keys.has('d')?1:0)-(keys.has('a')?1:0), z=(keys.has('w')?1:0)-(keys.has('s')?1:0), n=Math.hypot(x,z)||1;state.dash=Math.max(0,state.dash-dt);state.dashCd=Math.max(0,state.dashCd-dt);let speed=state.dash>0?14:6;
  state.player.x+=x/n*speed*dt;state.player.z+=z/n*speed*dt;state.time=Math.max(0,state.time-dt);state.pulse=Math.max(0,state.pulse-dt);
  state.motes=state.motes.filter(m=>{if(state.player.carried<10&&Math.hypot(m.x-state.player.x,m.z-state.player.z)<=1){state.player.carried++;return false}return true});
  for(const s of state.shades){if(s.stun>0){s.stun-=dt;continue}let dx=state.player.x-s.x,dz=state.player.z-s.z,d=Math.hypot(dx,dz);if(d<18&&d>0){s.x+=dx/d*4*dt;s.z+=dz/d*4*dt}}
  if(state.time<=0)finish(false); renderHud();
}
function interact(){let near=state.lanterns.filter(l=>!l.lit&&Math.hypot(l.x-state.player.x,l.z-state.player.z)<=2).sort((a,b)=>a.id.localeCompare(b.id))[0];if(!near)return;let n=Math.min(state.player.carried,10-near.dep);near.dep+=n;state.player.carried-=n;state.score+=n*10;if(near.dep===10){near.lit=true;state.score+=100;if(state.lanterns.every(l=>l.lit))finish(true)}}
function pulse(){if(state.player.carried<3||state.pulse>0)return;state.player.carried-=3;state.pulse=3;for(const s of state.shades)if(Math.hypot(s.x-state.player.x,s.z-state.player.z)<=5){s.stun=2;state.score+=5}}
function renderHud(){let t=Math.ceil(state.time);document.querySelector('#flames').textContent='🔥'.repeat(state.player.flames);document.querySelector('#timer').textContent=`${String(Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;document.querySelector('#stats').innerHTML=`Đêm ${currentNight} · Đèn ${state.lanterns.filter(l=>l.lit).length}/${state.lanterns.length}<br>Điểm ${state.score}`;document.querySelector('#motes').textContent='◆'.repeat(state.player.carried)+'◇'.repeat(10-state.player.carried);let l=state.lanterns.find(l=>!l.lit&&Math.hypot(l.x-state.player.x,l.z-state.player.z)<=2);document.querySelector('#prompt').textContent=paused?'TẠM DỪNG · P để tiếp tục':l?`E — Nạp ánh sáng (${l.dep}/10)`:''}
function finish(win){running=false;result.hidden=false;result.querySelector('h2').textContent=win?'Bình minh trở lại':'Sương đen phủ đảo';result.querySelector('p').textContent=`Điểm: ${state.score}`}
function loop(now){let dt=Math.min(.05,(now-last)/1000||0);last=now;update(dt);draw();requestAnimationFrame(loop)}
function size(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio}addEventListener('resize',size);size();reset();requestAnimationFrame(loop);
addEventListener('keydown',e=>{keys.add(e.key.toLowerCase());if(e.key.toLowerCase()==='e')interact();if(e.key.toLowerCase()==='q')pulse();if((e.key==='Shift')&&state.dashCd<=0){state.dash=.2;state.dashCd=1.5}if(['p','escape'].includes(e.key.toLowerCase())){paused=!paused;renderHud()}if(e.key.toLowerCase()==='r'){reset();running=true}});addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
document.querySelector('#start').onclick=()=>{currentNight=Number(document.querySelector('#night').value);menu.hidden=true;hud.hidden=false;reset();running=true};result.querySelector('button').onclick=()=>{reset();running=true};
