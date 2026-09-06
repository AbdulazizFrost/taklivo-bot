/**
 * TAKLIVO Minimal Modern — Vogue Editorial Controller
 */

let isPlaying = false;
const audio = document.getElementById('weddingAudio');
const eqBars = document.getElementById('eqBars');
const audioLabel = document.getElementById('audioLabel');

function toggleMusic() {
    if (!audio) return;
    if (isPlaying) {
        audio.pause();
        isPlaying = false;
        updateAudioUI(false);
    } else {
        audio.play().then(() => {
            isPlaying = true;
            updateAudioUI(true);
        }).catch(err => {
            console.log('Autoplay policy restriction:', err);
            isPlaying = false;
            updateAudioUI(false);
        });
    }
}

function updateAudioUI(playing) {
    if (eqBars) {
        if (playing) eqBars.classList.add('active');
        else eqBars.classList.remove('active');
    }
    if (audioLabel) {
        audioLabel.innerText = playing ? 'PLAYING' : 'SOUNDTRACK 01';
    }
}

function initScrollReveal() {
    const items = document.querySelectorAll('.reveal-item');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.08 });

    items.forEach(el => observer.observe(el));
}

document.addEventListener('DOMContentLoaded', () => {
    // Immediately reveal hero section
    const hero = document.querySelector('.editorial-hero');
    if (hero) hero.classList.add('active');

    // Initialize Taklivo Universal Engine
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            defaultDate: '2026-11-12T18:00:00'
        });
    }

    initScrollReveal();
});

