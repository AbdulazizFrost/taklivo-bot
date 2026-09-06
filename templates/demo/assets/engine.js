/**
 * TAKLIVO Universal Web Invitation Engine
 * Handles Dynamic API Data Loading, Demo Watermark, Language Switcher, and RSVP.
 */

(function () {
    window.TaklivoEngine = {
        lang: 'uz',
        orderData: null,
        translations: {
            uz: {
                openInvite: "Taklifnomani Ochish ⚜️",
                subtitle: "Hayotimizning eng go'zal sahifasi boshlanmoqda",
                inviteText: "Hurmatli mehmonimiz! Hayotimizning eng quvonchli va unutilmas kuni — nikoh to'yimiz tantanasida sizni aziz va qadrli mehmonimiz sifatida ko'rishdan behad mamnun bo'lamiz.",
                celebrationTitle: "THE CELEBRATION",
                venueTitle: "MANZIL & QABUL",
                venueHall: "Xonadonimizda",
                ourDay: "BIZNING KUNIMIZ 💍",
                ourStoryTitle: "Bizning Hikoya",
                galleryTitle: "Galereya",
                countdownTitle: "Tantanagacha Qoldi",
                gatheringTitle: "MEHMONLAR TASHRIFI",
                mapButton: "Yandex Xaritada ochish 📍",
                googleMapButton: "Google Xaritada ochish 🗺️",
                days: "Kun",
                hours: "Soat",
                minutes: "Daqiqa",
                seconds: "Soniya",
                scheduleTitle: "TO'Y DASTURI",
                schedule1Title: "Mehmonlar tashrifi",
                schedule1Desc: "Aziz mehmonlarni kutib olish va xush kelibsiz qadami",
                schedule2Title: "Nikoh Oqshomi Boshlanishi",
                schedule2Desc: "Kelin va kuyovning tantanali kirib kelishi",
                schedule3Title: "To'y Tantanasi & Qutlovlar",
                schedule3Desc: "Yaqinlar duosi va samimiy tilaklar dasturxoni",
                ayatText: "«Uning oyatlaridan biri — sizlar xotirjam bo‘lishingiz uchun o‘zingizdan juftlar yaratishi va o‘rtangizda mehr-muhabbat hamda rahm-shafqat paydo qilishidir.»",
                ayatSource: "RUM SURASI, 21-OYAT",
                coupleLead: "Ikki qalbning abadiy ittifoqi, o'zaro hurmat va cheksiz muhabbat dostoni.",
                coupleBody: "Hayotimizning eng muhim va unutilmas oqshomida siz kabi aziz va qadrli insonlarni yonimizda ko'rishdan behad baxtiyormiz.",
                toyonaTitle: "To'yona",
                toyonaDesc: "Agar bizni tabriklab, to'yona yubormoqchi bo'lsangiz, quyidagi karta raqamidan foydalanishingiz mumkin:",
                cardHolder: "KARTA EGASI",
                cardCopy: "Nusxalash",
                cardCopied: "Nusxalandi!",
                rsvpTitle: "Tashrifni tasdiqlash",
                rsvpSubtitle: "Sizning tashrifingiz biz uchun juda muhim",
                rsvpNameLabel: "Ismingiz",
                rsvpNamePlaceholder: "Masalan: Sardor",
                rsvpPhoneLabel: "Telefon raqamingiz",
                rsvpPhonePlaceholder: "+998 90 123 45 67",
                rsvpMsgLabel: "Ezgu tilaklaringiz (ixtiyoriy)",
                rsvpMsgPlaceholder: "O'z tilaklaringizni yozishingiz mumkin...",
                rsvpAccept: "Albatta boraman ✨",
                rsvpDecline: "Afsuski, kela olmayman",
                rsvpThanks: "Rahmat!",
                rsvpSuccessMsg: "Sizning javobingiz muvaffaqiyatli qabul qilindi.",
                closeBtn: "Yopish",
                demoCatalogTitle: "✨ TAKLIVO DEMO",
                demoCatalogDesc: "Sizga ushbu dizayn yoqdimi? O'zingiz uchun 5 daqiqada buyurtma qiling!",
                demoOrderBtn: "Buyurtma berish 💍",
                demoUnpaidTitle: "🛡 SINOV REJIMI",
                demoUnpaidDesc: "Sayt namunaviy ko'rinishda. To'lov qilingach, suv belgisi olib tashlanadi.",
                demoBotBtn: "Botda tasdiqlash",
                dresscodeTitle: "DRESS CODE",
                dresscodeSub: "BLACK TIE & EVENING ATTIRE",
                dresscodeGentlemen: "JANOB LAR UCHUN",
                dresscodeGentlemenDesc: "Klassik qora smoking yoki to'q rangli tantanali kostyum-shim, oq ko'ylak va kapalak-galstuk.",
                dresscodeLadies: "XONIMLAR UCHUN",
                dresscodeLadiesDesc: "Kechki uzun liboslar, to'q zumrad, to'q bordo, qora yoki nozik tillarang tuslar.",
                dresscodePalette: "TAVSIYA ETILADIGAN RANGLAR:"
            },
            ru: {
                openInvite: "Открыть приглашение ⚜️",
                subtitle: "Начинается самая прекрасная глава нашей жизни",
                inviteText: "Дорогие гости! В один из самых счастливых и знаменательных дней нашей жизни — день нашей свадьбы, мы будем искренне рады видеть вас среди наших почётных гостей.",
                celebrationTitle: "СВАДЕБНОЕ ТОРЖЕСТВО",
                venueTitle: "АДРЕС И ПРИЁМ ГОСТЕЙ",
                venueHall: "В кругу семьи",
                ourDay: "НАШ ДЕНЬ 💍",
                ourStoryTitle: "Наша история",
                galleryTitle: "Галерея",
                countdownTitle: "До торжества осталось",
                gatheringTitle: "СБОР ГОСТЕЙ",
                mapButton: "Открыть в Яндекс Картах 📍",
                googleMapButton: "Открыть в Google Картах 🗺️",
                days: "Дней",
                hours: "Часов",
                minutes: "Минут",
                seconds: "Секунд",
                scheduleTitle: "ПРОГРАММА ТОРЖЕСТВА",
                schedule1Title: "Сбор гостей",
                schedule1Desc: "Встреча дорогих гостей и приветственный фуршет",
                schedule2Title: "Начало торжества",
                schedule2Desc: "Торжественный выход жениха и невесты",
                schedule3Title: "Свадебный банкет & Поздравления",
                schedule3Desc: "Праздничный ужин, теплые слова и благословения",
                ayatText: "«Среди Его знамений — то, что Он сотворил из вас самих жен для вас, чтобы вы находили в них успокоение, и установил между вами любовь и милосердие.»",
                ayatSource: "СУРА АР-РУМ, 21-Й АЯТ",
                coupleLead: "Вечный союз двух сердец, история взаимного уважения и бесконечной любви.",
                coupleBody: "Мы будем счастливы разделить этот незабываемый вечер с самыми дорогими и близкими людьми.",
                toyonaTitle: "Подарки (Тоёна)",
                toyonaDesc: "Если вы хотите поздравить нас и отправить подарок, вы можете воспользоваться картой:",
                cardHolder: "ВЛАДЕЛЕЦ КАРТЫ",
                cardCopy: "Скопировать",
                cardCopied: "Скопировано!",
                rsvpTitle: "Подтверждение присутствия",
                rsvpSubtitle: "Ваше присутствие очень важно для нас",
                rsvpNameLabel: "Ваше имя",
                rsvpNamePlaceholder: "Например: Азиз",
                rsvpPhoneLabel: "Номер телефона",
                rsvpPhonePlaceholder: "+998 90 123 45 67",
                rsvpMsgLabel: "Теплые пожелания (необязательно)",
                rsvpMsgPlaceholder: "Напишите ваши пожелания молодожёнам...",
                rsvpAccept: "Я обязательно приду ✨",
                rsvpDecline: "К сожалению, не смогу",
                rsvpThanks: "Спасибо!",
                rsvpSuccessMsg: "Ваш ответ успешно принят.",
                closeBtn: "Закрыть",
                demoCatalogTitle: "✨ TAKLIVO ДЕМО",
                demoCatalogDesc: "Понравился дизайн? Закажите для своего торжества за 5 минут в боте!",
                demoOrderBtn: "Заказать в боте 💍",
                demoUnpaidTitle: "🛡 ДЕМО-РЕЖИМ",
                demoUnpaidDesc: "Сайт в предварительном просмотре. После оплаты водяной знак будет снят.",
                demoBotBtn: "Подтвердить в боте",
                dresscodeTitle: "ДРЕСС-КОД",
                dresscodeSub: "BLACK TIE & ВЕЧЕРНИЙ СТИЛЬ",
                dresscodeGentlemen: "ДЛЯ ДЖЕНТЛЬМЕНОВ",
                dresscodeGentlemenDesc: "Классический черный смокинг или темный торжественный костюм, белая рубашка и галстук-бабочка.",
                dresscodeLadies: "ДЛЯ ДАМ",
                dresscodeLadiesDesc: "Элегантные вечерние платья в пол, темный изумруд, глубокий бордо, черный или оттенки шампань.",
                dresscodePalette: "РЕКОМЕНДУЕМАЯ ПАЛИТРА:"
            }
        },

        init: function (config) {
            config = config || {};
            const urlParams = new URLSearchParams(window.location.search);
            const orderId = config.orderId || urlParams.get('order_id');
            const langParam = urlParams.get('lang');

            if (langParam && (langParam === 'ru' || langParam === 'uz')) {
                this.lang = langParam;
            } else {
                const storedLang = localStorage.getItem('taklivo_lang');
                if (storedLang && (storedLang === 'ru' || storedLang === 'uz')) {
                    this.lang = storedLang;
                }
            }

            if (config.secondLanguage !== false) {
                this.createLanguageToggle();
            }
            this.applyTranslations();

            if (orderId) {
                this.loadOrderData(orderId, config);
            } else {
                this.renderCatalogDemoBanner();
            }

            this.initCountdown(config.defaultDate || '2026-10-24T18:30:00');
            this.setupRSVPForm(orderId, config);
            this.setupCardCopy();
        },

        createLanguageToggle: function () {
            if (this.orderData && this.orderData.options && this.orderData.options.second_language === false) {
                const existing = document.getElementById('taklivoLangToggle');
                if (existing) existing.style.display = 'none';
                return;
            }
            let container = document.getElementById('taklivoLangToggle');
            if (!container) {
                container = document.createElement('div');
                container.id = 'taklivoLangToggle';
                container.className = 'taklivo-lang-toggle';
                container.innerHTML = `
                    <button class="taklivo-lang-btn ${this.lang === 'uz' ? 'active' : ''}" onclick="TaklivoEngine.setLanguage('uz')">UZ</button>
                    <button class="taklivo-lang-btn ${this.lang === 'ru' ? 'active' : ''}" onclick="TaklivoEngine.setLanguage('ru')">RU</button>
                `;
                document.body.appendChild(container);
            } else {
                container.style.display = 'flex';
                container.querySelectorAll('.taklivo-lang-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.innerText.toLowerCase() === this.lang);
                });
            }
        },

        setLanguage: function (newLang) {
            this.lang = newLang;
            try { localStorage.setItem('taklivo_lang', newLang); } catch (e) {}
            document.querySelectorAll('.taklivo-lang-btn').forEach(btn => {
                btn.classList.toggle('active', btn.innerText.toLowerCase() === newLang);
            });
            this.applyTranslations();
            if (this.orderData && this.orderData.is_demo) {
                this.renderUnpaidWatermark();
            } else if (!this.orderData) {
                this.renderCatalogDemoBanner();
            }
        },

        applyTranslations: function () {
            const dict = this.translations[this.lang];
            if (!dict) return;

            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (dict[key]) {
                    el.innerText = dict[key];
                }
            });

            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                const key = el.getAttribute('data-i18n-placeholder');
                if (dict[key]) {
                    el.setAttribute('placeholder', dict[key]);
                }
            });
        },

        loadOrderData: function (orderId, config) {
            const self = this;
            fetch(`/api/order/${orderId}`)
                .then(res => {
                    if (!res.ok) throw new Error('Order not found');
                    return res.json();
                })
                .then(data => {
                    self.orderData = data;
                    self.populateOrder(data);

                    if (data.is_demo) {
                        self.renderUnpaidWatermark();
                    }
                })
                .catch(err => {
                    console.warn('Could not load dynamic order from API, using defaults:', err);
                    if (config.orderData) {
                        self.orderData = config.orderData;
                        self.populateOrder(config.orderData);
                        if (config.orderData.is_demo) {
                            self.renderUnpaidWatermark();
                        }
                    } else if (config.orderId) {
                        self.orderData = { order_id: config.orderId, is_demo: true };
                        self.renderUnpaidWatermark();
                    } else {
                        self.renderCatalogDemoBanner();
                    }
                });
        },

        populateOrder: function (data) {
            const couple = data.couple || {};
            const event = data.event || {};

            const groom = couple.groom_name || 'Kuyov';
            const bride = couple.bride_name || 'Kelin';
            const coupleNames = `${groom} & ${bride}`;
            const initials = `${groom.charAt(0).toUpperCase()}${bride.charAt(0).toUpperCase()}`;

            document.querySelectorAll('[data-taklivo="groom_name"]').forEach(el => el.innerText = groom);
            document.querySelectorAll('[data-taklivo="bride_name"]').forEach(el => el.innerText = bride);
            document.querySelectorAll('[data-taklivo="couple_names"]').forEach(el => {
                if (!el.querySelector('[data-taklivo="groom_name"]')) {
                    el.innerText = coupleNames;
                }
            });
            document.querySelectorAll('[data-taklivo="monogram"]').forEach(el => {
                const letters = el.querySelectorAll('.crest-letter');
                if (letters.length >= 2) {
                    letters[0].innerText = groom.charAt(0).toUpperCase();
                    letters[1].innerText = bride.charAt(0).toUpperCase();
                } else {
                    el.innerText = initials;
                }
            });
            document.querySelectorAll('[data-taklivo="groom_initial"]').forEach(el => el.innerText = groom.charAt(0).toUpperCase());
            document.querySelectorAll('[data-taklivo="bride_initial"]').forEach(el => el.innerText = bride.charAt(0).toUpperCase());

            if (event.event_date) {
                document.querySelectorAll('[data-taklivo="event_date"]').forEach(el => el.innerText = event.event_date);
            }
            if (event.event_time) {
                document.querySelectorAll('[data-taklivo="event_time"]').forEach(el => el.innerText = event.event_time);
            }
            if (event.venue) {
                document.querySelectorAll('[data-taklivo="venue"]').forEach(el => el.innerText = event.venue);
            }
            if (event.address) {
                document.querySelectorAll('[data-taklivo="address"]').forEach(el => el.innerText = event.address);
            }

            if (event.venue || event.address) {
                const query = encodeURIComponent(`${event.venue || ''} ${event.address || ''}`.trim());
                document.querySelectorAll('a[href*="maps.google.com"]').forEach(a => {
                    a.href = `https://www.google.com/maps/search/?api=1&query=${query}`;
                });
            }

            const options = data.options || {};
            if (options.rsvp === false) {
                document.querySelectorAll('.rsvp-section, #rsvpForm, .success-modal').forEach(el => el.style.display = 'none');
            }
            if (options.gallery === false) {
                document.querySelectorAll('.gallery-section').forEach(el => el.style.display = 'none');
            }
            if (options.music === false) {
                const audio = document.getElementById('weddingAudio');
                if (audio) {
                    audio.pause();
                    audio.remove();
                }
                const mBtn = document.getElementById('musicBtn');
                if (mBtn) mBtn.style.display = 'none';
            }
            if (options.second_language === false) {
                const langToggle = document.getElementById('taklivoLangToggle');
                if (langToggle) langToggle.style.display = 'none';
            }
            if (options.dresscode === false) {
                document.querySelectorAll('.dresscode-section').forEach(el => el.style.display = 'none');
            }
            if (options.schedule === false) {
                document.querySelectorAll('.schedule-section, .timeline-section').forEach(el => el.style.display = 'none');
            }
            if (options.map === false) {
                document.querySelectorAll('.luxury-action-btn, .location-btn').forEach(el => el.style.display = 'none');
            }

            if (event.event_date) {
                const timeStr = event.event_time || '18:00';
                this.initCountdown(`${event.event_date} ${timeStr}`);
            }
        },

        renderCatalogDemoBanner: function () {
            let banner = document.getElementById('taklivoBanner');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'taklivoBanner';
                banner.className = 'taklivo-floating-banner';
                document.body.appendChild(banner);
            }
            const dict = this.translations[this.lang];
            banner.innerHTML = `
                <div class="taklivo-banner-left">
                    <span class="taklivo-banner-title">
                        ${dict.demoCatalogTitle}
                        <span class="taklivo-banner-badge">Demo</span>
                    </span>
                    <span class="taklivo-banner-desc">${dict.demoCatalogDesc}</span>
                </div>
                <a href="https://t.me/taklivo_bot" class="taklivo-banner-btn" target="_blank">${dict.demoOrderBtn}</a>
            `;
        },

        renderUnpaidWatermark: function () {
            let watermark = document.getElementById('taklivoWatermark');
            if (!watermark) {
                watermark = document.createElement('div');
                watermark.id = 'taklivoWatermark';
                watermark.className = 'taklivo-unpaid-watermark';
                document.body.appendChild(watermark);
            }
            const dict = this.translations[this.lang];
            watermark.innerHTML = `🛡 TAKLIVO DEMO PREVIEW • 24H`;

            let banner = document.getElementById('taklivoBanner');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'taklivoBanner';
                banner.className = 'taklivo-floating-banner';
                document.body.appendChild(banner);
            }
            const badge = this.orderData && this.orderData.order_id ? `<span class="taklivo-banner-badge">Buyurtma #${this.orderData.order_id}</span>` : '';
            banner.innerHTML = `
                <div class="taklivo-banner-left">
                    <span class="taklivo-banner-title">
                        ${dict.demoUnpaidTitle}
                        ${badge}
                    </span>
                    <span class="taklivo-banner-desc">${dict.demoUnpaidDesc}</span>
                </div>
                <a href="https://t.me/taklivo_bot" class="taklivo-banner-btn" target="_blank">${dict.demoBotBtn}</a>
            `;
        },

        initCountdown: function (targetDateStr) {
            let targetDate;
            try {
                if (targetDateStr.includes('.')) {
                    // format DD.MM.YYYY
                    const parts = targetDateStr.split(' ')[0].split('.');
                    if (parts.length === 3) {
                        const day = parts[0];
                        const month = parts[1];
                        const year = parts[2];
                        const time = targetDateStr.split(' ')[1] || '18:00';
                        targetDate = new Date(`${year}-${month}-${day}T${time}:00`).getTime();
                    } else {
                        targetDate = new Date(targetDateStr).getTime();
                    }
                } else {
                    targetDate = new Date(targetDateStr).getTime();
                }
            } catch (e) {
                targetDate = new Date('2026-10-24T18:30:00').getTime();
            }

            if (isNaN(targetDate)) {
                targetDate = new Date('2026-10-24T18:30:00').getTime();
            }

            const updateTimer = () => {
                const now = new Date().getTime();
                const diff = targetDate - now;

                const daysEl = document.getElementById('days');
                const hoursEl = document.getElementById('hours');
                const minsEl = document.getElementById('minutes');
                const secsEl = document.getElementById('seconds');

                if (diff <= 0) {
                    if (daysEl) daysEl.innerText = '00';
                    if (hoursEl) hoursEl.innerText = '00';
                    if (minsEl) minsEl.innerText = '00';
                    if (secsEl) secsEl.innerText = '00';
                    return;
                }

                const d = Math.floor(diff / (1000 * 60 * 60 * 24));
                const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const s = Math.floor((diff % (1000 * 60)) / 1000);

                if (daysEl) daysEl.innerText = String(d).padStart(2, '0');
                if (hoursEl) hoursEl.innerText = String(h).padStart(2, '0');
                if (minsEl) minsEl.innerText = String(m).padStart(2, '0');
                if (secsEl) secsEl.innerText = String(s).padStart(2, '0');
            };

            updateTimer();
            if (this._timerInterval) clearInterval(this._timerInterval);
            this._timerInterval = setInterval(updateTimer, 1000);
        },

        setupRSVPForm: function (orderId, config) {
            const form = document.getElementById('rsvpForm');
            if (!form) return;

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const name = (document.getElementById('name') || {}).value || '';
                const phone = (document.getElementById('phone') || {}).value || '';
                const message = (document.getElementById('message') || {}).value || '';
                const statusInput = document.getElementById('attendanceStatus');
                const status = statusInput ? statusInput.value : 'Boraman';

                if (!name.trim() || !phone.trim()) {
                    alert(this.lang === 'ru' ? 'Пожалуйста, введите имя и телефон!' : 'Iltimos, ism va telefon raqamingizni kiriting!');
                    return;
                }

                // If orderId is present, post to API
                if (orderId) {
                    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                    const apiBase = isLocal ? '' : ((config && config.apiBase) || 'https://taklivo.uz');
                    fetch(`${apiBase}/api/order/${orderId}/rsvp`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, phone, message, status })
                    }).catch(err => console.log('RSVP logged:', err));
                }

                const modal = document.getElementById('successModal');
                if (modal) {
                    modal.classList.add('open');
                } else {
                    alert(this.translations[this.lang].rsvpSuccessMsg);
                }
                form.reset();
            });
        },

        setupCardCopy: function () {
            window.copyCardNumber = function () {
                const cardEl = document.getElementById('cardNumber');
                const btnText = document.getElementById('copyBtnText');
                if (!cardEl) return;
                const text = cardEl.innerText.replace(/\s+/g, '');
                navigator.clipboard.writeText(text).then(() => {
                    if (btnText) {
                        const original = btnText.innerText;
                        btnText.innerText = TaklivoEngine.translations[TaklivoEngine.lang].cardCopied;
                        setTimeout(() => { btnText.innerText = original; }, 2000);
                    }
                });
            };
        }
    };
})();
