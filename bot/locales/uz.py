"""
O‘zbekcha lokalizatsiya TAKLIVO boti uchun.
"""

TEXTS = {
    # Umumiy
    "btn_back": "⬅️ Orqaga",
    "btn_cancel": "❌ Bekor qilish",
    "btn_main_menu": "🏠 Asosiy menyu",
    "cancelled": "❌ Buyurtma bekor qilindi.",
    "select_language": "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
    "language_selected": "🇺🇿 O‘zbek tili tanlandi.",

    # Asosiy menyu
    "main_menu_title": (
        "💍 <b>TAKLIVO</b>\n\n"
        "To‘yingiz uchun bir necha daqiqada zamonaviy onlayn taklifnoma yarating.\n\n"
        "✨ Chiroyli moslashuvchan dizayn\n"
        "📱 Smartfonlarda qulay ochiladi\n"
        "💌 Mehmonlar uchun RSVP so‘rovnomasi\n"
        "📍 Manzilga interaktiv xarita\n"
        "🎵 Yoqimli fon musiqasi\n"
        "📸 Kelin-kuyov fotogalereyasi\n\n"
        "Nima qilmoqchisiz?"
    ),
    "btn_create_invitation": "💍 Taklifnoma yaratish",
    "btn_pricing": "💰 Funksiyalar narxlari",
    "btn_my_orders": "📦 Mening buyurtmalarim",
    "btn_about": "ℹ️ Xizmat haqida",
    "btn_instagram": "📸 Bizning Instagram",
    "btn_change_language": "🌐 Tilni o‘zgartirish",

    # Xizmat haqida
    "about_text": (
        "ℹ️ <b>TAKLIVO xizmati haqida</b>\n\n"
        "<b>TAKLIVO</b> — to‘y va maxsus tantanalar uchun zamonaviy raqamli taklifnomalar servisi.\n\n"
        "🌟 <b>Nega aynan biz:</b>\n"
        "• <b>Tezkor:</b> sayt 24 soat ichida tayyor bo‘ladi\n"
        "• <b>Faqat kerakli funksiyalarga to‘laysiz:</b> qulay konstruktor\n"
        "• <b>Zamonaviy va tejamkor:</b> havola Telegram, WhatsApp yoki Instagram orqali yuboriladi\n"
        "• <b>Mehmonlarga qulay:</b> bir bosishda lokatsiya, kelishini tasdiqlash (RSVP), dress-kod\n"
        "• <b>Individual:</b> sizning suratlaringiz, sevimli musiqangiz va sevgi tarixingiz\n\n"
        "📸 <b>Instagram:</b> <a href='https://www.instagram.com/wedding_websites_uzbekistan/'>@wedding_websites_uzbekistan</a>\n"
        "📞 <b>Bog‘lanish va aloqa:</b> @Abdulaziz5335"
    ),

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
        "• 🗓 To‘y kun tartibi: +{schedule_price}\n"
        "• 🌐 Ikkinchi til (UZ/RU): +{second_language_price}"
    ),

    # Buyurtma konstruktori (FSM)
    "step_template": "🎨 <b>1-qadam (7 tadan): Taklifnoma uslubini tanlang</b>\n\nO‘zingizga ma’qul kelgan dizaynni bosing:",
    "step_options": (
        "⚙️ <b>2-qadam (7 tadan): Saytingiz uchun kerakli funksiyalarni tanlang</b>\n\n"
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

    "step_bride_name": "👰 <b>3.1-qadam: Kelinning ismini kiriting</b>\n\n<i>Masalan: Malika yoki Malikaxon</i>",
    "step_groom_name": "🤵 <b>3.2-qadam: Kuyovning ismini kiriting</b>\n\n<i>Masalan: Aziz yoki Azizbek</i>",
    "step_date": (
        "📅 <b>4.1-qadam: To‘y sanasini kiriting</b>\n\n"
        "<i>Format: KK.OO.YYYY (masalan, 15.09.2026)</i>"
    ),
    "err_invalid_date": "⚠️ <b>Noto‘g‘ri sana!</b> Iltimos, sanani <b>KK.OO.YYYY</b> formatida kiriting (masalan, <code>15.09.2026</code>).",

    "step_time": "🕐 <b>4.2-qadam: Tantananing boshlanish vaqtini kiriting</b>\n\n<i>Format: SS:DD (masalan, 18:00)</i>",
    "err_invalid_time": "⚠️ <b>Noto‘g‘ri vaqt!</b> Vaqtni <b>SS:DD</b> formatida kiriting (masalan, <code>18:00</code>).",

    "step_venue": "🏰 <b>5.1-qadam: To‘yxona / restoran nomini kiriting</b>\n\n<i>Masalan: «Oqsaroy» to‘yxonasi</i>",
    "step_address": "📍 <b>5.2-qadam: Manzil yoki mo‘ljalni kiriting</b>\n\n<i>Masalan: Toshkent sh., Navoiy ko‘chasi, 15-uy</i>",
    "step_phone": "📞 <b>5.3-qadam: Bog‘lanish uchun telefon raqamingizni kiriting</b>\n\n<i>Masalan: +998901234567</i>",
    "err_invalid_phone": "⚠️ <b>Noto‘g‘ri telefon raqami!</b> Xalqaro formatda kiriting (masalan, <code>+998901234567</code>).",

    # Media: Galereya va Musiqa
    "step_gallery_upload": (
        "📸 <b>6-qadam: Galereya uchun rasmlar</b>\n\n"
        "1 tadan 10 tagacha sifatli birgalikdagi suratlarni yuboring.\n\n"
        "Yuklandi: <b>{count}/10</b>"
    ),
    "btn_add_more_photos": "➕ Yana rasm yuklash",
    "btn_photos_done": "✅ Rasmlar yuklashni yakunlash",
    "btn_skip_media": "⏩ O‘tkazib yuborish",
    "photo_received": "📸 Rasm qabul qilindi! Jami: <b>{count}/10</b>",
    "photo_limit_reached": "⚠️ 10 ta rasm limiti to‘ldi. «Rasmlar yuklashni yakunlash» tugmasini bosing.",
    "err_not_photo": "⚠️ Iltimos, aynan fotosurat (rasm) yuboring.",

    "step_music_upload": (
        "🎵 <b>7-qadam: Fon musiqasi</b>\n\n"
        "Saytda yangraydigan audio faylni (MP3) yuboring yoki «O‘tkazib yuborish» tugmasini bosing."
    ),
    "music_received": "🎵 Musiqa muvaffaqiyatli yuklandi: <b>{filename}</b>",
    "err_not_music": "⚠️ Iltimos, MP3 formatidagi audio fayl yuboring.",

    # Buyurtma ko‘rinishi (preview)
    "preview_title": (
        "💍 <b>SIZNING BUYURTMANGIZ #{order_id}</b>\n\n"
        "👰 <b>Kelin:</b> {bride_name}\n"
        "🤵 <b>Kuyov:</b> {groom_name}\n\n"
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
        "To‘lov tasdiqlanishi bilan sizga xabar keladi va biz saytingizni tayyorlashni boshlaymiz! 💍"
    ),
    "err_not_receipt": "⚠️ Iltimos, to‘lov chekining fotosurati yoki skrinshotini yuboring.",

    # Statuslar va Mening buyurtmalarim
    "my_orders_title": "📦 <b>Sizning buyurtmalaringiz:</b>",
    "no_orders": "Sizda hali buyurtmalar mavjud emas. Boshlash uchun «💍 Taklifnoma yaratish» tugmasini bosing!",
    "order_card": (
        "💍 <b>Buyurtma #{order_id}</b>\n"
        "👰🤵 {bride_name} & {groom_name}\n"
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
    "website_approved": "🎉 <b>Tabriklaymiz!</b> Sayt sizga ma’qul kelganidan xursandmiz. Baxtli hayot va go‘zal to‘y tilaymiz! ❤️",

    # Mijozga bildirishnomalar
    "notify_payment_confirmed": (
        "✅ <b>To‘lov muvaffaqiyatli tasdiqlandi!</b>\n\n"
        "Buyurtmangiz <b>#{order_id}</b> ishga qabul qilindi.\n"
        "Biz sizning shaxsiy to‘y veb-saytingizni tayyorlashga kirishdik 💍"
    ),
    "notify_payment_rejected": (
        "❌ <b>#{order_id}-raqamli buyurtma to‘lovi tasdiqlanmadi.</b>\n\n"
        "Sabab: to‘lov chekini tekshirib bo‘lmadi.\n"
        "Iltimos, haqiqiy chekni yuboring yoki qo‘llab-quvvatlash bilan bog‘laning: @Abdulaziz5335."
    ),
    "notify_website_ready": (
        "🎉 <b>SIZNING TAKLIFNOMANGIZ TAYYOR!</b>\n\n"
        "<b>{bride_name} & {groom_name} 💍</b>\n\n"
        "Biz sizning shaxsiy onlayn taklifnomangizni tayyorladik.\n"
        "Iltimos, ochib ko‘rib barcha ma’lumotlarni tekshiring:\n\n"
        "🔗 <a href='{website_url}'>{website_url}</a>\n\n"
        "Agar barchasi ma’qul bo‘lsa — «Barchasi ajoyib» tugmasini bosing. Agar tuzatishlar kerak bo‘lsa — «O‘zgartirish kiritish» tugmasini bosing."
    ),

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
