// ── State ──
const state = { q: '', location: '', level: '', job_type: '', job_group: '', skills: '', page: 1, total_pages: 1 };
let debounceTimer = null;
let skillChoices = null;

// ── Helpers ──
const $ = id => document.getElementById(id);
const AVATAR_COLORS = ['#6366f1','#8b5cf6','#ec4899','#ef4444','#f97316','#eab308','#22c55e','#06b6d4','#3b82f6','#14b8a6'];

function avatarColor(name) {
  if (!name) return AVATAR_COLORS[0];
  let h = 0; for (const c of name) h = h * 31 + c.charCodeAt(0);
  return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length];
}

function initials(name) {
  if (!name) return '?';
  const w = name.trim().split(/\s+/);
  return w.length === 1 ? w[0].slice(0, 2).toUpperCase() : (w[0][0] + w[w.length - 1][0]).toUpperCase();
}

function fmtDate(d) {
  if (!d) return '';
  try { return new Date(d).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' }); }
  catch { return d; }
}

// Fallback khi logo không load được
function handleLogoError(img) {
  const div = document.createElement('div');
  div.className = 'avatar';
  div.style.background = img.dataset.color;
  div.textContent = img.dataset.ini;
  img.parentNode.replaceChild(div, img);
}

// ── Fetch Filters ──
async function loadFilters() {
  try {
    const res  = await fetch('/api/filters');
    const data = await res.json();
    populate('location-filter', data.locations, '📍 Tất cả địa điểm');
    populate('level-filter',    data.levels,    '🏷️ Tất cả cấp độ');
    populate('job-type-filter', data.job_types, '💼 Tất cả loại hình');
    populate('job-group-filter', data.job_groups, '👨‍💻 Tất cả nhóm công việc');
    
    if (skillChoices) {
      const skillOptions = data.skills.map(s => ({ value: s, label: s }));
      skillChoices.setChoices(skillOptions, 'value', 'label', true);
    }
  } catch (e) {
    console.error('loadFilters error:', e);
  }
}

function populate(id, items, placeholder) {
  const el = $(id);
  el.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach(v => {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = v;
    el.appendChild(o);
  });
}

// ── Fetch Jobs ──
async function loadJobs() {
  $('loading-state').style.display = 'flex';
  $('jobs-grid').style.display     = 'none';
  $('empty-state').style.display   = 'none';
  $('pagination').style.display    = 'none';
  $('result-count').innerHTML      = '';

  const p = new URLSearchParams({
    q:        state.q,
    location: state.location,
    level:    state.level,
    job_type: state.job_type,
    job_group: state.job_group,
    skills:   state.skills,
    page:     state.page,
  });

  try {
    const res  = await fetch(`/api/jobs?${p}`);
    const data = await res.json();
    state.total_pages = data.total_pages;

    $('loading-state').style.display = 'none';
    renderCount(data.total, data.page, data.per_page);
    renderJobs(data.jobs);
    renderPagination(data.page, data.total_pages);
  } catch (e) {
    console.error('loadJobs error:', e);
    $('loading-state').style.display = 'none';
    $('empty-state').style.display   = 'flex';
  }
}

// ── Render: Result Count ──
function renderCount(total, page, per) {
  if (!total) {
    $('result-count').textContent = 'Không tìm thấy kết quả nào';
    return;
  }
  const s = (page - 1) * per + 1;
  const e = Math.min(page * per, total);
  $('result-count').innerHTML =
    `Hiển thị <strong>${s}–${e}</strong> trong <strong>${total.toLocaleString('vi-VN')}</strong> việc làm`;
}

// ── Render: Job Cards ──
function renderJobs(jobs) {
  const grid = $('jobs-grid');
  if (!jobs.length) {
    $('empty-state').style.display = 'flex';
    return;
  }
  grid.style.display = 'grid';
  grid.innerHTML = jobs.map((job, i) => cardHTML(job, i)).join('');
}

function cardHTML(job, i) {
  const col  = avatarColor(job.company);
  const ini  = initials(job.company);
  const loc  = job.province || job.city || '';
  const tags = [];

  if (loc)            tags.push(`<span class="tag tag-loc">📍 ${loc}</span>`);
  if (job.job_type)   tags.push(`<span class="tag tag-type">💼 ${job.job_type}</span>`);
  if (job.level)      job.level.split(',').forEach(l => { if (l.trim()) tags.push(`<span class="tag tag-lvl">🏷️ ${l.trim()}</span>`); });
  if (job.salary)     tags.push(`<span class="tag tag-sal">💰 ${job.salary}</span>`);
  if (job.experience) tags.push(`<span class="tag tag-exp">⏱️ ${job.experience}</span>`);
  if (job.skills)     job.skills.split(',').forEach(s => { if (s.trim()) tags.push(`<span class="tag tag-skill" style="background:#f1f5f9;color:#475569;border-color:#cbd5e1">💡 ${s.trim()}</span>`); });

  return `
    <article class="job-card" style="animation-delay:${i * 40}ms">
      <div class="card-header">
        ${job.logo_link
          ? `<img class="avatar avatar-img" src="${job.logo_link}" alt="${job.company}" data-color="${col}" data-ini="${ini}" onerror="handleLogoError(this)">`
          : `<div class="avatar" style="background:${col}">${ini}</div>`
        }
        <div class="card-header-info">
          <p class="company-name" title="${job.company}">${job.company || 'N/A'}</p>
          <p class="posted-date">📅 ${fmtDate(job.posted_date)}</p>
        </div>
      </div>
      <h3 class="job-title" title="${job.job_title}">${job.job_title}</h3>
      <div class="tags">${tags.join('')}</div>
      <div class="card-footer">
        <a href="${job.link}" target="_blank" rel="noopener" class="view-btn">Xem việc làm →</a>
      </div>
    </article>`;
}

// ── Render: Pagination ──
function renderPagination(page, total) {
  const pg = $('pagination');
  if (total <= 1) { pg.style.display = 'none'; return; }
  pg.style.display = 'flex';

  const pages = buildPageNumbers(page, total);
  pg.innerHTML = `
    <button class="page-btn" id="pg-prev" ${page <= 1 ? 'disabled' : ''}>← Trước</button>
    ${pages.map(p =>
      p === '…'
        ? `<span class="page-dots">…</span>`
        : `<button class="page-btn ${p === page ? 'active' : ''}" data-page="${p}">${p}</button>`
    ).join('')}
    <button class="page-btn" id="pg-next" ${page >= total ? 'disabled' : ''}>Sau →</button>`;

  pg.querySelectorAll('[data-page]').forEach(btn =>
    btn.addEventListener('click', () => {
      state.page = +btn.dataset.page;
      loadJobs();
      scrollTo({ top: 0, behavior: 'smooth' });
    })
  );
  $('pg-prev').addEventListener('click', () => { state.page--; loadJobs(); scrollTo({ top: 0, behavior: 'smooth' }); });
  $('pg-next').addEventListener('click', () => { state.page++; loadJobs(); scrollTo({ top: 0, behavior: 'smooth' }); });
}

function buildPageNumbers(page, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [];
  if (page <= 4) {
    for (let i = 1; i <= 5; i++) pages.push(i);
    pages.push('…', total);
  } else if (page >= total - 3) {
    pages.push(1, '…');
    for (let i = total - 4; i <= total; i++) pages.push(i);
  } else {
    pages.push(1, '…', page - 1, page, page + 1, '…', total);
  }
  return pages;
}

// ── Event Listeners ──
document.addEventListener('DOMContentLoaded', () => {
  // Init Choices.js
  const skillEl = $('skill-filter');
  if (skillEl) {
    skillChoices = new Choices(skillEl, {
      removeItemButton: true,
      searchPlaceholderValue: 'Tìm kỹ năng...',
      placeholder: true,
      placeholderValue: '💡 Tất cả kỹ năng',
      itemSelectText: 'Nhấn để chọn',
      shouldSort: false,
    });
  }

  loadFilters();
  loadJobs();

  // Search with debounce
  $('search-input').addEventListener('input', e => {
    $('clear-btn').style.display = e.target.value ? 'block' : 'none';
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.q = e.target.value.trim();
      state.page = 1;
      loadJobs();
    }, 320);
  });

  // Clear search
  $('clear-btn').addEventListener('click', () => {
    $('search-input').value = '';
    $('clear-btn').style.display = 'none';
    state.q = '';
    state.page = 1;
    loadJobs();
  });

  // Filters
  $('location-filter').addEventListener('change', e => { state.location = e.target.value; state.page = 1; loadJobs(); });
  $('level-filter').addEventListener('change',    e => { state.level    = e.target.value; state.page = 1; loadJobs(); });
  $('job-type-filter').addEventListener('change', e => { state.job_type = e.target.value; state.page = 1; loadJobs(); });
  $('job-group-filter').addEventListener('change', e => { state.job_group = e.target.value; state.page = 1; loadJobs(); });
  
  $('skill-filter').addEventListener('change', e => { 
    if (skillChoices) {
      const selected = skillChoices.getValue(true) || [];
      state.skills = selected.join(',');
    }
    state.page = 1; 
    loadJobs(); 
  });

  // Reset all filters
  $('reset-btn').addEventListener('click', () => {
    state.q = ''; state.location = ''; state.level = ''; state.job_type = ''; state.job_group = ''; state.skills = ''; state.page = 1;
    $('search-input').value      = '';
    $('clear-btn').style.display = 'none';
    $('location-filter').value   = '';
    $('level-filter').value      = '';
    $('job-type-filter').value   = '';
    $('job-group-filter').value  = '';
    if (skillChoices) skillChoices.removeActiveItems();
    loadJobs();
  });

  // Analytics Modal
  initAnalyticsModal();
});

