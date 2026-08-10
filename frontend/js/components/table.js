/**
 * CyberGuard-ID — Data Table & Badge Formatting Components (Stitch SOC Style)
 */
const DataTable = {
    /**
     * Render a badge for risk level
     */
    riskBadge(level) {
        const lvl = (level || 'low').toLowerCase();
        const names = { low: 'RENDAH', medium: 'SEDANG', high: 'TINGGI', critical: 'KRITIS' };
        const clsMap = {
            low: 'chip-rendah',
            medium: 'chip-sedang',
            high: 'chip-tinggi',
            critical: 'chip-kritis'
        };
        return `<span class="chip ${clsMap[lvl] || 'chip-rendah'} font-mono">${names[lvl] || lvl.toUpperCase()}</span>`;
    },

    /**
     * Render a badge for predicted label (C0–C7)
     */
    labelBadge(label) {
        const map = {
            normal: { code: 'C0', name: 'Normal', cls: 'chip-c0' },
            abusive: { code: 'C1', name: 'Bahasa Kasar', cls: 'chip-c1' },
            hate_speech_weak: { code: 'C2', name: 'Hate Speech Lemah', cls: 'chip-c2' },
            hate_speech_moderate: { code: 'C3', name: 'Hate Speech Sedang', cls: 'chip-c3' },
            hate_speech_strong: { code: 'C4', name: 'Hate Speech Kuat', cls: 'chip-c4' },
            uncertain: { code: 'C5', name: 'Tidak Pasti', cls: 'chip-c5' },
        };
        const info = map[label] || { code: 'C?', name: label, cls: 'chip-c5' };
        return `<span class="chip ${info.cls}" title="${info.name}"><strong style="margin-right:2px;">${info.code}</strong> ${info.name}</span>`;
    },

    /**
     * Render verification status badge
     */
    verificationBadge(status) {
        const map = {
            MODEL_VERIFIED: { class: 'status-pill verified', text: '● Model Verified' },
            RECOMMENDED_REVIEW: { class: 'status-pill pending', text: '● Disarankan Review' },
            MANDATORY_REVIEW: { class: 'status-pill pending', text: '● Wajib Review' },
            UNCERTAIN: { class: 'status-pill pending', text: '● Abstensi C5' },
            HUMAN_VERIFIED: { class: 'status-pill verified', text: '● Human Verified' },
        };
        const info = map[status] || { class: 'status-pill auto', text: status };
        return `<span class="${info.class}">${info.text}</span>`;
    },

    /**
     * Format confidence as percentage
     */
    confidenceText(confidence) {
        const pct = (confidence * 100).toFixed(1);
        let color = 'var(--success)';
        if (confidence < 0.55) color = 'var(--danger)';
        else if (confidence < 0.70) color = 'var(--warning)';
        return `<span class="font-mono" style="color: ${color}; font-weight: 700;">${pct}%</span>`;
    },

    /**
     * Truncate text with tooltip
     */
    truncateText(text, maxLen = 80) {
        if (!text) return '';
        if (text.length <= maxLen) return this.escapeHtml(text);
        return `<span title="${this.escapeHtml(text)}">${this.escapeHtml(text.substring(0, maxLen))}…</span>`;
    },

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    },

    /**
     * Render pagination controls (Dark cyber style)
     */
    renderPagination(page, totalPages, onPageChange) {
        if (totalPages <= 1) return '';

        let html = '<div class="flex items-center justify-center gap-1" style="margin-top: 16px;">';
        html += `<button class="btn btn-secondary btn-sm" ${page <= 1 ? 'disabled style="opacity:0.4;pointer-events:none;"' : ''} data-page="${page - 1}">‹ Prev</button>`;

        const range = 2;
        let start = Math.max(1, page - range);
        let end = Math.min(totalPages, page + range);

        if (start > 1) {
            html += `<button class="btn btn-secondary btn-sm" data-page="1">1</button>`;
            if (start > 2) html += `<span class="text-muted" style="padding: 0 4px;">…</span>`;
        }

        for (let i = start; i <= end; i++) {
            const isActive = i === page;
            html += `<button class="btn ${isActive ? 'btn-primary' : 'btn-secondary'} btn-sm font-mono" data-page="${i}">${i}</button>`;
        }

        if (end < totalPages) {
            if (end < totalPages - 1) html += `<span class="text-muted" style="padding: 0 4px;">…</span>`;
            html += `<button class="btn btn-secondary btn-sm" data-page="${totalPages}">${totalPages}</button>`;
        }

        html += `<button class="btn btn-secondary btn-sm" ${page >= totalPages ? 'disabled style="opacity:0.4;pointer-events:none;"' : ''} data-page="${page + 1}">Next ›</button>`;
        html += '</div>';

        return html;
    },

    attachPagination(containerId, callback) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.querySelectorAll('button[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                if (!isNaN(page) && !btn.disabled) callback(page);
            });
        });
    },
};

window.DataTable = DataTable;
