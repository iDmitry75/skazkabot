"""
Skazkabot — автоматизированный бот для ручного/автоматического фарма в игре для VK "Другая Сказка".

Назначение:
  - Автоматизирует поиск и нажатия по элементам интерфейса игры для проведения боёв,
    сбора наград и повторного запуска боёв.

Ключевые функции:
  - event(n_attack): провести указанное количество боёв в событии.
  - play(n_attack): провести указанное количество боёв в игровом режиме "Игра".
  - endless_play(n_attack=15): запускать `play(15)` и ждать до 73 минут от начала цикла
    перед следующим запуском (подходит для циклического фарма).

Параметры командной строки (поддерживаются короткие и полные варианты):
  /e:n или /event:n   - выполнить `event` n раз
  /p:n или /play:n    - выполнить `play` n раз
  /endless             - запустить бесконечный режим `endless_play`
  /?                   - показать справку

Зависимости:
  - Python 3.x, библиотеки: pyautogui, opencv-python (cv2), numpy

Предупреждение:
  - Скрипт управляет курсором и кликами по экрану — запускайте только на системе,
    где можно безопасно автоматизировать клики (например, в отдельном окне игры).
"""

import random
import cv2
import numpy as np
import pyautogui
import time
import sys

stRegular = 0
stWeighted = 1

class Hero:
    def __init__(self, name, image, priority, element=None, strategy=stRegular):
        self.name = name
        self.image = image
        self.priority = priority
        # element всегда кортеж (даже если один элемент)
        if element is None:
            self.element = ()
        elif isinstance(element, tuple):
            self.element = element
        else:
            self.element = (element,)
        self.strategy = strategy

    def __repr__(self):
        return f"Hero(name={self.name}, image={self.image}, priority={self.priority}, element={self.element}, strategy={self.strategy})"

heroes = [
    Hero('Горыныч', 'gor.png', 1, ('fire','physical'), strategy=stWeighted),
    Hero('Котофей', 'kotofei.png', 2, ('earth','physical')),
    Hero('Святогор', 'svyat.png', 1, ('water','physical')),
    Hero('Несмеяна', 'nosmile.png', 1, ('water','physical')),
    Hero('Руслан', 'ruslan.png', 3, ('physical',)),
    Hero('Василиса', 'vasilisa.png', 2, ('physical','fire'), strategy=stWeighted),
    Hero('Яга', 'yaga.png', 2, ('fire',)),
    Hero('Жар-птица', 'phoenix.png', 3, ('fire','physical')),
    Hero('София', 'sofia.png', 4, ('water',)),
    Hero('Мухолов', 'flycatcher.png', 3, ('earth',)),
    Hero('Древень', 'dreven.png', 3, ('earth','physical')),
    Hero('Ледогрыз', 'icecracker.png', 2, ('water',)),
    Hero('Мракана', 'mrakana.png', 3, ('water',)),
]


def find_image_on_screen(template_path, threshold=0.8):
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path)
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    if locations[0].size > 0:
        x = int(locations[1][0] + template.shape[1] / 2)
        y = int(locations[0][0] + template.shape[0] / 2)
        return (x, y)
    return None


def find_runes(template_path, threshold=0.94):
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path)
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    # print(f"Найдено {len(locations[0])} руны")
    # print(locations)
    points = []
    w, h = template.shape[1], template.shape[0]
    for pt in zip(*locations[::-1]):
        center = (int(pt[0] + w / 2), int(pt[1] + h / 2))
        points.append(center)
    # С точностью 0.95 находятся фантомные руны, поэтому фильтруем близко расположенные руны
    # Сначала сортируем по x, чтобы фильтрация была последовательной
    points.sort(key=lambda p: p[0])
    filtered = []
    for p in points:
        if not filtered or abs(p[0] - filtered[-1][0]) >= 10:
            filtered.append(p)
    return filtered


def list_of_heroes():
    found_heroes = []
    for hero in heroes:
        image_path = f"img/{hero.image}"
        pos = find_image_on_screen(image_path)
        if pos:
            found_heroes.append(hero.name)
    return found_heroes


def select_hero(hero_names):
    # Фильтруем объекты Hero по именам
    filtered = [hero for hero in heroes if hero.name in hero_names]
    if not filtered:
        return None
    min_priority = min(hero.priority for hero in filtered)
    candidates = [hero for hero in filtered if hero.priority == min_priority]
    selected = random.choice(candidates)
    return selected


def click_on_picture(image_path):
    pos = find_image_on_screen(image_path)
    # print(pos)
    if pos:
        pyautogui.moveTo(pos[0], pos[1])
        pyautogui.click()
    else:
        print("Изображение не найдено.")
    return pos

def press():
    pos = click_on_picture("img/press.png")
    if not pos:
        print("Кнопка 'Press' не найдена.")
        pos = click_on_picture("img/ataka.png")
    time.sleep(4)
    return(pos)


