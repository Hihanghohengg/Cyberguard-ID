/**
 * CyberGuard-ID — High Contrast, Readable Chart Components
 * Renders Category Doughnut, Risk Distribution Bar, and Dataset sample distributions.
 */
const Charts = {
    instances: {},

    // Clean, distinct colors (calm, accessible)
    colors: {
        'C0': '#10b981', // Emerald Safe
        'C1': '#fbbf24', // Amber Slang
        'C2': '#38bdf8', // Sky Constructive
        'C3': '#f87171', // Red Hate Speech
        'C4': '#fb923c', // Orange Harassment
        'C5': '#f472b6', // Pink Sexual Harassment
        'C6': '#dc2626', // Deep Red Threat
        'C7': '#94a3b8', // Slate Review
        'normal_konstruktif': '#10b981',
        'kritik_wajar': '#38bdf8',
        'bahasa_kasar': '#fbbf24',
        'personal_harassment': '#fb923c',
        'hate_speech': '#f87171',
        'sexual_harassment': '#f472b6',
        'threat_intimidation': '#dc2626',
        'Normal': '#10b981',
        'Abusive': '#fbbf24',
        'HS Lemah': '#38bdf8',
        'HS Sedang': '#f87171',
        'HS Kuat': '#fb923c',
    },

    riskColors: {
        'rendah': '#10b981',
        'sedang': '#fbbf24',
        'tinggi': '#f87171',
        'kritis': '#dc2626',
        'low': '#10b981',
        'medium': '#fbbf24',
        'high': '#f87171',
        'critical': '#dc2626',
    },

    labelNames: {
        'C0': 'Normal / Aman',
        'C1': 'Bahasa Kasar',
        'C2': 'Kritik Wajar',
        'C3': 'Ujaran Kebencian',
        'C4': 'Pelecehan Personal',
        'C5': 'Pelecehan Seksual',
        'C6': 'Ancaman / Intimidasi',
        'normal_konstruktif': 'Normal / Aman',
        'kritik_wajar': 'Kritik Wajar',
        'bahasa_kasar': 'Bahasa Kasar',
        'personal_harassment': 'Pelecehan Personal',
        'hate_speech': 'Ujaran Kebencian',
        'sexual_harassment': 'Pelecehan Seksual',
        'threat_intimidation': 'Ancaman / Intimidasi',
        'Normal': 'Normal',
        'Abusive': 'Bahasa Kasar',
        'HS Lemah': 'Hate Speech Lemah',
        'HS Sedang': 'Hate Speech Sedang',
        'HS Kuat': 'Hate Speech Kuat',
    },

    riskNames: {
        'rendah': 'Aman',
        'sedang': 'Perhatian (Review Opsional)',
        'tinggi': 'Berbahaya (Wajib Review)',
        'kritis': 'Sangat Berbahaya (Prioritas Eskalasi)',
        'low': 'Aman',
        'medium': 'Perhatian (Review Opsional)',
        'high': 'Berbahaya (Wajib Review)',
        'critical': 'Sangat Berbahaya (Prioritas Eskalasi)',
    },

    destroy(id) {
        if (this.instances[id]) {
            try {
                this.instances[id].destroy();
            } catch (e) {
                console.warn('Error destroying chart instance:', e);
            }
            delete this.instances[id];
        }
    },

    _renderEmptyState(canvas, message = 'Belum ada data visualisasi.') {
        const parent = canvas.parentElement;
        if (!parent) return;
        
        let emptyEl = parent.querySelector('.chart-empty-state');
        if (!emptyEl) {
            emptyEl = document.createElement('div');
            emptyEl.className = 'chart-empty-state';
            emptyEl.style.cssText = 'position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--text-muted);font-size:0.95rem;text-align:center;padding:16px;pointer-events:none;';
            parent.appendChild(emptyEl);
        }
        emptyEl.innerHTML = `<span class="material-symbols-outlined" style="font-size:32px;margin-bottom:8px;color:var(--text-muted);">pie_chart</span><span>${message}</span>`;
        canvas.style.opacity = '0.05';
    },

    _clearEmptyState(canvas) {
        const parent = canvas.parentElement;
        if (!parent) return;
        const emptyEl = parent.querySelector('.chart-empty-state');
        if (emptyEl) emptyEl.remove();
        canvas.style.opacity = '1';
    },

    categoryDoughnut(canvasId, distribution = {}) {
        this.destroy(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (typeof Chart === 'undefined') {
            console.error('Chart.js library is not loaded');
            return;
        }

        const entries = Object.entries(distribution || {}).filter(([_, count]) => count > 0);
        const total = entries.reduce((acc, [_, count]) => acc + (Number(count) || 0), 0);

        if (entries.length === 0 || total === 0) {
            this._renderEmptyState(canvas, 'Belum ada komentar terklasifikasi.');
            return;
        }
        this._clearEmptyState(canvas);

        const labels = entries.map(([k]) => k);
        const data = entries.map(([_, v]) => v);
        const bgColors = labels.map(l => this.colors[l] || '#94a3b8');
        const displayLabels = labels.map(l => this.labelNames[l] || l);

        this.instances[canvasId] = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: displayLabels,
                datasets: [{
                    data,
                    backgroundColor: bgColors,
                    borderWidth: 2,
                    borderColor: '#121e31',
                    hoverBorderWidth: 3,
                    hoverBorderColor: '#ffffff',
                    hoverOffset: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                layout: {
                    padding: { top: 6, bottom: 6, left: 6, right: 6 }
                },
                plugins: {
                    legend: {
                        position: window.innerWidth < 768 ? 'bottom' : 'right',
                        labels: {
                            color: '#cbd5e1',
                            font: { family: "'Inter', sans-serif", size: 12.5, weight: '600' },
                            padding: 10,
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            boxWidth: 10,
                        },
                    },
                    tooltip: {
                        backgroundColor: '#18273f',
                        titleColor: '#38bdf8',
                        bodyColor: '#ffffff',
                        titleFont: { family: "'Inter', sans-serif", weight: '700', size: 13 },
                        bodyFont: { family: "'Inter', sans-serif", size: 13 },
                        borderColor: '#334b6b',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            label(context) {
                                const val = context.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${val.toLocaleString()} komentar (${pct}%)`;
                            }
                        }
                    },
                },
            },
        });
    },

    categoryDonut(canvasId, distribution) {
        return this.categoryDoughnut(canvasId, distribution);
    },

    renderCategoryChart(canvasId, distribution) {
        return this.categoryDoughnut(canvasId, distribution);
    },

    riskBar(canvasId, distribution = {}) {
        this.destroy(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (typeof Chart === 'undefined') {
            console.error('Chart.js library is not loaded');
            return;
        }

        // Fix parsing bug: backend uses 'low', 'medium', 'high', 'critical'
        // Need to read exact fields and fallback properly without omitting actual 0s
        const order = ['rendah', 'sedang', 'tinggi', 'kritis'];
        const normalizedData = {
            'rendah': distribution.low !== undefined ? distribution.low : (distribution.rendah || 0),
            'sedang': distribution.medium !== undefined ? distribution.medium : (distribution.sedang || 0),
            'tinggi': distribution.high !== undefined ? distribution.high : (distribution.tinggi || 0),
            'kritis': distribution.critical !== undefined ? distribution.critical : (distribution.kritis || 0),
        };

        const total = Object.values(normalizedData).reduce((acc, v) => acc + (Number(v) || 0), 0);

        if (total === 0) {
            this._renderEmptyState(canvas, 'Belum ada data risiko.');
            return;
        }
        this._clearEmptyState(canvas);

        const labels = order;
        const data = labels.map(l => normalizedData[l]);
        const bgColors = labels.map(l => this.riskColors[l] || '#94a3b8');
        const displayLabels = labels.map(l => this.riskNames[l] || l);

        this.instances[canvasId] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: 'Jumlah Komentar',
                    data,
                    backgroundColor: bgColors,
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 28,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: 'rgba(51, 75, 107, 0.4)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: "'Inter', sans-serif", size: 12 },
                            precision: 0,
                        },
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: '#cbd5e1',
                            font: { family: "'Inter', sans-serif", size: 12.5, weight: '600' },
                        },
                    },
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#18273f',
                        titleColor: '#38bdf8',
                        bodyColor: '#ffffff',
                        titleFont: { family: "'Inter', sans-serif", weight: '700', size: 13 },
                        bodyFont: { family: "'Inter', sans-serif", size: 13 },
                        borderColor: '#334b6b',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            label(context) {
                                const val = context.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${val.toLocaleString()} komentar (${pct}%)`;
                            }
                        }
                    },
                },
            },
        });
    },

    renderRiskChart(canvasId, distribution) {
        return this.riskBar(canvasId, distribution);
    },

    datasetBar(canvasId, distribution = {}) {
        this.destroy(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (typeof Chart === 'undefined') return;

        const entries = Object.entries(distribution || {}).filter(([_, count]) => count > 0);
        if (entries.length === 0) {
            this._renderEmptyState(canvas, 'Dataset belum memiliki label.');
            return;
        }
        this._clearEmptyState(canvas);

        const labels = entries.map(([k]) => k);
        const data = entries.map(([_, v]) => v);
        const total = data.reduce((a, b) => a + b, 0);
        const bgColors = labels.map(l => this.colors[l] || '#0ea5e9');
        const displayLabels = labels.map(l => this.labelNames[l] || l);

        this.instances[canvasId] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: 'Sampel Komentar',
                    data,
                    backgroundColor: bgColors,
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 32,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#cbd5e1',
                            font: { family: "'Inter', sans-serif", size: 11.5, weight: '600' },
                            maxRotation: 45,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(51, 75, 107, 0.4)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: "'Inter', sans-serif", size: 12 },
                            precision: 0,
                        },
                    },
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#18273f',
                        titleColor: '#38bdf8',
                        bodyColor: '#ffffff',
                        titleFont: { family: "'Inter', sans-serif", weight: '700', size: 13 },
                        bodyFont: { family: "'Inter', sans-serif", size: 13 },
                        borderColor: '#334b6b',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            label(context) {
                                const val = context.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${val.toLocaleString()} sampel (${pct}%)`;
                            }
                        }
                    },
                },
            },
        });
    }
};
