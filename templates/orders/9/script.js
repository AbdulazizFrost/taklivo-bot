// ==========================================================================
// Oriental Wedding Invitation Scripts — Uchqunbek & Charosxon
// ==========================================================================

function openInvitation() {
    const introScreen = document.getElementById('introScreen');
    if (introScreen) {
        introScreen.classList.add('hide');
        setTimeout(() => {
            introScreen.style.display = 'none';
        }, 800);
    }
}

// Add to Calendar helper
function addToCalendar() {
    const title = encodeURIComponent("Uchqunbek & Charosxon Nikoh To‘yi");
    const details = encodeURIComponent("Uchqunbek va Charosxonlarning nikoh to‘y tantanasi. Manzil: Buxoro viloyati, Olot tumani, Xo‘jaqul Ota to‘yxonasi.");
    const location = encodeURIComponent("Xo‘jaqul Ota to‘yxonasi, Olot tumani, Buxoro viloyati");
    
    // Google Calendar Event Link (2026-10-09 18:00 - 23:00)
    const startDate = "20261009T180000";
    const endDate = "20261009T230000";
    const googleCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startDate}/${endDate}&details=${details}&location=${location}`;
    
    window.open(googleCalUrl, '_blank');
}

// Subtle golden particle animation
document.addEventListener('DOMContentLoaded', () => {
    const bg = document.getElementById('particlesBg');
    if (!bg) return;

    for (let i = 0; i < 24; i++) {
        const p = document.createElement('div');
        p.className = 'gold-dust-dot';
        p.style.left = Math.random() * 100 + '%';
        p.style.top = Math.random() * 100 + '%';
        p.style.animationDelay = (Math.random() * 5) + 's';
        p.style.animationDuration = (4 + Math.random() * 6) + 's';
        bg.appendChild(p);
    }
});
