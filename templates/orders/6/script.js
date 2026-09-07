/**
 * PREMIUM UZBEK WEDDING DIGITAL INVITATION — AXADBEK & SABRINAXON
 * Master Design System: Photo 2 Master Artwork Background + Photo 3 Ornate Plaque Button
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. AUDIO MUSIC PLAYER LOGIC
  const audio = document.getElementById('weddingAudio');
  const musicBtn = document.getElementById('musicBtn');
  const playIcon = document.getElementById('musicIconPlay');
  const pauseIcon = document.getElementById('musicIconPause');
  let isPlaying = false;

  function playMusic() {
    if (!audio) return;
    audio.play().then(() => {
      isPlaying = true;
      if (playIcon) playIcon.style.display = 'none';
      if (pauseIcon) pauseIcon.style.display = 'block';
    }).catch(err => {
      console.log('Autoplay blocked:', err);
      isPlaying = false;
      if (playIcon) playIcon.style.display = 'block';
      if (pauseIcon) pauseIcon.style.display = 'none';
    });
  }

  window.toggleMusic = function() {
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
      }).catch(err => console.log('Audio error:', err));
    }
  };

  // 2. CTA SCREEN TRANSITION ("TAKLIFNOMANI OCHISH")
  const ctaBtn = document.getElementById('hero-cta-btn');
  const heroSectionEl = document.getElementById('hero-section');

  if (ctaBtn && heroSectionEl) {
    ctaBtn.addEventListener('click', (e) => {
      e.preventDefault();

      // Start music automatically when invitation is opened
      playMusic();
      if (musicBtn) {
        musicBtn.style.display = 'flex';
      }

      // Play closing exit animation on the Hero cover screen
      heroSectionEl.classList.add('hero-closing');

      // Smoothly switch to the unlocked full invitation site
      setTimeout(() => {
        document.body.classList.add('site-unlocked');
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 700);
    });
  }

  // 3. ADD TO CALENDAR (GOOGLE CALENDAR)
  const calendarBtn = document.getElementById('add-calendar-btn');
  if (calendarBtn) {
    calendarBtn.addEventListener('click', (e) => {
      e.preventDefault();
      
      const title = "Axadbek & Sabrinaxon Nikoh To‘yi";
      const description = "Axadbek va Sabrinaxonlarning nikoh to‘yi tantanasi va fayzli dasturxoni. «Osiyo» To‘yxonasi, Qashqadaryo viloyati, Qarshi, Beshkent.";
      const location = "«Osiyo» To‘yxonasi, Qashqadaryo viloyati, Qarshi, Beshkent";
      const startDate = "20261018T130000Z"; // 18:00 UTC+5 is 13:00 UTC
      const endDate = "20261018T180000Z";   // 23:00 UTC+5 is 18:00 UTC

      const googleCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${startDate}/${endDate}&details=${encodeURIComponent(description)}&location=${encodeURIComponent(location)}`;
      
      window.open(googleCalUrl, '_blank');
    });
  }
});
