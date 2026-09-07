/**
 * PREMIUM UZBEK WEDDING DIGITAL INVITATION — UCHQUNBEK & CHAROSXON
 * Core JavaScript Logic adapted from Order 4 Design System
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. HERO OPENING ANIMATION SEQUENCE
  const heroSection = document.getElementById('hero-section');
  
  // Trigger opening animation sequence
  setTimeout(() => {
    if (heroSection) {
      heroSection.classList.add('hero-loaded');
    }
  }, 100);

  // 2. CTA 2-PHASE SCREEN TRANSITION ("TAKLIFNOMANI OCHISH")
  const ctaBtn = document.getElementById('hero-cta-btn');
  const heroSectionEl = document.getElementById('hero-section');

  if (ctaBtn && heroSectionEl) {
    ctaBtn.addEventListener('click', (e) => {
      e.preventDefault();

      // 1. Play closing exit animation on the Hero cover screen
      document.body.classList.add('is-transitioning');
      heroSectionEl.classList.add('hero-closing');

      // 2. Smoothly switch to the unlocked full invitation site
      setTimeout(() => {
        document.body.classList.remove('is-transitioning');
        document.body.classList.add('site-unlocked');
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 750);
    });
  }

  // 4. ADD TO CALENDAR (ICS FILE GENERATION & GOOGLE CALENDAR)
  const calendarBtn = document.getElementById('add-calendar-btn');
  if (calendarBtn) {
    calendarBtn.addEventListener('click', (e) => {
      e.preventDefault();
      
      const title = "Uchqunbek & Charosxon Nikoh To‘yi";
      const description = "Uchqunbek va Charosxonlarning nikoh to‘yi tantanasi va dasturxoni. «Xo‘jaqul Ota» Tantanalar Saroyi, Olot tumani, Buxoro viloyati.";
      const location = "«Xo‘jaqul Ota» Tantanalar Saroyi, Olot tumani, Buxoro viloyati";
      const startDate = "20261009T130000Z"; // 18:00 UTC+5 is 13:00 UTC
      const endDate = "20261009T180000Z";   // 23:00 UTC+5 is 18:00 UTC

      // Google Calendar URL
      const googleCalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${startDate}/${endDate}&details=${encodeURIComponent(description)}&location=${encodeURIComponent(location)}`;
      
      // Open Google Calendar in new tab
      window.open(googleCalUrl, '_blank');
      showToast("Tadbir taqvimingizga qo'shilmoqda... 📅");
    });
  }

  // 5. COPY ADDRESS WITH TOAST
  const copyBtn = document.getElementById('copy-address-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const addressText = "Buxoro viloyati, Olot tumani, «Xo‘jaqul Ota» Tantanalar Saroyi";
      
      if (navigator.clipboard) {
        navigator.clipboard.writeText(addressText).then(() => {
          showToast("Manzil nusxalandi! 📋");
        }).catch(() => {
          fallbackCopyText(addressText);
        });
      } else {
        fallbackCopyText(addressText);
      }
    });
  }

  function fallbackCopyText(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast("Manzil nusxalandi! 📋");
    } catch (err) {
      showToast("Nusxa olish imkoni bo'lmadi");
    }
    document.body.removeChild(textArea);
  }

  // 6. TOAST NOTIFICATION UTILITY
  function showToast(message) {
    let toast = document.getElementById('global-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'global-toast';
      toast.className = 'toast-msg';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3200);
  }
});
