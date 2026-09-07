// ==========================================================================
// Uchqunbek & Charosxon Wedding Invitation Scripts
// ==========================================================================

function openInvitation() {
    const curtain = document.getElementById('curtainOverlay');
    if (curtain) {
        curtain.classList.add('opened');
        document.body.classList.remove('curtain-active');
        
        setTimeout(() => {
            curtain.style.display = 'none';
        }, 1200);
    }
}

function saveToCalendar() {
    const title = encodeURIComponent("Uchqunbek & Charosxon Nikoh To‘yi");
    const details = encodeURIComponent("Uchqunbek va Charosxonlarning nikoh to‘y tantanasi. Manzil: Buxoro viloyati, Olot tumani, Xo‘jaqul Ota to‘yxonasi.");
    const location = encodeURIComponent("Xo‘jaqul Ota to‘yxonasi, Olot tumani, Buxoro viloyati");
    
    // Google Calendar Event Link (2026-10-09 18:00 - 23:00)
    const startDate = "20261009T180000";
    const endDate = "20261009T230000";
    const googleCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startDate}/${endDate}&details=${details}&location=${location}`;
    
    window.open(googleCalUrl, '_blank');
}
