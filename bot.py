import asyncio
import datetime
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType, ParseMode
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, ChatMemberUpdated, Message

import config
import engine
import storage
from keyboards import channel_menu, channels_menu, interval_menu, remove_confirm_menu

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

router = Router()

PROTO_LABELS = {"http": "HTTP", "https": "HTTPS", "socks4": "SOCKS4", "socks5": "SOCKS5"}
CREDIT_LINE = "𝗠َِ𝗢َِ𝗛َِ𝗔َ\n• 𝗠َِ𝗢َِ𝗛َِ𝗔َ | مــــووحــــا •\n@mouhamed_ma"


def is_bot_owner(user_id: int) -> bool:
    return user_id in config.OWNER_IDS


def format_stats(stats: dict | None) -> str:
    if not stats:
        return (
            "<blockquote>📭 لا توجد إحصائيات متاحة حتى الآن.</blockquote>"
            "\n<blockquote>🔄 استخدم زر «بدء الفحص» لجلب البيانات وتحديث النتائج.</blockquote>"
        )

    return (
        "<blockquote>📈 <b>ملخص آخر عملية فحص</b></blockquote>\n"
        f"<blockquote>🗓️ وقت التنفيذ: {stats['timestamp']}</blockquote>\n"
        f"<blockquote>📦 إجمالي المنشورات: <b>{stats['scraped']}</b></blockquote>\n"
        f"<blockquote>🟢 السليمة: <b>{stats['working']}</b></blockquote>\n"
        f"<blockquote>❌ الفاشلة: <b>{stats['failed']}</b></blockquote>"
    )


def build_proxy_file(working: list[dict]) -> BufferedInputFile:
    lines = [CREDIT_LINE, "", "-" * 20, ""]
    for p in working:
        lines.append(
            f"{p['proxy']} | {PROTO_LABELS.get(p['protocol'], p['protocol'])} | {p['country']} | {p['latency']}ms"
        )
    lines += ["", "-" * 20, "", CREDIT_LINE]

    data = "\n".join(lines).encode("utf-8")
    filename = f"proxies_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
    return BufferedInputFile(data, filename=filename)


async def publish_working_proxies(bot: Bot, channel_id: int, working: list[dict]) -> None:
    if not working:
        return

    if len(working) >= config.PUBLISH_BATCH_AS_FILE_THRESHOLD:
        file = build_proxy_file(working)
        await bot.send_document(
            channel_id,
            file,
            caption=(
                f"<blockquote>✅ عدد البروكسيات الشغالة: <b>{len(working)}</b></blockquote>\n"
                f"<blockquote>{CREDIT_LINE}</blockquote>"
            ),
        )
        return

    chunk_size = 15
    for i in range(0, len(working), chunk_size):
        chunk = working[i:i + chunk_size]
        lines = ["<blockquote>🟢 <b>قائمة البروكسيات الشغالة</b></blockquote>"]
        for p in chunk:
            lines.append(
                f"<blockquote><code>{p['proxy']}</code> | {PROTO_LABELS.get(p['protocol'], p['protocol'])} | {p['country']} | {p['latency']}ms</blockquote>"
            )
        lines.append(f"<blockquote>{CREDIT_LINE}</blockquote>")
        await bot.send_message(channel_id, "\n".join(lines))


async def run_scrape_and_publish(bot: Bot, channel_id: int, notify_chat_id: int | None = None) -> dict:
    async def notify(text: str) -> None:
        if not notify_chat_id:
            return
        try:
            await bot.send_message(notify_chat_id, text)
        except Exception:
            pass

    try:
        await notify("<blockquote>⏳ جاري تشغيل الذكي وجلب البروكسيات...</blockquote>")
        proxies_by_protocol, working = await engine.scrape_check_smart()
        total_scraped = sum(len(v) for v in proxies_by_protocol.values())

        await storage.save_run_result(channel_id, total_scraped, working)

        if working:
            await publish_working_proxies(bot, channel_id, working)
        else:
            await notify("<blockquote>⚠️ لم يتم العثور على أي بروكسي شغال في هذه الجولة.</blockquote>")

        stats = await storage.get_last_stats(channel_id)
        await notify(format_stats(stats))

        return {"scraped": total_scraped, "working": len(working)}

    except Exception as e:
        logger.exception(f"خطأ أثناء عملية الجلب والفحص للقناة {channel_id}: {e}")
        await notify(f"<blockquote>❌ حدث خطأ أثناء التنفيذ: <b>{e}</b></blockquote>")
        return {"scraped": 0, "working": 0}


async def auto_loop(bot: Bot) -> None:
    while True:
        try:
            due_channels = await storage.get_due_channels()
            for channel_id in due_channels:
                asyncio.create_task(run_scrape_and_publish(bot, channel_id))
        except Exception as e:
            logger.exception(f"خطأ في الحلقة التلقائية: {e}")
        await asyncio.sleep(config.AUTO_LOOP_TICK_MINUTES * 60)


