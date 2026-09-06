// TAKLIVO Order #8 Script — Mirafzal & Sabina
let isAudioPlaying = false;

function revealInvitation() {
    const introOverlay = document.getElementById('introOverlay');
    const mainContent = document.getElementById('mainContent');
    const audio = document.getElementById('weddingAudio');
    const musicBtn = document.getElementById('musicBtn');

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

    // Play background soundtrack on user interaction
    if (audio) {
        audio.play().then(() => {
            isAudioPlaying = true;
            if (musicBtn) musicBtn.classList.add('playing');
        }).catch(() => {
            // Autoplay blocked until further click
            console.log('Audio autoplay prevented by browser');
        });
    }
}

function toggleMusic() {
    const audio = document.getElementById('weddingAudio');
    const musicBtn = document.getElementById('musicBtn');
    if (!audio) return;

    if (audio.paused) {
        audio.play().then(() => {
            isAudioPlaying = true;
            if (musicBtn) {
                musicBtn.classList.add('playing');
                musicBtn.innerText = '🎵';
            }
        }).catch(err => console.log('Audio play error:', err));
    } else {
        audio.pause();
        isAudioPlaying = false;
        if (musicBtn) {
            musicBtn.classList.remove('playing');
            musicBtn.innerText = '🔇';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            orderId: 8,
            secondLanguage: false,
            defaultDate: '20.10.2026 19:00'
        });
    }
});