// ──────────────────────────────────────────────────────────
// ANALYTICS DASHBOARD
// ──────────────────────────────────────────────────────────

let analyticsCharts = {}; // Store chart instances for cleanup

async function initAnalyticsModal() {
  const analysisBtn = $('analysis-btn');
  const modalOverlay = $('analysis-modal-overlay');
  const modal = $('analysis-modal');
  const closeBtn = $('modal-close-btn');
  const categorySelect = $('category-select');

  // Open modal
  analysisBtn.addEventListener('click', async () => {
    openAnalyticsModal();
  });

  // Close modal (X button)
  closeBtn.addEventListener('click', closeAnalyticsModal);

  // Close modal (overlay click)
  modalOverlay.addEventListener('click', closeAnalyticsModal);

  // Prevent modal close when clicking inside modal
  modal.addEventListener('click', e => e.stopPropagation());

  // Category dropdown change
  categorySelect.addEventListener('change', async e => {
    const category = e.target.value;
    if (category) {
      await updateSkillsChart(category);
    } else {
      $('skills-empty-message').style.display = 'block';
      if (analyticsCharts.skillsByCategory) {
        analyticsCharts.skillsByCategory.destroy();
        delete analyticsCharts.skillsByCategory;
      }
      $('chart-skills-by-category').style.display = 'none';
    }
  });
}