async def _get_single_channel(user_id: int) -> dict | None:
    channels = await storage.get_channels_by_owner(user_id)
    return channels[0] if len(channels) == 1 else None


@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated) -> None:
    if event.chat.type != ChatType.CHANNEL:
        return

    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status
    actor = event.from_user

    if new_status == ChatMemberStatus.ADMINISTRATOR and old_status != ChatMemberStatus.ADMINISTRATOR:
        if not actor:
            return

        existing = await storage.get_channel(event.chat.id)
        if not existing and config.MAX_CHANNELS_PER_USER > 0:
            count = await storage.count_channels_by_owner(actor.id)
            if count >= config.MAX_CHANNELS_PER_USER:
                try:
                    await event.bot.send_message(
                        actor.id,
                        f"<blockquote>⚠️ لقد تجاوزت الحد الأقصى المسموح به من القنوات (<b>{config.MAX_CHANNELS_PER_USER}</b>).</blockquote>",
                    )
                except Exception:
                    pass
                return

        await storage.register_channel(event.chat.id, actor.id, event.chat.title or str(event.chat.id))
        try:
            await event.bot.send_message(
                actor.id,
                (
                    f"<blockquote>✅ تم ربط قناة «<b>{event.chat.title}</b>» بحسابك بنجاح.</blockquote>\n"
                    f"<blockquote>📌 استخدم <b>/start</b> لإدارتها والتحكم فيها.</blockquote>"
                ),
            )
        except Exception:
            logger.info(f"تعذر مراسلة المستخدم {actor.id} مباشرة")

    elif new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        await storage.deactivate_channel(event.chat.id)


@router.message(Command("start"))
@router.message(Command("channels"))
async def cmd_start(message: Message) -> None:
    channels = await storage.get_channels_by_owner(message.from_user.id)
    if not channels:
        await message.answer(
            "<blockquote>🐺 <b>مرحباً بك في بوت 𝗠َِ𝗢َِ𝗛َِ𝗔َ 𝗣َِ𝗥َِ𝗢َِ𝗫َِ𝗬َِ لإدارة البروكسيات</b></blockquote>\n"
            "<blockquote>📭 لا توجد أي قناة مرتبطة بحسابك بعد.</blockquote>\n"
            "<blockquote>📌 لربط قناتك تلقائياً:</blockquote>\n"
            "<blockquote>1️⃣ أضف هذا البوت كمشرف (Admin) في قناتك مع صلاحية نشر الرسائل.</blockquote>\n"
            "<blockquote>2️⃣ سيتم تسجيل القناة على حسابك فوراً، وستصلك رسالة تأكيد هنا.</blockquote>\n"
            "<blockquote>3️⃣ بعد ذلك، استخدم <b>/start</b> لإدارة القناة عبر الأزرار.</blockquote>"
        )
        return

    await message.answer(
        "<blockquote>🐺 <b>قنواتك المرتبطة</b></blockquote>\n"
        "<blockquote>📌 اختر قناة لإدارتها:</blockquote>",
        reply_markup=channels_menu(channels),
    )


@router.message(Command("scrape"))
async def cmd_scrape(message: Message) -> None:
    channel = await _get_single_channel(message.from_user.id)
    if not channel:
        await message.answer(
            "<blockquote>📌 استخدم <b>/start</b> لاختيار القناة.</blockquote>\n"
            "<blockquote>⚠️ إما أنك مرتبط بأكثر من قناة، أو لا توجد قناة مرتبطة بعد.</blockquote>"
        )
        return
    await message.answer("<blockquote>⏳ جاري تنفيذ عملية الفحص في الخلفية...</blockquote>")
    asyncio.create_task(run_scrape_and_publish(message.bot, channel["channel_id"], notify_chat_id=message.chat.id))


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    channel = await _get_single_channel(message.from_user.id)
    if not channel:
        await message.answer("<blockquote>📌 استخدم <b>/start</b> لاختيار القناة.</blockquote>")
        return
    stats = await storage.get_last_stats(channel["channel_id"])
    await message.answer(format_stats(stats))


@router.message(Command("auto_on"))
async def cmd_auto_on(message: Message) -> None:
    channel = await _get_single_channel(message.from_user.id)
    if not channel:
        await message.answer("<blockquote>📌 استخدم <b>/start</b> لاختيار القناة.</blockquote>")
        return
    await storage.set_channel_auto(channel["channel_id"], True)
    await message.answer(
        f"<blockquote>✅ تم تفعيل التشغيل التلقائي لهذه القناة.</blockquote>\n"
        f"<blockquote>⏱ الفاصل الزمني: <b>{channel['interval_hours']:g}</b> ساعة.</blockquote>"
    )


