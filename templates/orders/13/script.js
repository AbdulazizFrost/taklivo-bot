/**
 * TAKLIVO MINIMAL MODERN — СЕРГЕЙ & ЮЛИЯ (ЗАКАЗ #13)
 * Wedding Invitation Interactive Controller
 */

// --- 0. Interactive 3D Envelope Opening ---
let isEnvelopeOpened = false;

function openEnvelope(e) {
  if (e && e.stopPropagation) e.stopPropagation();
  if (isEnvelopeOpened) return;
  isEnvelopeOpened = true;

  const screen = document.getElementById('envelopeScreen');
  const card = document.getElementById('envelopeCard');
  const topFlap = document.getElementById('envelopeTopFlap');
  const waxSeal = document.getElementById('envelopeWaxSeal');
  const ribbon = document.getElementById('envelopeRibbon');

  // 1. Trigger audio play directly on user gesture
  if (audio && !isPlaying) {
    audio.play().then(() => {
      isPlaying = true;
      updateAudioUI(true);
    }).catch(err => {
      console.log('Audio autoplay policy:', err);
    });
  }

  if (screen) screen.classList.add('opening');
  if (waxSeal) waxSeal.classList.add('broken');
  if (ribbon) ribbon.classList.add('dissolve');
  if (topFlap) topFlap.classList.add('open');

  // 3. Slide letter card out of the envelope
  setTimeout(() => {
    if (card) card.classList.add('slid-out');
  }, 380);

  // 4. Fade out overlay and unlock page scroll
  setTimeout(() => {
    if (screen) screen.classList.add('opened');
    document.body.classList.remove('locked');
  }, 1350);
}

// --- 1. Audio Player Controller ---
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
      console.log('Autoplay restriction prevented audio:', err);
      isPlaying = false;
      updateAudioUI(false);
    });
  }
}

function updateAudioUI(playing) {
  if (eqBars) {
    if (playing) {
      eqBars.classList.add('active');
    } else {
      eqBars.classList.remove('active');
    }
  }
  if (audioLabel) {
    audioLabel.innerText = playing ? 'ИГРАЕТ ♫' : 'ВАЛЬС № 2';
  }
}

// Auto-play attempt on first user gesture
let initialGestureTriggered = false;
function handleInitialUserGesture() {
  if (initialGestureTriggered || isPlaying) return;
  initialGestureTriggered = true;

  if (audio) {
    audio.play().then(() => {
      isPlaying = true;
      updateAudioUI(true);
    }).catch(() => {
      // Autoplay blocked without direct interaction, ignore
    });
  }

  window.removeEventListener('click', handleInitialUserGesture);
  window.removeEventListener('touchstart', handleInitialUserGesture);
}

window.addEventListener('click', handleInitialUserGesture, { once: true });
window.addEventListener('touchstart', handleInitialUserGesture, { once: true });


// --- 2. Scroll Reveal Animations ---
function initScrollReveal() {
  const items = document.querySelectorAll('.reveal-item');
  if (!('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('active'));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: '0px 0px -40px 0px'
  });

  items.forEach(el => observer.observe(el));
}


// --- 3. Architectural Countdown Timer ---
// Target: 05 June 2027 at 14:00 (Moscow Time UTC+3)
const targetDate = new Date('2027-06-05T14:00:00+03:00').getTime();

function updateCountdown() {
  const now = new Date().getTime();
  const diff = targetDate - now;

  const daysEl = document.getElementById('days');
  const hoursEl = document.getElementById('hours');
  const minutesEl = document.getElementById('minutes');
  const secondsEl = document.getElementById('seconds');

  if (diff <= 0) {
    if (daysEl) daysEl.innerText = '00';
    if (hoursEl) hoursEl.innerText = '00';
    if (minutesEl) minutesEl.innerText = '00';
    if (secondsEl) secondsEl.innerText = '00';
    return;
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);

  if (daysEl) daysEl.innerText = String(days).padStart(2, '0');
  if (hoursEl) hoursEl.innerText = String(hours).padStart(2, '0');
  if (minutesEl) minutesEl.innerText = String(minutes).padStart(2, '0');
  if (secondsEl) secondsEl.innerText = String(seconds).padStart(2, '0');
}


