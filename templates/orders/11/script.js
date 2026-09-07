document.addEventListener('DOMContentLoaded', () => {
  // --- 1. HERO ANIMATION & SPARKLES ---
  const hero = document.getElementById('heroSection');
  if (hero) {
    requestAnimationFrame(() => hero.classList.add('ready'));
  }

  const sparkleBox = document.getElementById('sparkles');
  if (sparkleBox) {
    function spawnSparkle() {
      const s = document.createElement('div');
      s.className = 'sparkle';
      const size = Math.random() * 4 + 2;
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.left = Math.random() * 100 + '%';
      s.style.top = (Math.random() * 70 + 20) + '%';
      s.style.animationDuration = (Math.random() * 3 + 3) + 's';
      sparkleBox.appendChild(s);
      setTimeout(() => s.remove(), 6500);
    }
    setInterval(spawnSparkle, 400);
    for (let i = 0; i < 8; i++) setTimeout(spawnSparkle, i * 150);
  }

  // --- 2. COUNTDOWN TIMER (15.09.2026 18:00) ---
  const WEDDING_DATE = new Date("2026-09-15T18:00:00");
  function tick() {
    const now = new Date();
    const diff = WEDDING_DATE - now;

    if (diff <= 0) {
      document.getElementById('cd-d').textContent = "00";
      document.getElementById('cd-h').textContent = "00";
      document.getElementById('cd-m').textContent = "00";
      document.getElementById('cd-s').textContent = "00";
      return;
    }

    const day = 86400000;
    const hour = 3600000;
    const minute = 60000;

    const d = Math.floor(diff / day);
    const h = Math.floor((diff % day) / hour);
    const m = Math.floor((diff % hour) / minute);
    const s = Math.floor((diff % minute) / 1000);

    const elD = document.getElementById('cd-d');
    const elH = document.getElementById('cd-h');
    const elM = document.getElementById('cd-m');
    const elS = document.getElementById('cd-s');

    if (elD) elD.textContent = String(d).padStart(2, '0');
    if (elH) elH.textContent = String(h).padStart(2, '0');
    if (elM) elM.textContent = String(m).padStart(2, '0');
    if (elS) elS.textContent = String(s).padStart(2, '0');
  }
  setInterval(tick, 1000);
  tick();

  // --- 3. 3D COVER CARD OPENING ---
  const coverCard = document.getElementById('coverCard');
  const cover = document.getElementById('cover');
  const site = document.getElementById('site');
  let opened = false;

  if (coverCard && cover && site) {
    coverCard.addEventListener('click', () => {
      if (opened) return;
      opened = true;
      coverCard.classList.add('open');

      setTimeout(() => {
        cover.classList.add('gone');
        document.body.classList.remove('locked');
        site.classList.add('on');
      }, 900);

      setTimeout(() => {
        cover.style.display = 'none';
      }, 2000);
    });
  }

  // --- 4. SCROLL REVEAL OBSERVER ---
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.05, rootMargin: "0px 0px 100px 0px" });

  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  function checkReveals() {
    const triggerBottom = window.innerHeight * 0.95;
    document.querySelectorAll('.reveal:not(.in)').forEach(el => {
      const box = el.getBoundingClientRect();
      if (box.top < triggerBottom) {
        el.classList.add('in');
      }
    });
  }
  window.addEventListener('scroll', checkReveals);
  setTimeout(checkReveals, 1200);

  // --- 5. RSVP FORM SUBMISSION ---
  const rsvpForm = document.getElementById('rsvpForm');
  const formMsg = document.getElementById('formMsg');
  if (rsvpForm && formMsg) {
    rsvpForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = rsvpForm.querySelector('.rsvp-btn');
      if (btn) btn.disabled = true;

      const successText = currentLang === 'uz'
        ? "✓ Rahmat! Javobingiz qabul qilindi."
        : "✓ Спасибо! Ваш ответ принят.";

      formMsg.textContent = successText;
      formMsg.style.color = "var(--gold-dark)";
    });
  }

  // --- 6. BACKGROUND MUSIC TOGGLE ---
  const musicBtn = document.getElementById('musicBtn');
  let audioContext = null;
  let isPlaying = false;
  let noteInterval = null;

  function playSoftRomanticChime() {
    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }

      const notes = [261.63, 329.63, 392.00, 523.25, 659.25]; // C, E, G, C5, E5
      let step = 0;

      noteInterval = setInterval(() => {
        if (!isPlaying) return;
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(notes[step % notes.length], audioContext.currentTime);

        gain.gain.setValueAtTime(0.01, audioContext.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.08, audioContext.currentTime + 0.15);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 1.2);

        osc.connect(gain);
        gain.connect(audioContext.destination);

        osc.start();
        osc.stop(audioContext.currentTime + 1.3);
        step++;
      }, 1600);
    } catch (e) {
      console.warn("Audio unavailable", e);
    }
  }

  if (musicBtn) {
    musicBtn.addEventListener('click', () => {
      isPlaying = !isPlaying;
      musicBtn.textContent = isPlaying ? '⏸' : '♪';
      if (isPlaying) {
        playSoftRomanticChime();
      } else {
        if (noteInterval) clearInterval(noteInterval);
      }
    });
  }

  // --- 7. LANGUAGE TRANSLATIONS ---
  const T = {
    uz: {
      coverHint: "Ochish uchun bosing",
      heroEyebrow: "Bizning to‘yimiz",
      heroLoc: "Toshkent sh., «Oqsaroy» to‘yxonasi",
      cdEyebrow: "Unutilmas kun",
      cdTitle: "To‘ygacha qoldi",
      days: "Kun",
      hours: "Soat",
      mins: "Daqiqa",
      secs: "Soniya",
      inviteEyebrow: "Taklifnoma",
      inviteTitle: "Aziz mehmonlarimiz!",
      inviteText: "Taqdir bizning yuraklarimizni birlashtirdi va endi biz birgalikda yangi hayot ostonasiga qadam qo'ymoqdamiz. Sizni ushbu eng quvonchli va unutilmas kunimizda — nikoh to‘yimizda qadrdon mehmonimiz bo‘lishga taklif etamiz.",
      tlEyebrow: "Kun dasturi",
      tlTitle: "Tantana rejasi",
      tl1Time: "18:00",
      tl1Title: "Mehmonlar tashrifi va kutib olish",
      tl2Time: "18:30",
      tl2Title: "Kelin-kuyovning tantanali kirib kelishi",
      tl3Time: "19:00",
      tl3Title: "Bayramona to‘y oqshomi dasturxoni",
      tl4Time: "21:00",
      tl4Title: "To‘y torti va qutlovlar",
      venueEyebrow: "Tadbir joyi",
      venueTitle: "To‘yxona manzili",
      venueName: "«Oqsaroy» to‘yxonasi",
      venueAddr: "Toshkent sh., Navoiy ko‘chasi, 15-uy",
      venueTime: "15-sentyabr, 2026-yil · 18:00",
      venueBtn: "Google xaritasida ochish",
      dcEyebrow: "Tavsiyalar",
      dcTitle: "Dress-kod",
      dcGold: "Oltin rang",
      dcBlush: "Pudra",
      dcCream: "Krem",
      dcDark: "Klassik to'q",
      dcText: "Bizning bayramimiz uchun qulay va chiroyli kiyinishingizni so'raymiz. Pastel, tilla va nozik pudra tusidagi liboslar bayramimizga yanada ko‘rk bag‘ishlaydi.",
      rsvpEyebrow: "Tasdiqlash",
      rsvpTitle: "Ishtirokingizni tasdiqlang",
      nameLabel: "Ismingiz va familiyangiz",
      namePh: "Ism va familiyangizni kiriting",
      attendLabel: "To‘yda ishtirok etasizmi?",
      willAttend: "Ha, albatta kelaman",
      wontAttend: "Afsuski, kela olmayman",
      guestsLabel: "Hamrohlaringiz soni",
      guests1: "Bir o‘zim",
      guests2: "Juftlikda (+1)",
      guests3: "Oila bilan",
      commentLabel: "Kelin-kuyovga tilaklar (ixtiyoriy)",
      commentPh: "Bizga samimiy tilaklaringizni yozing...",
      submitBtn: "Javobni tasdiqlash",
      ftDate: "15-sentyabr, 2026-yil",
      ftCredit: "Taklivo · Maxsus taklifnomalar"
    },
    ru: {
      coverHint: "Нажмите, чтобы открыть",
      heroEyebrow: "Приглашаем на свадьбу",
      heroLoc: "г. Ташкент, «Oqsaroy» to‘yxonasi",
      cdEyebrow: "Особый день",
      cdTitle: "До свадьбы осталось",
      days: "Дней",
      hours: "Часов",
      mins: "Минут",
      secs: "Секунд",
      inviteEyebrow: "Приглашение",
      inviteTitle: "Дорогие гости!",
      inviteText: "Судьба соединила наши сердца, и теперь мы готовы начать новую главу нашей жизни. Приглашаем вас разделить с нами радость этого особенного и счастливого дня.",
      tlEyebrow: "Программа дня",
      tlTitle: "Расписание торжества",
      tl1Time: "18:00",
      tl1Title: "Сбор и встреча гостей",
      tl2Time: "18:30",
      tl2Title: "Торжественный вход жениха и невесты",
      tl3Time: "19:00",
      tl3Title: "Праздничный банкет",
      tl4Time: "21:00",
      tl4Title: "Свадебный торт и поздравления",
      venueEyebrow: "Место торжества",
      venueTitle: "Локация",
      venueName: "«Oqsaroy» to‘yxonasi",
      venueAddr: "г. Ташкент, ул. Навои, дом 15",
      venueTime: "15 сентября 2026 года · 18:00",
      venueBtn: "Открыть на Google карте",
      dcEyebrow: "Рекомендации",
      dcTitle: "Дресс-код",
      dcGold: "Золотой",
      dcBlush: "Пудровый",
      dcCream: "Кремовый",
      dcDark: "Классический",
      dcText: "Будем признательны, если вы поддержите нашу цветовую гамму — пастельные, золотистые и нежные пудровые оттенки.",
      rsvpEyebrow: "Подтверждение",
      rsvpTitle: "Ваше присутствие",
      nameLabel: "Ваше имя и фамилия",
      namePh: "Имя и фамилия",
      attendLabel: "Планируете ли присутствовать?",
      willAttend: "Я обязательно приду",
      wontAttend: "К сожалению, не смогу",
      guestsLabel: "Количество гостей",
      guests1: "Один(на)",
      guests2: "С парой (+1)",
      guests3: "Всей семьей",
      commentLabel: "Ваше пожелание (необязательно)",
      commentPh: "Напишите нам несколько теплых слов...",
      submitBtn: "Отправить ответ",
      ftDate: "15 сентября 2026 года",
      ftCredit: "Taklivo · Индивидуальные пригласительные"
    }
  };

  let currentLang = 'uz';

  function applyLang(lang) {
    currentLang = lang;
    const dict = T[lang];
    if (!dict) return;

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const k = el.getAttribute('data-i18n');
      if (dict[k] !== undefined) el.textContent = dict[k];
    });

    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const k = el.getAttribute('data-i18n-ph');
      if (dict[k] !== undefined) el.placeholder = dict[k];
    });

    document.querySelectorAll('.lang-toggle button').forEach(b => {
      b.classList.toggle('active', b.dataset.lang === lang);
    });
  }

  window.applyLang = applyLang;

  document.querySelectorAll('.lang-toggle button').forEach(b => {
    b.addEventListener('click', () => applyLang(b.dataset.lang));
  });

  // Default to UZ
  applyLang('uz');
});