async function openAnalyticsModal() {
  const overlay = $('analysis-modal-overlay');
  const modal = $('analysis-modal');
  const loading = $('modal-loading-state');
  const content = $('modal-content');

  // Show loading state
  overlay.classList.add('active');
  modal.classList.add('active');
  loading.style.display = 'flex';
  content.style.display = 'none';

  try {
    // Fetch all analytics data in parallel
    const [catData, levelData, skillsData, trendData] = await Promise.all([
      fetch('/api/analytics/job-category-distribution').then(r => r.json()),
      fetch('/api/analytics/level-distribution').then(r => r.json()),
      fetch('/api/analytics/top-skills').then(r => r.json()),
      fetch('/api/analytics/jobs-posted-trend').then(r => r.json()),
    ]);

    // Hide loading, show content
    loading.style.display = 'none';
    content.style.display = 'flex';

    // Init charts
    await initAllCharts(catData, levelData, skillsData, trendData);

    // Populate category dropdown
    populateCategoryDropdown(catData.categories || []);
  } catch (error) {
    console.error('Error loading analytics data:', error);
    loading.innerHTML = '<p style="color: var(--rose);">❌ Lỗi tải dữ liệu</p>';
  }
}

function closeAnalyticsModal() {
  const overlay = $('analysis-modal-overlay');
  const modal = $('analysis-modal');

  overlay.classList.remove('active');
  modal.classList.remove('active');

  // Destroy all charts
  Object.values(analyticsCharts).forEach(chart => {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  });
  analyticsCharts = {};
}