// --- 4. RSVP Choice UI & Form Handler ---
function updateChoiceUI(radioInput) {
  const cards = document.querySelectorAll('.rsvp-choice-card');
  cards.forEach(card => card.classList.remove('active'));

  if (radioInput && radioInput.closest('.rsvp-choice-card')) {
    radioInput.closest('.rsvp-choice-card').classList.add('active');
  }
}

function handleRsvpSubmit(e) {
  e.preventDefault();

  const nameInput = document.getElementById('guestName');
  const phoneInput = document.getElementById('guestPhone');
  const messageInput = document.getElementById('guestMessage');
  const attendanceInput = document.querySelector('input[name="attendance"]:checked');
  const submitBtn = document.getElementById('submitBtn');

  if (!nameInput || !nameInput.value.trim()) {
    alert('Пожалуйста, укажите ваше имя.');
    return;
  }

  // Button loading state
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>ОТПРАВКА...</span>';
  }

  // Store response in localStorage
  const rsvpData = {
    order_id: 13,
    guest_name: nameInput.value.trim(),
    guest_phone: phoneInput ? phoneInput.value.trim() : '',
    attendance: attendanceInput ? attendanceInput.value : 'С удовольствием приду',
    message: messageInput ? messageInput.value.trim() : '',
    timestamp: new Date().toISOString()
  };

  try {
    const existing = JSON.parse(localStorage.getItem('taklivo_order_13_rsvp') || '[]');
    existing.push(rsvpData);
    localStorage.setItem('taklivo_order_13_rsvp', JSON.stringify(existing));
  } catch (err) {
    console.warn('Storage warning:', err);
  }

  // Send RSVP notification to Taklivo Telegram Bot API
  try {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const apiBase = isLocal ? '' : 'https://taklivo.uz';
    fetch(`${apiBase}/api/order/13/rsvp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: rsvpData.guest_name,
        phone: rsvpData.guest_phone,
        status: rsvpData.attendance,
        message: rsvpData.message
      })
    }).catch(err => {
      console.log('RSVP online sync notice:', err);
    });
  } catch (err) {}

  setTimeout(() => {
    // Restore button
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span>ОТПРАВИТЬ ОТВЕТ</span><span class="btn-arrow">→</span>';
    }

    // Show Russian success modal
    const modal = document.getElementById('successModal');
    if (modal) {
      modal.classList.add('open');
    }

    // Reset fields
    const form = document.getElementById('rsvpForm');
    if (form) form.reset();

    // Reset active choice radio back to default
    const yesCard = document.getElementById('choiceYes');
    const noCard = document.getElementById('choiceNo');
    if (yesCard) yesCard.classList.add('active');
    if (noCard) noCard.classList.remove('active');
  }, 600);
}

function closeSuccessModal() {
  const modal = document.getElementById('successModal');
  if (modal) {
    modal.classList.remove('open');
  }
}


// --- 5. Lightbox Modal ---
function openPhotoModal(src) {
  const modal = document.getElementById('photoModal');
  const img = document.getElementById('lightboxImg');
  if (modal && img) {
    img.src = src;
    modal.classList.add('open');
  }
}

function closePhotoModal(e) {
  if (e && e.target && e.target.tagName === 'IMG') {
    return; // Don't close if clicked directly on image
  }
  const modal = document.getElementById('photoModal');
  if (modal) {
    modal.classList.remove('open');
  }
}


// --- 6. Initialization on DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', () => {
  // Ensure hero is active immediately
  const hero = document.getElementById('hero');
  if (hero) hero.classList.add('active');

  // Start Countdown
  updateCountdown();
  setInterval(updateCountdown, 1000);

  // Initialize Scroll Reveal
  initScrollReveal();

  // Escape key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSuccessModal();
      closePhotoModal();
    }
  });
});
