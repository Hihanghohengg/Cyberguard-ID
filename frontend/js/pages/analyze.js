/**
 * CyberGuard-ID — Stitch Refined Analyze Workflow Page (04_proses_analisis)
 * Features dual-source intake, SOC terminal log stream, and pipeline telemetry.
 */
const AnalyzePage = {
    currentSse: null,

    async render(container) {
        // Check if tab query param is passed
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
        const initialTab = urlParams.get('tab') === 'csv' ? 'csv' : 'yt';

        // Check if quick URL was passed from dashboard hero
        const quickUrl = sessionStorage.getItem('cyberguard_quick_url') || '';
        if (quickUrl) {
            sessionStorage.removeItem('cyberguard_quick_url');
        }

        container.innerHTML = `
            <div class="page-header mb-4">
                <div class="flex items-center gap-2 mb-1">
                    <span class="chip chip-sedang">WORKFLOW PIPELINE</span>
                    <span class="text-xs text-muted font-mono">IndoBERT (indobenchmark/indobert-base-p1)</span>
                </div>
                <h1 style="font-size: 1.6rem; font-weight: 800; color: var(--text-primary);">Mulai Analisis & Skrining Komentar</h1>
                <p class="text-secondary text-sm">Pilih sumber komentar YouTube atau unggah dataset CSV untuk klasifikasi, risk scoring, dan deteksi pola terkoordinasi.</p>
            </div>

            <!-- Tabs: YouTube vs CSV (Stitch Style) -->
            <div class="priority-queue-bar mb-4">
                <button class="priority-pill ${initialTab === 'yt' ? 'active' : ''}" id="tab-yt" onclick="AnalyzePage.switchTab('yt')">
                    <span class="material-symbols-outlined" style="font-size: 18px; color: #ff5449;">smart_display</span>
                    <span>YouTube Video Crawler</span>
                </button>
                <button class="priority-pill ${initialTab === 'csv' ? 'active' : ''}" id="tab-csv" onclick="AnalyzePage.switchTab('csv')">
                    <span class="material-symbols-outlined" style="font-size: 18px; color: #44e2cd;">table_chart</span>
                    <span>Unggah Dataset CSV</span>
                </button>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); align-items: start;">
                <!-- Left: Form Input Card -->
                <div class="card-soc" id="form-card">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">tune</span>
                            <span id="form-card-title">Parameter Pemindaian YouTube</span>
                        </div>
                    </div>
                    <div class="card-body" style="padding: var(--space-5);">
                        <!-- YouTube Form -->
                        <form id="yt-form" class="${initialTab === 'yt' ? '' : 'hidden'}" onsubmit="AnalyzePage.handleSubmitYt(event)">
                            <div class="form-group mb-4">
                                <label class="form-label" for="yt-url">
                                    Tautan URL Video YouTube <span style="color: var(--danger);">*</span>
                                </label>
                                <div style="position: relative;">
                                    <input 
                                        type="text" 
                                        id="yt-url" 
                                        class="form-input font-mono" 
                                        placeholder="Contoh: https://www.youtube.com/watch?v=..." 
                                        value="${DataTable.escapeHtml(quickUrl)}"
                                        required 
                                        style="padding-right: 80px;"
                                    />
                                    <button 
                                        type="button" 
                                        class="btn btn-ghost btn-sm" 
                                        style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); color: var(--accent);"
                                        onclick="AnalyzePage.pasteFromClipboard()"
                                        title="Tempel dari clipboard"
                                    >
                                        <span class="material-symbols-outlined text-xs">content_paste</span>
                                        <span>Tempel</span>
                                    </button>
                                </div>
                                <div class="text-xs text-muted" style="margin-top: 6px;">
                                    Mendukung format tautan: <code>watch?v=</code>, <code>youtu.be/</code>, dan <code>shorts/</code>
                                </div>
                            </div>

                            <!-- Collapsible Settings -->
                            <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: var(--space-4); overflow: hidden;">
                                <button 
                                    type="button" 
                                    class="flex items-center justify-between w-full" 
                                    onclick="AnalyzePage.toggleAdvancedSettings()"
                                    style="padding: 10px 14px; background: none; border: none; font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); cursor: pointer; text-align: left;"
                                >
                                    <span class="flex items-center gap-2">
                                        <span class="material-symbols-outlined text-primary" style="font-size: 16px;">tune</span>
                                        <span>Pengaturan Lanjutan (Batas Komentar & Balasan)</span>
                                    </span>
                                    <span class="material-symbols-outlined" id="adv-settings-icon" style="font-size: 18px; transition: transform 0.2s;">expand_more</span>
                                </button>
                                
                                <div id="adv-settings-content" class="hidden" style="padding: 12px 14px; border-top: 1px solid var(--border);">
                                    <div class="form-group mb-3">
                                        <label class="form-label" for="yt-name">Label Analisis (Opsional)</label>
                                        <input type="text" id="yt-name" class="form-input" placeholder="Contoh: Audit Video Debat Pilpres" />
                                    </div>

                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                        <div class="form-group" style="margin-bottom: 0;">
                                            <label class="form-label" for="yt-max">Maksimal Komentar</label>
                                            <input type="number" id="yt-max" class="form-input font-mono" value="500" min="10" max="5000" step="50" />
                                            <div class="text-xs text-muted" style="margin-top: 4px;">10 - 5.000 komentar</div>
                                        </div>
                                        <div class="form-group" style="margin-bottom: 0;">
                                            <label class="form-label">Sertakan Balasan (Replies)</label>
                                            <label class="flex items-center gap-2" style="margin-top: 8px; cursor: pointer;">
                                                <input type="checkbox" id="yt-replies" checked style="accent-color: var(--accent);" />
                                                <span class="text-xs text-secondary">Crawl thread balasan</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <button type="submit" class="btn btn-primary btn-lg w-full flex items-center justify-center gap-2" id="btn-submit-yt">
                                <span class="material-symbols-outlined">rocket_launch</span>
                                <span>Mulai Pemindaian YouTube</span>
                            </button>
                        </form>

                        <!-- CSV Form -->
                        <form id="csv-form" class="${initialTab === 'csv' ? '' : 'hidden'}" onsubmit="AnalyzePage.handleSubmitCsv(event)">
                            <div class="form-group mb-4">
                                <label class="form-label">
                                    Berkas Dataset Komentar (.csv) <span style="color: var(--danger);">*</span>
                                </label>
                                <div 
                                    id="csv-dropzone" 
                                    onclick="document.getElementById('csv-file').click()" 
                                    style="padding: 28px 16px; border: 2px dashed var(--border-strong); border-radius: var(--radius-sm); text-align: center; cursor: pointer; background: var(--bg-input); transition: all 0.2s;"
                                >
                                    <span class="material-symbols-outlined text-primary" style="font-size: 36px; margin-bottom: 6px;">cloud_upload</span>
                                    <p style="margin-bottom: 4px; font-weight: 600; color: var(--text-primary);" id="csv-file-name">Pilih berkas CSV atau seret ke sini</p>
                                    <div class="text-xs text-muted">Kolom didukung: <code>text</code>, <code>comment</code>, atau <code>komentar</code> (Maks. 50MB)</div>
                                </div>
                                <input type="file" id="csv-file" accept=".csv" class="hidden" onchange="AnalyzePage.handleFileSelected(event)" />
                            </div>

                            <div class="form-group mb-4">
                                <label class="form-label" for="csv-name">Label Analisis (Opsional)</label>
                                <input type="text" id="csv-name" class="form-input" placeholder="Contoh: Audit Dataset Internal Komentar" />
                            </div>

                            <button type="submit" class="btn btn-primary btn-lg w-full flex items-center justify-center gap-2" id="btn-submit-csv">
                                <span class="material-symbols-outlined">rocket_launch</span>
                                <span>Proses & Skrining CSV</span>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Right: Telemetry & Terminal Console -->
                <div class="card-soc" id="status-card">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">terminal</span>
                            <span>Pemantau Telemetri Pipeline</span>
                        </div>
                        <span class="chip chip-sedang" id="pipeline-status-badge">STANDBY</span>
                    </div>
                    <div class="card-body" style="padding: var(--space-4);">
                        <div id="pipeline-steps-container" class="mb-4">
                            <!-- Stepper rendered here -->
                        </div>

                        <!-- Stitch Mac Dots Terminal Panel -->
                        <div class="terminal-panel">
                            <div class="terminal-header">
                                <div class="mac-dots">
                                    <div class="mac-dot red"></div>
                                    <div class="mac-dot yellow"></div>
                                    <div class="mac-dot green"></div>
                                </div>
                                <span class="terminal-title font-mono">cyberguard-engine://telemetry</span>
                            </div>
                            <div class="terminal-body" id="progress-log-box">
                                <div class="terminal-log-row">
                                    <span class="log-time">[00:00:00]</span>
                                    <span class="log-level-info">[SYSTEM]</span>
                                    <span>Menunggu pemicu analisis dari pengguna...</span>
                                </div>
                            </div>
                        </div>

                        <div id="progress-action-area" class="mt-4 hidden" style="margin-top: 16px;">
                            <a href="#/results" id="btn-view-results" class="btn btn-primary btn-lg w-full flex items-center justify-center gap-2">
                                <span class="material-symbols-outlined">analytics</span>
                                <span>Buka Hasil & Antrean Moderasi</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;

        Progress.render('pipeline-steps-container', 0);
        this.setupDragDrop();
    },

    toggleAdvancedSettings() {
        const content = document.getElementById('adv-settings-content');
        const icon = document.getElementById('adv-settings-icon');
        if (!content) return;

        const isHidden = content.classList.toggle('hidden');
        if (icon) {
            icon.textContent = isHidden ? 'expand_more' : 'expand_less';
        }
    },

    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                const input = document.getElementById('yt-url');
                if (input) {
                    input.value = text.trim();
                    input.focus();
                    Toast.info('Tautan Ditempel', 'URL video YouTube telah dimasukkan.');
                }
            }
        } catch (e) {
            Toast.warning('Pemberitahuan', 'Silakan tempel URL secara manual menggunakan Ctrl+V.');
        }
    },

    switchTab(tab) {
        const tabYt = document.getElementById('tab-yt');
        const tabCsv = document.getElementById('tab-csv');
        const formYt = document.getElementById('yt-form');
        const formCsv = document.getElementById('csv-form');
        const titleEl = document.getElementById('form-card-title');

        if (tab === 'yt') {
            tabYt?.classList.add('active');
            tabCsv?.classList.remove('active');
            formYt?.classList.remove('hidden');
            formCsv?.classList.add('hidden');
            if (titleEl) titleEl.textContent = 'Parameter Pemindaian YouTube';
        } else {
            tabCsv?.classList.add('active');
            tabYt?.classList.remove('active');
            formCsv?.classList.remove('hidden');
            formYt?.classList.add('hidden');
            if (titleEl) titleEl.textContent = 'Unggah Berkas Dataset CSV';
        }
    },

    setupDragDrop() {
        const dropzone = document.getElementById('csv-dropzone');
        if (!dropzone) return;

        ['dragenter', 'dragover'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.style.borderColor = 'var(--accent)';
                dropzone.style.background = 'rgba(56, 189, 248, 0.08)';
            });
        });

        ['dragleave', 'drop'].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.style.borderColor = 'var(--border-strong)';
                dropzone.style.background = 'var(--bg-input)';
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer?.files;
            if (files && files.length > 0 && files[0].name.endsWith('.csv')) {
                const fileInput = document.getElementById('csv-file');
                if (fileInput) fileInput.files = files;
                const nameEl = document.getElementById('csv-file-name');
                if (nameEl) nameEl.textContent = files[0].name;
                Toast.info('Berkas Dipilih', files[0].name);
            }
        });
    },

    handleFileSelected(event) {
        const file = event.target.files?.[0];
        if (file) {
            const nameEl = document.getElementById('csv-file-name');
            if (nameEl) nameEl.textContent = file.name;
        }
    },

    async handleSubmitYt(event) {
        event.preventDefault();
        const urlInput = document.getElementById('yt-url');
        const url = urlInput ? urlInput.value.trim() : '';
        if (!url) {
            Toast.warning('URL Kosong', 'Silakan masukkan tautan video YouTube.');
            return;
        }

        const name = document.getElementById('yt-name')?.value.trim() || undefined;
        const maxComments = parseInt(document.getElementById('yt-max')?.value || '500');
        const includeReplies = document.getElementById('yt-replies')?.checked ?? true;

        const btn = document.getElementById('btn-submit-yt');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></div> Memulai...';
        }

        try {
            this.clearTerminal();
            this.log('INIT', 'Membuat sesi analisis baru...');
            const res = await API.createYoutubeAnalysis(url, maxComments, includeReplies, name);
            const analysisId = res.id;

            this.log('SUCCESS', `Sesi ID #${analysisId} berhasil dibuat.`);
            this.updateBadge('RUNNING', 'chip-c0');
            this.listenProgress(analysisId);
        } catch (err) {
            Toast.error('Gagal Memulai Analisis', err.message);
            this.log('ERROR', err.message);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span class="material-symbols-outlined">rocket_launch</span> Mulai Pemindaian YouTube';
            }
        }
    },

    async handleSubmitCsv(event) {
        event.preventDefault();
        const fileInput = document.getElementById('csv-file');
        const file = fileInput?.files?.[0];
        if (!file) {
            Toast.warning('Berkas Kosong', 'Silakan pilih berkas dataset CSV.');
            return;
        }

        const name = document.getElementById('csv-name')?.value.trim() || undefined;
        const btn = document.getElementById('btn-submit-csv');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></div> Mengunggah...';
        }

        try {
            this.clearTerminal();
            this.log('INIT', `Mengunggah berkas ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`);
            const res = await API.createCsvAnalysis(file, name);
            const analysisId = res.id;

            this.log('SUCCESS', `Sesi ID #${analysisId} berhasil dibuat.`);
            this.updateBadge('RUNNING', 'chip-c0');
            this.listenProgress(analysisId);
        } catch (err) {
            Toast.error('Gagal Memulai Analisis', err.message);
            this.log('ERROR', err.message);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span class="material-symbols-outlined">rocket_launch</span> Proses & Skrining CSV';
            }
        }
    },

    listenProgress(analysisId) {
        if (this.currentSse) {
            this.currentSse.close();
        }

        this.currentSse = API.streamSSE(`/api/analyze/${analysisId}/progress`, {
            onMessage: (data) => {
                const step = data.step || 0;
                const msg = data.message || '';
                Progress.render('pipeline-steps-container', step);
                this.log('PROGRESS', msg);
            },
            onDone: (data) => {
                Progress.render('pipeline-steps-container', 9);
                this.log('COMPLETED', 'Analisis Selesai');
                this.updateBadge('COMPLETED', 'chip-c0');
                this.showResultsAction(analysisId);
                Toast.success('Analisis Selesai!', 'Komentar telah berhasil diklasifikasi.');
                if (this.currentSse) this.currentSse.close();
            },
            onError: (err) => {
                let displayErr = err;
                if (typeof err === 'string') {
                    if (err.includes('not defined') || err.includes('KeyError')) {
                        displayErr = "Kesalahan internal backend. Jika Anda baru mengubah kode, pastikan server telah di-restart (Ctrl+C lalu 'python run.py').";
                    }
                }
                this.log('FAILED', displayErr);
                this.updateBadge('FAILED', 'chip-kritis');
                Toast.error('Analisis Gagal', displayErr);
                if (this.currentSse) this.currentSse.close();
            }
        });
    },

    clearTerminal() {
        const box = document.getElementById('progress-log-box');
        if (box) box.innerHTML = '';
    },

    log(level, msg) {
        const box = document.getElementById('progress-log-box');
        if (!box) return;

        const time = new Date().toTimeString().split(' ')[0];
        let lvlCls = 'log-level-info';
        if (level === 'ERROR' || level === 'FAILED') lvlCls = 'log-level-danger';
        else if (level === 'SUCCESS' || level === 'COMPLETED') lvlCls = 'log-level-success';
        else if (level === 'WARN') lvlCls = 'log-level-warn';

        const row = document.createElement('div');
        row.className = 'terminal-log-row';
        row.innerHTML = `
            <span class="log-time">[${time}]</span>
            <span class="${lvlCls}">[${level}]</span>
            <span>${DataTable.escapeHtml(msg)}</span>
        `;
        box.appendChild(row);
        box.scrollTop = box.scrollHeight;
    },

    updateBadge(text, cls) {
        const badge = document.getElementById('pipeline-status-badge');
        if (badge) {
            badge.className = `chip ${cls}`;
            badge.textContent = text;
        }
    },

    showResultsAction(analysisId) {
        const area = document.getElementById('progress-action-area');
        const btn = document.getElementById('btn-view-results');
        if (area && btn) {
            btn.href = `#/results?id=${analysisId}`;
            area.classList.remove('hidden');
        }
    }
};

window.AnalyzePage = AnalyzePage;
