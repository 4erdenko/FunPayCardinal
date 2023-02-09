"""
В данном модуле описаны функции для ПУ конфига авто-выдачи.
Модуль реализован в виде плагина.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

from tg_bot import utils, keyboards, CBT
from telebot.types import InlineKeyboardButton as Button
from telebot import types

from Utils import cardinal_tools

import traceback
import itertools
import random
import string
import logging
import os


logger = logging.getLogger("TGBot")


def init_auto_delivery_cp(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot

    def check_ad_lot_exists(lot_index: int, message_obj: types.Message, reply_mode: bool = True) -> bool:
        """
        Проверяет, существует ли лот с авто-выдачей с переданным индексом.
        Если лота не существует - отправляет сообщение с кнопкой обновления списка лотов с авто-выдачей.

        :param lot_index: числовой индекс лота.

        :param message_obj: экземпляр Telegram-сообщения.

        :param reply_mode: режим ответа на переданное сообщение.
        Если True - отвечает на переданное сообщение,
        если False - редактирует переданное сообщение.

        :return: True, если лот существует, False, если нет.
        """
        if lot_index > len(cardinal.AD_CFG.sections()) - 1:
            update_button = types.InlineKeyboardMarkup().add(Button("🔄 Обновить",
                                                                    callback_data=f"{CBT.AD_LOTS_LIST}:0"))
            if reply_mode:
                bot.reply_to(message_obj, f"❌ Не удалось обнаружить лот с индексом <code>{lot_index}</code>.",
                             allow_sending_without_reply=True, parse_mode="HTML", reply_markup=update_button)
            else:
                bot.edit_message_text(f"❌ Не удалось обнаружить лот с индексом <code>{lot_index}</code>.",
                                      message_obj.chat.id, message_obj.id,
                                      parse_mode="HTML", reply_markup=update_button)
            return False
        return True

    def check_products_file_exists(pf_index: int, files_list: list[str],
                                   message_obj: types.Message, reply_mode: bool = True) -> bool:
        """
        Проверяет, существует ли файл с товарами с переданным индексом.
        Если лота не существует - отправляет сообщение с кнопкой обновления списка файлов с товарами.

        :param pf_index: числовой индекс файла с товарами.

        :param files_list: список файлов.

        :param message_obj: экземпляр Telegram-сообщения.

        :param reply_mode: режим ответа на переданное сообщение.
        Если True - отвечает на переданное сообщение,
        если False - редактирует переданное сообщение.

        :return: True, если файл существует, False, если нет.
        """
        if pf_index > len(files_list) - 1:
            update_button = types.InlineKeyboardMarkup().add(Button("🔄 Обновить",
                                                                    callback_data=f"{CBT.PRODUCTS_FILES_LIST}:0"))
            if reply_mode:
                bot.reply_to(message_obj, f"❌ Не удалось обнаружить товарный файл с индексом <code>{pf_index}</code>.",
                             allow_sending_without_reply=True, parse_mode="HTML", reply_markup=update_button)
            else:
                bot.edit_message_text(f"❌ Не удалось обнаружить товарный файл с индексом <code>{pf_index}</code>.",
                                      message_obj.chat.id, message_obj.id,
                                      parse_mode="HTML", reply_markup=update_button)
            return False
        return True

    # Основное меню настроек авто-выдачи.
    def open_lots_list(c: types.CallbackQuery):
        """
        Открывает список лотов с авто-выдачей.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"Выберите интересующий вас лот.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.lots_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def open_funpay_lots_list(c: types.CallbackQuery):
        """
        Открывает список лотов FunPay.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text(f"""Выберите интересующий вас лот (все лоты получена напрямую с вашей страницы FunPay).