@router.message(Command("auto_off"))
async def cmd_auto_off(message: Message) -> None:
    channel = await _get_single_channel(message.from_user.id)
    if not channel:
        await message.answer("<blockquote>📌 استخدم <b>/start</b> لاختيار القناة.</blockquote>")
        return
    await storage.set_channel_auto(channel["channel_id"], False)
    await message.answer("<blockquote>🔴 تم إيقاف التشغيل التلقائي لهذه القناة.</blockquote>")


@router.callback_query(F.data == "back_channels")
async def cb_back_channels(callback: CallbackQuery) -> None:
    channels = await storage.get_channels_by_owner(callback.from_user.id)
    if not channels:
        await callback.message.edit_text("<blockquote>📭 لا توجد أي قناة مرتبطة بحسابك حالياً.</blockquote>")
        await callback.answer()
        return
    await callback.message.edit_text(
        "<blockquote>🐺 <b>قنواتك المرتبطة</b></blockquote>\n"
        "<blockquote>📌 اختر قناة لإدارتها:</blockquote>",
        reply_markup=channels_menu(channels),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ch:"))
async def cb_channel_actions(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    channel_id = int(parts[1])
    action = parts[2]

    channel = await storage.get_channel(channel_id)
    if not channel or (channel["owner_id"] != callback.from_user.id and not is_bot_owner(callback.from_user.id)):
        await callback.answer("⛔️ لا تملك صلاحية الوصول إلى هذه القناة.", show_alert=True)
        return

    if action == "menu":
        await callback.message.edit_text(
            f"<blockquote>⚙️ إدارة قناة: <b>{channel['title']}</b></blockquote>",
            reply_markup=channel_menu(channel),
        )
        await callback.answer()

    elif action == "scrape":
        await callback.answer("⏳ جاري تنفيذ عملية الفحص في الخلفية...")
        asyncio.create_task(run_scrape_and_publish(callback.bot, channel_id, notify_chat_id=callback.from_user.id))

    elif action == "stats":
        stats = await storage.get_last_stats(channel_id)
        await callback.message.answer(format_stats(stats))
        await callback.answer()

    elif action in ("auto_on", "auto_off"):
        await storage.set_channel_auto(channel_id, action == "auto_on")
        channel = await storage.get_channel(channel_id)
        await callback.message.edit_reply_markup(reply_markup=channel_menu(channel))
        await callback.answer(
            "<blockquote>✅ تم تفعيل التشغيل التلقائي لهذه القناة.</blockquote>"
            if action == "auto_on"
            else "<blockquote>🔴 تم إيقاف التشغيل التلقائي لهذه القناة.</blockquote>"
        )

    elif action == "interval":
        await callback.message.edit_text(
            "<blockquote>⏱ اختر الفاصل الزمني بين كل عملية جلب تلقائية:</blockquote>",
            reply_markup=interval_menu(channel_id),
        )
        await callback.answer()

    elif action == "interval_set":
        hours = float(parts[3])
        await storage.set_channel_interval(channel_id, hours)
        channel = await storage.get_channel(channel_id)
        await callback.message.edit_text(
            f"<blockquote>⚙️ إدارة قناة: <b>{channel['title']}</b></blockquote>",
            reply_markup=channel_menu(channel),
        )
        await callback.answer(f"<blockquote>✅ تم ضبط الفاصل الزمني على <b>{hours:g}</b> ساعة.</blockquote>")

    elif action == "last_list":
        working = await storage.get_working_proxies(channel_id)
        if not working:
            await callback.answer("<blockquote>📭 لا توجد قائمة بروكسيات محفوظة بعد.</blockquote>", show_alert=True)
            return
        file = build_proxy_file(working)
        await callback.message.answer_document(
            file,
            caption=f"<blockquote>📁 آخر قائمة بروكسيات شغالة — <b>{len(working)}</b> بروكسي</blockquote>",
        )
        await callback.answer()

    elif action == "remove":
        await callback.message.edit_text(
            f"<blockquote>⚠️ هل تريد فعلاً إلغاء ربط قناة «<b>{channel['title']}</b>» من حسابك؟</blockquote>",
            reply_markup=remove_confirm_menu(channel_id),
        )
        await callback.answer()

    elif action == "remove_confirm":
        await storage.remove_channel(channel_id, callback.from_user.id)
        await callback.message.edit_text(
            "<blockquote>🗑 تم إلغاء ربط القناة بنجاح.</blockquote>\n"
            "<blockquote>🔄 لإعادة ربطها، أعد إضافة البوت كمشرف في القناة.</blockquote>"
        )
        await callback.answer()


async def main() -> None:
    await storage.init_db()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(auto_loop(bot))

    logger.info("البوت يعمل الآن بشكل مستقل ويقبل ربط أي قناة تلقائياً...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())