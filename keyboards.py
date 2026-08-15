from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def channels_menu(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{'🟢' if c['auto_enabled'] else '⚪️'} {c['title']}",
            callback_data=f"ch:{c['channel_id']}:menu", style="success")]
        for c in channels
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_menu(channel: dict) -> InlineKeyboardMarkup:
    cid = channel["channel_id"]
    auto_label = "إيقاف التلقائي 🔴" if channel["auto_enabled"] else "تفعيل التلقائي 🟢"
    auto_action = "auto_off" if channel["auto_enabled"] else "auto_on"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 جلب وفحص الآن", callback_data=f"ch:{cid}:scrape", style="success")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data=f"ch:{cid}:stats", style="primary")],
        [InlineKeyboardButton(text=auto_label, callback_data=f"ch:{cid}:{auto_action}", style="danger")],
        [InlineKeyboardButton(
            text=f"⏱ الفاصل الزمني: {channel['interval_hours']:g} ساعة",
            callback_data=f"ch:{cid}:interval", style="success")],
        [InlineKeyboardButton(text="📁 آخر قائمة شغالة", callback_data=f"ch:{cid}:last_list", style="danger")],
        [InlineKeyboardButton(text="🗑 إلغاء ربط القناة", callback_data=f"ch:{cid}:remove", style="primary")],
        [InlineKeyboardButton(text="⬅️ رجوع لقنواتي", callback_data="back_channels", style="success")],
    ])


def interval_menu(channel_id: int) -> InlineKeyboardMarkup:
    hours = [1, 2, 3, 6, 12, 24]
    buttons = [
        InlineKeyboardButton(text=f"{h} ساعة", callback_data=f"ch:{channel_id}:interval_set:{h}", style="success")
        for h in hours
    ]
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data=f"ch:{channel_id}:menu", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def remove_confirm_menu(channel_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ نعم، إلغاء الربط", callback_data=f"ch:{channel_id}:remove_confirm", style="success"),
            InlineKeyboardButton(text="❌ تراجع", callback_data=f"ch:{channel_id}:menu", style="primary"),
        ],
    ])
