/**
 * TAKLIVO Dark Luxury — Muslimbek & Oyshaxon
 * Black-Tie Cartier Editorial Controller
 */

// Ensure browser always starts from top on reload/refresh
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}
window.scrollTo(0, 0);

window.addEventListener('beforeunload', () => {
    window.scrollTo(0, 0);
});

let isPlaying = false;
const audio = document.getElementById('weddingAudio');
const vinylDisc = document.getElementById('vinylDisc');
const eqBars = document.getElementById('eqBars');
const vinylLabel = document.getElementById('vinylLabel');

function openInvitation() {
    document.body.classList.remove('curtain-active');
    window.scrollTo(0, 0);
    const curtain = document.getElementById('curtainOverlay');
    if (curtain) {
        curtain.classList.add('opened');
        setTimeout(() => {
            curtain.style.display = 'none';
        }, 1200);
    }

    startMusic();
    initStardust();
    initScrollReveal();
}

function startMusic() {
    if (!audio) return;
    audio.play().then(() => {
        isPlaying = true;
        updateMusicUI(true);
    }).catch(err => {
        console.log('Autoplay restriction encountered:', err);
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
    if (vinylDisc) {
        if (playing) vinylDisc.classList.add('spinning');
        else vinylDisc.classList.remove('spinning');
    }
    if (eqBars) {
        if (playing) eqBars.classList.add('active');
        else eqBars.classList.remove('active');
    }
    if (vinylLabel) {
        vinylLabel.innerText = playing ? 'PLAYING' : 'SOUNDTRACK';
    }
}

function initStardust() {
    const container = document.getElementById('stardustContainer');
    if (!container) return;

    const count = 16;
    for (let i = 0; i < count; i++) {
        const spark = document.createElement('div');
        spark.className = 'stardust-spark';

        const size = Math.random() * 3 + 1.5;
        spark.style.width = `${size}px`;
        spark.style.height = `${size}px`;
        spark.style.left = `${Math.random() * 100}vw`;

        const duration = Math.random() * 10 + 10;
        const delay = Math.random() * 6;
        spark.style.animationDuration = `${duration}s`;
        spark.style.animationDelay = `${delay}s`;

        container.appendChild(spark);
    }
}

function initScrollReveal() {
    const items = document.querySelectorAll('.reveal-block');
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
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;

    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            orderId: 7,
            defaultDate: '2026-09-20T19:00:00',
            secondLanguage: true,
            orderData: {
                order_id: 7,
                is_demo: false,
                is_paid: true,
                couple: {
                    groom_name: 'Muslimbek',
                    bride_name: 'Oyshaxon'
                },
                event: {
                    event_date: '20.09.2026',
                    event_time: '19:00',
                    venue: 'Uy',
                    address: "Namangan sh. Yangi yo'l ko'cha 4-uy"
                }
            }
        });
    }

    initScrollReveal();
});