"""
                              f"""<i>Время последнего сканирования: </i>"""
                              f"""<code>{cardinal.last_telegram_lots_update.strftime("%d.%m.%Y %H:%M:%S")}</code>""",
                              c.message.chat.id, c.message.id,
                              parse_mode="HTML", reply_markup=keyboards.funpay_lots_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    def act_add_lot(c: types.CallbackQuery):
        """
        Активирует режим добавления нового лота для авто-выдачи.
        """
        offset = int(c.data.split(":")[1])
        result = bot.send_message(c.message.chat.id, "Скопируйте название лота с FunPay и отправьте его мне.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.ADD_AD_TO_LOT_MANUALLY,
                          data={"offset": offset})
        bot.answer_callback_query(c.id)

    def add_lot(m: types.Message):
        """
        Добавляет новый лот для авто-выдачи.
        """
        fp_lots_offset = tg.get_user_state(m.chat.id, m.from_user.id)["data"]["offset"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        lot = m.text.strip()
        error_keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.FP_LOTS_LIST}:{fp_lots_offset}"),
                 Button("➕ Добавить другой", callback_data=f"{CBT.ADD_AD_TO_LOT_MANUALLY}:{fp_lots_offset}"))

        if lot in cardinal.AD_CFG.sections():
            bot.reply_to(m, f"❌ Лот <code>{utils.escape(lot)}</code> уже есть в конфиге авто-выдачи.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=error_keyboard)
            return

        cardinal.AD_CFG.add_section(lot)
        cardinal.AD_CFG.set(lot, "response", """Спасибо за покупку, $username!