function populateCategoryDropdown(categories) {
  const select = $('category-select');
  select.innerHTML = '<option value="">Select a Job Category...</option>';
  categories.forEach(cat => {
    const option = document.createElement('option');
    option.value = cat.category;
    option.textContent = `${cat.category} (${cat.count})`;
    select.appendChild(option);
  });
  
  // Auto-select first category and load skills
  if (categories.length > 0) {
    select.value = categories[0].category;
    updateSkillsChart(categories[0].category);
  }
}

async function updateSkillsChart(category) {
  try {
    console.log('Fetching skills for category:', category);
    const res = await fetch(`/api/analytics/skills-by-category?category=${encodeURIComponent(category)}`);
    const data = await res.json();
    
    console.log('Skills data received:', data);

    if (!data.skills || data.skills.length === 0) {
      $('skills-empty-message').style.display = 'block';
      $('skills-empty-message').textContent = 'No skills data available for this category';
      $('chart-skills-by-category').style.display = 'none';
      if (analyticsCharts.skillsByCategory) {
        analyticsCharts.skillsByCategory.destroy();
        delete analyticsCharts.skillsByCategory;
      }
      return;
    }

    $('skills-empty-message').style.display = 'none';
    $('chart-skills-by-category').style.display = 'block';

    if (analyticsCharts.skillsByCategory) {
      analyticsCharts.skillsByCategory.destroy();
    }

    const ctx = $('chart-skills-by-category').getContext('2d');
    const bgColor = 'rgba(99, 102, 241, 0.15)';
    const borderColor = 'rgba(99, 102, 241, 0.8)';

    console.log('Creating chart with labels:', data.skills.map(s => s.skill));
    console.log('Creating chart with data:', data.skills.map(s => s.frequency));

    analyticsCharts.skillsByCategory = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.skills.map(s => s.skill),
        datasets: [{
          label: `Skills for ${category}`,
          data: data.skills.map(s => s.frequency),
          backgroundColor: bgColor,
          borderColor: borderColor,
          borderWidth: 2,
          borderRadius: 8,
          barThickness: 'flex',
          maxBarThickness: 40,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 10,
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 11 },
            cornerRadius: 8,
            displayColors: false,
          },
        },
        scales: {
          x: {
            grid: { drawBorder: false, color: 'rgba(148, 163, 184, 0.1)' },
            ticks: { color: 'rgba(148, 163, 184, 0.7)', font: { size: 10 } },
          },
          y: {
            grid: { display: false },
            ticks: { color: 'rgba(241, 245, 249, 0.8)', font: { size: 11 } },
          },
        },
      },
    });
    
    console.log('Chart created successfully');
  } catch (error) {
    console.error('Error updating skills chart:', error);
    $('skills-empty-message').style.display = 'block';
    $('skills-empty-message').textContent = '❌ Error loading skills data: ' + error.message;
    $('chart-skills-by-category').style.display = 'none';
  }
}

