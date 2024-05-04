import pandas as pd
import numpy as np

from pathlib import Path

from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import SingleColumnLayout
from borb.pdf import Paragraph
from borb.pdf import PDF
from borb.pdf import Alignment

from borb.pdf.canvas.font.simple_font.true_type_font import TrueTypeFont

import PySimpleGUI as sg

# Рендерим первое окошко
main_screen_layout = [  [sg.Text('Заполните небольшую анкету:')],
            [sg.Text('Введите вашу фамилию'), sg.InputText()],
            [sg.Text('Введите ваше имя'), sg.InputText()],
            [sg.Text('Введите ваш рост'), sg.InputText()],
            [sg.Button('Получить результаты анализа'), sg.Button('Отмена')] ]

# Задаем, куда будет сохранен файл отчета
path_pdf = 'path/to/pdf/file'

# Рендерим второе окошко
second_screen_layout = [  [sg.Text('Отчет о результатах измерения находится в: ' + path_pdf)], 
                [sg.Button('Завершить')]  ]

main_window = sg.Window('Анализ постурального контроля', main_screen_layout)
second_window = sg.Window('Результаты измерений', second_screen_layout)


## Начало анализа данных из файла
df = pd.read_csv(r"path/to/your/csv")
df = df.rename(columns = {"0" : "time", " 0.0 " : "angle_1", " 0.0.1" : "angle_2", " 0.0;" : "angle_3"})

df['angle_3'] = df['angle_3'].replace(to_replace = ';', value = '', regex = True)
df = df.astype({'angle_3': np.float64})

## Считаем средние углы 
angle_2_mean = round(df.angle_2.mean(), 2) 
angle_3_mean = round(df.angle_3.mean(), 2) 

anl_2 = df.angle_2.values
anl_3 = df.angle_3.values
rad_2 = np.deg2rad(anl_2)
rad_3 = np.deg2rad(anl_3)
df['w_2 * t'] = rad_2 * df['time']
df['w_3 * t'] = rad_3 * df['time']
df['sum_cos'] = np.cos(df['w_2 * t']) + np.cos(df['w_3 * t'])


while True:
    event, values = main_window.read()
    if event == sg.WIN_CLOSED or event == 'Отмена': # if user closes window or clicks cancel
        break
    surname = values[0]
    name = values[1]
    height = int(values[2])
    
    if event == 'Получить результаты анализа':
        main_window.close()
        second_window.read()
        if event == sg.WIN_CLOSED:
            break
                
second_window.close()

radius = round(height / 2 * df.sum_cos.std(), 2)
norm_radius = round(radius / height, 4)

## Конец анализа данных

## получаем рост и имя человека из GUI

## Границы доверительного интервала
left_border = 0.4855 
right_border = 0.5125

# Создаем структуру файла отчета
pdf = Document()
page = Page()
pdf.add_page(page)

layout = SingleColumnLayout(page)
font_path: Path = Path(__file__).parent / "GentiumBookPlus-Regular.ttf"
custom_font = TrueTypeFont.true_type_font_from_file(font_path)

layout.add(Paragraph("Протокол результатов измерений", 
    font = custom_font, 
    font_size = 16,
    horizontal_alignment = Alignment.CENTERED))
layout.add(Paragraph(
    "Благодарим за использование нашего диагностического инструмента, " + surname + ' ' + name + '.', 
    font = custom_font,
    font_size = 14))
layout.add(Paragraph("Рассчитанный радиус центра масс: " + str(radius) + " см", 
    font = custom_font,
    font_size = 14))
layout.add(Paragraph("Рассчитанное среднее значение угла крена: " + str(angle_2_mean) + " град", 
    font = custom_font,
    font_size = 14))
layout.add(Paragraph("Рассчитанное среднее значение угла тангажа: " + str(angle_3_mean) + " град", 
    font = custom_font,
    font_size = 14))
layout.add(Paragraph("Рассчитанный нормированный радиус центра масс: " + str(norm_radius), 
    font = custom_font, 
    font_size = 14))

if norm_radius > right_border or norm_radius < left_border:
    layout.add(Paragraph("Нормированный радиус центра масс отличается от нормы. Рекомендуем обратиться к врачу!", 
        font = custom_font, 
        font_size = 14))
else:
    layout.add(Paragraph("Нормированный радиус центра масс в пределах нормы",
        font = custom_font, 
        font_size = 14))
    
# Сохраняем файл отчета
with open(Path("output.pdf"), "wb") as pdf_file_handle:
    PDF.dumps(pdf_file_handle, pdf)
