
// Small cross-browser UI fixes that should apply to every page.
const globalStyle=document.createElement('style');
globalStyle.textContent=`
.hot-inner{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.hot-inner::-webkit-scrollbar{display:none;width:0;height:0}
.legal-links{display:flex;flex-wrap:wrap;gap:12px 18px;margin-top:18px;padding-top:16px;border-top:1px solid rgba(255,255,255,.08)}
.legal-links a{font-size:10px;color:#718596}.legal-links a:hover{color:#dce6ee}
`;
document.head.appendChild(globalStyle);

document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.choice').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.choice').forEach(x=>x.classList.remove('active'));
      btn.classList.add('active');
      const result=document.querySelector('.diag-result');
      if(result){
        const type=btn.dataset.choice;
        const map={
          easy:'あなたは「手軽さ重視」。タブレット系を最初に比較すると選びやすいです。',
          cost:'あなたは「コスパ重視」。粉末系を基準に1回あたり費用を比べるのがおすすめです。',
          power:'あなたは「洗浄力重視」。油汚れ・茶渋など、汚れ別の評価を優先して見てください。'
        };
        result.innerHTML='<b>診断：</b>'+map[type];
        result.classList.add('show');
      }
    });
  });

  const buttons=[...document.querySelectorAll('.focus-btn')];
  const panel=document.querySelector('#focus-panel');
  const content={
    power:['洗浄力を重視するなら','油汚れ・茶渋・こびりつきなど、汚れの種類ごとの評価を確認します。平均点だけではなく「何の汚れに強かったか」を見るのがポイントです。'],
    easy:['手軽さを重視するなら','計量不要、投入しやすさ、保管しやすさを確認します。毎日使う場合は、小さな手間の差が継続利用の満足度につながります。'],
    cost:['コスパを重視するなら','本体価格だけでなく、1回あたりの使用量と購入頻度を確認します。便利な商品ほど1回単価が上がる場合があります。']
  };
  buttons.forEach(btn=>btn.addEventListener('click',()=>{
    buttons.forEach(x=>x.classList.remove('active'));btn.classList.add('active');
    if(panel){const [h,p]=content[btn.dataset.focus];panel.innerHTML='<h3>'+h+'</h3><p>'+p+'</p>';}
  }));

  const footer=document.querySelector('.footer .wrap');
  if(footer && !footer.querySelector('.legal-links')){
    const nav=document.createElement('nav');
    nav.className='legal-links';
    nav.setAttribute('aria-label','サイト情報');
    nav.innerHTML=[
      ['about.html','運営者情報'],
      ['methodology.html','調査方法'],
      ['disclosure.html','広告・アフィリエイト方針'],
      ['privacy.html','プライバシーポリシー'],
      ['contact.html','お問い合わせ']
    ].map(([href,label])=>`<a href="${href}">${label}</a>`).join('');
    footer.appendChild(nav);
  }
});