async function initAllCharts(catData, levelData, skillsData, trendData) {
  // 1. Job Category Distribution (Pie Chart)
  const ctxCat = $('chart-job-category').getContext('2d');
  const categoryColors = [
    'rgba(99, 102, 241, 0.8)',
    'rgba(56, 189, 248, 0.8)',
    'rgba(34, 197, 94, 0.8)',
    'rgba(245, 158, 11, 0.8)',
    'rgba(244, 63, 94, 0.8)',
    'rgba(139, 92, 246, 0.8)',
  ];

  analyticsCharts.jobCategory = new Chart(ctxCat, {
    type: 'pie',
    data: {
      labels: catData.categories.map(c => c.category),
      datasets: [{
        data: catData.categories.map(c => c.count),
        backgroundColor: categoryColors,
        borderColor: 'rgba(6, 12, 26, 0.8)',
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: 'rgba(241, 245, 249, 0.8)',
            padding: 12,
            font: { size: 11 },
            usePointStyle: true,
            pointStyle: 'circle',
          },
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 10,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          cornerRadius: 8,
          callbacks: {
            label: ctx => `${ctx.label}: ${ctx.parsed} jobs`,
          },
        },
      },
    },
  });

  // 2. Level Distribution (Bar Chart)
  const ctxLevel = $('chart-level-distribution').getContext('2d');
  analyticsCharts.levelDistribution = new Chart(ctxLevel, {
    type: 'bar',
    data: {
      labels: levelData.levels.map(l => l.level),
      datasets: [{
        label: 'Number of Jobs',
        data: levelData.levels.map(l => l.count),
        backgroundColor: 'rgba(167, 139, 250, 0.15)',
        borderColor: 'rgba(167, 139, 250, 0.8)',
        borderWidth: 2,
        borderRadius: 8,
        barThickness: 'flex',
        maxBarThickness: 50,
      }],
    },
    options: {
      indexAxis: 'x',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 10,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          cornerRadius: 8,
          displayColors: false,
        },
      },
      scales: {
        y: {
          grid: { drawBorder: false, color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: 'rgba(148, 163, 184, 0.7)', font: { size: 10 } },
        },
        x: {
          grid: { display: false },
          ticks: { color: 'rgba(241, 245, 249, 0.8)', font: { size: 10 } },
        },
      },
    },
  });

  // 3. Top 10 Skills (Horizontal Bar Chart)
  const ctxTopSkills = $('chart-top-skills').getContext('2d');
  analyticsCharts.topSkills = new Chart(ctxTopSkills, {
    type: 'bar',
    data: {
      labels: skillsData.skills.map(s => s.skill),
      datasets: [{
        label: 'Job Count',
        data: skillsData.skills.map(s => s.frequency),
        backgroundColor: 'rgba(56, 189, 248, 0.15)',
        borderColor: 'rgba(56, 189, 248, 0.8)',
        borderWidth: 2,
        borderRadius: 8,
        barThickness: 'flex',
        maxBarThickness: 35,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 10,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          cornerRadius: 8,
          displayColors: false,
        },
      },
      scales: {
        x: {
          grid: { drawBorder: false, color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: 'rgba(148, 163, 184, 0.7)', font: { size: 10 } },
        },
        y: {
          grid: { display: false },
          ticks: { color: 'rgba(241, 245, 249, 0.8)', font: { size: 11 } },
        },
      },
    },
  });

  // 4. Jobs Posted Trend (Line Chart)
  const ctxTrend = $('chart-jobs-trend').getContext('2d');
  const trendLabels = trendData.trend.map(t => `${t.month}/${t.year}`);
  
  analyticsCharts.jobsTrend = new Chart(ctxTrend, {
    type: 'line',
    data: {
      labels: trendLabels,
      datasets: [{
        label: 'Jobs Posted',
        data: trendData.trend.map(t => t.count),
        borderColor: 'rgba(16, 185, 129, 0.8)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgba(16, 185, 129, 0.8)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          labels: {
            color: 'rgba(241, 245, 249, 0.8)',
            font: { size: 11 },
            usePointStyle: true,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 10,
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          cornerRadius: 8,
          displayColors: false,
        },
      },
      scales: {
        y: {
          grid: { drawBorder: false, color: 'rgba(148, 163, 184, 0.1)' },
          ticks: { color: 'rgba(148, 163, 184, 0.7)', font: { size: 10 } },
        },
        x: {
          grid: { display: false },
          ticks: { color: 'rgba(241, 245, 249, 0.8)', font: { size: 10 }, maxRotation: 45, minRotation: 0 },
        },
      },
    },
  });
}
