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

// 5. COUNTDOWN TIMER (18-Oktabr 2026, 18:00)
function initCountdown(targetDateStr) {
    const targetDate = new Date(targetDateStr).getTime();
    const daysEl = document.getElementById('days');
    const hoursEl = document.getElementById('hours');
    const minsEl = document.getElementById('minutes');
    const secsEl = document.getElementById('seconds');

    if (!daysEl || !hoursEl || !minsEl || !secsEl) return;

    function update() {
        const now = new Date().getTime();
        const diff = targetDate - now;

        if (diff <= 0) {
            daysEl.innerText = '00';
            hoursEl.innerText = '00';
            minsEl.innerText = '00';
            secsEl.innerText = '00';
            return;
        }

        const d = Math.floor(diff / (1000 * 60 * 60 * 24));
        const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);

        daysEl.innerText = d < 10 ? '0' + d : d;
        hoursEl.innerText = h < 10 ? '0' + h : h;
        minsEl.innerText = m < 10 ? '0' + m : m;
        secsEl.innerText = s < 10 ? '0' + s : s;
    }

    update();
    setInterval(update, 1000);
}

// 6. DOM READY
document.addEventListener('DOMContentLoaded', () => {
    initCountdown('2026-10-18T18:00:00+05:00');
});
