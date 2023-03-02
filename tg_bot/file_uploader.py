"""
В данном модуле реализован загрузчик файлов из телеграм чата.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal
    from tg_bot.bot import TGBot

from Utils import config_loader as cfg_loader, exceptions as excs, cardinal_tools
from telebot.types import InlineKeyboardButton as Button
from tg_bot import utils, keyboards, CBT
from telebot import types
import logging
import os


logger = logging.getLogger("TGBot")


def check_file(tg: TGBot, msg: types.Message) -> bool:
    """
    Проверяет выгруженный файл. Чистит состояние пользователя. Отправляет сообщение в TG в зависимости от ошибки.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :return: True, если все ок, False, если файл проверку не прошел.
    """
    if not msg.document:
        tg.bot.send_message(msg.chat.id, "❌ Файл не обнаружен.")
        return False
    if not any((msg.document.file_name.endswith(".cfg"), msg.document.file_name.endswith(".txt"),
                msg.document.file_name.endswith(".py"))):
        tg.bot.send_message(msg.chat.id, "❌ Файл должен быть текстовым.")
        return False
    if msg.document.file_size >= 20971520:
        tg.bot.send_message(msg.chat.id, "❌ Размер файла не должен превышать 20МБ.")
        return False
    return True


def download_file(tg: TGBot, msg: types.Message, file_name: str = "temp_file.txt",
                  custom_path: str = "") -> bool:
    """
    Скачивает выгруженный файл и сохраняет его в папку storage/cache/.

    :param tg: экземпляр TG бота.

    :param msg: экземпляр сообщения.

    :param file_name: название сохраненного файла.

    :param custom_path: кастомный путь (если надо сохранить не в storage/cache/).

    :return: True, если все ок, False, при ошибке.
    """
    tg.bot.send_message(msg.chat.id, "⏬ Загружаю файл...")
    try:
        file_info = tg.bot.get_file(msg.document.file_id)
        file = tg.bot.download_file(file_info.file_path)
    except:
        tg.bot.send_message(msg.chat.id, "❌ Произошла ошибка при загрузке файла. Подробнее в файле "
                                         "<code>logs/log.log</code>.", parse_mode="HTML")
        logger.debug("------TRACEBACK------", exc_info=True)
        return False

    path = f"storage/cache/{file_name}" if not custom_path else os.path.join(custom_path, file_name)
    with open(path, "wb") as new_file:
        new_file.write(file)
    return True


def init_uploader(cardinal: Cardinal):
    tg = cardinal.telegram
    bot = tg.bot

    def act_upload_products_file(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Отправьте мне файл с товарами.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.UPLOAD_PRODUCTS_FILE)
        bot.answer_callback_query(c.id)

    def upload_products_file(m: types.Message):
        """
        Загружает файл с товарами.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m):
            return
        if not download_file(tg, m, m.document.file_name,
                             custom_path=f"storage/products"):
            return

        try:
            products_count = cardinal_tools.count_products(f"storage/products/{utils.escape(m.document.file_name)}")
        except:
            bot.send_message(m.chat.id,
                             "❌ Произошла ошибка при подсчете товаров. Подробнее в файле "
                             "<code>logs/log.log</code>.", parse_mode="HTML")
            logger.debug("------TRACEBACK------", exc_info=True)
            return

        file_number = os.listdir("storage/products").index(m.document.file_name)

        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("✏️ Редактировать файл", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_number}:0"))

        logger.info(f"Пользователь $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"загрузил в бота файл с товарами $YELLOWstorage/products/{m.document.file_name}$RESET.")

        bot.send_message(m.chat.id,
                         f"✅ Файл с товарами <code>storage/products/{m.document.file_name}</code> успешно загружен. "
                         f"Товаров в файле: <code>{products_count}.</code>",
                         parse_mode="HTML", reply_markup=keyboard)

    def act_upload_main_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Отправьте мне основной конфиг.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "upload_main_config")
        bot.answer_callback_query(c.id)

    def upload_main_config(m: types.Message):
        """
        Загружает и проверяет основной конфиг.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m):
            return
        if not download_file(tg, m, "temp_main.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Проверяю валидность файла...")
        try:
            new_config = cfg_loader.load_main_config("storage/cache/temp_main.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Произошла ошибка при обработке основного конфига: "
                                        f"<code>{utils.escape(str(e))}</code>", parse_mode="HTML")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                             "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                             parse_mode="HTML")
            return
        except:
            bot.send_message(m.chat.id,
                             "❌ Произошла ошибка при проверке конфига автовыдачи. Подробнее в файле "
                             "<code>logs/log.log</code>", parse_mode="HTML")
            logger.debug("------TRACEBACK------", exc_info=True)
            return

        cardinal.save_config(new_config, "configs/_main.cfg")
        logger.info(f"Пользователь $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"загрузил в бота основной конфиг.")
        bot.send_message(m.chat.id, "✅ Основной конфиг успешно загружен. \n"
                                    "Необходимо перезагрузить бота, что бы применить изменения. \n"
                                    "Любое изменение основного конфига через переключатели на ПУ отменит все изменения.")

    def act_upload_auto_response_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Отправьте мне конфиг автоответчика.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "upload_auto_response_config")
        bot.answer_callback_query(c.id)

    def upload_auto_response_config(m: types.Message):
        """
        Загружает, проверяет и устанавливает конфиг автовыдачи.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m):
            return
        if not download_file(tg, m, "temp_auto_response.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Проверяю валидность файла...")
        try:
            new_config = cfg_loader.load_auto_response_config("storage/cache/temp_auto_response.cfg")
            raw_new_config = cfg_loader.load_raw_auto_response_config("storage/cache/temp_auto_response.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Произошла ошибка при обработке конфига автоответчика: "
                                        f"<code>{utils.escape(str(e))}</code>", parse_mode="HTML")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                             "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                             parse_mode="HTML")
            return
        except:
            bot.send_message(m.chat.id,
                             "❌ Произошла ошибка при проверке конфига автоответчика. Подробнее в файле "
                             "<code>logs/log.log</code>", parse_mode="HTML")
            logger.debug("------TRACEBACK------", exc_info=True)
            return

        cardinal.RAW_AR_CFG, cardinal.AR_CFG = raw_new_config, new_config
        cardinal.save_config(cardinal.RAW_AR_CFG, "configs/auto_response.cfg")

        logger.info(f"Пользователь $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"загрузил в бота и установил конфиг автоответчика.")
        bot.send_message(m.chat.id, "✅ Конфиг автоответчика успешно применен.")

    def act_upload_auto_delivery_config(c: types.CallbackQuery):
        result = bot.send_message(c.message.chat.id, "Отправьте мне конфиг автовыдачи.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, "upload_auto_delivery_config")
        bot.answer_callback_query(c.id)

    def upload_auto_delivery_config(m: types.Message):
        """
        Загружает, проверяет и устанавливает конфиг автовыдачи.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_file(tg, m):
            return
        if not download_file(tg, m, "temp_auto_delivery.cfg"):
            return

        bot.send_message(m.chat.id, "🔁 Проверяю валидность файла...")
        try:
            new_config = cfg_loader.load_auto_delivery_config("storage/cache/temp_auto_delivery.cfg")
        except excs.ConfigParseError as e:
            bot.send_message(m.chat.id, f"❌ Произошла ошибка при обработке конфига автовыдачи: "
                                        f"<code>{utils.escape(str(e))}</code>", parse_mode="HTML")
            return
        except UnicodeDecodeError:
            bot.send_message(m.chat.id,
                             "Произошла ошибка при расшифровке <code>UTF-8</code>. Убедитесь, что кодировка "
                             "файла = <code>UTF-8</code>, а формат конца строк = <code>LF</code>.",
                             parse_mode="HTML")
            return
        except:
            bot.send_message(m.chat.id,
                             "❌ Произошла ошибка при проверке конфига автовыдачи. Подробнее в файле "
                             "<code>logs/log.log</code>", parse_mode="HTML")
            logger.debug("------TRACEBACK------", exc_info=True)
            return

        cardinal.AD_CFG = new_config
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        logger.info(f"Пользователь $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"загрузил в бота и установил конфиг автовыдачи.")
        bot.send_message(m.chat.id, "✅ Конфиг автовыдачи успешно применен.")

    def upload_plugin(m: types.Message):
        offset = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["offset"]
        if not check_file(tg, m):
            return
        if not download_file(tg, m, f"{utils.escape(m.document.file_name)}",
                             custom_path=f"plugins"):
            return

        logger.info(f"Пользователь $MAGENTA@{m.from_user.username} (id: {m.from_user.id})$RESET "
                    f"загрузил в бота плагин $YELLOWplugins/{m.document.file_name}$RESET.")

        keyboard = types.InlineKeyboardMarkup() \
            .add(Button("◀️Назад", callback_data=f"{CBT.PLUGINS_LIST}:{offset}"))
        bot.send_message(m.chat.id,
                         f"✅ Плагин <code>{utils.escape(m.document.file_name)}</code> успешно загружен.\n\n"
                         f"⚠️Чтобы плагин активировался, <u><b>перезагрузите FPC!</b></u> (/restart)",
                         parse_mode="HTML", reply_markup=keyboard)

    tg.cbq_handler(act_upload_products_file, lambda c: c.data == CBT.UPLOAD_PRODUCTS_FILE)
    tg.cbq_handler(act_upload_auto_response_config, lambda c: c.data == "upload_auto_response_config")
    tg.cbq_handler(act_upload_auto_delivery_config, lambda c: c.data == "upload_auto_delivery_config")
    tg.cbq_handler(act_upload_main_config, lambda c: c.data == "upload_main_config")

    tg.file_handler(CBT.UPLOAD_PRODUCTS_FILE, upload_products_file)
    tg.file_handler("upload_auto_response_config", upload_auto_response_config)
    tg.file_handler("upload_auto_delivery_config", upload_auto_delivery_config)
    tg.file_handler("upload_main_config", upload_main_config)
    tg.file_handler(CBT.UPLOAD_PLUGIN, upload_plugin)


BIND_TO_PRE_INIT = [init_uploader]
