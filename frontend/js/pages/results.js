/**
 * CyberGuard-ID — Clean, Senior-Friendly Results Page
 * Includes: Direct Download Buttons at Top, High-Contrast Metrics, Visual Charts, Comment List, & Human Review Modal
 */
const ResultsPage = {
    currentAnalysisId: null,
    currentCommentsPage: 1,
    currentComments: [],
    selectedCommentIndex: null,
    activeFilter: 'all', // 'all' | 'harmful' | 'review' | 'safe'
    searchTimeout: null,

    async render(container) {
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
        this.currentAnalysisId = urlParams.get('id');

        container.innerHTML = `
            <!-- Top Action & Download Toolbar -->
            <div class="top-action-bar">
                <div style="flex: 1; min-width: 260px;">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="chip chip-c0">HASIL PEMERIKSAAN</span>
                        <span class="text-xs text-muted" id="res-meta-text">Memuat sesi...</span>
                    </div>
                    <h1 id="res-video-title" style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-bottom: 2px;">
                        Memuat Hasil Analisis...
                    </h1>
                </div>

                <!-- Direct Download & Action Buttons -->
                <div class="download-btn-group" style="display: flex; gap: 8px;">
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
                        <summary class="btn btn-secondary btn-sm" style="cursor:pointer;">
                            <span class="material-symbols-outlined" style="font-size: 18px;">download</span>
                            <span>Ekspor</span>
                        </summary>
                        <div class="dropdown-content">
                            <button type="button" class="btn btn-secondary btn-sm" style="width:100%; justify-content:flex-start;" onclick="ResultsPage.handleDownloadPDF()" title="Cetak atau Simpan sebagai PDF">
                                <span class="material-symbols-outlined" style="font-size: 18px;">print</span> PDF
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" style="width:100%; justify-content:flex-start;" onclick="ResultsPage.handleDownloadHTML()" title="Unduh Berkas Laporan Web">
                                <span class="material-symbols-outlined" style="font-size: 18px;">html</span> HTML
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" style="width:100%; justify-content:flex-start;" onclick="ResultsPage.handleDownloadCSV()" title="Unduh Data Mentah CSV">
                                <span class="material-symbols-outlined" style="font-size: 18px;">table_view</span> CSV
                            </button>
                        </div>
                    </details>
                    <a href="#/" class="btn btn-primary btn-sm">
                        <span class="material-symbols-outlined" style="font-size: 18px;">add</span>
                        <span>Periksa Video Baru</span>
                    </a>
                </div>
            </div>

            <!-- Analysis Selector Dropdown (if multiple runs exist) -->
            <div class="card-soc mb-4" style="padding: 10px 16px;">
                <div class="flex items-center justify-between" style="flex-wrap: wrap; gap: 10px;">
                    <div class="flex items-center gap-3" style="flex: 1; min-width: 260px;">
                        <label class="form-label mb-0 whitespace-nowrap flex items-center gap-1 font-semibold" style="font-size: 0.9rem;">
                            <span class="material-symbols-outlined text-primary" style="font-size: 20px;">history</span>
                            <span>Pilih Video yang Dianalisis:</span>
                        </label>
                        <select id="analysis-dropdown" class="form-select" style="max-width: 440px;" onchange="ResultsPage.handleSelectAnalysis(this.value)">
                            <option value="">Memuat daftar video...</option>
                        </select>
                        <button type="button" class="btn btn-danger btn-sm" onclick="ResultsPage.handleDeleteCurrent()" title="Hapus Riwayat Video Ini" style="padding: 6px 9px; min-width: unset; display: inline-flex; align-items: center; justify-content: center; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171;" onmouseover="this.style.background='rgba(239, 68, 68, 0.3)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.15)'">
                            <span class="material-symbols-outlined" style="font-size: 18px;">delete</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- 4 Main KPI Cards (Large, high contrast, clean) -->
            <div class="stat-grid" id="res-metrics-container">
                <div class="stat-card info">
                    <div class="stat-card-header">
                        <span class="stat-label">Total Komentar</span>
                        <div class="stat-icon info"><span class="material-symbols-outlined">forum</span></div>
                    </div>
                    <div class="stat-value" id="val-total-comments">-</div>
                    <div class="text-xs text-muted">Komentar berhasil diperiksa</div>
                </div>

                <div class="stat-card safe">
                    <div class="stat-card-header">
                        <span class="stat-label">Komentar Aman</span>
                        <div class="stat-icon safe"><span class="material-symbols-outlined">check_circle</span></div>
                    </div>
                    <div class="stat-value" id="val-safe-comments" style="color: var(--safe-text);">-</div>
                    <div class="text-xs text-muted">Normal & apresiatif</div>
                </div>

                <div class="stat-card warning">
                    <div class="stat-card-header">
                        <span class="stat-label">Perlu Ditinjau</span>
                        <div class="stat-icon warning"><span class="material-symbols-outlined">help</span></div>
                    </div>
                    <div class="stat-value" id="val-review-comments" style="color: var(--warning-text);">-</div>
                    <div class="text-xs text-muted">Kritik atau ambigu</div>
                </div>

                <div class="stat-card danger">
                    <div class="stat-card-header">
                        <span class="stat-label">Komentar Berbahaya</span>
                        <div class="stat-icon danger"><span class="material-symbols-outlined">gpp_maybe</span></div>
                    </div>
                    <div class="stat-value" id="val-danger-comments" style="color: var(--danger-text);">-</div>
                    <div class="text-xs text-muted">Ujaran kebencian & kata kasar</div>
                </div>
            </div>

            <!-- 2 Clean Charts Grid -->
            <div class="grid-soc mb-4" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: var(--space-4);">
                <!-- Chart 1: Categories -->
                <div class="card-soc">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">pie_chart</span>
                            <span>Kategori Komentar</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div style="position: relative; height: 260px;">
                            <canvas id="chart-categories"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 2: Risks -->
                <div class="card-soc">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">bar_chart</span>
                            <span>Tingkat Risiko Komentar</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div style="position: relative; height: 260px;">
                            <canvas id="chart-risks"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bot Clusters Card (Shown only if bot attack patterns found) -->
            <div class="card-soc mb-4 hidden" id="clusters-container">
                <div class="card-header-sep">
                    <div class="card-title">
                        <span class="material-symbols-outlined" style="color: var(--warning);">crisis_alert</span>
                        <span>Dugaan Serangan Bot / Komentar Berulang</span>
                    </div>
                    <span class="chip chip-sedang" id="cluster-badge">0 Pola Ditemukan</span>
                </div>
                <div class="card-body" style="padding: 0;">
                    <div class="table-container" style="border: none;">
                        <table class="cyber-table" id="cluster-table">
                            <thead>
                                <tr>
                                    <th>Kategori Dominan</th>
                                    <th>Jumlah Komentar</th>
                                    <th>Akun Unik</th>
                                    <th>Tingkat Indikasi</th>
                                </tr>
                            </thead>
                            <tbody id="cluster-tbody"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Comments List Table Section -->
            <div class="card-soc mb-5">
                <div class="card-header-sep">
                    <div class="card-title">
                        <span class="material-symbols-outlined text-primary">format_list_bulleted</span>
                        <span>Daftar Seluruh Komentar</span>
                    </div>
                </div>

                <div class="card-body" style="padding: var(--space-4);">
                    <!-- Filter Controls -->
                    <div class="flex items-center justify-between mb-4" style="flex-wrap: wrap; gap: 12px;">
                        <!-- Filter Tabs -->
                        <div class="flex gap-1" style="flex-wrap: wrap;">
                            <button type="button" class="btn btn-sm btn-secondary active" id="btn-filter-all" onclick="ResultsPage.setFilter('all')">
                                Semua Komentar
                            </button>
                            <button type="button" class="btn btn-sm btn-secondary" id="btn-filter-harmful" onclick="ResultsPage.setFilter('harmful')">
                                🔴 Berbahaya
                            </button>
                            <button type="button" class="btn btn-sm btn-secondary" id="btn-filter-review" onclick="ResultsPage.setFilter('review')">
                                🟡 Perlu Ditinjau
                            </button>
                            <button type="button" class="btn btn-sm btn-secondary" id="btn-filter-safe" onclick="ResultsPage.setFilter('safe')">
                                🟢 Aman
                            </button>
                        </div>

                        <!-- Search Box -->
                        <div style="min-width: 240px;">
                            <input 
                                type="text" 
                                id="comment-search-box" 
                                class="form-input" 
                                placeholder="Cari teks komentar..." 
                                oninput="ResultsPage.handleSearch(this.value)"
                            />
                        </div>
                    </div>

                    <!-- Table -->
                    <div class="table-container">
                        <table class="cyber-table">
                            <thead>
                                <tr>
                                    <th style="width: 50px;">No</th>
                                    <th>Isi Komentar</th>
                                    <th style="width: 160px;">Kategori</th>
                                    <th style="width: 140px;">Tingkat Risiko</th>
                                    <th style="width: 110px; text-align: center;">Aksi</th>
                                </tr>
                            </thead>
                            <tbody id="comments-tbody">
                                <tr>
                                    <td colspan="5" style="text-align: center; padding: 40px;">
                                        <div class="spinner" style="margin: 0 auto 12px;"></div>
                                        <p>Memuat komentar...</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Pagination -->
                    <div class="flex items-center justify-between mt-4" style="flex-wrap: wrap; gap: 12px; padding-top: 12px;">
                        <span class="text-sm text-secondary" id="pagination-info">Menampilkan halaman 1</span>
                        <div class="flex gap-2">
                            <button type="button" class="btn btn-secondary btn-sm" id="btn-page-prev" onclick="ResultsPage.changePage(-1)" disabled>
                                &larr; Sebelumnya
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" id="btn-page-next" onclick="ResultsPage.changePage(1)">
                                Berikutnya &rarr;
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Human Review Modal Dialog -->
            <div class="modal-overlay hidden" id="review-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <div class="flex items-center gap-2">
                            <span class="material-symbols-outlined text-primary">rate_review</span>
                            <h3>Tinjau & Koreksi Komentar</h3>
                        </div>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="ResultsPage.closeReviewModal()">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <!-- Comment Text Box -->
                        <div style="margin-bottom: 20px;">
                            <label class="form-label">Teks Komentar:</label>
                            <div id="modal-comment-text" style="background: var(--bg-input); padding: 16px; border-radius: var(--radius-md); border: 1.5px solid var(--border-strong); color: #ffffff; font-size: 1.05rem; line-height: 1.6;">
                                -
                            </div>
                        </div>

                        <!-- Current Detection Info -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; background: var(--bg-card); padding: 14px; border-radius: var(--radius-md);">
                            <div>
                                <span class="text-xs text-muted">Kategori Terdeteksi AI:</span>
                                <div id="modal-detected-cat" style="font-weight: 700; color: #ffffff; margin-top: 2px;">-</div>
                            </div>
                            <div>
                                <span class="text-xs text-muted">Tingkat Risiko:</span>
                                <div id="modal-detected-risk" style="font-weight: 700; color: #ffffff; margin-top: 2px;">-</div>
                            </div>
                        </div>

                        <!-- Correction Selector -->
                        <div style="margin-bottom: 20px;">
                            <label class="form-label">Ubah Kategori (Jika Prediksi AI Kurang Sesuai):</label>
                            <select id="modal-new-cat" class="form-select" style="font-size: 1rem; padding: 12px;">
                                <option value="normal">Normal / Konstruktif (Aman)</option>
                                <option value="abusive">Abusive (Kasar / Slang)</option>
                                <option value="hate_speech_weak">Hate Speech Lemah</option>
                                <option value="hate_speech_moderate">Hate Speech Sedang</option>
                                <option value="hate_speech_strong">Hate Speech Kuat</option>
                                <option value="uncertain">Tidak Pasti / Perlu Tinjauan Lanjut</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="ResultsPage.closeReviewModal()">Batal</button>
                        <button type="button" class="btn btn-primary" onclick="ResultsPage.saveCorrection()">Simpan Perubahan</button>
                    </div>
                </div>
            </div>
        `;

        await this.loadInitialData();
    },

    async loadInitialData() {
        try {
            const analyses = await API.getAnalyses(30).catch(() => []);
            this.populateAnalysisDropdown(analyses);

            if (!this.currentAnalysisId && analyses.length > 0) {
                this.currentAnalysisId = analyses[0].id;
            }

            if (this.currentAnalysisId) {
                const dropdown = document.getElementById('analysis-dropdown');
                if (dropdown) dropdown.value = this.currentAnalysisId;
                await this.loadAnalysisDetail(this.currentAnalysisId);
            } else {
                document.getElementById('res-video-title').textContent = 'Belum Ada Hasil Pemeriksaan';
                document.getElementById('comments-tbody').innerHTML = `
                    <tr><td colspan="5" style="text-align: center; padding: 30px;">Silakan lakukan pemeriksaan video terlebih dahulu di halaman Beranda.</td></tr>
                `;
            }
        } catch (err) {
            Toast.error('Gagal Memuat Data', err.message);
        }
    },

    populateAnalysisDropdown(analyses) {
        const dropdown = document.getElementById('analysis-dropdown');
        if (!dropdown) return;

        if (!analyses || analyses.length === 0) {
            dropdown.innerHTML = '<option value="">(Tidak ada riwayat)</option>';
            return;
        }

        dropdown.innerHTML = analyses.map(item => {
            const title = item.video_title || `Video (${item.video_id || item.id})`;
            const count = item.total_comments || 0;
            const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: '2-digit', year: '2-digit' }) : '';
            return `<option value="${item.id}">[${dateStr}] ${title} (${count} komentar)</option>`;
        }).join('');
    },

    async handleSelectAnalysis(analysisId) {
        if (!analysisId) return;
        this.currentAnalysisId = analysisId;
        window.location.hash = `#/results?id=${analysisId}`;
        await this.loadAnalysisDetail(analysisId);
    },

    async loadAnalysisDetail(analysisId) {
        try {
            const detail = await API.getAnalysis(analysisId);
            this.renderHeaderAndKPIs(detail);
            this.renderCharts(detail);
            this.renderClusters(detail.clusters || []);
            this.currentCommentsPage = 1;
            await this.loadComments();
        } catch (err) {
            Toast.error('Gagal Memuat Detail', err.message);
        }
    },

    renderHeaderAndKPIs(detail) {
        const titleEl = document.getElementById('res-video-title');
        const metaEl = document.getElementById('res-meta-text');
        if (titleEl) titleEl.textContent = detail.video_title || (detail.source_type === 'csv' ? `Dataset CSV (${detail.video_id || 'Berkas'})` : `Video: ${detail.video_id}`);
        
        const dateStr = detail.created_at ? new Date(detail.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-';
        if (metaEl) metaEl.textContent = `ID: ${detail.id} • Tanggal: ${dateStr}`;

        const total = detail.total_comments || 0;
        const riskStats = detail.risk_distribution || {};
        
        // Match with Chart Risk Logic
        const lowRiskCount = (riskStats.rendah || riskStats.low || 0);
        const mediumRiskCount = (riskStats.sedang || riskStats.medium || 0);
        const highRiskCount = (riskStats.tinggi || riskStats.high || 0);
        const criticalRiskCount = (riskStats.kritis || riskStats.critical || 0);

        const danger = highRiskCount + criticalRiskCount;
        const review = mediumRiskCount + (detail.uncertain_count || 0);
        const safe = Math.max(0, total - danger - review); // Fallback safe counting

        document.getElementById('val-total-comments').textContent = `${total}`;
        document.getElementById('val-safe-comments').textContent = `${safe}`;
        document.getElementById('val-review-comments').textContent = `${review}`;
        document.getElementById('val-danger-comments').textContent = `${danger}`;
    },

    renderCharts(detail) {
        const stats = detail.category_distribution || {};
        const riskStats = detail.risk_distribution || {};

        // Donut Chart for Categories
        Charts.categoryDonut('chart-categories', {
            'Normal': stats.normal || stats.C0 || 0,
            'Abusive': stats.abusive || stats.C1 || 0,
            'HS Lemah': stats.hate_speech_weak || stats.C2 || 0,
            'HS Sedang': stats.hate_speech_moderate || stats.C3 || 0,
            'HS Kuat': stats.hate_speech_strong || stats.C4 || 0,
        });

        // Bar Chart for Risks
        Charts.riskBar('chart-risks', {
            'rendah': riskStats.rendah || riskStats.low || 0,
            'sedang': riskStats.sedang || riskStats.medium || 0,
            'tinggi': riskStats.tinggi || riskStats.high || 0,
            'kritis': riskStats.kritis || riskStats.critical || 0,
        });
    },

    renderClusters(clusters) {
        const container = document.getElementById('clusters-container');
        const tbody = document.getElementById('cluster-tbody');
        const badge = document.getElementById('cluster-badge');

        if (!container || !tbody) return;

        if (!clusters || clusters.length === 0) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');
        if (badge) badge.textContent = `${clusters.length} Pola Ditemukan`;

        tbody.innerHTML = clusters.map(c => {
            return `
                <tr>
                    <td style="font-weight: 700; color: #ffffff;">${c.dominant_label || 'Bermasalah'}</td>
                    <td>${c.comment_count || 0} Komentar</td>
                    <td>${c.unique_authors || 0} Akun</td>
                    <td><span class="chip chip-kritis">${c.indication_level || 'Tinggi'}</span></td>
                </tr>
            `;
        }).join('');
    },

    async loadComments() {
        const tbody = document.getElementById('comments-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr><td colspan="5" style="text-align: center; padding: 30px;"><div class="spinner" style="margin: 0 auto 8px;"></div><p>Memuat komentar...</p></td></tr>
        `;

        try {
            const searchQuery = document.getElementById('comment-search-box')?.value.trim() || '';
            const resp = await API.getComments(this.currentAnalysisId, {
                page: this.currentCommentsPage,
                per_page: 25,
                priority: this.activeFilter === 'all' ? undefined : this.activeFilter,
                search: searchQuery || undefined,
            });

            this.currentComments = resp.items || [];
            this.renderCommentsTable(this.currentComments, resp.total, resp.pages);
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--danger-text); padding: 20px;">Gagal memuat daftar komentar.</td></tr>`;
        }
    },

    renderCommentsTable(comments, total, totalPages) {
        const tbody = document.getElementById('comments-tbody');
        const infoEl = document.getElementById('pagination-info');
        const btnPrev = document.getElementById('btn-page-prev');
        const btnNext = document.getElementById('btn-page-next');

        if (!tbody) return;

        if (infoEl) infoEl.textContent = `Menampilkan ${comments.length} dari ${total || 0} komentar (Halaman ${this.currentCommentsPage} dari ${totalPages || 1})`;
        if (btnPrev) btnPrev.disabled = this.currentCommentsPage <= 1;
        if (btnNext) btnNext.disabled = this.currentCommentsPage >= (totalPages || 1);

        if (!comments || comments.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="5" style="text-align: center; padding: 30px; color: var(--text-muted);">Tidak ada komentar yang sesuai dengan filter.</td></tr>
            `;
            return;
        }

        const categoryNames = {
            'normal': { label: 'Normal', chip: 'chip-aman' },
            'abusive': { label: 'Bahasa Kasar', chip: 'chip-sedang' },
            'hate_speech_weak': { label: 'Hate Speech Lemah', chip: 'chip-sedang' },
            'hate_speech_moderate': { label: 'Hate Speech Sedang', chip: 'chip-kritis' },
            'hate_speech_strong': { label: 'Hate Speech Kuat', chip: 'chip-kritis' },
            // Fallbacks for code responses
            'C0': { label: 'Normal', chip: 'chip-aman' },
            'C1': { label: 'Bahasa Kasar', chip: 'chip-sedang' },
            'C2': { label: 'Hate Speech Lemah', chip: 'chip-sedang' },
            'C3': { label: 'Hate Speech Sedang', chip: 'chip-kritis' },
            'C4': { label: 'Hate Speech Kuat', chip: 'chip-kritis' },
        };

        const riskBadges = {
            'rendah': '<span class="chip chip-aman">Aman</span>',
            'sedang': '<span class="chip chip-sedang">Perhatian</span>',
            'tinggi': '<span class="chip chip-kritis">Berbahaya</span>',
            'kritis': '<span class="chip chip-kritis">Sangat Berbahaya</span>',
        };

        const startIndex = (this.currentCommentsPage - 1) * 25;
        tbody.innerHTML = comments.map((item, idx) => {
            const catKey = item.final_label || item.predicted_label || 'C0';
            const catInfo = categoryNames[catKey] || { label: catKey, chip: 'chip-sedang' };
            const riskKey = (item.risk_level || 'rendah').toLowerCase();
            const riskBadge = riskBadges[riskKey] || `<span class="chip chip-aman">${item.risk_level || 'Aman'}</span>`;
            const text = item.text_original || item.text || '';
            
            const maxLength = 180;
            let displayHtml = '';
            if (text.length > maxLength) {
                const shortText = text.substring(0, maxLength) + '...';
                displayHtml = `
                    <div class="comment-text-container">
                        <span class="comment-text-content" data-full-text="${escapeHtml(text)}" data-short-text="${escapeHtml(shortText)}">${escapeHtml(shortText)}</span>
                        <a href="javascript:void(0)" onclick="ResultsPage.toggleText(this)" style="color: var(--primary); font-size: 0.85rem; display: block; margin-top: 4px; text-decoration: none; font-weight: 500;">Lihat lebih detail</a>
                    </div>
                `;
            } else {
                displayHtml = `<span>${escapeHtml(text)}</span>`;
            }

            return `
                <tr>
                    <td style="color: var(--text-muted); font-size: 0.85rem; vertical-align: top; padding-top: 14px;">${startIndex + idx + 1}</td>
                    <td style="color: #ffffff; line-height: 1.5; font-size: 0.95rem; vertical-align: top; padding-top: 14px;">
                        ${displayHtml}
                        ${item.is_reviewed ? `<span class="chip chip-aman" style="font-size: 0.7rem; margin-top: 8px; display: inline-block;">Ditinjau Manual</span>` : ''}
                    </td>
                    <td><span class="chip ${catInfo.chip}">${catInfo.label}</span></td>
                    <td>${riskBadge}</td>
                    <td style="text-align: center;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="ResultsPage.openReviewModal(${idx})">
                            <span class="material-symbols-outlined" style="font-size: 16px;">edit</span>
                            <span>Tinjau</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    },

    setFilter(filter) {
        this.activeFilter = filter;
        ['all', 'harmful', 'review', 'safe'].forEach(f => {
            const btn = document.getElementById(`btn-filter-${f}`);
            if (btn) {
                if (f === filter) btn.classList.add('active', 'btn-primary');
                else btn.classList.remove('active', 'btn-primary');
            }
        });
        this.currentCommentsPage = 1;
        this.loadComments();
    },

    handleSearch(val) {
        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.currentCommentsPage = 1;
            this.loadComments();
        }, 400);
    },

    changePage(delta) {
        this.currentCommentsPage += delta;
        this.loadComments();
    },

    toggleText(btn) {
        const container = btn.closest('.comment-text-container');
        const contentSpan = container.querySelector('.comment-text-content');
        const isExpanded = btn.innerText === 'Lebih ringkas';
        
        if (isExpanded) {
            contentSpan.innerHTML = contentSpan.getAttribute('data-short-text');
            btn.innerText = 'Lihat lebih detail';
        } else {
            contentSpan.innerHTML = contentSpan.getAttribute('data-full-text');
            btn.innerText = 'Lebih ringkas';
        }
    },

    openReviewModal(index) {
        const item = this.currentComments[index];
        if (!item) return;

        this.selectedCommentIndex = index;
        const modal = document.getElementById('review-modal');
        const textEl = document.getElementById('modal-comment-text');
        const detCatEl = document.getElementById('modal-detected-cat');
        const detRiskEl = document.getElementById('modal-detected-risk');
        const selectNewCat = document.getElementById('modal-new-cat');

        if (textEl) textEl.textContent = item.text_original || item.text || '';
        if (detCatEl) detCatEl.textContent = item.predicted_label || item.label || 'C0';
        if (detRiskEl) detRiskEl.textContent = item.risk_level || 'Rendah';
        if (selectNewCat) selectNewCat.value = item.final_label || item.predicted_label || 'C0';

        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('active');
        }
    },

    closeReviewModal() {
        const modal = document.getElementById('review-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.classList.add('hidden');
        }
        this.selectedCommentIndex = null;
    },

    async saveCorrection() {
        if (this.selectedCommentIndex === null) return;
        const item = this.currentComments[this.selectedCommentIndex];
        const selectNewCat = document.getElementById('modal-new-cat');
        const newCat = selectNewCat?.value;

        if (!item || !newCat) return;

        try {
            await API.submitReview(this.currentAnalysisId, {
                comment_id: item.comment_id || item.id,
                corrected_label: newCat,
                notes: 'Koreksi pengawas manusia',
            });

            item.final_label = newCat;
            item.is_reviewed = true;
            Toast.success('Tinjauan Tersimpan', 'Koreksi kategori berhasil disimpan ke database.');
            this.closeReviewModal();
            this.loadComments();
        } catch (err) {
            Toast.error('Gagal Menyimpan', err.message);
        }
    },

    handleDownloadPDF() {
        if (!this.currentAnalysisId) return;
        const apiKey = API.getApiKey();
        const suffix = apiKey ? `?api_key=${apiKey}` : '';
        window.open(`/api/reports/${this.currentAnalysisId}/html/preview${suffix}`, '_blank');
    },

    handleDownloadHTML() {
        if (!this.currentAnalysisId) return;
        const apiKey = API.getApiKey();
        const suffix = apiKey ? `?api_key=${apiKey}` : '';
        window.location.href = `/api/reports/${this.currentAnalysisId}/html${suffix}`;
    },

    handleDownloadCSV() {
        if (!this.currentAnalysisId) return;
        const apiKey = API.getApiKey();
        const suffix = apiKey ? `?api_key=${apiKey}` : '';
        window.location.href = `/api/reports/${this.currentAnalysisId}/csv${suffix}`;
    },

    async handleDeleteCurrent() {
        if (!this.currentAnalysisId) return;
        const select = document.getElementById('analysis-dropdown');
        const title = select?.options[select.selectedIndex]?.text || this.currentAnalysisId;
        App.confirmDeleteAnalysis(this.currentAnalysisId, title, () => {
            window.location.hash = '#/';
        });
    }
};