def battle(attacker):
    # Для stWeighted: запоминаем сколько рун выбрано по каждому типу
    weighted_selected = {elem: 0 for elem in attacker.element}
    for round in range(3):
        print(f"Раунд {round + 1}")
        press()
        if round != 3:
            # Подсчитываем руны для каждого элемента героя
            element_runes = {}
            for elem in attacker.element:
                runes = find_runes(f"img/{elem}.png")
                element_runes[elem] = runes
                print(f"Найдено {len(runes)} рун(ы) {elem}: {runes}")
            if attacker.strategy == stRegular:
                found_any = False
                for elem, runes in element_runes.items():
                    if runes:
                        found_any = True
                        for rune in runes:
                            pyautogui.moveTo(rune[0], rune[1])
                            pyautogui.click()
                            time.sleep(1)
                    if round == 0:
                        break
                if not found_any:
                    print(f'Руны {attacker.element} не найдены')
            elif attacker.strategy == stWeighted:
                # stWeighted: особый алгоритм по раундам
                elems = list(attacker.element)
                if round == 0:
                    # В первом раунде — не больше 2 рун каждого типа
                    for elem in elems:
                        runes = element_runes[elem]
                        count = min(2, len(runes))
                        for rune in runes[:count]:
                            pyautogui.moveTo(rune[0], rune[1])
                            pyautogui.click()
                            time.sleep(1)
                        weighted_selected[elem] += count
                        print(f"Выбрано {count} рун типа {elem} в первом раунде")
                elif round == 1:
                    # Во втором раунде — не больше 3 рун первого типа и 2 второго, учитывая уже выбранные
                    if len(elems) > 0:
                        elem1 = elems[0]
                        max1 = 3 - weighted_selected[elem1]
                        runes1 = element_runes[elem1]
                        count1 = min(max1, len(runes1)) if max1 > 0 else 0
                        for rune in runes1[:count1]:
                            pyautogui.moveTo(rune[0], rune[1])
                            pyautogui.click()
                            time.sleep(1)
                        weighted_selected[elem1] += count1
                        print(f"Выбрано {count1} рун типа {elem1} во втором раунде")
                    if len(elems) > 1:
                        elem2 = elems[1]
                        max2 = 2 - weighted_selected[elem2]
                        runes2 = element_runes[elem2]
                        count2 = min(max2, len(runes2)) if max2 > 0 else 0
                        for rune in runes2[:count2]:
                            pyautogui.moveTo(rune[0], rune[1])
                            pyautogui.click()
                            time.sleep(1)
                        weighted_selected[elem2] += count2
                        print(f"Выбрано {count2} рун типа {elem2} во втором раунде")
                else:
                    # В третьем раунде — прежний алгоритм (кликаем по всем)
                    for elem, runes in element_runes.items():
                        for rune in runes:
                            pyautogui.moveTo(rune[0], rune[1])
                            pyautogui.click()
                            time.sleep(1)
    time.sleep(10)
    # Проверяем победу
    pos = find_image_on_screen("img/victory.png")
    return pos

def play(n_attack=10):
    """
    Выполняет серию боёв в игровом режиме "Игра".

    Аргументы:
        n_attack (int): Количество атак (боёв), которые нужно провести в режиме "Игра".

    Описание:
        - Переходит в раздел "Игра" в интерфейсе.
        - Для каждой атаки:
            - Находит и выбирает босса для фарма.
            - Жмёт кнопку "В бой".
            - Выбирает доступного героя с наивысшим приоритетом.
            - Проводит бой с выбранным героем, используя руны его элементов.
            - После победы собирает награду.
        - Все действия автоматизированы с помощью поиска и кликов по изображениям на экране.
    """
    # Ищем кнопку Игра
    print("Переходим в игру (если есть)")
    print("Количество атак:", n_attack)
    pos = click_on_picture("img/play.png")
    if pos:
       time.sleep(3)
       pyautogui.moveTo(pos[0]-131, pos[1]+10)
       pyautogui.click()
       time.sleep(1)
       pyautogui.moveTo(pos[0]-131, pos[1]+10)
       pyautogui.click()
       time.sleep(1)
    for i in range(n_attack):    
        # Ищем босса для фарма
        pos = click_on_picture("img/bnosmile.png")
        time.sleep(2)
        if not pos:
            print('Босс не найден')
        
        # Жмем кнопку В бой
        pos = click_on_picture("img/attack.png")
        time.sleep(3)
        
        # Бой
        in_battle = True
        while in_battle:
            print("Начинаем бой")
            attacker = select_hero(list_of_heroes())
            print(f"Атакующий: {attacker}")
            if not attacker:
                print("Нет доступных героев для атаки")
                break
            if attacker:
                pos = click_on_picture(f"img/{attacker.image}")
                time.sleep(2)
            else:
                print('Шаблон атакующего не найден')
                break
            pos = battle(attacker)
            if pos:
                print("Бой завершен, победа!") 
                in_battle = False
            else:
                print("Следующий тур.")
        pos = click_on_picture("img/loot.png")
        time.sleep(2)

