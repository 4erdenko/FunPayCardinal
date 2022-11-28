<h1 align="center">FunPay Cardinal</h1>
<h4 align="center">Консольное приложение для автоматизации рутинных действий на FunPay</h4>

## :clipboard: **Содержание**

- [Возможности](#robot-возможности)
  - [FunPay](#shopping_cart-funpay)
  - [Уведомления в Telegram](#left_speech_bubble-уведомления-в-telegram)
  - [Дополнительные возможности](#gear-дополнительные-возможности)

- [Преимущества](#1st_place_medal-преимущества)
  - [Для пользователей](#grinning-для-пользователей)
  - [Для разработчиков](#computer-для-разработчиков)

- [Плагины](#electric_plug-плагины)
- [Установка](#arrow_down-установка)
  - [Windows](#large_blue_diamond-windows)
  - [Linux (Ubuntu)](#hotsprings-linux-ubuntu)
- [Настройка конфигов](#hammer_and_wrench-настройка-конфигов)
- [Установка плагинов](#electric_plug-установка-плагинов)
- [Мне нужна помощь](#question-мне-нужна-помощь)
- [Star it!](#star-star-it!)


## :robot: **Возможности**

### :shopping_cart: **FunPay**

- Авто-выдача товаров.
- Авто-поднятие лотов.
- Авто-ответ на заготовленные команды.
- Авто-восстановление лотов после продажи.
- Вечный онлайн.
- Уведомления в телеграм.

### :left_speech_bubble: **Уведомления в Telegram**

- Возможность установки нескольких чатов для уведомлений.
- Уведомления о поднятии лотов.
- Уведомления о новых заказах.
- Уведомления о выдаче товара.
- Уведомления о новых сообщениях
- Возможность отвечать на сообщения прямо из Telegram.

### :gear: **Дополнительные возможности**

- Использование переменных в тексте для авто-ответа / авто-выдачи.
- Создание плагинов для кастомизации функционала без редактирования исходного кода самого Кардинала.

## :1st_place_medal: **Преимущества**

### :grinning: **Для пользователей**

- **Больше**, чем наличие самого нужного функционала.
- **Оптимизация**. _20 МБ свободного места на диске, до 50 МБ ОЗУ, доступ в интернет_ - все что нужно для работы.
- Возможность установить на **любую платформу**, которую поддерживает _Python: Windows, Linux, IOS, Android_ и т.д.
- Возможность установки плагинов дает **огромную вариативность** модификации стандартного функционала под самые разные нужды.
- Гибкие и при этом простые конфиги, написанные в INI-формате.
- Постоянные обновления, быстрое реагирования на баги / предложения о новом функционале.

### :computer: **Для разработчиков**

- Выбран самый простой и при этом один из самых мощных языков для такого рода приложений - _Python_.
- Полная документация кода. Все классы / методы / функции имеют док-строки, type-хинты.
- Широкое использование ООП. Почти каждый эвент / сообщение / заказ и т.д. представляют собой экземпляр соответствующего класса, а не просто набор данных в JSON.
- Возможность легкого создания плагинов.
- Сконфигурированный логгер. Никаких принтов!
- Собственный Python-пакет FunPayAPI, который никак не привязан к FunPay Cardinal.
- Поддержка лично от меня :)


## :electric_plug: Плагины

- [FPC Newbie Greetings Plugin](https://github.com/Woopertail/FPC-Newbie_Greetings_Plugin) (отправляет приветственное сообщение пользователям, которые написали впервые)
- [FPC Lot Deactivate Plugin](https://github.com/Woopertail/FPC-Lot_Deactivate_Plugin) (деактивирует лот, если для него закончились товары)


## :arrow_down: Установка

### :large_blue_diamond: Windows

1. Скачайте и установите [Python](https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe).
   1. При установке поставьте галочку у `Add python.exe to PATH` на первом экране установки. <img src="https://i.ibb.co/jgXZ1nf/image.png">
2. Скачайте [FunPay Cardinal](https://github.com/Woopertail/FunPayCardinal/archive/refs/heads/master.zip)
3. Перенести папку `FunPayCardinal-master` в нужное вам место.
4. Перейдите в папку `FunPayCardinal-master`.
5. В адресной строке введите `cmd` и нажмите `Enter`. <img src="https://i.ibb.co/0mjkf9Q/explorer-Zcsm-Ife-XFl.png">
6. В открывшейся командной строке введите `pip install -r requirements.txt`. Дождитесь окончания загрузки пакетов.
7. Закройте командную строку, настройте конфиги и запустите файл `Start.bat`.

### :hotsprings: Linux (Ubuntu)

1. Введите следующие команды для установки Python 3.11.
   1. `sudo apt update`
   2. `sudo apt install software-properties-common`
   3. `sudo add-apt-repository ppa:deadsnakes/ppa`
   4. `sudo apt update`
   5. `sudo apt install python3.11 python3.11-dev python3.11-gdbm python3.11-venv`
   6. `sudo apt install curl`
   7. `curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11`

2. Скачайте `git` с помощью команды `sudo apt install git`.
3. Скачайте FunPayCardinal с помощью команды `git clone https://github.com/woopertail/FunPayCardinal`.
4. Перейдите в папку `FunPayCardinal` с помощью команрды `cd FunPayCardinal`.
5. Установите нужные пакеты с помощью команды `python3.11 -m pip install -r requirements.txt`.
6. Настройте конфиги и запустите FunPay Cardinal с помощью команды `python3.11 main.py`.

## :hammer_and_wrench: Настройка конфигов

1. Все конфиги находятся в папке `configs`
2. Все инструкции по настройке конфигов находятся внутри самих конфигов.
3. Основной конфиг со всеми переключателями: `configs/_main.cfg`
4. Конфиг авто-ответчика: `configs/auto_response.cfg`
5. Конфиг авто-выдачи: `configs/auto_delivery.cfg`

## :electric_plug: Установка плагинов
Установка плагинов крайне проста. Просто скопируйте файл плагина (с расширением `.py`) в папку `plugins`.

## :question: Мне нужна помощь
Если у вас остались какие-либо вопросы, мы с радостью ответим на них в нашем [Telegram канале](https://t.me/funpay_cardinal).
Там же вы сможете найти больше плагинов для FunPay Cardinal.

## :star: Star it!
Если вам удобно пользоваться FunPay Cardinal, не забудьте поставить :star: звезду :star: данному проекту :)