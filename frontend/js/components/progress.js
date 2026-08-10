/**
 * CyberGuard-ID — Pipeline Progress Stepper Component (HCI Visual Feedback)
 */
const Progress = {
    steps: [
        { label: 'Validasi', icon: 'check-circle' },
        { label: 'Koleksi', icon: 'download-cloud' },
        { label: 'Preprocessing', icon: 'binary' },
        { label: 'Klasifikasi AI', icon: 'cpu' },
        { label: 'Pola Serangan', icon: 'network' },
        { label: 'Skor Risiko', icon: 'shield-alert' },
        { label: 'Verifikasi', icon: 'user-check' },
        { label: 'Laporan', icon: 'file-text' },
    ],

    render(containerId, currentStep = 0, error = false) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const totalSteps = this.steps.length;
        const boundedStep = Math.max(0, Math.min(currentStep, totalSteps));
        const progressPct = boundedStep === 0 ? 0 : Math.round((boundedStep / totalSteps) * 100);

        let html = `
            <div style="margin-bottom: var(--space-3);">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-secondary font-semibold" style="font-size: 0.85rem;">
                        ${error ? '⚠️ Proses Terhenti' : boundedStep >= totalSteps ? '✅ Selesai (100%)' : `Tahap ${boundedStep} dari ${totalSteps}`}
                    </span>
                    <span class="badge ${error ? 'badge-danger' : boundedStep >= totalSteps ? 'badge-success' : 'badge-info'}">
                        ${progressPct}%
                    </span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: ${progressPct}%; ${error ? 'background: var(--danger);' : ''}"></div>
                </div>
            </div>

            <div class="pipeline-stepper" style="overflow-x: auto; padding-bottom: 8px;">
        `;

        this.steps.forEach((step, i) => {
            const stepNum = i + 1;
            let stateClass = '';

            if (error && stepNum === boundedStep) {
                stateClass = 'error';
            } else if (stepNum < boundedStep || boundedStep >= totalSteps) {
                stateClass = 'completed';
            } else if (stepNum === boundedStep) {
                stateClass = 'active';
            }

            html += `
                <div class="pipeline-step ${stateClass}" style="flex: 1; min-width: 60px;">
                    <div class="step-node ${stateClass}">
                        <i data-lucide="${stateClass === 'completed' ? 'check' : step.icon}" style="width: 16px; height: 16px;"></i>
                    </div>
                    <span class="step-label" style="font-size: 0.72rem; margin-top: 4px;">${step.label}</span>
                </div>
            `;
        });

        html += '</div>';

        container.innerHTML = html;
        if (window.lucide) {
            lucide.createIcons();
        }
    },

    renderComplete(containerId) {
        this.render(containerId, this.steps.length);
    },
};

window.Progress = Progress;
