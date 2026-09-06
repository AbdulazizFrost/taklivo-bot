function revealInvitation() {
    const introOverlay = document.getElementById('introOverlay');
    const mainContent = document.getElementById('mainContent');
    if (introOverlay) {
        introOverlay.classList.add('intro-parted');
        setTimeout(() => { introOverlay.style.display = 'none'; }, 850);
    }
    if (mainContent) {
        mainContent.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({ defaultDate: '2026-10-24T18:30:00' });
    }
});

