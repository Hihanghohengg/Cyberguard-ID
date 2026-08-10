/**
 * CyberGuard-ID — Toast Notification System
 */
const Toast = {
    container: null,

    init() {
        this.container = document.getElementById('toast-container');
    },

    show(type, title, message = '', duration = 5000) {
        if (!this.container) this.init();

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info',
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon"><i data-lucide="${icons[type] || 'info'}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
            <button class="toast-close" onclick="this.closest('.toast').remove()">
                <i data-lucide="x" style="width:14px;height:14px"></i>
            </button>
            <div class="toast-progress" style="animation-duration:${duration}ms"></div>
        `;

        this.container.appendChild(toast);
        lucide.createIcons({ attrs: {}, nameAttr: 'data-lucide' });

        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    success(title, message = '') { this.show('success', title, message); },
    error(title, message = '') { this.show('error', title, message, 8000); },
    warning(title, message = '') { this.show('warning', title, message, 6000); },
    info(title, message = '') { this.show('info', title, message); },
};

window.Toast = Toast;
