// Musiqa holatini nazorat qilish uchun o\'zgaruvchilar
let isPlaying = false;

const audio = document.getElementById('weddingAudio');
const playIcon = document.getElementById('musicIconPlay');
const pauseIcon = document.getElementById('musicIconPause');
const musicBtn = document.getElementById('musicBtn');

// 1. TAKLIFNOMANI OCHISH
function revealInvitation() {
    const introOverlay = document.getElementById('introOverlay');
    const mainContent = document.getElementById('mainContent');

    if (introOverlay) {
        introOverlay.classList.add('intro-parted');
    }

    setTimeout(() => {
        if (mainContent) mainContent.classList.add('active');
        initScrollReveal();
        initParticles();

        if (musicBtn) {
            musicBtn.classList.add('visible');
        }
        startMusic();
    }, 500);

    setTimeout(() => {
        if (introOverlay) {
            introOverlay.style.display = 'none';
        }
    }, 1500);
}

// 2. MUSIQANI BOSHQARISH
function startMusic() {
    if (!audio) return;
    audio.play().then(() => {
        isPlaying = true;
        if (playIcon) playIcon.style.display = 'none';
        if (pauseIcon) pauseIcon.style.display = 'block';
    }).catch(error => {
        console.log('Brauzer avtomatik ijroga ruxsat bermadi:', error);
        isPlaying = false;
        if (playIcon) playIcon.style.display = 'block';
        if (pauseIcon) pauseIcon.style.display = 'none';
    });
}

function toggleMusic() {
    if (!audio) return;
    if (isPlaying) {
        audio.pause();
        if (playIcon) playIcon.style.display = 'block';
        if (pauseIcon) pauseIcon.style.display = 'none';
        isPlaying = false;
    } else {
        audio.play().then(() => {
            if (playIcon) playIcon.style.display = 'none';
            if (pauseIcon) pauseIcon.style.display = 'block';
            isPlaying = true;
        }).catch(err => {
            console.log('Musiqa ijro etishda xatolik:', err);
        });
    }
}

// 3. AMBIENT BACKGROUND PARTICLES (Zarralar generatsiyasi)
function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    container.innerHTML = '';
    const particleCount = 22;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');

        const size = Math.random() * 4 + 2;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = (Math.random() * 100) + 'vw';

        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        particle.style.animationDelay = (Math.random() * 5) + 's';

        container.appendChild(particle);
    }
}

// 4. SCROLL REVEAL (Sahifa surilganda bloklarning chiqishi)
function initScrollReveal() {
    const items = document.querySelectorAll('.reveal-item');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    items.forEach(item => observer.observe(item));
}
