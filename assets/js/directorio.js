// Búsqueda y filtros del directorio (todo en el navegador; las fichas ya están en el HTML).
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var q = document.getElementById('q');
  var pais = document.getElementById('pais');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var contador = document.getElementById('contador');
  var vacio = document.getElementById('vacio');
  var cat = '';

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  cards.forEach(function (c) { c._texto = norm(c.dataset.texto); });

  function aplicar() {
    var palabras = norm(q.value).split(/\s+/).filter(Boolean);
    var p = pais.value;
    var n = 0;
    cards.forEach(function (c) {
      var ok = (!cat || c.dataset.cat === cat) &&
               (!p || c.dataset.pais === p) &&
               palabras.every(function (w) { return c._texto.indexOf(w) !== -1; });
      c.hidden = !ok;
      if (ok) n++;
    });
    contador.textContent = n === 1 ? '1 profesional' : n + ' profesionales';
    vacio.hidden = n !== 0;
  }

  function elegir(valor) {
    cat = valor;
    chips.forEach(function (b) {
      var activo = b.dataset.cat === valor;
      b.classList.toggle('is-active', activo);
      b.setAttribute('aria-pressed', activo ? 'true' : 'false');
    });
    aplicar();
  }

  chips.forEach(function (b) {
    b.addEventListener('click', function () { elegir(b.dataset.cat); });
  });
  q.addEventListener('input', aplicar);
  pais.addEventListener('change', aplicar);

  // Permite llegar filtrado desde una ficha: /?cat=Derecho
  var params = new URLSearchParams(location.search);
  var inicial = params.get('cat') || '';
  if (inicial && chips.some(function (b) { return b.dataset.cat === inicial; })) elegir(inicial);
  else elegir('');
})();
