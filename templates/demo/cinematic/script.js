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
        rootMargin: '-50px 0px', // Trigger slightly after it enters screen
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Unobserve to keep the fade permanent once revealed
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
            // Get bounding rect
            const rect = luxuryCard.getBoundingClientRect();
            // Calculate mouse position relative to the center of the card
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate rotation (max 10 degrees)
            const rotateX = ((y - centerY) / centerY) * -10; 
            const rotateY = ((x - centerX) / centerX) * 10;
            
            // Apply transform using requestAnimationFrame for 60fps smoothness
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
        // Also allow clicking the number directly
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
    // 5. COUNTDOWN TIMER
    // ==========================================
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        // Set the date we're counting down to
        let targetYear = 2026;
        // If the date is already in the past (e.g. testing in late 2026), push to next year so the timer ticks
        if (new Date().getTime() > new Date("Aug 12, 2026 18:00:00").getTime()) {
            targetYear = new Date().getFullYear() + 1;
        }
        const countDownDate = new Date(`Aug 12, ${targetYear} 18:00:00`).getTime();

        // Update the count down every 1 second
        const x = setInterval(function() {
            // Get today's date and time
            const now = new Date().getTime();

            // Find the distance between now and the count down date
            const distance = countDownDate - now;

            // Time calculations for days, hours, minutes and seconds
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            // Display the result in the elements
            document.getElementById("days").innerText = days.toString().padStart(2, '0');
            document.getElementById("hours").innerText = hours.toString().padStart(2, '0');
            document.getElementById("minutes").innerText = minutes.toString().padStart(2, '0');
            document.getElementById("seconds").innerText = seconds.toString().padStart(2, '0');

            // If the count down is finished, write some text
            if (distance < 0) {
                clearInterval(x);
                document.getElementById("days").innerText = "00";
                document.getElementById("hours").innerText = "00";
                document.getElementById("minutes").innerText = "00";
                document.getElementById("seconds").innerText = "00";
            }
        }, 1000);
    }
    
    // ==========================================
    // 6. ADD TO CALENDAR
    // ==========================================
    const addToCalendarBtn = document.getElementById('addToCalendarBtn');
    if (addToCalendarBtn) {
        // Tashkent is UTC+5. 18:00 local is 13:00 UTC.
        // Format: YYYYMMDDThhmmssZ
        const title = encodeURIComponent("Javohir va Malika Nikoh To'yi");
        const details = encodeURIComponent("Sizni baxtli kunimizda kutib qolamiz!");
        const location = encodeURIComponent("Versal Tantanalar Saroyi, Yunusobod tumani, Amir Temur ko'chasi 15-uy");
        const dates = "20260812T130000Z/20260812T180000Z";
        
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
                        const speed = el.getAttribute('data-speed') || 0.1;
                        const rect = el.getBoundingClientRect();
                        const elementCenter = rect.top + (rect.height / 2);
                        const viewportCenter = window.innerHeight / 2;
                        
                        // Only apply if the element is near the viewport
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
    // 8. RSVP FORM SUBMISSION
    // ==========================================
    const rsvpForm = document.getElementById('rsvpForm');
    const rsvpSuccess = document.getElementById('rsvpSuccess');
    
    if (rsvpForm && rsvpSuccess) {
        rsvpForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Fade out form
            rsvpForm.style.opacity = '0';
            rsvpForm.style.pointerEvents = 'none';
            
            // Show simple success popup
            setTimeout(() => {
                rsvpSuccess.classList.remove('hidden');
            }, 300);
        });
    }
});


if (window.TaklivoEngine) { window.TaklivoEngine.init({ isCatalogDemo: true }); }
