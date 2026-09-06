document.addEventListener("DOMContentLoaded", () => {
    
    // ==========================================
    // 1. INTRO SCREEN & UNLOCK (START FROM BEGINNING ON EVERY REFRESH)
    // ==========================================
    const introScreen = document.getElementById('introScreen');
    const unlockBtn = document.getElementById('unlockBtn');
    const body = document.body;

    function resetToBeginning() {
        if ('scrollRestoration' in history) {
            history.scrollRestoration = 'manual';
        }
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;

        if (window.location.hash) {
            history.replaceState(null, '', window.location.pathname + window.location.search);
        }

        body.classList.add('locked');

        if (introScreen) {
            introScreen.classList.remove('hidden');
            introScreen.style.removeProperty('opacity');
            introScreen.style.removeProperty('visibility');
            introScreen.style.removeProperty('transform');
        }

        if (unlockBtn) {
            unlockBtn.style.removeProperty('transform');
            unlockBtn.style.removeProperty('box-shadow');
        }
    }

    // Force reset immediately on DOM load
    resetToBeginning();

    // Handle bfcache (Safari/Chrome back-forward and mobile reload/pull-to-refresh)
    window.addEventListener('pageshow', () => {
        resetToBeginning();
    });

    window.addEventListener('beforeunload', () => {
        window.scrollTo(0, 0);
    });

    if (unlockBtn && introScreen) {
        unlockBtn.addEventListener('click', () => {
            // Visual feedback on button press before disappearing
            unlockBtn.style.transform = 'scale(0.95)';
            unlockBtn.style.boxShadow = '0 0 50px rgba(255,255,255,0.8)';

            // Wait for visual lock to open, then dissolve the intro screen
            setTimeout(() => {
                introScreen.classList.add('hidden');
                body.classList.remove('locked');
            }, 600);
        });
    } else {
        body.classList.remove('locked');
    }

    // ==========================================
    // 2. CINEMATIC SCROLL REVEALS
    // ==========================================
    const observerOptions = {
        root: null,
        rootMargin: '-50px 0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); 
            }
        });
    }, observerOptions);

    document.querySelectorAll('.cinematic-fade').forEach(el => {
        observer.observe(el);
    });

    // ==========================================
    // 3. MAGNETIC 3D CARD HOVER
    // ==========================================
    const luxuryCard = document.getElementById('luxuryCard');
    if (luxuryCard) {
        luxuryCard.addEventListener('mousemove', (e) => {
            const rect = luxuryCard.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -10; 
            const rotateY = ((x - centerX) / centerX) * 10;
            
            requestAnimationFrame(() => {
                luxuryCard.style.transform = `perspective(1500px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            });
        });

        luxuryCard.addEventListener('mouseleave', () => {
            requestAnimationFrame(() => {
                luxuryCard.style.transform = 'perspective(1500px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
            });
        });
    }

    // ==========================================
    // 4. COPY TO CLIPBOARD
    // ==========================================
    const copyBtn = document.getElementById('copyBtn');
    const cardNumber = document.getElementById('cardNumber');

    if (copyBtn && cardNumber) {
        [copyBtn, cardNumber].forEach(trigger => {
            trigger.addEventListener('click', async () => {
                const textToCopy = cardNumber.innerText.replace(/\s/g, '');
                const btnText = copyBtn.querySelector('span') || copyBtn;
                const originalText = btnText.innerText;
                
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    successFeedback();
                } catch (err) {
                    fallbackCopy(textToCopy);
                }

                function successFeedback() {
                    btnText.innerText = "NUSXALANDI!";
                    copyBtn.style.backgroundColor = "var(--primary)";
                    copyBtn.style.color = "#fff";
                    copyBtn.style.borderColor = "var(--primary)";
                    
                    setTimeout(() => {
                        btnText.innerText = originalText;
                        copyBtn.style.backgroundColor = "rgba(255,255,255,0.7)";
                        copyBtn.style.color = "var(--primary)";
                        copyBtn.style.borderColor = "rgba(26,26,26,0.15)";
                    }, 2000);
                }

                function fallbackCopy(text) {
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        successFeedback();
                    } catch (e) {
                        console.error('Fallback failed', e);
                    }
                    document.body.removeChild(textArea);
                }
            });
        });
    }

    // ==========================================
    // 5. COUNTDOWN TIMER (20-OKTABR 2026, 19:00)
    // ==========================================
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        const countDownDate = new Date("Oct 20, 2026 19:00:00").getTime();

        const x = setInterval(function() {
            const now = new Date().getTime();
            const distance = countDownDate - now;

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            const dEl = document.getElementById("days");
            const hEl = document.getElementById("hours");
            const mEl = document.getElementById("minutes");
            const sEl = document.getElementById("seconds");

            if (dEl) dEl.innerText = String(Math.max(0, days)).padStart(2, '0');
            if (hEl) hEl.innerText = String(Math.max(0, hours)).padStart(2, '0');
            if (mEl) mEl.innerText = String(Math.max(0, minutes)).padStart(2, '0');
            if (sEl) sEl.innerText = String(Math.max(0, seconds)).padStart(2, '0');

            if (distance < 0) {
                clearInterval(x);
            }
        }, 1000);
    }
    
    // ==========================================
    // 6. ADD TO GOOGLE CALENDAR
    // ==========================================
    const addToCalendarBtn = document.getElementById('addToCalendarBtn');
    if (addToCalendarBtn) {
        const title = encodeURIComponent("Mirafzal va Sabina Nikoh To'yi 💍");
        const details = encodeURIComponent("Mirafzal va Sabinalarning nikoh to'yiga lutfan taklif etamiz!");
        const location = encodeURIComponent("«Dilifori» Tantanalar Saroyi, Forish tumani, Jizzax");
        const dates = "20261020T140000Z/20261020T190000Z";
        
        const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${dates}&details=${details}&location=${location}`;
        addToCalendarBtn.href = googleCalendarUrl;
    }
    
    // ==========================================
    // 7. PARALLAX SCROLLING DEPTH
    // ==========================================
    const parallaxElements = document.querySelectorAll('.parallax-scroll');
    
    if (parallaxElements.length > 0) {
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(() => {
                    parallaxElements.forEach(el => {
                        const speed = parseFloat(el.getAttribute('data-speed')) || 0.1;
                        const rect = el.getBoundingClientRect();
                        const elementCenter = rect.top + (rect.height / 2);
                        const viewportCenter = window.innerHeight / 2;
                        
                        if (rect.top < window.innerHeight && rect.bottom > 0) {
                            const distance = elementCenter - viewportCenter;
                            const yPos = distance * speed;
                            el.style.transform = `translateY(${yPos}px)`;
                        }
                    });
                    ticking = false;
                });
            }
        }, { passive: true });
    }
    

    // ==========================================
    // 9. TAKLIVO UNIVERSAL ENGINE INIT
    // ==========================================
    if (window.TaklivoEngine) {
        window.TaklivoEngine.init({
            orderId: 8,
            secondLanguage: false,
            defaultDate: '20.10.2026 19:00'
        });
    }
});
