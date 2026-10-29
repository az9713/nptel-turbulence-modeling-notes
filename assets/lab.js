/* Constructed covariance and local momentum budgets. No external state. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  if (!byId('correlation')) return;
  const fixed = (value, digits = 6) => Number(value).toFixed(digits);
  const set = (id, value) => { byId(id).textContent = value; };
  const svgNS = 'http://www.w3.org/2000/svg';
  function covariance() {
    const c = Number(byId('correlation').value);
    const su = 2, sv = 1, rho = 1.2, shear = 100;
    const uv = su * sv * c;
    set('correlation-value', fixed(c, 2));
    set('covariance-value', fixed(uv) + ' m²/s²');
    set('stress-value', fixed(-rho * uv) + ' Pa');
    set('production-value', fixed(-uv * shear) + ' m²/s³');
    byId('covariance-results').dataset.r12 = String(uv);
    byId('covariance-results').dataset.production = String(-uv * shear);
    const points = [];
    for (let i = 0; i <= 100; i++) {
      const theta = 2 * Math.PI * i / 100;
      const u = su * Math.cos(theta);
      const v = sv * (c * Math.cos(theta) + Math.sqrt(1-c*c) * Math.sin(theta));
      points.push((200 + 65 * u) + ',' + (155 - 65 * v));
    }
    byId('covariance-ellipse').setAttribute('points', points.join(' '));
    const states = byId('state-rows');
    states.replaceChildren();
    for (const x of [-1, 1]) {
      for (const y of [-1, 1]) {
        const row = document.createElement('tr');
        const u = su * x;
        const v = sv * (c * x + Math.sqrt(1-c*c) * y);
        for (const value of [u, v, u*v]) {
          const td = document.createElement('td');
          td.textContent = fixed(value, 4);
          row.append(td);
        }
        states.append(row);
      }
    }
  }
  function channel() {
    const shear = Number(byId('mean-gradient').value);
    const rho = 1.2, nu = 1.5e-5, h = .02, g = 10;
    const total = g * h / 2;
    const molecular = rho * nu * shear;
    const turbulent = total - molecular;
    const r12 = -turbulent / rho;
    set('gradient-value', fixed(shear, 0));
    set('channel-molecular', fixed(molecular) + ' Pa');
    set('channel-turbulent', fixed(turbulent) + ' Pa');
    set('channel-r12', fixed(r12, 8) + ' m²/s²');
    set('channel-fraction', fixed(100 * turbulent / total, 2) + '%');
    byId('channel-results').dataset.r12 = String(r12);
    byId('channel-results').dataset.total = String(total);
    byId('channel-results').dataset.residual = String(total - molecular - turbulent);
  }
  byId('correlation').addEventListener('input', covariance);
  byId('mean-gradient').addEventListener('input', channel);
  covariance(); channel();
  window.LAB_READY = true;
})();
