/**
 * CyberGuard-ID — Stitch Refined Executive Reporting Page (05_laporan)
 */
const ReportPage = {
    currentAnalysisId: null,

    async render(container) {
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
        this.currentAnalysisId = urlParams.get('id');

        container.innerHTML = `
            <div class="flex items-center justify-between mb-4" style="flex-wrap: wrap; gap: 16px;">
                <div class="page-header" style="margin-bottom: 0;">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="chip chip-c0 font-mono">AUDIT REPORT</span>
                        <span class="text-xs text-muted">Dokumen Moderasi Resmi</span>
                    </div>
                    <h1 style="font-size: 1.5rem; font-weight: 800; color: var(--text-primary);">Pusat Laporan & Audit Moderasi</h1>
                    <p id="report-meta-text" class="text-secondary text-sm">Memuat metadata laporan audit...</p>
                </div>
                <div class="flex gap-2" id="report-actions" style="flex-wrap: wrap;">
                    <style>
                        details.dropdown-export > summary::-webkit-details-marker { display: none; }
                        details.dropdown-export > summary { list-style: none; }
                        details.dropdown-export > div.dropdown-content {
                            position: absolute; right: 0; top: 100%; margin-top: 4px;
                            background: var(--bg-card); border: 1px solid var(--border-strong);
                            border-radius: var(--radius-md); padding: 8px; z-index: 100;
                            min-width: 180px; display: flex; flex-direction: column; gap: 6px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                        }
                        details.dropdown-export:not([open]) > div.dropdown-content {
                            display: none !important;
                        }
                    </style>
                    <details class="dropdown-export" style="position:relative; display:inline-block;">
                        <summary class="btn btn-primary btn-sm" style="cursor:pointer; display:flex; align-items:center; gap:4px;">
                            <span class="material-symbols-outlined text-xs" style="font-size:18px;">download</span>
                            <span>Ekspor</span>
                        </summary>
                        <div class="dropdown-content">
                            <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="ReportPage.printReport()" style="width:100%; justify-content:flex-start;">
                                <span class="material-symbols-outlined text-xs">print</span>
                                <span>Cetak / PDF</span>
                            </button>
                            <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="ReportPage.download('html')" style="width:100%; justify-content:flex-start;">
                                <span class="material-symbols-outlined text-xs">code</span>
                                <span>HTML</span>
                            </button>
                            <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="ReportPage.download('csv')" style="width:100%; justify-content:flex-start;">
                                <span class="material-symbols-outlined text-xs">table_chart</span>
                                <span>CSV</span>
                            </button>
                            <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="ReportPage.download('json')" style="width:100%; justify-content:flex-start;">
                                <span class="material-symbols-outlined text-xs">data_object</span>
                                <span>JSON</span>
                            </button>
                        </div>
                    </details>
                    <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="ReportPage.regenerate()">
                        <span class="material-symbols-outlined text-xs">refresh</span>
                        <span>Buat Ulang</span>
                    </button>
                </div>
            </div>

            <!-- Report Selector Toolbar -->
            <div class="card-soc mb-4" style="padding: 12px 18px;">
                <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 12px;">
                    <div class="flex items-center gap-3" style="flex: 1; min-width: 280px;">
                        <label class="form-label mb-0 whitespace-nowrap text-sm font-semibold flex items-center gap-1">
                            <span class="material-symbols-outlined text-primary" style="font-size: 18px;">description</span>
                            <span>Pilih Laporan Target:</span>
                        </label>
                        <select id="report-dropdown" class="form-select font-mono text-xs" style="max-width: 520px;" onchange="ReportPage.handleSelectAnalysis(this.value)">
                            <option value="">Memuat daftar laporan...</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="chip chip-sedang font-mono text-xs">ISO/IEC AUDIT</span>
                        <span class="chip chip-c0 font-mono text-xs">INDOBERT</span>
                    </div>
                </div>
            </div>

            <!-- Executive Summary Card (Stitch 05) -->
            <div class="card-soc mb-4 hidden" id="exec-summary-card">
                <div class="card-header-sep">
                    <div class="card-title">
                        <span class="material-symbols-outlined text-primary">auto_awesome</span>
                        <span>Ringkasan Eksekutif & Temuan AI</span>
                    </div>
                    <span class="chip chip-c0 font-mono" id="summary-provider-badge">AI SUMMARY</span>
                </div>
                <div class="card-body" style="padding: var(--space-4);">
                    <div id="exec-summary-narrative" style="line-height: 1.7; color: var(--text-primary); margin-bottom: 18px; padding: 14px 18px; background: var(--bg-card); border-radius: var(--radius-sm); border-left: 4px solid var(--accent); font-size: 0.92rem;">
                        <!-- Narrative text -->
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);" id="exec-summary-details">
                        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px;">
                            <h3 class="flex items-center gap-2 mb-2 text-sm font-bold" style="color: var(--text-primary);">
                                <span class="material-symbols-outlined text-primary" style="font-size: 18px;">search</span>
                                <span>Temuan Utama (Key Findings)</span>
                            </h3>
                            <ul id="exec-findings-list" style="padding-left: 18px; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6;"></ul>
                        </div>
                        <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px;">
                            <h3 class="flex items-center gap-2 mb-2 text-sm font-bold" style="color: var(--text-primary);">
                                <span class="material-symbols-outlined text-primary" style="font-size: 18px;">task_alt</span>
                                <span>Rekomendasi Tindak Lanjut</span>
                            </h3>
                            <ul id="exec-actions-list" style="padding-left: 18px; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6;"></ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Report Document Preview Frame -->
            <div class="card-soc">
                <div class="card-header-sep">
                    <div class="card-title">
                        <span class="material-symbols-outlined text-primary">article</span>
                        <span>Pratinjau Dokumen Laporan Resmi (Format A4)</span>
                    </div>
                    <button class="btn btn-ghost btn-sm flex items-center gap-1" onclick="ReportPage.openInNewTab()">
                        <span class="material-symbols-outlined text-xs">open_in_new</span>
                        <span>Buka Layar Penuh</span>
                    </button>
                </div>
                <div class="card-body" style="padding: 0;">
                    <div style="width: 100%; height: 750px; background: #010f1f; border-radius: 0 0 var(--radius-sm) var(--radius-sm); overflow: hidden;">
                        <iframe id="report-preview-frame" style="width: 100%; height: 100%; border: none;" src="about:blank" title="CyberGuard Audit Report Preview"></iframe>
                    </div>
                </div>
            </div>
        `;

        await this.init();
    },

    async init() {
        await this.loadDropdown();

        if (!this.currentAnalysisId) {
            const dropdown = document.getElementById('report-dropdown');
            if (dropdown && dropdown.options.length > 1) {
                this.currentAnalysisId = dropdown.options[1].value;
                dropdown.value = this.currentAnalysisId;
            }
        }

        if (this.currentAnalysisId) {
            await this.loadReport(this.currentAnalysisId);
        } else {
            const metaText = document.getElementById('report-meta-text');
            if (metaText) metaText.textContent = 'Belum ada riwayat analisis untuk dilaporkan. Silakan lakukan analisis baru.';
        }
    },

    async loadDropdown() {
        try {
            const analyses = await API.getAnalyses(50);
            const select = document.getElementById('report-dropdown');
            if (!select) return;

            select.innerHTML = '<option value="">-- Pilih Laporan Analisis --</option>';
            analyses.forEach(a => {
                const date = a.started_at ? new Date(a.started_at).toLocaleDateString('id-ID', { dateStyle: 'short' }) : '';
                const title = (a.video_title || a.name || a.id).substring(0, 50);
                const opt = document.createElement('option');
                opt.value = a.id;
                opt.textContent = `[${(a.source_type || 'ANALYSIS').toUpperCase()}] ${title} (${(a.total_comments || 0).toLocaleString()} komentar • ${date})`;
                if (a.id === this.currentAnalysisId) opt.selected = true;
                select.appendChild(opt);
            });
        } catch (e) {
            console.error('Failed to load dropdown', e);
        }
    },

    handleSelectAnalysis(id) {
        if (!id) return;
        location.hash = `#/report?id=${id}`;
        this.currentAnalysisId = id;
        this.loadReport(id);
    },

    async loadReport(id) {
        const frame = document.getElementById('report-preview-frame');
        const metaText = document.getElementById('report-meta-text');
        const summaryCard = document.getElementById('exec-summary-card');
        const narrativeEl = document.getElementById('exec-summary-narrative');
        const findingsList = document.getElementById('exec-findings-list');
        const actionsList = document.getElementById('exec-actions-list');
        const providerBadge = document.getElementById('summary-provider-badge');

        try {
            const rep = await API.getReportSummary(id);
            const genDate = rep.generated_at ? new Date(rep.generated_at).toLocaleString('id-ID') : '-';
            if (metaText) {
                metaText.textContent = `Dokumen Audit ID: CG-${id.substring(0, 10).toUpperCase()} • Dibuat: ${genDate} • Status: Terverifikasi`;
            }

            const sum = rep.summary || {};
            const execNarrative = sum.executive_summary || sum.summary_text || '';
            const keyFindings = sum.key_findings || [];
            const recommendedActions = sum.recommended_actions || [];

            if (execNarrative) {
                if (summaryCard) summaryCard.classList.remove('hidden');
                if (narrativeEl) narrativeEl.textContent = execNarrative;
                if (providerBadge) {
                    providerBadge.textContent = rep.provider === 'gemini' ? 'GEMINI AI' : 'INTERNAL AI';
                }

                if (findingsList) {
                    findingsList.innerHTML = keyFindings.length > 0
                        ? keyFindings.map(f => `<li style="margin-bottom: 6px;">${DataTable.escapeHtml(f)}</li>`).join('')
                        : '<li>Analisis pola komentar telah diproses sesuai ambang batas.</li>';
                }

                if (actionsList) {
                    actionsList.innerHTML = recommendedActions.length > 0
                        ? recommendedActions.map(a => `<li style="margin-bottom: 6px;">${DataTable.escapeHtml(a)}</li>`).join('')
                        : '<li>Lakukan peninjauan berkala pada komentar berisiko tinggi.</li>';
                }
            } else {
                if (summaryCard) summaryCard.classList.add('hidden');
            }

            if (frame) {
                const apiKey = API.getApiKey();
                const suffix = apiKey ? `&api_key=${apiKey}` : '';
                frame.src = `/api/reports/${id}/html/preview?t=${Date.now()}${suffix}`;
            }
        } catch (err) {
            if (metaText) metaText.textContent = `Gagal memuat laporan: ${err.message}`;
            if (frame) {
                frame.srcdoc = `<body style="background:#010f1f;color:#ff5449;font-family:sans-serif;padding:40px;text-align:center;"><h3>Gagal memuat pratinjau dokumen: ${err.message}</h3></body>`;
            }
        }
    },

    printReport() {
        const frame = document.getElementById('report-preview-frame');
        if (frame && frame.contentWindow) {
            try {
                frame.contentWindow.focus();
                frame.contentWindow.print();
                return;
            } catch (e) {
                // fallback
            }
        }
        if (this.currentAnalysisId) {
            const apiKey = API.getApiKey();
            const suffix = apiKey ? `?api_key=${apiKey}` : '';
            window.open(`/api/reports/${this.currentAnalysisId}/html/preview${suffix}`, '_blank');
        }
    },

    download(format) {
        if (!this.currentAnalysisId) {
            Toast.warning('Pilih Laporan', 'Silakan pilih analisis terlebih dahulu');
            return;
        }
        window.open(API.getReportDownloadUrl(this.currentAnalysisId, format), '_blank');
    },

    openInNewTab() {
        if (!this.currentAnalysisId) return;
        const apiKey = API.getApiKey();
        const suffix = apiKey ? `?api_key=${apiKey}` : '';
        window.open(`/api/reports/${this.currentAnalysisId}/html/preview${suffix}`, '_blank');
    },

    async regenerate() {
        if (!this.currentAnalysisId) return;
        try {
            Toast.info('Memproses', 'Sedang menggenerasi ulang dokumen audit...');
            await API.regenerateReport(this.currentAnalysisId);
            Toast.success('Laporan Selesai', 'Dokumen audit berhasil dibuat ulang.');
            await this.loadReport(this.currentAnalysisId);
        } catch (err) {
            Toast.error('Gagal Regenerasi', err.message);
        }
    }
};

window.ReportPage = ReportPage;
