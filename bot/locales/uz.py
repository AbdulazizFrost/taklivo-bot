"""
O‘zbekcha lokalizatsiya TAKLIVO boti uchun.
"""

TEXTS = {
    # Umumiy
    "btn_back": "⬅️ Orqaga",
    "btn_cancel": "❌ Bekor qilish",
    "btn_main_menu": "🏠 Asosiy menyu",
    "cancelled": "❌ Amal bekor qilindi.",
    "select_language": "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
    "language_selected": "🇺🇿 O‘zbek tili tanlandi.",

    # Asosiy menyu
    "main_menu_title": (
        "💍 <b>TAKLIVO</b>\n\n"
        "<b>Nikoh to‘yi, Tug‘ilgan kun / Yubiley yoki Sunnat to‘yi</b> uchun bir necha daqiqada zamonaviy onlayn taklifnoma yarating!\n\n"
        "✨ Nafis interaktiv dizayn\n"
        "📱 Barcha smartfonlarda qulay ochiladi\n"
        "💌 Mehmonlar uchun RSVP so‘rovnomasi\n"
        "📍 Manzilga interaktiv xarita va lokatsiya\n"
        "🎵 Sevimli fon musiqangiz\n"
        "📸 Fotogalereya va taymer\n\n"
        "Nima qilmoqchisiz?"
    ),
    "btn_create_invitation": "✨ Taklifnoma yaratish",
    "btn_portfolio": "🎨 Dizaynlar katalogi",
    "btn_pricing": "💰 Funksiyalar narxlari",
    "btn_my_orders": "📦 Mening buyurtmalarim",
    "btn_faq": "❓ Ko‘p beriladigan savollar",
    "btn_referral": "🎁 Do‘stlarni taklif qilish",
    "btn_about": "ℹ️ Xizmat haqida",
    "btn_instagram": "📸 Bizning Instagram",
    "btn_change_language": "🌐 Tilni o‘zgartirish",

    # Portfolio va namunalar
    "portfolio_title": (
        "🎨 <b>TAKLIVO tayyor dizaynlar katalogi</b>\n\n"
        "Namunani ko‘rish va ma’lumot olish uchun quyidagi dizaynlardan birini tanlang:"
    ),
    "btn_demo_link": "🌐 Namunani ko‘rish",
    "btn_choose_template": "✨ Tanlash va buyurtma berish",

    # Muvaffaqiyat va xatoliklar
    "cancel_success": "❌ Amal bekor qilindi. Siz asosiy menyudasiz.",
    "err_text_too_long": "⚠️ <b>Matn juda uzun!</b> Iltimos, qisqaroq yozing (maksimal {max_len} ta belgi).",
    "order_paid_bonuses_success": (
        "🎉 <b>#{order_id}-raqamli buyurtmangiz muvaffaqiyatli qabul qilindi va bonuslar orqali to‘landi!</b>\n\n"
        "Biz sizning shaxsiy veb-saytingizni tayyorlashga kirishdik ✨\n"
        "Sayt tayyor bo‘lishi bilan sizga tekshirish uchun havola yuboramiz!"
    ),

    # Xizmat haqida
    "about_text": (
        "ℹ️ <b>TAKLIVO xizmati haqida</b>\n\n"
        "<b>TAKLIVO</b> — barcha turdagi tantanalar uchun zamonaviy raqamli taklifnomalar servisi:\n"
        "💍 <b>Nikoh to‘ylari</b>\n"
        "🎂 <b>Tug‘ilgan kun va Yubileylar</b>\n"
        "✂️ <b>Sunnat to‘ylari (Xatna to‘y)</b>\n\n"
        "🌟 <b>Nega aynan biz:</b>\n"
        "• <b>Tezkor:</b> sayt 24 soat ichida tayyor bo‘ladi\n"
        "• <b>Faqat kerakli funksiyalarga to‘laysiz:</b> qulay konstruktor\n"
        "• <b>Zamonaviy va tejamkor:</b> havola Telegram, Instagram, WhatsApp orqali yuboriladi\n"
        "• <b>Mehmonlarga qulay:</b> 1 bosishda lokatsiya (Yandex / Google Maps), RSVP so‘rovnoma, dress-kod\n"
        "• <b>Individual:</b> sizning suratlaringiz, sevimli musiqangiz va shaxsiy matningiz\n\n"
        "📸 <b>Instagram:</b> <a href='https://www.instagram.com/wedding_websites_uzbekistan/'>@wedding_websites_uzbekistan</a>\n"
        "📞 <b>Bog‘lanish va aloqa:</b> @Abdulaziz5335"
    ),

    # Ko‘p beriladigan savollar (FAQ)
    "faq_title": "❓ <b>Ko‘p beriladigan savollar (FAQ)</b>\n\nQuyidagi savollardan birini tanlang:",
    "faq_q1": "⏱ Sayt qancha vaqtda tayyor bo‘ladi?",
    "faq_a1": "⏱ <b>Tayyorlanish muddati:</b>\nOdatda sayt to‘lov tasdiqlanganidan so‘ng 12–24 soat ichida to‘liq tayyor bo‘ladi. Agar shoshilinch bo‘lsa — @Abdulaziz5335 administratoriga yozing, eng qisqa vaqtda tayyorlab beramiz!",

    "faq_q2": "📱 Mehmonlarga qanday yuboriladi?",
    "faq_a2": "📱 <b>Mehmonlarga yuborish:</b>\nSizga tayyor nafis havola beriladi (masalan: <code>taklivo.uz/wedding/aziz-malika</code>). Uni Telegram, Instagram Direct, WhatsApp orqali yoki Stories/Bio-ga joylab osongina ulashishingiz mumkin!",

    "faq_q3": "🎵 Musiqa iPhone va Android-da qanday ishlaydi?",
    "faq_a3": "🎵 <b>Fon musiqasi:</b>\nSayt ochilganda chiroyli musiqa tugmasi chiqadi. Mehmon tugmani bosishi bilan musiqangiz yangraydi. Barcha iPhone (iOS) va Android smartfonlarida 100% ishlaydi!",

    "faq_q4": "✏️ Sayt tayyor bo‘lgach ma’lumotlarni o‘zgartirsa bo‘ladimi?",
    "faq_a4": "✏️ <b>Tuzatishlar kiritish:</b>\nAlbatta! Sayt tayyor bo‘lganda sizga tekshirish uchun yuboriladi. «O‘zgartirish kiritish» tugmasini bosib matn, sana, rasm yoki musiqani bepul tuzatishingiz mumkin.",

    "faq_q5": "💳 To‘lov qanday amalga oshiriladi?",
    "faq_a5": "💳 <b>To‘lov tartibi:</b>\nTo‘lov Uzcard yoki Humo kartasiga o‘tkazma orqali qabul qilinadi. To‘lovdan so‘ng chek (skrinshot) rasmini botga yuborasiz va buyurtmangiz darhol ishga olinadi.",

    # Do‘stlarni taklif qilish (Referral)
    "referral_title": (
        "🎁 <b>TAKLIVO HAMKORLIK DASTURI</b>\n\n"
        "Do‘stlaringizni taklif qiling va o‘zingizning taklifnomangiz uchun bonuslarga ega bo‘ling!\n\n"
        "🌟 <b>Har ikki tomon uchun foydali:</b>\n"
        "• <b>Siz olasiz:</b> do‘stingizning har bir buyurtmasi uchun <code>+{reward_bonus}</code>!\n"
        "• <b>Do‘stingiz oladi:</b> ilk buyurtmasi uchun <code>{welcome_bonus}</code> chegirma!\n"
        "• <b>1 bonus = 1 so‘m</b> — to‘plangan bonuslar bilan o‘z saytingiz narxini 100% gacha to‘lashingiz mumkin.\n\n"
        "💰 <b>Sizning bonus balansingiz:</b> <b>{bonus_balance}</b>\n\n"
        "📊 <b>Sizning statistikangiz:</b>\n"
        "• Taklif qilingan do‘stlar: <b>{invited_count}</b> ta\n"
        "• Rasmiylashtirilgan buyurtmalar: <b>{orders_count}</b> ta\n\n"
        "🔗 <b>Taklif qilish havolangiz:</b>\n"
        "<code>{referral_link}</code>\n\n"
        "📋 <b>Do‘stingizga yuborish uchun tayyor matn</b> <i>(nusxalash uchun bosing)</i>:\n"
        "<code>💍 Salom! Agar sizda to‘y, tug‘ilgan kun yoki sunnat to‘y bo‘layotgan bo‘lsa — TAKLIVO xizmatini tavsiya qilaman! Ushbu havola orqali o‘tib 10 000 so‘m chegirmaga ega bo‘ling: {referral_link}</code>"
    ),
    "btn_share_ref": "📲 Telegram orqali ulashish",

    # Promokodlar
    "btn_enter_promo": "🎟 Promokodni kiritish",
    "prompt_promocode": "🎟 <b>Promokodingizni kiriting:</b>\n\n<i>(masalan: OQSAROY2026)</i>",
    "promo_applied_percent": "✅ <b>Promokod faollashtirildi!</b> Chegirma: <b>{discount}%</b> (-{amount})",
    "promo_applied_amount": "✅ <b>Promokod faollashtirildi!</b> Chegirma: -<b>{amount}</b>",
    "err_invalid_promo": "⚠️ <b>Noto‘g‘ri promokod!</b> Kod to‘g‘riligini yoki amal qilish muddatini tekshiring.",

    # Narxlar
    "pricing_title": (
        "💰 <b>TAKLIVO narxlari va imkoniyatlari</b>\n\n"
        "Siz faqat o‘zingizga kerakli bo‘lgan funksiyalarga to‘laysiz:\n\n"
        "🔹 <b>Asosiy taklifnoma:</b> {base_price}\n"
        "<i>(tanlangan dizayn, ismlar, sana, vaqt, manzil va aloqa ma’lumotlarini o‘z ichiga oladi)</i>\n\n"
        "<b>Qo‘shimcha bloklar (ixtiyoriy):</b>\n"
        "• ⏱ Ortga hisoblash taymeri: +{timer_price}\n"
        "• 💌 Mehmonlar uchun RSVP so‘rovnomasi: +{rsvp_price}\n"
        "• 📍 Interaktiv xarita: +{map_price}\n"
        "• 📸 Fotogalereya (10 tagacha rasm): +{gallery_price}\n"
        "• 🎵 Fon musiqasi: +{music_price}\n"
        "• 👗 Dress-kod ranglar palitrasi: +{dresscode_price}\n"
        "• 🗓 Kun tartibi / dasturi: +{schedule_price}\n"
        "• 🌐 Ikkinchi til (UZ/RU): +{second_language_price}"
    ),

    # Buyurtma konstruktori (FSM)
    "step_event_type": "🎉 <b>1-qadam (8 tadan): Tantanangiz turini tanlang</b>\n\nQaysi bayram uchun onlayn taklifnoma yaratmoqchisiz?",
    "event_wedding": "💍 Nikoh to‘yi",
    "event_birthday": "🎂 Tug‘ilgan kun / Yubiley",
    "event_sunnat": "✂️ Sunnat to‘yi (Xatna to‘y)",

    "step_template": "🎨 <b>2-qadam (8 tadan): Taklifnoma uslubini tanlang</b>\n\nO‘zingizga ma’qul kelgan dizaynni bosing:",
    "step_options": (
        "⚙️ <b>3-qadam (8 tadan): Saytingiz uchun kerakli funksiyalarni tanlang</b>\n\n"
        "Tugmalarni bosish orqali kerakli bloklarni yoqing (🟢) yoki o‘chiring (⚪️):\n\n"
        "• Asosiy taklifnoma: <b>{base_price}</b>\n"
        "• Qo‘shimcha funksiyalar: <b>+{extra_price}</b>\n"
        "────────────────\n"
        "💰 <b>JAMI TO‘LOV: {total_price}</b>"
    ),
    "btn_continue": "➡️ Davom etish",
    "option_timer": "⏱ Ortga hisoblash taymeri",
    "option_rsvp": "💌 RSVP so‘rovnoma",
    "option_map": "📍 Xarita lokatsiyasi",
    "option_music": "🎵 Fon musiqasi",
    "option_gallery": "📸 Fotogalereya",
    "option_dresscode": "👗 Dress-kod",
    "option_schedule": "🗓 Kun tartibi",
    "option_second_language": "🌐 Ikkinchi til",

    # Ma'lumot kiritish: Nikoh to'yi
    "step_bride_name": "👰 <b>4.1-qadam: Kelinning ismini kiriting</b>\n\n<i>Masalan: Malika yoki Malikaxon</i>",
    "step_groom_name": "🤵 <b>4.2-qadam: Kuyovning ismini kiriting</b>\n\n<i>Masalan: Aziz yoki Azizbek</i>",

    # Ma'lumot kiritish: Tug'ilgan kun
    "step_birthday_name": "🎂 <b>4.1-qadam: Tug‘ilgan kun sohibi yoki yubilyar ismini kiriting</b>\n\n<i>Masalan: Azizbek yoki Lola</i>",
    "step_birthday_age": "🎉 <b>4.2-qadam: Yoshi yoki yubiley sanasini kiriting (yoki o‘tkazib yuborish uchun «-» yozing)</b>\n\n<i>Masalan: 18 yosh, 25 yosh yoki 50 yillik yubiley</i>",

    # Ma'lumot kiritish: Sunnat to'y
    "step_sunnat_child_name": "👦 <b>4.1-qadam: Tantananing bosh qahramoni (bolaning) ismini kiriting</b>\n\n<i>Masalan: Muhammadali yoki Behruzbek</i>",
    "step_sunnat_parents_name": "👨‍👩‍👦 <b>4.2-qadam: Ota-onasining yoki to‘y egalarining ismlarini kiriting</b>\n\n<i>Masalan: Alisher va Nigora yoki Karimovlar oilasi</i>",

    # Umumiy maydonlar
    "step_date": (
        "📅 <b>5.1-qadam: Tantananing sanasini kiriting</b>\n\n"
        "<i>Format: KK.OO.YYYY (masalan, 15.09.2026)</i>"
    ),
    "err_invalid_date": "⚠️ <b>Noto‘g‘ri sana!</b> Iltimos, sanani <b>KK.OO.YYYY</b> formatida kiriting (masalan, <code>15.09.2026</code>).",

    "step_time": "🕐 <b>5.2-qadam: Tantananing boshlanish vaqtini kiriting</b>\n\n<i>Format: SS:DD (masalan, 18:00)</i>",
    "err_invalid_time": "⚠️ <b>Noto‘g‘ri vaqt!</b> Vaqtni <b>SS:DD</b> formatida kiriting (masalan, <code>18:00</code>).",

    "step_venue": "🏰 <b>6.1-qadam: To‘yxona / restoran / kafe nomini kiriting</b>\n\n<i>Masalan: «Oqsaroy» to‘yxonasi</i>",
    "step_address": "📍 <b>6.2-qadam: Manzil yoki mo‘ljalni kiriting</b>\n\n<i>Masalan: Toshkent sh., Navoiy ko‘chasi, 15-uy</i>",
    "step_phone": "📞 <b>6.3-qadam: Bog‘lanish uchun telefon raqamingizni kiriting</b>\n\n<i>Masalan: +998901234567</i>",
    "err_invalid_phone": "⚠️ <b>Noto‘g‘ri telefon raqami!</b> Xalqaro formatda kiriting (masalan, <code>+998901234567</code>).",

    # Media: Galereya va Musiqa
    "step_gallery_upload": (
        "📸 <b>7-qadam: Galereya uchun rasmlar</b>\n\n"
        "1 tadan 10 tagacha sifatli suratlarni yuboring.\n\n"
        "Yuklandi: <b>{count}/10</b>"
    ),
    "btn_add_more_photos": "➕ Yana rasm yuklash",
    "btn_photos_done": "✅ Rasmlar yuklashni yakunlash",
    "btn_skip_media": "⏩ O‘tkazib yuborish",
    "photo_received": "📸 Rasm qabul qilindi! Jami: <b>{count}/10</b>",
    "photo_limit_reached": "⚠️ 10 ta rasm limiti to‘ldi. «Rasmlar yuklashni yakunlash» tugmasini bosing.",
    "err_not_photo": "⚠️ Iltimos, aynan fotosurat (rasm) yuboring.",

    "step_music_upload": (
        "🎵 <b>8-qadam: Fon musiqasi</b>\n\n"
        "Saytda yangraydigan audio faylni (MP3) yuboring yoki «O‘tkazib yuborish» tugmasini bosing."
    ),
    "music_received": "🎵 Musiqa muvaffaqiyatli yuklandi: <b>{filename}</b>",
    "err_not_music": "⚠️ Iltimos, MP3 formatidagi audio fayl yuboring.",

    # Buyurtma ko‘rinishi (preview)
    "preview_title": (
        "✨ <b>SIZNING BUYURTMANGIZ #{order_id} ({event_title})</b>\n\n"
        "{hero_info}\n\n"
        "📅 <b>Sana:</b> {wedding_date}\n"
        "🕐 <b>Vaqt:</b> {wedding_time}\n"
        "🏰 <b>To‘yxona:</b> {venue}\n"
        "📍 <b>Manzil:</b> {address}\n"
        "📞 <b>Telefon:</b> {phone}\n\n"
        "🎨 <b>Dizayn:</b> {template_name}\n\n"
        "<b>Tanlangan funksiyalar:</b>\n"
        "{features_list}\n\n"
        "📸 <b>Rasmlar soni:</b> {photos_count}\n"
        "🎵 <b>Musiqa:</b> {music_status}\n\n"
        "{promo_line}"
        "💰 <b>JAMI TO‘LOV SUMMASI:</b>\n"
        "<b>{total_price}</b>"
    ),
    "btn_confirm_order": "✅ Barchasi to‘g‘ri, to‘lovga o‘tish",
    "btn_edit_order": "✏️ Ma’lumotlarni o‘zgartirish",

    # To‘lov
    "payment_screen": (
        "💳 <b>BUYURTMA TO‘LOVI #{order_id}</b>\n\n"
        "To‘lov summasi: <b>{total_price}</b>\n\n"
        "<b>To‘lov rekvizitlari:</b>\n"
        "{payment_details}\n\n"
        "⚠️ <i>To‘lovni amalga oshirgandan so‘ng, chek (skrinshot) rasmini shu yerga yuboring.</i>"
    ),
    "receipt_received": (
        "✅ <b>To‘lov cheki qabul qilindi!</b>\n\n"
        "Buyurtmangiz <b>#{order_id}</b> administrator tekshiruviga yuborildi.\n"
        "Tekshirish odatda 10–30 daqiqa vaqt oladi.\n\n"
        "To‘lov tasdiqlanishi bilan sizga xabar keladi va biz saytingizni tayyorlashni boshlaymiz! ✨"
    ),
    "err_not_receipt": "⚠️ Iltimos, to‘lov chekining fotosurati yoki skrinshotini yuboring.",

    # Statuslar va Mening buyurtmalarim
    "my_orders_title": "📦 <b>Sizning buyurtmalaringiz:</b>",
    "no_orders": "Sizda hali buyurtmalar mavjud emas. Boshlash uchun «✨ Taklifnoma yaratish» tugmasini bosing!",
    "order_card": (
        "✨ <b>Buyurtma #{order_id} ({event_title})</b>\n"
        "{hero_info}\n"
        "📅 {wedding_date} | 🎨 {template_name}\n"
        "📊 Holati: <b>{status_badge}</b>\n"
        "💰 Summa: {total_price}\n"
    ),
    "btn_order_details": "📋 Buyurtma #{order_id} haqida batafsil",
    "btn_open_website": "🌐 Taklifnomani ochish",
    "btn_request_revisions": "✏️ O‘zgartirish kiritish",
    "btn_approve_website": "✅ Barchasi ajoyib!",

    # O‘zgartirishlar
    "prompt_revisions": "✏️ <b>Taklifnomada nimalarni o‘zgartirish kerakligini yozing:</b>\n\n(matn, rasm, musiqa, sana, manzil va h.k.)",
    "revisions_sent": "✅ <b>O‘zgartirishlar dizaynerga yuborildi!</b> Tez orada tuzatishlar kiritiladi.",
    "website_approved": "🎉 <b>Tabriklaymiz!</b> Sayt sizga ma’qul kelganidan xursandmiz. Baxtli va yorqin bayram tilaymiz! ❤️",

    # Mijozga bildirishnomalar
    "notify_payment_confirmed": (
        "✅ <b>To‘lov muvaffaqiyatli tasdiqlandi!</b>\n\n"
        "Buyurtmangiz <b>#{order_id}</b> ishga qabul qilindi.\n"
        "Biz sizning shaxsiy veb-saytingizni tayyorlashga kirishdik ✨"
    ),
    "notify_payment_rejected": (
        "❌ <b>#{order_id}-raqamli buyurtma to‘lovi tasdiqlanmadi.</b>\n\n"
        "Sabab: to‘lov chekini tekshirib bo‘lmadi.\n"
        "Iltimos, haqiqiy chekni yuboring yoki qo‘llab-quvvatlash bilan bog‘laning: @Abdulaziz5335."
    ),
    "notify_website_ready": (
        "🎉 <b>SIZNING TAKLIFNOMANGIZ TAYYOR!</b>\n\n"
        "<b>{hero_title} ✨</b>\n\n"
        "Biz sizning shaxsiy onlayn taklifnomangizni tayyorladik.\n"
        "Iltimos, ochib ko‘rib barcha ma’lumotlarni tekshiring:\n\n"
        "🔗 <a href='{website_url}'>{website_url}</a>\n\n"
        "Agar barchasi ma’qul bo‘lsa — «Barchasi ajoyib» tugmasini bosing. Agar tuzatishlar kerak bo‘lsa — «O‘zgartirish kiritish» tugmasini bosing."
    ),

    # Havola orqali maxsus dizayn
    "btn_custom_template": "🌐 O‘z namunangiz (havola orqali)",
    "step_reference_url": (
        "🌐 <b>2.1-qadam: O‘zingizga yoqqan sayt havolasini yuboring</b>\n\n"
        "Internetda sizga yoqqan istalgan taklifnoma saytining havolasini (linkini) yuboring. "
        "Biz aynan shunday dizayn, animatsiyalar va uslubda siz uchun maxsus taklifnoma yaratamiz! ✨\n\n"
        "<i>Masalan: https://taklivo.uz/demo/floral yoki boshqa veb-havola</i>"
    ),
    "err_invalid_url": "⚠️ <b>Noto‘g‘ri havola!</b> Iltimos, <code>http://</code> yoki <code>https://</code> bilan boshlanuvchi to‘liq havolani yuboring.",
    "reference_url_received": "✅ <b>Havola muvaffaqiyatli qabul qilindi!</b>\n\nEndi saytingiz uchun kerakli funksiyalarni tanlang:",

    # Holatlar (badge)
    "status_NEW": "🆕 Yangi",
    "status_WAITING_PAYMENT": "💳 To‘lov kutilmoqda",
    "status_PAYMENT_REVIEW": "⏳ Chek tekshirilmoqda",
    "status_PAID": "✅ To‘landi",
    "status_IN_PROGRESS": "🔨 Dizayner ishlamoqda",
    "status_PREVIEW": "👀 Tekshirishga tayyor",
    "status_REVISION": "✏️ Tuzatish kiritilmoqda",
    "status_COMPLETED": "🎉 Yakunlandi",
    "status_CANCELLED": "❌ Bekor qilindi",
}
