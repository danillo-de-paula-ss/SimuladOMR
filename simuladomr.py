import PySimpleGUI as sg
import numpy as np
import cv2
import os
from glob import glob
from copy import deepcopy
import string
import pickle

def extrairMaiorCtn(img):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgTh = cv2.adaptiveThreshold(imgGray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 12)
    kernel = np.ones((2, 2), np.uint8)
    imgDil = cv2.dilate(imgTh, kernel)
    contours, _ = cv2.findContours(imgDil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    maiorCtn = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(maiorCtn)
    bbox = [x, y, w, h]
    recorte = img[y:y + h, x:x + w]
    recorte = cv2.resize(recorte, (600, 700))

    return recorte, bbox

def valid_float_br(text: str):
    if len(text) == 1 and text in '+-':
        return True
    else:
        for t in text:
            if t in ' ':
                return False
        try:
            float(text.replace(',', '.'))
            return True
        except:
            return False

class Program:
    def __init__(self):
        self.set_default()
    
    def set_default(self):
        self.imgs: dict[str, list] = {'imgOg': [], 'imgTp': [], 'imgTh': [], 'filename': [], 'imgRect': [[] for _ in range(5)], 'percentage': [[] for _ in range(5)], 'settingData': [[] for _ in range(5)], 'questionsMarked': [[] for _ in range(5)]}
        self.imgsBackup1 = deepcopy(self.imgs)
        self.current_img = 0
        self.img_length = 0

    def make_win(self):
        size_x = 25
        amount_fields = 5
        current_fields = 1
        border = 0

        setting_layout = [
            [sg.Button('Importar imagens', key='-BUTTON1-'), sg.Button('Importar pasta de imagens', key='-BUTTON2-'), sg.Push(), sg.Button('Remover todas as imagens', key='-BUTTON4-')],
            [sg.Text('Quantidade de campos para leitura:'), sg.Spin([i for i in range(1, 6)], initial_value=current_fields, size=(2, 0), enable_events=True, key='-SPIN-')],
            [sg.HorizontalSeparator()],
            [sg.Push(), sg.Text('Estrutura do arquivo .csv'), sg.Push()],
            [sg.Text('Selecionar gabarito oficial:'), sg.Combo(values=[], readonly=True, expand_x=True, key='-COMBO0-')],
            [*[sg.Frame('', [
                [sg.Text(f'Coluna {i}', expand_x=True, justification='center')],
                [sg.Input(expand_x=True, key=f'-INPUT{i}-', disabled=False if current_fields >= i else True)],
                [sg.Combo(values=['Campo 1'], readonly=True, expand_x=True, key=f'-COMBO{i}-', disabled=False if current_fields >= i else True, default_value=f'Campo {i}' if current_fields >= i else '')],
                [sg.Radio('Número', f'radio{i}', default=True, expand_x=True, size=(0, 1), key=f'-RADIO-A{i}-', disabled=False if current_fields >= i else True)],
                [sg.Radio('Texto', f'radio{i}', expand_x=True, size=(0, 1), key=f'-RADIO-B{i}-', disabled=False if current_fields >= i else True)],
                [sg.Text(size=(0, 1))],
                [sg.Checkbox('Unir', expand_x=True, key=f'-CHECKBOX{i}-', disabled=False if current_fields >= i else True, enable_events=True)],
            ], size=(87, 200), border_width=border) if i > 0 else sg.Frame('', [
                [sg.Text()],
                [sg.Text('Cabeçalhos:')],
                [sg.Text('Dados:')],
                [sg.Text('\nTipo de dados:', size=(10, 0))],
                [sg.Text('O que fazer com os dados?', size=(10, 0))]
            ], size=(87, 200), border_width=border) for i in range(6)]],
            [sg.Text('Parâmetros especiais:'), sg.Input(expand_x=True, key='-INPUT0-')],
            [sg.Push(), sg.Button('Exportar como CSV', key='-BUTTON3-'), sg.Push()]
        ]

        field_layouts = []
        for k in range(1, amount_fields + 1):
            field_layouts.append([
                [sg.Button('Salvar parâmetros', key=f'-BUTTON5-TAB{k}-'), sg.Button('Importar parâmetros', key=f'-BUTTON6-TAB{k}-')],
                [sg.HorizontalSeparator()],
                [sg.Push(), sg.Text('Retângulo'), sg.Push()],
                [sg.Text('Esquerda:', size=(size_x, 0)), sg.Input(key=f'-LEFT-TAB{k}-', enable_events=True)],
                [sg.Text('Topo:', size=(size_x, 0)), sg.Input(key=f'-TOP-TAB{k}-', enable_events=True)],
                [sg.Text('Largura:', size=(size_x, 0)), sg.Input(key=f'-WIDTH-TAB{k}-', enable_events=True)],
                [sg.Text('Altura:', size=(size_x, 0)), sg.Input(key=f'-HEIGHT-TAB{k}-', enable_events=True)],
                [sg.Push(), sg.Text('Abas'), sg.Push()],
                [sg.Text('Abas:', size=(size_x, 0)), sg.Input(key=f'-TAB-TAB{k}-', enable_events=True)],
                [sg.Text('Deslocamento entre abas em X:', size=(size_x, 0)), sg.Input(key=f'-OFFSET-X-TAB-TAB{k}-', enable_events=True)],
                [sg.Text('Deslocamento entre abas em Y:', size=(size_x, 0)), sg.Input(key=f'-OFFSET-Y-TAB-TAB{k}-', enable_events=True)],
                [sg.Push(), sg.Text('Linhas'), sg.Push()],
                [sg.Text('Linhas:', size=(size_x, 0)), sg.Input(key=f'-ROW-TAB{k}-', enable_events=True)],
                [sg.Text('Deslocamento entre linhas:', size=(size_x, 0)), sg.Input(key=f'-OFFSET-ROW-TAB{k}-', enable_events=True)],
                [sg.Push(), sg.Text('Colunas'), sg.Push()],
                [sg.Text('Colunas:', size=(size_x, 0)), sg.Input(key=f'-COLUMN-TAB{k}-', enable_events=True)],
                [sg.Text('Deslocamento entre colunas:', size=(size_x, 0)), sg.Input(key=f'-OFFSET-COLUMN-TAB{k}-', enable_events=True)],
                [sg.HorizontalSeparator()],
                [sg.Text('Orientação das questões:', size=(size_x, 0)), sg.Radio('Linha por linha', f'orientacao{k}', default=True, size=(19, 0), key=f'-RADIO1-TAB{k}-'), sg.Radio('Coluna por coluna', f'orientacao{k}', default=False, size=(0, 0), key=f'-RADIO2-TAB{k}-')],
                [sg.Text('Tolerância:', size=(size_x, 0)), sg.Slider(range=(0, 100), size=(35, 20), orientation='h', key=f'-PERCENTAGE-TAB{k}-')],
                [sg.Button('Aplicar', key=f'-BUTTON1-TAB{k}-'), sg.Button('Aplicar tudo', key=f'-BUTTON2-TAB{k}-')],
                [sg.VPush()],
                [sg.Push(), sg.Button('<', key=f'-BUTTON3-TAB{k}-'), sg.Text(self.imgs['filename'][self.current_img] if len(self.imgs['filename']) > 0 else '', size=(size_x, 0), justification='center', key=f'-TEXT1-TAB{k}-'), sg.Button('>', key=f'-BUTTON4-TAB{k}-'), sg.Push()],
                [sg.VPush()],
            ])

        main_frame = sg.Frame('', size=(600, 800), border_width=None, element_justification='center', layout=[
            [sg.TabGroup([[
                sg.Tab('Configurações', setting_layout),
                *[sg.Tab(f'Campo {i}', field_layouts[i - 1], key=f'-TAB{i}-',
                         visible=True if current_fields >= i else False) for i in range(1, 6)]
            ]], expand_x=True, expand_y=True, enable_events=True, key='-TABS-')]
        ])
        image_frame = sg.Frame('', size=(600, 800), border_width=None,
                               element_justification='center',
                               layout=[[sg.Image(filename='', key='-IMAGE-')]])
        layout = [[main_frame, image_frame]]
        return sg.Window('Extrator de respostas', layout=layout, size=(1280, 720), resizable=True, element_justification='center', finalize=True)
    
    def update_rect(self):
        for key in range(5):
            imgsMarked = []
            for index, img in enumerate(zip(self.imgs['imgOg'], self.imgs['imgTp'], self.imgs['imgTh'])):
                imgMarks = []
                for v1 in self.imgs['imgRect'][key][index]:
                    marks = []
                    for k2, v2 in enumerate(v1):
                        x, y, w, h = v2
                        cv2.rectangle(img[1], (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.rectangle(img[2], (x, y), (x + w, y + h), (255, 255, 255), 1)
                        rect = img[2][y:y + h, x:x + w]
                        height, width = rect.shape[:2]
                        size = height * width
                        black = cv2.countNonZero(rect)
                        try:
                            percentage = round((black / size) * 100, 2)
                        except ZeroDivisionError:
                            break
                        if percentage >= 100 - self.imgs['percentage'][key][index]:
                            cv2.rectangle(img[1], (x, y), (x + w, y + h), (255, 0, 0), 2)
                            marks.append(k2)
                    imgMarks.append(marks)
                imgsMarked.append(imgMarks)
            self.imgs['questionsMarked'][key] = imgsMarked

    def import_assets(self, path):
        if path != '':
            extensions = ('.png', '.jpg', '.jpeg', '.jpe', '.jfif', '.exif')
            paths: list[str] = path if type(path) == tuple else [p for p in glob(path + r'\*') if os.path.splitext(p)[-1] in extensions]
            for file in paths:
                img = cv2.imread(file, 1)
                img = cv2.resize(img, (600, 700))
                imgTp, _ = extrairMaiorCtn(img)
                imgGray = cv2.cvtColor(imgTp, cv2.COLOR_BGR2GRAY)
                _, imgTh = cv2.threshold(imgGray, 70, 255, cv2.THRESH_BINARY_INV)
                self.imgs['imgOg'].append(img)
                self.imgs['imgTp'].append(imgTp)
                self.imgs['imgTh'].append(imgTh)
                self.imgs['filename'].append(os.path.basename(file))
                for k in range(5):
                    self.imgs['imgRect'][k].append([])
                    self.imgs['percentage'][k].append(0)
                    self.imgs['settingData'][k].append(['', '', '', '', '', '', '', '', '', '', '', 0.0, True, False])
                    self.imgs['questionsMarked'][k].append([])
            self.imgsBackup1 = deepcopy(self.imgs)
            self.img_length = len(self.imgs['filename'])

    def main(self):
        window = self.make_win()
        tabs_keys = [[f'-LEFT-TAB{i}-', f'-TOP-TAB{i}-', f'-WIDTH-TAB{i}-', f'-HEIGHT-TAB{i}-', f'-TAB-TAB{i}-', f'-OFFSET-X-TAB-TAB{i}-', f'-OFFSET-Y-TAB-TAB{i}-', f'-ROW-TAB{i}-', f'-OFFSET-ROW-TAB{i}-', f'-COLUMN-TAB{i}-', f'-OFFSET-COLUMN-TAB{i}-'] for i in range(1, 6)]

        while True:
            event, values = window.read()
            # main tab
            if event == sg.WIN_CLOSED:
                window.close()
                break

            if event == '-SPIN-':
                for k in range(1, 6):
                    window[f'-TAB{k}-'].update(visible=True if values['-SPIN-'] >= k else False)
                    window[f'-INPUT{k}-'].update(disabled=False if values['-SPIN-'] >= k else True)
                    window[f'-COMBO{k}-'].update('' if values['-SPIN-'] < k else values[f'-COMBO{k}-'] if values[f'-COMBO{k}-'] in [f'Campo {i + 1}' for i in range(values['-SPIN-'])] else f'Campo {k}', 
                                                 disabled=False if values['-SPIN-'] >= k else True,
                                                 values=[f'Campo {i + 1}' for i in range(values['-SPIN-'])])
                    window[f'-RADIO-A{k}-'].update(disabled=False if values['-SPIN-'] >= k else True)
                    window[f'-RADIO-B{k}-'].update(disabled=False if values['-SPIN-'] >= k else True)
                    window[f'-CHECKBOX{k}-'].update(disabled=False if values['-SPIN-'] >= k else True)

            if event == '-BUTTON1-':
                file_path = sg.popup_get_file('', no_window=True, multiple_files=True, file_types=(
                    ('Todo tipo de imagem', ('*.png', '*.jpg', '*.jpeg', '*.jpe', '*.jfif', '*.exif')),
                    ('PNG', ('*.png')),
                    ('JPEG', ('*.jpg', '*.jpeg', '*.jpe', '*.jfif', '*.exif'))
                    ))
                self.import_assets(file_path)
                if file_path != '':
                    window['-COMBO0-'].update(self.imgs['filename'][0], values=self.imgs['filename'])

            if event == '-BUTTON2-':
                folder_path = sg.popup_get_folder('', no_window=True)
                self.import_assets(folder_path)
                if folder_path != '':
                    window['-COMBO0-'].update(self.imgs['filename'][0], values=self.imgs['filename'])

            if event == '-BUTTON3-':
                index = [i[0] for i in enumerate(self.imgs['filename']) if i[1] == values['-COMBO0-']]
                index = index[0] if index != [] else None
                if index is not None and len(self.imgs['questionsMarked'][0][0]) > 0:
                    file_path = sg.popup_get_file('', no_window=True, save_as=True, default_path='resultado', default_extension='.csv', file_types=(("CSV Files", ".csv"),))
                    if file_path != '':
                        try:
                            parameters = [sp.split('=') for sp in ''.join([char for char in values['-INPUT0-'] if char != ' ']).split(';')]
                            parameters = [p for p in parameters if len(p) == 2]
                            parameters = [p for p in parameters if p[1] != '' and p[1].isnumeric()]
                            parameter_values = [int(p[1]) for p in parameters]
                        except:
                            parameters = []
                            parameter_values = []
                        
                        tab_sequence = []
                        for key in [f'-COMBO{i}-' for i in range(1, 6)]:
                            if values[key] != '':
                                tab_sequence.append(int(values[key][-1]) - 1)

                        headers = []
                        result_sheets = []
                        for tab_index, tab in enumerate(tab_sequence, 1):
                            result_sheet = []
                            correct_answers = [i for i in self.imgs['questionsMarked'][tab]][index]
                            answers_marked = [[i for i in self.imgs['questionsMarked'][tab]][j] for j in range(self.img_length) if j != index]

                            headers.append([values[f'-INPUT{tab_index}-']] if values[f'-CHECKBOX{tab_index}-'] else [f"{values[f'-INPUT{tab_index}-']} {k + 1}" for k in range(len(correct_answers))])

                            if values[f'-RADIO-A{tab_index}-']:
                                correct_answers_sheet = []
                                for answer in correct_answers:
                                    if len(answer) == 1:
                                        correct_answers_sheet.append(str(answer[0]))
                                    elif len(answer) > 1:
                                        correct_answers_sheet.append(','.join(map(lambda k: str(k), answer)))
                                    elif len(answer) == 0:
                                        correct_answers_sheet.append('')
                                result_sheet.append(correct_answers_sheet)

                                for answers in answers_marked:
                                    answers_sheet = []
                                    for answer in answers:
                                        if len(answer) == 1:
                                            answers_sheet.append(str(answer[0]))
                                        elif len(answer) > 1:
                                            answers_sheet.append(','.join(map(lambda k: str(k), answer)))
                                        elif len(answer) == 0:
                                            answers_sheet.append('')
                                    result_sheet.append(answers_sheet)
                                result_sheets.append(result_sheet if not values[f'-CHECKBOX{tab_index}-'] else [[''.join(k)] for k in result_sheet])

                            elif values[f'-RADIO-B{tab_index}-']:
                                # set correct answers
                                successes = failures = 0
                                correct_answers_sheet = []
                                for answer in correct_answers:
                                    for parameter in parameters:
                                        if len(answer) == int(parameter[1]):
                                            correct_answers_sheet.append(parameter[0])
                                    if len(answer) == 1 and len(answer) not in parameter_values:
                                        correct_answers_sheet.append(string.ascii_uppercase[answer[0]])
                                    elif len(answer) > 1 and len(answer) not in parameter_values:
                                        correct_answers_sheet.append(','.join(
                                            map(lambda k: string.ascii_uppercase[k], answer)
                                            ))
                                    elif len(answer) == 0 and len(answer) not in parameter_values:
                                        correct_answers_sheet.append('')
                                result_sheet.append(correct_answers_sheet)

                                # compare other answers with correct answers
                                for answers in answers_marked:
                                    answers_sheet = []
                                    for answer, correct_answer in zip(answers, correct_answers_sheet):
                                        if correct_answer in [value[0] for value in parameters]:
                                            answers_sheet.append(correct_answer)
                                        else:
                                            if len(answer) > 1:
                                                answers_sheet.append(','.join(
                                                    map(lambda k: string.ascii_uppercase[k], answer)
                                                    ))
                                            elif len(answer) == 1:
                                                if string.ascii_uppercase[answer[0]] == correct_answer:
                                                    successes += 1
                                                else:
                                                    failures += 1
                                                answers_sheet.append(string.ascii_uppercase[answer[0]])
                                            else:
                                                for parameter in parameters:
                                                    if int(parameter[1]) == 0:
                                                        answers_sheet.append(parameter[0])
                                                if 0 not in parameter_values:
                                                    answers_sheet.append('')
                                    result_sheet.append(answers_sheet)
                                result_sheets.append(result_sheet if not values[f'-CHECKBOX{tab_index}-'] else [[''.join(k)] for k in result_sheet])

                        with open(file_path, 'wt') as file:
                            file.writelines([';'.join([';'.join(k) for k in headers]) + '\n',
                                            *[';'.join([';'.join(k[l]) for k in result_sheets]) + '\n' for l in range(len(result_sheets[0]))]])
                        
                        sg.popup_ok('Arquivo CSV foi gerado com sucesso.', title='Aviso')

            if event == '-BUTTON4-':
                default_parameters = ['', '', '', '', '', '', '', '', '', '', '', 0.0, True, False]
                for i, tab_keys in enumerate(tabs_keys, 1):
                    for index, key in enumerate(tab_keys + [f'-PERCENTAGE-TAB{i}-', f'-RADIO1-TAB{i}-', f'-RADIO2-TAB{i}-']):
                        window[key].update(default_parameters[index])
                    window[f'-TEXT1-TAB{i}-'].update('')
                window['-IMAGE-'].update(filename='')
                window['-COMBO0-'].update(values=[])
                self.set_default()

            # other tabs
            for i, tab_keys in enumerate(tabs_keys, 1):
                if self.img_length > 0:
                    if (event == f'-BUTTON1-TAB{i}-' or event == f'-BUTTON2-TAB{i}-'):
                        imgBackup2 = deepcopy(self.imgs)
                        self.imgs = deepcopy(self.imgsBackup1)

                        if event == f'-BUTTON1-TAB{i}-':
                            for k1 in range(self.img_length):
                                if k1 != self.current_img:
                                    for k2 in self.imgs.keys():
                                        if k2 in ['imgRect', 'percentage', 'settingData', 'questionsMarked']:
                                            for k3 in range(len(self.imgs['imgRect'])):
                                                self.imgs[k2][k3][k1] = imgBackup2[k2][k3][k1]
                                        else:
                                            self.imgs[k2][k1] = imgBackup2[k2][k1]

                        for k1 in range(len(self.imgs['imgRect'])):
                            if k1 != i - 1:
                                for k2 in self.imgs.keys():
                                    if k2 in ['imgRect', 'percentage', 'settingData', 'questionsMarked']:
                                        self.imgs[k2][k1] = imgBackup2[k2][k1]

                        dimensions = []
                        data = []
                        for key in tab_keys:
                            dimensions.append(float(values[key].replace(',', '.')) if values[key] != '' else 1 if key in [f'-WIDTH-TAB{i}-', f'-HEIGHT-TAB{i}-', f'-TAB-TAB{i}-', f'-ROW-TAB{i}-', f'-COLUMN-TAB{i}-'] else 0)
                            data.append(values[key])
                        data.extend(list(map(lambda key: values[key], [f'-PERCENTAGE-TAB{i}-', f'-RADIO1-TAB{i}-', f'-RADIO2-TAB{i}-'])))

                        rects = []
                        for tab in range(int(dimensions[4])):
                            if values[f'-RADIO1-TAB{i}-']:
                                for row in range(int(dimensions[7])):
                                    columns = []
                                    for column in range(int(dimensions[9])):
                                        columns.append(
                                            (int(dimensions[0] + (dimensions[2] + dimensions[10]) * column + dimensions[5] * tab),
                                            int(dimensions[1] + (dimensions[3] + dimensions[8]) * row + dimensions[6] * tab),
                                            int(dimensions[2]),
                                            int(dimensions[3]))
                                        )
                                    rects.append(columns)
                            elif values[f'-RADIO2-TAB{i}-']:
                                for column in range(int(dimensions[9])):
                                    rows = []
                                    for row in range(int(dimensions[7])):
                                        rows.append(
                                            (int(dimensions[0] + (dimensions[2] + dimensions[10]) * column + dimensions[5] * tab),
                                            int(dimensions[1] + (dimensions[3] + dimensions[8]) * row + dimensions[6] * tab),
                                            int(dimensions[2]),
                                            int(dimensions[3]))
                                        )
                                    rects.append(rows)

                        if event == f'-BUTTON1-TAB{i}-':
                            self.imgs['imgRect'][i - 1][self.current_img] = rects
                            self.imgs['percentage'][i - 1][self.current_img] = int(values[f'-PERCENTAGE-TAB{i}-'])
                            self.imgs['settingData'][i - 1][self.current_img] = data[:]
                        elif event == f'-BUTTON2-TAB{i}-':
                            for k in range(self.img_length):
                                self.imgs['imgRect'][i - 1][k] = rects
                                self.imgs['percentage'][i - 1][k] = int(values[f'-PERCENTAGE-TAB{i}-'])
                                self.imgs['settingData'][i - 1][k] = data[:]
                        self.update_rect()

                    if (event == f'-BUTTON3-TAB{i}-' or event == f'-BUTTON4-TAB{i}-' or (event == '-TABS-' and values['-TABS-'] == f'-TAB{i}-')):
                        if event == f'-BUTTON3-TAB{i}-':
                            self.current_img -= 1
                            if self.current_img < 0:
                                self.current_img = self.img_length - 1
                        elif event == f'-BUTTON4-TAB{i}-':
                            self.current_img += 1
                            if self.current_img >= self.img_length:
                                self.current_img = 0
                        for index, key in enumerate(tab_keys + [f'-PERCENTAGE-TAB{i}-', f'-RADIO1-TAB{i}-', f'-RADIO2-TAB{i}-']):
                            window[key].update(self.imgs['settingData'][i - 1][self.current_img][index])

                    if event == f'-BUTTON5-TAB{i}-':
                        file_path = sg.popup_get_file('', no_window=True, save_as=True, default_path=f'parâmetros {i}', default_extension='.pkl', file_types=(("PKL Files", ".pkl"),))
                        if file_path != '':
                            with open(file_path, 'wb') as file:
                                file.write(pickle.dumps([self.imgs['imgRect'], self.imgs['percentage'], self.imgs['settingData']]))

                    if event == f'-BUTTON6-TAB{i}-':
                        file_path = sg.popup_get_file('', no_window=True, default_extension='.pkl', file_types=(("PKL Files", ".pkl"),))
                        if file_path != '':
                            with open(file_path, 'rb') as file:
                                imgs: list = pickle.load(file)
                            for k1 in range(5):
                                for k2 in range(self.img_length):
                                    if k2 >= len(imgs[0][0]):
                                        self.imgs['imgRect'][k1][k2] = imgs[0][k1][-1]
                                        self.imgs['percentage'][k1][k2] = imgs[1][k1][-1]
                                        self.imgs['settingData'][k1][k2] = imgs[2][k1][-1]
                                    else:
                                        self.imgs['imgRect'][k1][k2] = imgs[0][k1][k2]
                                        self.imgs['percentage'][k1][k2] = imgs[1][k1][k2]
                                        self.imgs['settingData'][k1][k2] = imgs[2][k1][k2]
                            for index, key in enumerate(tab_keys + [f'-PERCENTAGE-TAB{i}-', f'-RADIO1-TAB{i}-', f'-RADIO2-TAB{i}-']):
                                window[key].update(self.imgs['settingData'][i - 1][self.current_img][index])
                            self.update_rect()

            for tab_keys in tabs_keys:
                for key in tab_keys:
                    if event == key:
                        text = values[key]
                        if not valid_float_br(text):
                            window[key].update(value=text[:-1])

            if self.img_length > 0:
                imgbytes = cv2.imencode('.png', self.imgs['imgTp'][self.current_img])[1].tobytes()
                window['-IMAGE-'].update(data=imgbytes)
                for i in range(1, 6):
                    window[f'-TEXT1-TAB{i}-'].update(
                        self.imgs['filename'][self.current_img])

        window.close()


if __name__ == '__main__':
    Program().main()