Вот твой товар:
$product""")
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        lot_number = len(cardinal.AD_CFG.sections()) - 1
        ad_lot_offset = lot_number - 4 if lot_number - 4 > 0 else 0
        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.FP_LOTS_LIST}:{fp_lots_offset}"),
                 Button("➕ Добавить еще", callback_data=f"{CBT.ADD_AD_TO_LOT_MANUALLY}:{fp_lots_offset}"),
                 Button("⚙️ Настроить", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_number}:{ad_lot_offset}"))

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET добавил секцию "
                    f"$YELLOW[{lot}]$RESET в конфиг авто-выдачи.")
        bot.send_message(m.chat.id, f"✅ Добавлена новая секция <code>{utils.escape(lot)}</code> в конфиг "
                                    f"авто-выдачи.", parse_mode="HTML", reply_markup=keyboard)

    def open_products_files_list(c: types.CallbackQuery):
        """
        Открывает список файлов с товарами.
        """
        offset = int(c.data.split(":")[1])
        bot.edit_message_text("Выберите интересующий вас файл с товарами.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.products_files_list(offset))
        bot.answer_callback_query(c.id)

    def act_create_product_file(c: types.CallbackQuery):
        """
        Активирует режим создания нового файла для товаров.
        """
        result = bot.send_message(c.message.chat.id, "Введите название для нового файла с товарами "
                                                     "(можно без <code>.txt</code>).\n\n",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.CREATE_PRODUCTS_FILE)
        bot.answer_callback_query(c.id)

    def create_products_file(m: types.Message):
        """
        Создает новый файл для товаров.
        """
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        file_name = m.text.strip()
        if not file_name.endswith(".txt"):
            file_name += ".txt"

        if os.path.exists(f"storage/products/{file_name}"):
            file_index = os.listdir("storage/products").index(file_name)
            offset = file_index - 4 if file_index - 4 > 0 else 0
            keyboard = types.InlineKeyboardMarkup()\
                .row(Button("◀️ Назад", callback_data=f"{CBT.CATEGORY}:autoDelivery"),
                     Button("➕ Создать другой", callback_data=CBT.CREATE_PRODUCTS_FILE),
                     Button("⚙️ Настроить", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}"))
            bot.reply_to(m, f"❌ Файл <code>storage/products/{utils.escape(file_name)}</code> уже существует.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
            return

        try:
            with open(f"storage/products/{file_name}", "w", encoding="utf-8"):
                pass
        except:
            logger.debug(traceback.format_exc())
            keyboard = types.InlineKeyboardMarkup() \
                .row(Button("◀️ Назад", callback_data=f"{CBT.CATEGORY}:autoDelivery"),
                     Button("➕ Создать другой", callback_data=CBT.CREATE_PRODUCTS_FILE))
            bot.reply_to(m, f"❌ Произошла ошибка при создании файла "
                            f"<code>storage/products/{utils.escape(file_name)}</code>. Подробнее в файле "
                            f"<code>logs/log.log</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

        file_index = os.listdir("storage/products").index(file_name)
        offset = file_index - 4 if file_index - 4 > 0 else 0
        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.CATEGORY}:autoDelivery"),
                 Button("➕ Создать еще", callback_data=CBT.CREATE_PRODUCTS_FILE),
                 Button("⚙️ Настроить", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}"))
        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET создал файл для товаров "
                    f"$YELLOWstorage/products/{file_name}$RESET.")
        bot.send_message(m.chat.id, f"✅ Файл <code>storage/products/{utils.escape(file_name)}</code> создан.",
                         parse_mode="HTML", reply_markup=keyboard)

    # Меню настройки лотов.
    def open_edit_lot_cp(c: types.CallbackQuery):
        """
        Открывает панель редактирования авто-выдачи лота.
        """
        split = c.data.split(":")
        lot_index, offset = int(split[1]), int(split[2])
        if not check_ad_lot_exists(lot_index, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_index]
        lot_obj = cardinal.AD_CFG[lot]

        bot.edit_message_text(utils.generate_lot_info_text(lot, lot_obj),
                              c.message.chat.id, c.message.id, parse_mode="HTML",
                              reply_markup=keyboards.edit_lot(cardinal, lot_index, offset))
        bot.answer_callback_query(c.id)

    def act_edit_lot_response(c: types.CallbackQuery):
        """
        Активирует режим изменения текста выдачи.
        """
        split = c.data.split(":")
        lot_index, offset = int(split[1]), int(split[2])
        result = bot.send_message(c.message.chat.id, "Введите новый текст выдачи товара.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.EDIT_LOT_DELIVERY_TEXT,
                          {"lot_index": lot_index, "offset": offset})
        bot.answer_callback_query(c.id)

    def edit_lot_response(m: types.Message):
        """
        Изменяет текст выдачи.
        """
        user_state = tg.get_user_state(m.chat.id, m.from_user.id)
        lot_index, offset = user_state["data"]["lot_index"], user_state["data"]["offset"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_ad_lot_exists(lot_index, m):
            return

        new_response = m.text.strip()
        lot = cardinal.AD_CFG.sections()[lot_index]
        lot_obj = cardinal.AD_CFG[lot]

        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_index}:{offset}"),
                 Button("✏️ Изменить", callback_data=f"{CBT.EDIT_LOT_DELIVERY_TEXT}:{lot_index}:{offset}"))

        if lot_obj.get("productsFileName") is not None and "$product" not in new_response:
            bot.reply_to(m, f"❌ К лоту <code>[{utils.escape(lot)}]</code> привязан файл с "
                            f"товарами, однако в тексте ответа нет переменной <code>$product</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
            return

        cardinal.AD_CFG.set(lot, "response", new_response)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET изменил текст выдачи "
                    f"лота $YELLOW[{lot}]$RESET на $YELLOW\"{new_response}\"$RESET.")

        bot.reply_to(m, f"✅ Ответ для лота <code>{utils.escape(lot)}</code> изменен на "
                        f"<code>{utils.escape(new_response)}</code>",
                     allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    def act_link_products_file(c: types.CallbackQuery):
        """
        Активирует режим привязки файла с товарами к лоту.
        """
        split = c.data.split(":")
        lot_index, offset = int(split[1]), int(split[2])
        result = bot.send_message(c.message.chat.id, "Введите название файла с товарами.\nЕсли вы хотите отвязать файл "
                                                     "с товарами, отправьте <code>-</code>\n\n"
                                                     "Если файла не существует, он будет создан автоматически.",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.BIND_PRODUCTS_FILE,
                          {"lot_index": lot_index, "offset": offset})
        bot.answer_callback_query(c.id)

    def link_products_file(m: types.Message):
        """
        Привязывает файл с товарами к лоту.
        """
        user_state = tg.get_user_state(m.chat.id, m.from_user.id)
        lot_index, offset = user_state["data"]["lot_index"], user_state["data"]["offset"]
        tg.clear_user_state(m.chat.id, m.from_user.id, True)
        if not check_ad_lot_exists(lot_index, m):
            return

        lot = cardinal.AD_CFG.sections()[lot_index]
        lot_obj = cardinal.AD_CFG[lot]
        file_name = m.text.strip()
        exists = 1

        if "$product" not in lot_obj.get("response") and file_name != "":
            keyboard = types.InlineKeyboardMarkup() \
                .add(Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_index}:{offset}"))
            bot.reply_to(m, "❌ Невозможно привязать файл с товарами, т.к. в тексте ответа "
                            "отсутствует переменная <code>$product</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
            return

        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_index}:{offset}"),
                 Button("⛓️ Перепривязать", callback_data=f"{CBT.BIND_PRODUCTS_FILE}:{lot_index}:{offset}"))

        if file_name == "-":
            cardinal.AD_CFG.remove_option(lot, "productsFileName")
            cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET отвязал файл с товарами от "
                f"лота $YELLOW[{lot}]$RESET.")
            bot.reply_to(m, f"✅ Файл с товарами успешно отвязан от лота <code>{utils.escape(lot)}</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
            return

        if not file_name.endswith(".txt"):
            file_name += ".txt"

        if not os.path.exists(f"storage/products/{file_name}"):
            bot.send_message(m.chat.id, f"🔄 Создаю файл для товаров "
                                        f"<code>storage/products/{utils.escape(file_name)} ...</code>",
                             parse_mode="HTML")
            exists = 0
            try:
                with open(f"storage/products/{file_name}", "w", encoding="utf-8"):
                    pass
            except:
                logger.debug(traceback.format_exc())
                bot.reply_to(m, f"❌ Произошла ошибка при создании файла "
                                f"<code>storage/products/{utils.escape(file_name)}</code>. Подробнее в файле "
                                f"<code>logs/log.log</code>.",
                             allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

        cardinal.AD_CFG.set(lot, "productsFileName", file_name)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        if exists:
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET привязал файл с товарами "
                f"$YELLOWstorage/products/{file_name}$RESET к лоту $YELLOW[{lot}]$RESET.")
            bot.reply_to(m, f"✅ Файл с товарами <code>storage/products/{utils.escape(file_name)}</code> "
                            f"успешно привязан к лоту <code>{utils.escape(lot)}</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)
        else:
            logger.info(
                f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET создал и привязал файл с "
                f"товарами $YELLOWstorage/products/{file_name}$RESET к лоту $YELLOW[{lot}]$RESET.")

            bot.reply_to(m, f"✅ Файл с товарами <code>storage/products/{utils.escape(file_name)}</code> "
                            f"успешно <b><u>создан</u></b> и привязан к лоту <code>{utils.escape(lot)}</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    def switch_lot_setting(c: types.CallbackQuery):
        """
        Переключает переключаемые параметры лота.
        """
        split = c.data.split(":")
        param, lot_number, offset = split[1], int(split[2]), int(split[3])
        if not check_ad_lot_exists(lot_number, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        lot_obj = cardinal.AD_CFG[lot]
        if lot_obj.get(param) in [None, "0"]:
            value = "1"
        else:
            value = "0"
        cardinal.AD_CFG.set(lot, param, value)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")
        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET изменил параметр $CYAN{param}$RESET "
            f"секции $YELLOW[{lot}]$RESET на $YELLOW{value}$RESET.")
        bot.edit_message_text(utils.generate_lot_info_text(lot, lot_obj),
                              c.message.chat.id, c.message.id, parse_mode="HTML",
                              reply_markup=keyboards.edit_lot(cardinal, lot_number, offset))
        bot.answer_callback_query(c.id)

    def create_lot_delivery_test(c: types.CallbackQuery):
        """
        Создает комбинацию [ключ: название лота] для теста авто-выдачи.
        """
        split = c.data.split(":")
        lot_index, offset = int(split[1]), int(split[2])

        if not check_ad_lot_exists(lot_index, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        lot_name = cardinal.AD_CFG.sections()[lot_index]

        simbols = string.ascii_letters + "0123456789"
        key = "".join(random.sample(simbols, 50))

        cardinal.delivery_tests[key] = lot_name

        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET создал одноразовый ключ для "
            f"авто-выдачи лота $YELLOW[{lot_name}]$RESET: $CYAN{key}$RESET.")

        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{lot_index}:{offset}"),
                 Button("👾 Еще 1 тест", callback_data=f"test_auto_delivery:{lot_index}:{offset}"))

        bot.send_message(c.message.chat.id, f"✅ Одноразовый ключ для теста авто-выдачи лота "
                                            f"<code>{utils.escape(lot_name)}</code> успешно создан. \n\n"
                                            f"Для теста авто-выдачи введите команду снизу в любой чат FunPay (ЛС).\n\n"
                                            f"<code>!автовыдача {key}</code>", parse_mode="HTML", reply_markup=keyboard)
        bot.answer_callback_query(c.id)

    def del_lot(c: types.CallbackQuery):
        """
        Удаляет лот из конфига.
        """
        split = c.data.split(":")
        lot_number, offset = int(split[1]), int(split[2])

        if not check_ad_lot_exists(lot_number, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.AD_CFG.sections()[lot_number]
        cardinal.AD_CFG.remove_section(lot)
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        logger.info(
            f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET удалил секцию "
            f"$YELLOW[{lot}]$RESET из конфига авто-выдачи.")
        bot.edit_message_text(f"Выберите интересующий вас лот.", c.message.chat.id, c.message.id,
                              reply_markup=keyboards.lots_list(cardinal, offset))
        bot.answer_callback_query(c.id)

    # Меню добавления лота с FunPay
    def update_funpay_lots_list(c: types.CallbackQuery):
        offset = int(c.data.split(":")[1])
        new_msg = bot.send_message(c.message.chat.id,
                                   "Обновляю данные о лотах и категориях (это может занять некоторое время)...")
        bot.answer_callback_query(c.id)
        result = cardinal.update_lots_and_categories()
        if not result:
            bot.edit_message_text("❌ Не удалось обновить данные о лотах и категориях. "
                                  "Подробнее в файле <code>logs/log.log</code>.", new_msg.chat.id, new_msg.id,
                                  parse_mode="HTML")
            return
        bot.delete_message(new_msg.chat.id, new_msg.id)
        c.data = f"{CBT.FP_LOTS_LIST}:{offset}"
        open_funpay_lots_list(c)

    def add_ad_to_lot(c: types.CallbackQuery):
        split = c.data.split(":")
        fp_lot_index, fp_lots_offset = int(split[1]), int(split[2])

        if fp_lot_index > len(cardinal.telegram_lots) - 1:
            update_button = types.InlineKeyboardMarkup().add(Button("🔄 Обновить",
                                                                    callback_data=f"{CBT.FP_LOTS_LIST}:0"))
            bot.edit_message_text(f"❌ Не удалось обнаружить лот с индексом <code>{fp_lot_index}</code>.",
                                  c.message.chat.id, c.message.id,
                                  parse_mode="HTML", reply_markup=update_button)
            bot.answer_callback_query(c.id)
            return

        lot = cardinal.telegram_lots[fp_lot_index]
        if lot.title in cardinal.AD_CFG.sections():
            ad_lot_index = cardinal.AD_CFG.sections().index(lot.title)
            ad_lots_offset = ad_lot_index - 4 if ad_lot_index - 4 > 0 else 0

            keyboard = types.InlineKeyboardMarkup() \
                .row(Button("◀️ Назад", callback_data=f"{CBT.FP_LOTS_LIST}:{fp_lots_offset}"),
                     Button("⚙️ Настроить", callback_data=f"{CBT.EDIT_AD_LOT}:{ad_lot_index}:{ad_lots_offset}"))

            bot.send_message(c.message.chat.id,
                             f"❌ Лот <code>{utils.escape(lot.title)}</code> уже есть в конфиге авто-выдачи.",
                             parse_mode="HTML", reply_markup=keyboard)
            bot.answer_callback_query(c.id)
            return

        cardinal.AD_CFG.add_section(lot.title)
        cardinal.AD_CFG.set(lot.title, "response", "Спасибо за покупку, $username!\n\nВот твой товар:\n\n$product")
        cardinal.save_config(cardinal.AD_CFG, "configs/auto_delivery.cfg")

        ad_lot_index = len(cardinal.AD_CFG.sections()) - 1
        ad_lots_offset = ad_lot_index - 4 if ad_lot_index - 4 > 0 else 0
        keyboard = types.InlineKeyboardMarkup() \
            .row(Button("◀️ Назад", callback_data=f"{CBT.FP_LOTS_LIST}:{fp_lots_offset}"),
                 Button("⚙️ Настроить", callback_data=f"{CBT.EDIT_AD_LOT}:{ad_lot_index}:{ad_lots_offset}"))

        logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET добавил секцию "
                    f"$YELLOW[{lot.title}]$RESET в конфиг авто-выдачи.")

        bot.send_message(c.message.chat.id,
                         f"✅ Добавлена новая секция <code>{utils.escape(lot.title)}</code> в конфиг "
                         f"авто-выдачи.", parse_mode="HTML", reply_markup=keyboard)
        bot.answer_callback_query(c.id)

    # Меню управления файлов с товарами.
    def open_products_file_action(c: types.CallbackQuery):
        """
        Открывает панель управления файлом с товарами.
        """
        split = c.data.split(":")
        file_index, offset = int(split[1]), int(split[2])
        files = [i for i in os.listdir("storage/products") if i.endswith(".txt")]
        if not check_products_file_exists(file_index, files, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        file_name = files[file_index]
        products_amount = cardinal_tools.count_products(f"storage/products/{file_name}")
        nl = "\n"
        delivery_objs = [i for i in cardinal.AD_CFG.sections() if
                         cardinal.AD_CFG[i].get("productsFileName") == file_name]

        text = f"""<b><u>{file_name}</u></b>
        
