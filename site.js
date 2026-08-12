
// Small cross-browser UI fixes that should apply to every page.
const globalStyle=document.createElement('style');
globalStyle.textContent=`
.hot-inner{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.hot-inner::-webkit-scrollbar{display:none;width:0;height:0}
.legal-links{display:flex;flex-wrap:wrap;gap:12px 18px;margin-top:18px;padding-top:16px;border-top:1px solid rgba(255,255,255,.08)}
.legal-links a{font-size:10px;color:#718596}.legal-links a:hover{color:#dce6ee}
.affiliate-kicker{font-size:9px;font-weight:900;letter-spacing:.14em;color:#8ccfff;margin-bottom:6px}
.affiliate-note{font-size:11px;color:#8296a7}
.affiliate-product{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:13px 0;border-top:1px solid rgba(255,255,255,.08)}
.affiliate-product b{display:block;font-size:13px}.affiliate-product small{display:block;margin-top:3px;color:#748797;font-size:9px}
.affiliate-buttons{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}
.affiliate-btn{display:inline-flex;align-items:center;justify-content:center;min-width:116px;padding:9px 12px;border-radius:9px;font-size:10px;font-weight:900}
.affiliate-amazon{background:#ffb84d;color:#15100a}.affiliate-rakuten{background:#bf0000;color:#fff}
.amazon-disclosure{max-width:1180px;margin:18px auto 0;padding:0 20px;color:#718596;font-size:9px}
@media(max-width:650px){.affiliate-product{align-items:flex-start;flex-direction:column}.affiliate-buttons{width:100%;justify-content:flex-start}.affiliate-btn{flex:1}.legal-links{gap:10px 14px}}
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
