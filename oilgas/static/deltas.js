'use strict';
const routes = JSON.parse(document.querySelector('#catalog-data').textContent);
const family = document.querySelector('#family');
const zone = document.querySelector('#zone');
const series = document.querySelector('#series');
const fx = document.querySelector('#eur_usd');
const form = document.querySelector('#delta-form');
function setOptions(select, items, previous) {
  select.replaceChildren(...items.map(([value, label]) => new Option(label, value)));
  if (items.some(([value]) => value === previous)) select.value = previous;
}
function updateSources() {
  const matching = routes.filter(r => r.family === family.value && r.zone === zone.value && r.series_id);
  setOptions(series, [['', 'Automatique'], ...matching.map(r => [r.series_id, r.series_id])], series.value);
  updateDetails();
}
function updateDetails() {
  const matching = routes.filter(r => r.family === family.value && r.zone === zone.value && (!series.value || r.series_id === series.value));
  const needsFx = matching.some(r => r.currency === 'EUR');
  document.querySelector('#fx-field').hidden = !needsFx;
  fx.disabled = !needsFx;
  const starts = matching.map(r => r.start_date).filter(Boolean).sort();
  const ends = matching.map(r => r.end_date).filter(Boolean).sort();
  const format = value => value.split('-').reverse().join('/');
  document.querySelector('#coverage').textContent = starts.length ? `Données : ${format(starts[0])} — ${format(ends.at(-1))}` : 'Aucune donnée disponible pour cette sélection.';
}
family.addEventListener('change', () => {
  const zones = [...new Set(routes.filter(r => r.family === family.value).map(r => r.zone))];
  setOptions(zone, zones.map(value => [value, value]), zone.value);
  updateSources();
});
zone.addEventListener('change', updateSources);
series.addEventListener('change', updateDetails);
updateDetails();
form.addEventListener('input', () => {
  const results = document.querySelector('.reference');
  if (results) {
    // Un résultat reste associé aux paramètres avec lesquels il a été calculé.
    document.querySelector('.output').replaceChildren(Object.assign(document.createElement('p'), {className: 'fx-applied', textContent: 'Paramètres modifiés. Relancez le calcul.'}));
  }
});
form.addEventListener('submit', () => {
  const button = document.querySelector('#calculate');
  button.disabled = true;
  button.textContent = 'Calcul en cours…';
});
window.addEventListener('pageshow', () => {
  const button = document.querySelector('#calculate');
  button.disabled = false;
  button.replaceChildren(document.createTextNode('Calculer les deltas '), Object.assign(document.createElement('span'), {textContent: '→'}));
});
const tooltip = document.querySelector('#chart-tooltip');
for (const bar of document.querySelectorAll('.delta-bar')) {
  const show = () => {
    const rect = bar.getBoundingClientRect();
    tooltip.textContent = `${bar.dataset.day} · ${bar.dataset.delta}`;
    tooltip.hidden = false;
    tooltip.style.left = `${Math.max(8, Math.min(rect.x, window.innerWidth - 240))}px`;
    tooltip.style.top = `${Math.max(8, rect.y - 44)}px`;
  };
  for (const event of ['mouseenter', 'focus']) bar.addEventListener(event, show);
  for (const event of ['mouseleave', 'blur']) bar.addEventListener(event, () => tooltip.hidden = true);
}
