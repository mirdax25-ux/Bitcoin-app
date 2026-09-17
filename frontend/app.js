const API='http://127.0.0.1:8000';
const backend=document.getElementById('backend');
const result=document.getElementById('result');
const activity=document.getElementById('activity');
const score=document.getElementById('score');
const challengeResult=document.getElementById('challengeResult');

async function health(){
  try{
    const r=await fetch(API+'/health');
    const d=await r.json();
    backend.textContent=d.status==='ok'?'Online':'Error';
  }catch(e){ backend.textContent='Offline'; }
}

function inactivityDays(blockTime){
  if(!blockTime) return null;
  const last=new Date(blockTime*1000);
  return Math.max(0,Math.floor((Date.now()-last.getTime())/86400000));
}

async function lookup(){
  const address=document.getElementById('address').value.trim();
  result.textContent='Loading public blockchain data...';
  activity.textContent='—'; score.textContent='—';
  try{
    const r=await fetch(API+'/public/address/'+encodeURIComponent(address));
    const d=await r.json();
    if(!r.ok) throw new Error(d.detail||'Lookup failed');
    result.textContent=JSON.stringify(d,null,2);
    const days=inactivityDays(d.latest_confirmed_block_time);
    activity.textContent=days===null?'Unknown':days+' days';
    const ar=await fetch(API+'/analyze-address',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        address:d.address,
        inactivity_days:days===null?0:days,
        tx_count:d.tx_count,
        balance_btc:d.balance_sats/100000000
      })
    });
    const analysis=await ar.json();
    if(!ar.ok) throw new Error(analysis.detail||'Analysis failed');
    score.textContent=analysis.dormancy_score+'/100';
    result.textContent += '\n\nResearch analysis:\n'+JSON.stringify(analysis,null,2);
  }catch(e){ result.textContent='Error: '+e.message; }
}

async function createChallenge(){
  const address=document.getElementById('address').value.trim();
  challengeResult.textContent='Creating challenge...';
  try{
    const r=await fetch(API+'/ownership/challenge',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({address})
    });
    const d=await r.json();
    if(!r.ok) throw new Error(d.detail||'Challenge failed');
    challengeResult.textContent=d.message_to_sign+'\n\nExpires: '+d.expires_at+'\n\n'+d.warning;
  }catch(e){ challengeResult.textContent='Error: '+e.message; }
}

document.getElementById('lookup').addEventListener('click',lookup);
document.getElementById('challenge').addEventListener('click',createChallenge);
health();

let activeChallengeId=null;
const oldChallenge=challenge;
challenge=async function(){
  await oldChallenge();
  try{const d=JSON.parse(challengeResult.textContent); activeChallengeId=d.challenge_id||null;}catch(e){}
};
document.getElementById('challenge').removeEventListener('click',oldChallenge);
document.getElementById('challenge').addEventListener('click',challenge);

async function verifySignature(){
  const address=document.getElementById('address').value.trim();
  const signature=document.getElementById('signature').value.trim();
  const out=document.getElementById('verifyResult');
  if(!activeChallengeId){out.textContent='Create a challenge first.';return;}
  if(!signature){out.textContent='Paste the wallet signature only.';return;}
  try{
    const r=await fetch(API+'/ownership/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challenge_id:activeChallengeId,signature,address})});
    const d=await r.json();
    out.textContent=r.ok?'OWNERSHIP VERIFIED\n'+JSON.stringify(d,null,2):'NOT VERIFIED: '+(d.detail||'Invalid signature');
  }catch(e){out.textContent='Verification error: '+e.message;}
}
document.getElementById('verify').addEventListener('click',verifySignature);
