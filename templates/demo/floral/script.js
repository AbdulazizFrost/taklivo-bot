/**
 * TAKLIVO Floral Romance — Luxury Botanical Stationery Controller
 */

let isPlaying = false;
const audio = document.getElementById('weddingAudio');
const musicWreath = document.getElementById('musicWreath');
const musicStatusText = document.getElementById('musicStatusText');

function openFloralInvitation() {
    const opening = document.getElementById('openingScreen');
    if (opening) {
        opening.classList.add('unfolded');
        setTimeout(() => {
            opening.style.display = 'none';
        }, 900);
    }

    startMusic();
    initPetals();
    initScrollReveal();
}

function startMusic() {
    if (!audio) return;
    audio.play().then(() => {
        isPlaying = true;
        updateMusicUI(true);
    }).catch(err => {
        console.log('Autoplay restriction:', err);
        isPlaying = false;
        updateMusicUI(false);
    });
}

function toggleMusic() {
    if (!audio) return;
    if (isPlaying) {
        audio.pause();
        isPlaying = false;
        updateMusicUI(false);
    } else {
        audio.play().then(() => {
            isPlaying = true;
            updateMusicUI(true);
        }).catch(err => {
            console.log('Play prevented:', err);
            isPlaying = false;
            updateMusicUI(false);
        });
    }
}

function updateMusicUI(playing) {
    if (musicWreath) {
        if (playing) musicWreath.classList.add('spinning');
        else musicWreath.classList.remove('spinning');
    }
    if (musicStatusText) {
        musicStatusText.innerText = playing ? 'PLAYING' : 'MELODY';
    }
}

function initPetals() {
    const container = document.getElementById('petalsContainer');
    if (!container) return;

    // Check prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const count = 10;
    for (let i = 0; i < count; i++) {
        const petal = document.createElement('div');
        petal.className = 'botanical-petal';

        const size = Math.random() * 9 + 8;
        petal.style.width = `${size}px`;
        petal.style.height = `${size * 1.3}px`;
        petal.style.left = `${Math.random() * 100}vw`;

        const duration = Math.random() * 8 + 8;
        const delay = Math.random() * 6;
        petal.style.animationDuration = `${duration}s`;
        petal.style.animationDelay = `${delay}s`;

        container.appendChild(petal);
    }
}

function initScrollReveal() {
    const items = document.querySelectorAll('.reveal-up');
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
    // Initialize Taklivo Universal Engine
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            defaultDate: '2026-09-18T18:30:00'
        });
    }

    initScrollReveal();
});
