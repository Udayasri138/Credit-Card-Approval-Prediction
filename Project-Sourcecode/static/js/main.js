/**
 * main.js
 * CreditAI — Global JavaScript
 * Handles: page loader, sidebar, topbar clock, stat counters,
 *          Chart.js dashboard charts, metric bar animation,
 *          toast notifications, form helpers.
 */

'use strict';

/* ══════════════════════════════════════
   1. Page Loader
══════════════════════════════════════ */
window.addEventListener('load', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    setTimeout(() => loader.classList.add('loaded'), 250);
  }
  // Animate metric bars after page load
  animateMetricBars();
  // Animate stat counters
  animateCounters();
});

/* ══════════════════════════════════════
   2. Sidebar Toggle
══════════════════════════════════════ */
const sidebar        = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const sidebarToggle  = document.getElementById('sidebarToggle');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('show');
  });
}
if (sidebarOverlay) {
  sidebarOverlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('show');
  });
}

/* ══════════════════════════════════════
   3. Topbar Live Clock
══════════════════════════════════════ */
const clockEl = document.getElementById('topbarTime');
if (clockEl) {
  function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  }
  updateClock();
  setInterval(updateClock, 1000);
}

/* ══════════════════════════════════════
   4. Animated Stat Counters
══════════════════════════════════════ */
function animateCounters() {
  const els = document.querySelectorAll('.stat-value[data-count]');
  els.forEach(el => {
    const target   = parseInt(el.getAttribute('data-count'), 10) || 0;
    const duration = 1200;
    const step     = Math.ceil(duration / (target || 1));
    let current    = 0;
    if (target === 0) { el.textContent = '0'; return; }
    const timer = setInterval(() => {
      current += Math.max(1, Math.floor(target / 40));
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = current.toLocaleString();
    }, step);
  });
}

/* ══════════════════════════════════════
   5. Dashboard Charts (Chart.js)
══════════════════════════════════════ */
async function initDashboardCharts() {
  const monthlyCanvas = document.getElementById('monthlyChart');
  const donutCanvas   = document.getElementById('donutChart');
  if (!monthlyCanvas && !donutCanvas) return;

  // Fetch monthly data
  let monthlyData = [];
  try {
    const res = await fetch('/api/chart/monthly');
    if (res.ok) monthlyData = await res.json();
  } catch (_) { /* offline fallback */ }

  // ── Monthly Bar Chart ──
  if (monthlyCanvas) {
    const labels   = monthlyData.map(d => d.month).reverse();
    const approved = monthlyData.map(d => parseInt(d.approved) || 0).reverse();
    const rejected = monthlyData.map(d => parseInt(d.rejected) || 0).reverse();

    new Chart(monthlyCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Approved',
            data: approved,
            backgroundColor: 'rgba(16, 185, 129, 0.7)',
            borderColor:     'rgba(16, 185, 129, 1)',
            borderWidth: 1, borderRadius: 6, borderSkipped: false,
          },
          {
            label: 'Rejected',
            data: rejected,
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor:     'rgba(239, 68, 68, 1)',
            borderWidth: 1, borderRadius: 6, borderSkipped: false,
          }
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            labels: { color: '#334155', font: { size: 12 } }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#e2e8f0', borderWidth: 1,
            titleColor: '#fff', bodyColor: 'rgba(255,255,255,0.8)',
          }
        },
        scales: {
          x: {
            grid:  { color: 'rgba(0,0,0,0.04)' },
            ticks: { color: '#64748b', font: { size: 11 } }
          },
          y: {
            beginAtZero: true,
            grid:  { color: 'rgba(0,0,0,0.05)' },
            ticks: { color: '#64748b', font: { size: 11 }, stepSize: 1 }
          }
        },
        animation: { duration: 1000, easing: 'easeOutQuart' }
      }
    });
  }

  // ── Donut Chart ──
  if (donutCanvas && window.DASH_STATS) {
    const { approved, rejected } = window.DASH_STATS;
    const hasData = (approved + rejected) > 0;
    new Chart(donutCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Approved', 'Rejected'],
        datasets: [{
          data: hasData ? [approved, rejected] : [1, 1],
          backgroundColor: ['rgba(19,136,8,0.85)', 'rgba(211,47,47,0.85)'],
          borderColor:     ['#138808',              '#d32f2f'],
          borderWidth: 2, hoverOffset: 6,
        }]
      },
      options: {
        responsive: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#334155', font: { size: 11 }, padding: 12 }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#e2e8f0', borderWidth: 1,
            callbacks: {
              label: ctx => hasData
                ? ` ${ctx.label}: ${ctx.parsed} (${Math.round(ctx.parsed / (approved+rejected) * 100)}%)`
                : ` No data yet`
            }
          }
        },
        animation: { animateRotate: true, duration: 1000, easing: 'easeOutQuart' }
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', initDashboardCharts);

/* ══════════════════════════════════════
   6. Metric Bar Animation (model_info page)
══════════════════════════════════════ */
function animateMetricBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.width = entry.target.dataset.width || entry.target.style.width;
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.metric-bar').forEach(bar => {
    const targetW = bar.style.width;
    bar.style.width = '0';
    bar.dataset.width = targetW;
    // small delay so CSS transition fires
    setTimeout(() => observer.observe(bar), 100);
  });
}

/* ══════════════════════════════════════
   7. Toast / showToast helper (used in forms)
══════════════════════════════════════ */
function showToast(message, type = 'info') {
  const container = document.querySelector('.flash-container')
    || (() => {
      const c = document.createElement('div');
      c.className = 'flash-container';
      document.querySelector('.page-content')?.prepend(c);
      return c;
    })();

  const alert = document.createElement('div');
  alert.className = `flash-alert flash-${type} fade-in`;
  const iconMap = { success: 'check-circle-fill', danger: 'x-circle-fill',
                    warning: 'exclamation-triangle-fill', info: 'info-circle-fill' };
  alert.innerHTML = `
    <i class="bi bi-${iconMap[type] || 'info-circle-fill'}"></i>
    ${message}
    <button class="flash-close" onclick="this.parentElement.remove()">
      <i class="bi bi-x"></i>
    </button>`;
  container.appendChild(alert);
  setTimeout(() => alert.remove(), 5000);
}

/* ══════════════════════════════════════
   8. Confidence Bars (animate on load)
══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.conf-bar[data-value]').forEach(bar => {
    const val = parseFloat(bar.dataset.value) || 0;
    bar.style.width = '0';
    setTimeout(() => {
      bar.style.transition = 'width 1s ease';
      bar.style.width = Math.min(val, 100) + '%';
    }, 200);
  });

  // Auto-close flash alerts after 6s
  document.querySelectorAll('.flash-alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.4s';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });
});

/* ══════════════════════════════════════
   9. Table Row Stagger Animation
══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('tbody tr').forEach((tr, i) => {
    tr.style.opacity = '0';
    tr.style.transform = 'translateY(8px)';
    tr.style.transition = `opacity 0.3s ease ${i * 0.04}s, transform 0.3s ease ${i * 0.04}s`;
    requestAnimationFrame(() => {
      tr.style.opacity = '1';
      tr.style.transform = 'translateY(0)';
    });
  });
});

/* ══════════════════════════════════════
   10. Dashboard — inject "now_hour" template variable polyfill
══════════════════════════════════════ */
// (Handled server-side via Jinja2 context processor — see app.py)
