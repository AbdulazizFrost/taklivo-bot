// TAKLIVO Modern Script
function revealInvitation() {
    const introOverlay = document.getElementById('introOverlay');
    const mainContent = document.getElementById('mainContent');

    if (introOverlay) {
        introOverlay.classList.add('intro-parted');
        setTimeout(() => {
            introOverlay.style.display = 'none';
        }, 850);
    }
    if (mainContent) {
        mainContent.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            orderId: 5,
            secondLanguage: false,
            defaultDate: '18.09.2026 19:00'
        });
    }
});

