import random
import cv2
import numpy as np
import pyautogui
import time



class Hero:
    def __init__(self, name, image, priority, element=None):
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

    def __repr__(self):
        return f"Hero(name={self.name}, image={self.image}, priority={self.priority}, element={self.element})"

heroes = [
    Hero('Горыныч', 'gor.png', 1, ('fire','physical')),
    Hero('Котофей', 'kotofei.png', 2, ('earth','physical')),
    Hero('Святогор', 'svyat.png', 1, ('water','physical')),
    Hero('Несмеяна', 'nosmile.png', 1, ('water','physical')),
    Hero('Руслан', 'ruslan.png', 3, ('physical',)),
    Hero('Василиса', 'vasilisa.png', 2, ('physical','fire')),
    Hero('Яга', 'yaga.png', 2, ('fire',)),
    Hero('Жар-птица', 'phoenix.png', 2, ('fire',)),
    Hero('София', 'sofia.png', 3, ('water',)),
    Hero('Мухолов', 'flycatcher.png', 3, ('earth',)),
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


def find_runes(template_path, threshold=0.95):
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
    for round in range(3):
        print(f"Раунд {round + 1}")
        press()
        if round != 3:
            # Ищем руны для всех элементов героя
            found_any = False
            for elem in attacker.element:
                runes = find_runes(f"img/{elem}.png")
                print(f"Найдено {len(runes)} рун(ы) {elem}: {runes}")
                if runes:
                    found_any = True
                    for rune in runes:
                        pyautogui.moveTo(rune[0], rune[1])
                        pyautogui.click()
                        time.sleep(1)
            if not found_any:
                print(f'Руны {attacker.element} не найдены')
    time.sleep(10)
    # Проверяем победу
    pos = find_image_on_screen("img/victory.png")
    return pos

if __name__ == "__main__":
    # Ищем кнопку Игра
    pos = click_on_picture("img/play.png")
    if pos:
        time.sleep(3)
        pyautogui.moveTo(pos[0]+185, pos[1]-71)
        pyautogui.click()
        time.sleep(1)
        pyautogui.moveTo(pos[0]+185, pos[1]-71)
        pyautogui.click()
        time.sleep(1)
    for i in range(5):    
        # Ищем Гарвену
        pos = click_on_picture("img/garvena.png")
        time.sleep(2)
        if not pos:
            print('Гарвена не найдена')
        
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
