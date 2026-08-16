
// v21 / 1-6: the runtime <style> injection and the runtime footer-link injection
// were removed. The ~20 CSS rules now live at the end of styles.css (no FOUC /
// layout shift on the affiliate blocks) and the 運営者情報・調査方法・広告方針・
// プライバシー・お問い合わせ links are written statically into every page, so ASP
// reviewers see them without executing JavaScript.
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.choice').forEach(btn=>{
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.choice').forEach(x=>x.classList.remove('active'));
      btn.classList.add('active');
      const result=document.querySelector('.diag-result');
      if(result){
        const type=btn.dataset.choice;
        const map={
          easy:'「ラクに続く」を重視。交換・装着・お手入れなど、毎回の小さな手間から比べてみましょう。',
          cost:'「ムダなく使える」を重視。価格だけでなく、使用量・交換回数・買い替え頻度まで確認しましょう。',
          power:'「しっかり役立つ」を重視。目的に合う機能と、使った人の評価が分かれた理由を先に見ましょう。'
        };
        result.innerHTML='<b>診断：</b>'+map[type]+' <a href="rankings.html" style="color:var(--lilac);font-weight:900;text-decoration:underline">調査一覧を見る →</a>';
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

  // v21 / 2-2: モバイル固定CTAバー。
  // 比較表(#comparison)を通過スクロールした後だけ出す。結論を読む前にCTAを
  // 出すと不信を買うため、位置ではなく「読み終えたか」で判定する。
  // バー自体は dist ビルド時（scripts/render_result_modules.py）に、有効な
  // アフィリエイトリンクがある記事へだけ挿入される。無ければここは何もしない。
  const stickyBar=document.querySelector('.sticky-cta-bar');
  const passMarker=document.querySelector('#comparison');
  if(stickyBar&&passMarker&&typeof IntersectionObserver==='function'){
    const toggle=passed=>{
      stickyBar.classList.toggle('is-visible',passed);
      stickyBar.setAttribute('aria-hidden',passed?'false':'true');
    };
    toggle(false);
    new IntersectionObserver(entries=>{
      entries.forEach(entry=>{
        // 上へ抜けた（= 比較表を読み終えた）ときだけ true。
        toggle(!entry.isIntersecting&&entry.boundingClientRect.top<0);
      });
    },{threshold:0}).observe(passMarker);
  }
});
