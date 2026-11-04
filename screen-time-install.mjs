const button=document.getElementById('copy');
const status=document.getElementById('status');
// URL fragments are not sent in HTTP requests. Never put this value in a URL,
// request, log, persistent storage or the rendered DOM.
const setup=location.hash.slice(1);
if(/^[a-f0-9]{64}$/.test(setup)){
  button.disabled=false;
  status.textContent='Private setup link ready. Copy the code, then download the shortcut.';
  button.addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(setup);status.textContent='Copied. Now download the shortcut and paste the code when it asks.';}
    catch{status.textContent='Clipboard permission was blocked. Open this QR link directly in Safari, then tap Copy again.';}
  });
}