<b><i>Товаров в файле:</i></b>  <code>{products_amount}</code>

<b><i>Используется в лотах:</i></b>
{nl.join(f"<code>{utils.escape(i)}</code>" for i in delivery_objs)}

<i>Обновлено:</i>  <code>{datetime.datetime.now().strftime('%H:%M:%S')}</code>"""
        bot.edit_message_text(text, c.message.chat.id, c.message.id,
                              reply_markup=keyboards.products_file_edit(file_index, offset),
                              parse_mode="HTML")
        bot.answer_callback_query(c.id)

    def act_add_products_to_file(c: types.CallbackQuery):
        """
        Активирует режим добавления товаров в файл с товарами.
        """
        split = c.data.split(":")
        file_index, el_index, offset, prev_page = int(split[1]), int(split[2]), int(split[3]), int(split[4])
        result = bot.send_message(c.message.chat.id, "Отправьте товары, которые вы хотите "
                                  "добавить. Каждый товар должен быть с новой строки",
                                  parse_mode="HTML", reply_markup=keyboards.CLEAR_STATE_BTN)
        tg.set_user_state(c.message.chat.id, result.id, c.from_user.id, CBT.ADD_PRODUCTS_TO_FILE,
                          {"file_index": file_index, "element_index": el_index,
                           "offset": offset, "previous_page": prev_page})
        bot.answer_callback_query(c.id)

    def add_products_to_file(m: types.Message):
        """
        Добавляет товары в файл с товарами.
        """
        state = tg.get_user_state(m.chat.id, m.from_user.id)["data"]
        file_index, el_index, offset, prev_page = (state["file_index"], state["element_index"],
                                                   state["offset"], state["previous_page"])
        tg.clear_user_state(m.chat.id, m.from_user.id, True)

        files = [i for i in os.listdir("storage/products") if i.endswith(".txt")]
        if file_index > len(files) - 1:

            if prev_page == 0:
                update_btn = Button("🔄 Обновить", callback_data=f"{CBT.PRODUCTS_FILES_LIST}:0")
            else:
                update_btn = Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{el_index}:{offset}")
            error_keyboard = types.InlineKeyboardMarkup().add(update_btn)

            bot.reply_to(m, f"❌ Не удалось обнаружить товарный файл с индексом <code>{file_index}</code>.",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=error_keyboard)
            return

        file_name = files[file_index]
        products = list(itertools.filterfalse(lambda el: not el, m.text.strip().split("\n")))

        if prev_page == 0:
            back_btn = Button("◀️ Назад", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}")
        else:
            back_btn = Button("◀️ Назад", callback_data=f"{CBT.EDIT_AD_LOT}:{el_index}:{offset}")

        try_again_btn = Button("➕ Еще раз",
                               callback_data=f"{CBT.ADD_PRODUCTS_TO_FILE}:{file_index}:{el_index}:{offset}:{prev_page}")

        add_more_btn = Button("➕ Добавить еще",
                              callback_data=f"{CBT.ADD_PRODUCTS_TO_FILE}:{file_index}:{el_index}:{offset}:{prev_page}")

        products_text = "\n".join(products)

        try:
            with open(f"storage/products/{file_name}", "a", encoding="utf-8") as f:
                f.write("\n")
                f.write(products_text)
        except:
            logger.debug(traceback.format_exc())
            keyboard = types.InlineKeyboardMarkup().row(back_btn, try_again_btn)
            bot.reply_to(m, f"❌ Не удалось добавить товары в файл. Подробнее в файле <code>logs/log.log</code>",
                         allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

        logger.info(f"Пользователь $MAGENTA{m.from_user.username} (id: {m.from_user.id})$RESET добавил "
                    f"$CYAN{len(products)}$RESET товар(-a, -oв) в файл $YELLOWstorage/products/{file_name}$RESET.")

        keyboard = types.InlineKeyboardMarkup().row(back_btn, add_more_btn)

        bot.reply_to(m, f"✅ В файл <code>storage/products/{file_name}</code> добавлен(-о) "
                        f"<code>{len(products)}</code> товар(-а / -ов).",
                     allow_sending_without_reply=True, parse_mode="HTML", reply_markup=keyboard)

    def send_products_file(c: types.CallbackQuery):
        """
        Отправляет файл с товарами.
        """
        split = c.data.split(":")
        file_index, offset = int(split[1]), int(split[2])
        files = [i for i in os.listdir("storage/products") if i.endswith(".txt")]
        if not check_products_file_exists(file_index, files, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return

        file_name = files[file_index]
        back_button = types.InlineKeyboardMarkup() \
            .add(types.InlineKeyboardButton("◀️ Назад",
                                            callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}"))

        with open(f"storage/products/{file_name}", "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                bot.send_message(c.message.chat.id, f"❌ Файл <code>storage/products/{file_name}</code> пуст.",
                                 parse_mode="HTML", reply_markup=back_button)
                bot.answer_callback_query(c.id)
                return

            logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET запросил "
                        f"файл с товарами $YELLOWstorage/products/{file_name}$RESET.")
            f.seek(0)
            bot.send_document(c.message.chat.id, f)
            bot.answer_callback_query(c.id)

    def ask_del_products_file(c: types.CallbackQuery):
        """
        Открывает суб-панель подтверждения удаления файла с товарами.
        """
        split = c.data.split(":")
        file_index, offset = int(split[1]), int(split[2])
        files = [i for i in os.listdir("storage/products") if i.endswith(".txt")]
        if not check_products_file_exists(file_index, files, c.message, reply_mode=False):
            bot.answer_callback_query(c.id)
            return
        bot.edit_message_reply_markup(c.message.chat.id, c.message.id,
                                      reply_markup=keyboards.products_file_edit(file_index, offset, True))
        bot.answer_callback_query(c.id)

    def del_products_file(c: types.CallbackQuery):
        """
        Удаляет файл с товарами.
        """

        split = c.data.split(":")
        file_index, offset = int(split[1]), int(split[2])
        files = [i for i in os.listdir("storage/products") if i.endswith(".txt")]
        if not check_products_file_exists(file_index, files, c.message, reply_mode=False):
            tg.answer_callback_query(c.id)
            return

        file_name = files[file_index]

        delivery_objs = [i for i in cardinal.AD_CFG.sections() if
                         cardinal.AD_CFG[i].get("productsFileName") == file_name]
        if delivery_objs:
            keyboard = types.InlineKeyboardMarkup()\
                .add(Button("◀️ Назад", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}"))
            bot.edit_message_text(f"❌ Файл <code>storage/products/{file_name}</code> используется в конфиге "
                                  f"авто-выдачи.\n Для начала необходимо удалить все лоты, которые используют этот "
                                  f"файл с товарами, из конфига авто-выдачи.",
                                  c.message.chat.id, c.message.id,
                                  parse_mode="HTML", reply_markup=keyboard)
            bot.answer_callback_query(c.id)
            return

        try:
            os.remove(f"storage/products/{file_name}")

            logger.info(f"Пользователь $MAGENTA{c.from_user.username} (id: {c.from_user.id})$RESET удалил "
                        f"файл с товарами $YELLOWstorage/products/{file_name}$RESET.")

            bot.edit_message_text(f"Выберите интересующий вас файл с товарами.",
                                  c.message.chat.id, c.message.id,
                                  reply_markup=keyboards.products_files_list(offset))

            bot.answer_callback_query(c.id)
        except:
            keyboard = types.InlineKeyboardMarkup() \
                .add(Button("◀️ Назад", callback_data=f"{CBT.EDIT_PRODUCTS_FILE}:{file_index}:{offset}"))
            bot.edit_message_text(f"❌ Не удалось удалить файл <code>storage/products/{file_name}</code>. "
                                  f"Подробнее в файле logs/log.log.",
                                  c.message.chat.id, c.message.id,
                                  parse_mode="HTML", reply_markup=keyboard)
            bot.answer_callback_query(c.id)
            logger.debug(traceback.format_exc())
            return

    # Основное меню настроек авто-выдачи.
    tg.cbq_handler(open_lots_list, lambda c: c.data.startswith(f"{CBT.AD_LOTS_LIST}:"))
    tg.cbq_handler(open_funpay_lots_list, lambda c: c.data.startswith(f"{CBT.FP_LOTS_LIST}:"))
    tg.cbq_handler(act_add_lot, lambda c: c.data.startswith(f"{CBT.ADD_AD_TO_LOT_MANUALLY}:"))
    tg.msg_handler(add_lot, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.ADD_AD_TO_LOT_MANUALLY))

    tg.cbq_handler(open_products_files_list, lambda c: c.data.startswith(f"{CBT.PRODUCTS_FILES_LIST}:"))

    tg.cbq_handler(act_create_product_file, lambda c: c.data == CBT.CREATE_PRODUCTS_FILE)
    tg.msg_handler(create_products_file, func=lambda m: tg.check_state(m.chat.id, m.from_user.id,
                                                                       CBT.CREATE_PRODUCTS_FILE))

    # Меню настройки лотов.
    tg.cbq_handler(open_edit_lot_cp, lambda c: c.data.startswith(f"{CBT.EDIT_AD_LOT}:"))

    tg.cbq_handler(act_edit_lot_response, lambda c: c.data.startswith(f"{CBT.EDIT_LOT_DELIVERY_TEXT}:"))
    tg.msg_handler(edit_lot_response,
                   func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.EDIT_LOT_DELIVERY_TEXT))

    tg.cbq_handler(act_link_products_file, lambda c: c.data.startswith(f"{CBT.BIND_PRODUCTS_FILE}:"))
    tg.msg_handler(link_products_file, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.BIND_PRODUCTS_FILE))

    tg.cbq_handler(switch_lot_setting, lambda c: c.data.startswith("switch_lot:"))
    tg.cbq_handler(create_lot_delivery_test, lambda c: c.data.startswith("test_auto_delivery:"))
    tg.cbq_handler(del_lot, lambda c: c.data.startswith(f"{CBT.DEL_AD_LOT}:"))

    # Меню добавления лота с FunPay
    tg.cbq_handler(add_ad_to_lot, lambda c: c.data.startswith(f"{CBT.ADD_AD_TO_LOT}:"))
    tg.cbq_handler(update_funpay_lots_list, lambda c: c.data.startswith("update_funpay_lots:"))

    # Меню управления файлов с товарами.
    tg.cbq_handler(open_products_file_action, lambda c: c.data.startswith(f"{CBT.EDIT_PRODUCTS_FILE}:"))

    tg.cbq_handler(act_add_products_to_file, lambda c: c.data.startswith(f"{CBT.ADD_PRODUCTS_TO_FILE}:"))
    tg.msg_handler(add_products_to_file,
                   func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT.ADD_PRODUCTS_TO_FILE))

    tg.cbq_handler(send_products_file, lambda c: c.data.startswith("download_products_file:"))
    tg.cbq_handler(ask_del_products_file, lambda c: c.data.startswith("del_products_file:"))
    tg.cbq_handler(del_products_file, lambda c: c.data.startswith("confirm_del_products_file:"))


BIND_TO_PRE_INIT = [init_auto_delivery_cp]