def event(n_attack=1):
    """
    Выполняет серию боёв в игровом событии.

    Аргументы:
        n_attack (int): Количество атак (боёв), которые нужно провести в событии.

    Описание:
        - Переходит в раздел "Событие" игры.
        - Для каждой атаки:
            - Нажимает кнопку "Призвать".
            - Выбирает доступного героя с наивысшим приоритетом.
            - Проводит бой с выбранным героем, используя руны его элементов.
            - После победы собирает награду.
        - Все действия автоматизированы с помощью поиска и кликов по изображениям на экране.
    """
    # Ищем кнопку Событие
    print("Переходим в событие  (если есть)")
    print("Количество атак:", n_attack)
    pos = click_on_picture("img/event.png")
    if pos:
       time.sleep(3)
       pyautogui.moveTo(pos[0]-32, pos[1]+40)
       pyautogui.click()
       time.sleep(3)
    for i in range(n_attack):
        # Жмем кнопку призвать
        pos = click_on_picture("img/summon.png")
        time.sleep(3)
        # Бой
        in_battle = True
        while in_battle:
            print("Начинаем бой")
            attacker = select_hero(list_of_heroes())
            print(f"Атакующий: {attacker}")
            if not attacker:
                print("Нет доступных героев для атаки")
                break
            if attacker:
                pos = click_on_picture(f"img/{attacker.image}")
                time.sleep(2)
            else:
                print('Шаблон атакующего не найден')
                break
            pos = battle(attacker)
            if pos:
                print("Бой завершен, победа!") 
                in_battle = False
            else:
                print("Следующий тур.")
        pos = click_on_picture("img/loot.png")
        time.sleep(2)

def restart():
    # Ищем кнопку Перезапустить
    pos = click_on_picture("img/restart.png")
    if pos:
        time.sleep(5)
        play_btn = find_image_on_screen("img/play.png")
        while not play_btn:
            print("Ждем кнопку 'Играть'...")
            time.sleep(3)
            play_btn = find_image_on_screen("img/play.png")
        print("Кнопка 'Играть' найдена, игра перезапущена.")
    else:
        print("Кнопка 'Перезапустить' не найдена.")

def endless_play(n_attack=15):
    """
    Запускает бесконечный цикл фарма:
      1. Сохраняет текущее время.
      2. Вызывает функцию play с параметром 15.
      3. Ждёт до истечения 73 минут с момента старта, затем повторяет цикл.
    """
    import datetime

    while True:
        start_time = datetime.datetime.now()
        restart()
        play(n_attack)
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        wait_time = 73 * 60 - elapsed
        if wait_time > 0:
            # Показываем обновляемый progress-bar до достижения 73 минут с момента start_time
            total = 73 * 60
            target_end = start_time + datetime.timedelta(seconds=total)
            bar_width = 40
            try:
                while True:
                    now = datetime.datetime.now()
                    if now >= target_end:
                        break
                    passed = (now - start_time).total_seconds()
                    if passed < 0:
                        passed = 0
                    if passed > total:
                        passed = total
                    remaining = int(total - passed)
                    percent = passed / total if total > 0 else 1.0
                    filled = int(percent * bar_width)
                    bar = "#" * filled + "-" * (bar_width - filled)
                    mins = remaining // 60
                    secs = remaining % 60
                    print(f"\rОжидание [{bar}] {int(percent*100):3d}%  {mins:02d}:{secs:02d} до следующего запуска", end="", flush=True)
                    time.sleep(1)
            except KeyboardInterrupt:
                # Позволяем пользователю прервать ожидание клавишей
                print("\nОжидание прервано пользователем.")
            else:
                # Завершаем строку прогресс-бара после завершения ожидания
                print()


if __name__ == "__main__":
    n_attack_event = 0
    n_attack_play = 15
    endless = False

    help_text = (
        "Использование:\n"
        "  python skazkabot.py /e:n /p:n [/endless]\n"
        "  /e:n или /event:n   - количество атак для event (по умолчанию 0)\n"
        "  /p:n или /play:n    - количество атак для play (по умолчанию 15)\n"
        "  /endless            - бесконечный режим фарма (play каждые 73 минуты)\n"
        "  /?                  - показать эту справку\n"
        "Пример:\n"
        "  python skazkabot.py /e:5 /p:20\n"
        "  python skazkabot.py /endless"
    )

    for arg in sys.argv[1:]:
        if arg.startswith("/e:") or arg.startswith("/event:"):
            try:
                n_attack_event = int(arg.split(":", 1)[1])
            except ValueError:
                print("Ошибка: неверный формат для /e:n или /event:n")
                print(help_text)
                sys.exit(1)
        elif arg.startswith("/p:") or arg.startswith("/play:"):
            try:
                n_attack_play = int(arg.split(":", 1)[1])
            except ValueError:
                print("Ошибка: неверный формат для /p:n или /play:n")
                print(help_text)
                sys.exit(1)
        elif arg == "/endless":
            endless = True
        elif arg == "/?":
            print(help_text)
            sys.exit(0)
        else:
            print(f"Неизвестный параметр: {arg}")
            print(help_text)
            sys.exit(1)

    if endless:
        endless_play(17)
    else:
        if n_attack_play > 0:
            restart()
            play(n_attack_play)
        if n_attack_event > 0:
            restart()
            event(n_attack_event)
