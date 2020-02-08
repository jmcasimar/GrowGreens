#!/usr/bin/env python
import os
import csv
import time
import PySimpleGUI as sg
from PIL import Image, ImageTk
import io
import base64
import re

# Pendiente integrar serialController to manage connection between devices
class GUI:
    def __init__(self, logger = None, serialControl = None):
        # Logger
        self.log = logger
        # Serial controller
        self.ser = serialControl

        # Colors
        self.black90 = '#3c3c3b'
        self.green1 = '#00783e'
        self.green2 = '#368f3f'
        self.green3 = '#00b44f'
        self.green4 = '#82bc00'
        self.disable_color = (self.black90, self.black90)

        # Table and image paths
        actualDirectory = os.getcwd()
        if actualDirectory.endswith('src'):
            self.filename = 'config.csv'
            self.paths = ['./GUI_Pics/Siembra.png',
                          './GUI_Pics/Siembra8.png',
                          './GUI_Pics/Siembra7.png',
                          './GUI_Pics/Siembra6.png',
                          './GUI_Pics/Siembra5.png',
                          './GUI_Pics/Siembra4.png',
                          './GUI_Pics/Siembra3.png',
                          './GUI_Pics/Siembra2.png',
                          './GUI_Pics/Siembra1.png',
                          './GUI_Pics/Tina.png',
                          './GUI_Pics/minus.png',
                          './GUI_Pics/plus.png']
        else:
            self.filename = './src/config.csv'
            self.paths = ['./src/GUI_Pics/Siembra.png',
                          './src/GUI_Pics/Siembra8.png',
                          './src/GUI_Pics/Siembra7.png',
                          './src/GUI_Pics/Siembra6.png',
                          './src/GUI_Pics/Siembra5.png',
                          './src/GUI_Pics/Siembra4.png',
                          './src/GUI_Pics/Siembra3.png',
                          './src/GUI_Pics/Siembra2.png',
                          './src/GUI_Pics/Siembra1.png',
                          './src/GUI_Pics/Tina.png',
                          './src/GUI_Pics/minus.png',
                          './src/GUI_Pics/plus.png']

        self.data = []
        self.header_list = []

        self.timer = 0
        self.timerAux = False

        # UI Variables
        self.cycleTime = 15
        self.evTime = 5
        self.piso = '1'
        self.lado = 'A'
        self.etapa = '1'
        self.solucion = 'H2O'

        # Aux variables
        self.total = 0

        # Main Window
        self.window = None
        self.isOpen = True

        self.DEF_BUTTON_COLOR = ('red', self.black90)

        # Seeding variables
        self.SeedValues = {'SA1':0, 'SA2':0, 'SA3':0, 'SA4':0, 'SB1':0, 'SB2':0, 'SB3':0, 'SB4':0}

        # array path


        # Add your new theme colors and settings
        sg.LOOK_AND_FEEL_TABLE['GrowGreens'] = {'BACKGROUND': self.black90,
                                                'TEXT': self.green4,
                                                'INPUT': '#d2d2d2',
                                                'TEXT_INPUT': 'black',
                                                'SCROLL': '#d2d2d2',
                                                'BUTTON': ('black', self.green1),
                                                'PROGRESS': ('white', self.green2),
                                                'BORDER': 3, 'SLIDER_DEPTH': 3, 'PROGRESS_DEPTH': 3,
                                                }
        # Switch to use your newly created theme
        sg.theme('GrowGreens')


    def str2log(self, msg, level = 'DEBUG'):
        if self.log!=None:
            if (level==0 or level=='DEBUG'): self.log.debug(msg)
            elif (level==1 or level=='INFO'): self.log.info(msg)
            elif (level==2 or level=='WARNING'): self.log.warning(msg)
            elif (level==3 or level=='ERROR'): self.log.error(msg)
            elif (level==4 or level=='CRITICAL'): self.log.critical(msg)
        else:
            print(msg)

    def serialMsg(self, msg):
        if self.ser != None:
            self.ser.write(self.ser.generalControl, msg)
        else:
            self.str2log(msg, 3)

    def str2UpdateCycle(self, valor):
        msg = 'solenoid,setCycleTime,'
        msg += str(valor)
        return msg

    def str2UpdateEV(self, piso, lado, etapa, solucion, valor):
        if(lado=='A'): ladoInt = 0
        else: ladoInt = 4
        if(solucion=='H2O'): sol = 0
        else: sol = int(solucion)

        msg = 'solenoid,setTimeOn,'
        msg += str(int(piso)-1)
        msg += ','
        msg += str(etapa+ladoInt-1)
        msg += ','
        msg += str(sol)
        msg += ','
        msg += str(valor)

        return msg

    def getEVlimits(self, cycle, etapa):
        evNumber = 32
        minSec = 3
        factor = 0.0833*etapa+0.1567
        maxSec = int((cycle*60/evNumber)*factor)
        if maxSec < minSec: maxSec = minSec
        return minSec, maxSec

    def getTotalIrrigationTime(self, dataSource):
        sum = [0, 0, 0, 0, 0]
        for i in range(len(dataSource)-1):
            for j in range(len(sum)):
                sum[j] += int(dataSource[i][j+1])
        return max(sum)

    def getEVvalue(self, piso, lado, etapa, solucion, dataSource):
        if(lado=='A'): ladoInt = 0
        else: ladoInt = 4
        if(solucion=='H2O'): sol = 1
        else: sol = int(solucion) + 1
        columna = ((piso-1)*8) + (etapa+ladoInt) - 1
        return dataSource[columna][sol]

    def changeEVvalue(self, piso, lado, etapa, solucion, dataSource, cycleTime, value, factor = 0.5):
        if(lado=='A'): ladoInt = 0
        else: ladoInt = 4
        if(solucion=='H2O'): sol = 1
        else: sol = int(solucion) + 1
        columna = ((piso-1)*8) + (etapa+ladoInt) - 1
        oldValue = dataSource[columna][sol]
        dataSource[columna][sol] = value
        if (self.getTotalIrrigationTime(dataSource)<=(int(cycleTime)*60*factor)):
            return True
        else:
            dataSource[columna][sol] = oldValue
            return False

    def rewriteCSV(self, file, header, dataSource):
        with open(file, mode='w', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(dataSource)

    def checkEV(self):
        if self.piso!='' and self.lado!='' and self.etapa!='' and self.solucion!='':
            evMin, evMax = self.getEVlimits(self.cycleTime, int(self.etapa))
            val = self.getEVvalue(int(self.piso), self.lado, int(self.etapa), self.solucion, self.data)
            self.window['evTime'].Update(range=(evMin, evMax))
            self.window['evTime'].Update(value=val)
        else:
            self.window['evTime'].Update(value=5, range=(5, 5))
            self.window['Actualizar'].Update(button_color=self.disable_color, disabled=True)

    def updateCurrentTimeValues(self):
        if(self.lado=='A'): ladoInt = 0
        else: ladoInt = 4
        if(self.solucion=='H2O'): sol = 1
        else: sol = int(self.solucion) + 1
        columna = ((int(self.piso)-1)*8)
        self.window['GerminacionATxt'].update(str(self.data[columna][sol])+' s')
        self.window['Etapa1ATxt'].update(str(self.data[columna+1][sol])+' s')
        self.window['Etapa2ATxt'].update(str(self.data[columna+2][sol])+' s')
        self.window['CosechaATxt'].update(str(self.data[columna+3][sol])+' s')
        self.window['GerminacionBTxt'].update(str(self.data[columna+4][sol])+' s')
        self.window['Etapa1BTxt'].update(str(self.data[columna+5][sol])+' s')
        self.window['Etapa2BTxt'].update(str(self.data[columna+6][sol])+' s')
        self.window['CosechaBTxt'].update(str(self.data[columna+7][sol])+' s')


    def get_img_data(self, f, maxsize=(450, 300), first=False):
        """Generate image data using PIL
        """
        img = Image.open(f)
        img.thumbnail(maxsize)
        if first:                     # tkinter is inactive the first time
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            del img
            return bio.getvalue()
        return ImageTk.PhotoImage(img)

    def GraphicButton(self,text, key, image_data, maxsize=(200, 50)):
        '''
        A user defined element.  Use this function inside of your layouts as if it were a Button element (it IS a Button Element)
        Only 3 parameters are required.

        :param text: (str) Text you want to display on the button
        :param key:  (Any) The key for the button
        :param image_data: (str) The Base64 image to use on the button
        :param color: Tuple[str, str] Button color
        :param size: Tuple[int, int] Size of the button to display in pixels (width, height)
        :return: (PySimpleGUI.Button) A button with a resized Base64 image applied to it
        '''
        return sg.Button(text, image_data=self.get_img_data(image_data, maxsize,first=True), button_color=self.DEF_BUTTON_COLOR, font='Any 15', pad=(0, 0), key=key, border_width=0)

    def ResetSeedValues(self):
        self.SeedValues = {'SA1':0, 'SA2':0, 'SA3':0, 'SA4':0, 'SB1':0, 'SB2':0, 'SB3':0, 'SB4':0}
        self.window['B_A4'].Update(value=self.SeedValues['SA4'])
        self.window['B_A3'].Update(value=self.SeedValues['SA3'])
        self.window['B_A2'].Update(value=self.SeedValues['SA2'])
        self.window['B_A1'].Update(value=self.SeedValues['SA1'])
        self.window['B_B4'].Update(value=self.SeedValues['SB4'])
        self.window['B_B3'].Update(value=self.SeedValues['SB3'])
        self.window['B_B2'].Update(value=self.SeedValues['SB2'])
        self.window['B_B1'].Update(value=self.SeedValues['SB1'])

    def begin(self):
         if self.filename is not None:
             with open(self.filename, "r") as infile:
                 reader = csv.reader(infile)
                 self.header_list = next(reader)
                 try:
                     self.data = list(reader)  # read everything else into a list of rows
                 except:
                     sg.popup_error('Error reading file')
                     return

         self.total = self.getTotalIrrigationTime(self.data)
         self.cycleTime = self.data[-1][1]

         col1 = sg.Column([
                      [sg.Text('Grow Greens', size=(44, 1), justification='center', font=("Helvetica 30 bold"), relief=sg.RELIEF_RIDGE, border_width=5)],
                      [sg.Text('_' * 150)]
               ])

         col2 = sg.Column([
                      [sg.Frame(layout=[
                          #[sg.Text(' '*50, key='Error1', text_color='red')],
                          [sg.Text('Selección de piso a visualizar:')],
                          [sg.Radio('Piso 1             ', "PISO", key='Piso1', default=True, text_color='white'),
                           sg.Radio('Piso 2             ', "PISO", key='Piso2', text_color='white'),
                           sg.Radio('Piso 3             ', "PISO", key='Piso3', text_color='white'),
                           sg.Radio('Piso 4', "PISO", key='Piso4', text_color='white')],
                          [sg.Text('Selección de solución a visualizar:')],
                          [sg.Radio('Agua', "SOL", key='H2O', default=True, text_color='white'),
                           sg.Radio('Solución 1', "SOL", key='S1', text_color='white'),
                           sg.Radio('Solución 2', "SOL", key='S2', text_color='white'),
                           sg.Radio('Solución 3', "SOL", key='S3', text_color='white'),
                           sg.Radio('Solución 4', "SOL", key='S4', text_color='white')],
                          #[sg.Text('')],
                          [sg.Text('Selección de etapa a editar:'),
                          sg.Text('Tiempo (s)'),
                           sg.Slider(range=(5, 5), orientation='h', key='evTime', size=(10, 15), default_value=self.evTime),
                           #sg.Text(' '*10),
                           sg.Button('Actualizar', size=(8, 1), key="Actualizar", pad=(10,10), disabled=True, button_color=self.disable_color)],
                          [sg.Radio('Germinación A', "Etapa", key='GerminacionA', default=True, text_color='white'),
                           sg.Radio('Etapa 1 A  ', "Etapa", key='Etapa1A', text_color='white'),
                           sg.Radio('Etapa 2 A  ', "Etapa", key='Etapa2A', text_color='white'),
                           sg.Radio('Cosecha A', "Etapa", key='CosechaA', text_color='white')],
                          [sg.Text(self.data[0][1]+' s', key='GerminacionATxt', size=(13, 1), justification='center'),
                           sg.Text(self.data[1][1]+' s', key='Etapa1ATxt', size=(10, 1), justification='center'),
                           sg.Text(self.data[2][1]+' s', key='Etapa2ATxt', size=(13, 1), justification='center'),
                           sg.Text(self.data[3][1]+' s', key='CosechaATxt', size=(11, 1), justification='center')],
                          [sg.Image(data=self.get_img_data(self.paths[9], first=True))],
                          [sg.Text(self.data[7][1]+' s', key='CosechaBTxt', size=(13, 1), justification='center'),
                           sg.Text(self.data[6][1]+' s', key='Etapa2BTxt', size=(10, 1), justification='center'),
                           sg.Text(self.data[5][1]+' s', key='Etapa1BTxt', size=(13, 1), justification='center'),
                           sg.Text(self.data[4][1]+' s', key='GerminacionBTxt', size=(11, 1), justification='center')],
                          [sg.Radio('Cosecha B     ', "Etapa", key='CosechaB', text_color='white'),
                           sg.Radio('Etapa 2 B  ', "Etapa", key='Etapa2B', text_color='white'),
                           sg.Radio('Etapa 1 B  ', "Etapa", key='Etapa1B', text_color='white'),
                           sg.Radio('Germinación B', "Etapa", key='GerminacionB', text_color='white')],
                          #[sg.Table(values=self.data,
                         #           key='Table',
                         #           headings=self.header_list,
                         #           max_col_width=25,
                         #           auto_size_columns=True,
                         #           justification='center',
                         #           num_rows=min(len(self.data), 8))],
                          [sg.Text('Ciclo de riego:', size=(10, 1)),
                          sg.Text(self.data[-1][1]+' min', key='TiempoCiclo', size=(6,1), justification='center'),
                          sg.Slider(range=(int(self.total/30)+1, 20), key='cycleTime', orientation='h', size=(15, 15), default_value=self.cycleTime),
                          sg.Button('Actualizar Ciclo', size=(12, 1), key="Actualizar Ciclo", pad=(10,10), disabled=True, button_color=self.disable_color)],
                          #[sg.Text('Piso:'),
                           #sg.Text('Lado:'),
                           #sg.Text('Etapa:'),
                           #sg.Text('Solución:'),
                           #sg.Text(' '*40, key='Error2', text_color='red')],
                          #[sg.Combo(('', '1', '2', '3', '4'), key="Piso", default_value='', size=(4, 1)),
                           #sg.Combo(('', 'A', 'B'), key="Lado", default_value='', size=(4, 1)),
                           #sg.Combo(('', '1', '2', '3', '4'), key="Etapa", default_value='', size=(4, 1)),
                           #sg.Combo(('', 'H2O', '1', '2', '3', '4'), key="Sol", default_value='', size=(4, 1)),

                          ], title='Configuración de riego', relief=sg.RELIEF_SUNKEN)]
                ])

         colB1 = sg.Column([
                      [self.GraphicButton('','B_A4+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SA4'] ,key='B_A4')],
                      [self.GraphicButton('','B_A4-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_A3+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SA3'],key='B_A3')],
                      [self.GraphicButton('','B_A3-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_A2+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SA2'],key='B_A2')],
                      [self.GraphicButton('','B_A2-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_A1+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SA1'],key='B_A1')],
                      [self.GraphicButton('','B_A1-',self.paths[10],maxsize=(30,30))],
         ])
         colB2 = sg.Column([
                      [self.GraphicButton('','B_B4+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SB4'],key='B_B4')],
                      [self.GraphicButton('','B_B4-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_B3+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SB3'],key='B_B3')],
                      [self.GraphicButton('','B_B3-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_B2+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SB2'],key='B_B2')],
                      [self.GraphicButton('','B_B2-',self.paths[10],maxsize=(30,30))],
                      [sg.Text('')],
                      [self.GraphicButton('','B_B1+',self.paths[11],maxsize=(30,30))],
                      [sg.Text(self.SeedValues['SB1'],key='B_B1')],
                      [self.GraphicButton('','B_B1-',self.paths[10],maxsize=(30,30))],
         ])

         col3 = sg.Column([
                      [sg.Frame(layout=[
                          [sg.Text('Presiona el botón de + o - para indicar en que piso se siembra', size = (56, 1), justification='center')],
                          [sg.Text('presiona la cantidad de veces que se haya sembrado', size = (56, 1), justification='center')],
                          [colB1,
                          sg.Image(data=self.get_img_data(self.paths[0], maxsize=(380,443), first=True), key='siembra'),
                          colB2],
                      ], title='Bitácora de siembra', relief=sg.RELIEF_SUNKEN)]
                ])

         layout = [[col1],[col2, col3]]

         self.window = sg.Window('Main', layout, no_titlebar=False,
                            auto_size_text=True, finalize=True)

         self.str2log('GUI started correctly', level = 1)

    def run(self):
        try:
            event, values = self.window.read(timeout=0, timeout_key='timeout')
            regex = re.findall('B_[AB][1-4][+-]', event)

            if int(values['cycleTime']) != self.cycleTime:
                self.cycleTime = int(values['cycleTime'])
                if(self.data[-1][1] == str(self.cycleTime)):
                    self.window['Actualizar Ciclo'].Update(button_color=self.disable_color, disabled=True)
                else: self.window['Actualizar Ciclo'].Update(button_color=('black', self.green1), disabled=False)
                if self.piso=='' or self.lado=='' or self.etapa=='' or self.solucion=='':
                    self.window['evTime'].Update(range=(5, 5))

            if int(values['evTime']) != self.evTime:
                self.evTime = int(values['evTime'])
                if self.piso!='' and self.lado!='' and self.etapa!='' and self.solucion!='':
                    ev = self.getEVvalue(int(self.piso), self.lado, int(self.etapa), self.solucion, self.data)
                    if (int(ev) == self.evTime): self.window['Actualizar'].Update(button_color=self.disable_color, disabled=True)
                    else: self.window['Actualizar'].Update(button_color=('black', self.green1), disabled=False)



            #if values['Piso'] != self.piso:
            #    self.piso = values['Piso']
            #    self.checkEV()

            if values['Piso1']:
                if (self.piso!=1):
                    self.piso = 1
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['Piso2']:
                if (self.piso!=2):
                    self.piso = 2
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['Piso3']:
                if (self.piso!=3):
                    self.piso = 3
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['Piso4']:
                if (self.piso!=1):
                    self.piso = 4
                    self.checkEV()
                    self.updateCurrentTimeValues()


            #if values['Lado'] != self.lado:
            #    self.lado = values['Lado']
            #    self.checkEV()

            #if values['Etapa'] != self.etapa:
            #    self.etapa = values['Etapa']
            #    self.checkEV()

            if values['GerminacionA']:
                if (self.lado!='A' or self.etapa!=1):
                    self.lado = 'A'
                    self.etapa = 1
                    self.checkEV()
            if values['Etapa1A']:
                if (self.lado!='A' or self.etapa!=2):
                    self.lado = 'A'
                    self.etapa = 2
                    self.checkEV()
            if values['Etapa2A']:
                if (self.lado!='A' or self.etapa!=3):
                    self.lado = 'A'
                    self.etapa = 3
                    self.checkEV()
            if values['CosechaA']:
                if (self.lado!='A' or self.etapa!=4):
                    self.lado = 'A'
                    self.etapa = 4
                    self.checkEV()
            if values['GerminacionB']:
                if (self.lado!='B' or self.etapa!=1):
                    self.lado = 'B'
                    self.etapa = 1
                    self.checkEV()
            if values['Etapa1B']:
                if (self.lado!='B' or self.etapa!=2):
                    self.lado = 'B'
                    self.etapa = 2
                    self.checkEV()
            if values['Etapa2B']:
                if (self.lado!='B' or self.etapa!=3):
                    self.lado = 'B'
                    self.etapa = 3
                    self.checkEV()
            if values['CosechaB']:
                if (self.lado!='B' or self.etapa!=4):
                    self.lado = 'B'
                    self.etapa = 4
                    self.checkEV()


            #if values['Sol'] != self.solucion:
            #    self.solucion = values['Sol']
            #    self.checkEV()

            if values['H2O']:
                if (self.solucion!='H2O'):
                    self.solucion = 'H2O'
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['S1']:
                if (self.solucion!='1'):
                    self.solucion = '1'
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['S2']:
                if (self.solucion!='2'):
                    self.solucion = '2'
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['S3']:
                if (self.solucion!='3'):
                    self.solucion = '3'
                    self.checkEV()
                    self.updateCurrentTimeValues()
            if values['S4']:
                if (self.solucion!='4'):
                    self.solucion = '4'
                    self.checkEV()
                    self.updateCurrentTimeValues()

            if event == 'Actualizar':
                resp = self.changeEVvalue(int(self.piso), self.lado, int(self.etapa), self.solucion, self.data, self.cycleTime, self.evTime)
                if(resp):
                    #self.window['Table'].Update(values=self.data)
                    self.window['Actualizar'].Update(button_color=self.disable_color, disabled=True)
                    self.total = self.getTotalIrrigationTime(self.data)
                    self.window['cycleTime'].Update(range=(int(self.total/30)+1, 20))
                    self.rewriteCSV(self.filename, self.header_list, self.data)
                    self.serialMsg(self.str2UpdateEV(int(self.piso), self.lado, int(self.etapa), self.solucion, self.evTime))
                    self.str2log("Update Success")
                    self.updateCurrentTimeValues()
                else: self.str2log("Update Failed")

            if event == 'Actualizar Ciclo':
                self.total = self.getTotalIrrigationTime(self.data)
                if self.total<=(int(self.cycleTime)*30):
                    self.data[-1][1] = str(self.cycleTime)
                    #self.window['Table'].Update(values=self.data)
                    self.window['Actualizar Ciclo'].Update(button_color=self.disable_color, disabled=True)
                    self.rewriteCSV(self.filename, self.header_list, self.data)
                    self.serialMsg(self.str2UpdateCycle(self.cycleTime))
                    if self.piso!='' and self.lado!='' and self.etapa!='' and self.solucion!='':
                        evMin, evMax = self.getEVlimits(self.cycleTime, int(self.etapa))
                        val = self.getEVvalue(int(self.piso), self.lado, int(self.etapa), self.solucion, self.data)
                        self.window['evTime'].Update(range=(evMin, evMax))
                        self.window['TiempoCiclo'].Update(self.data[-1][1]+' min')
                    self.str2log("Update Cycle Success")
                else:
                    self.str2log("Update Cycle Failed")

            if len(regex)==1:
                self.timer = time.time()
                self.timerAux = True
                self
                lado = regex[0][2]
                path = int(regex[0][3])
                if(lado=='B'):
                    path=path*2-1
                else:
                    path=path*2
                self.window['siembra'].Update(data=self.get_img_data(self.paths[path], maxsize=(380,443), first=True))

                txtBKey=regex[0][:-1]
                txtSeedValueKey='S'+regex[0][2]+regex[0][3]
                if regex[0][4]=='+':
                    self.SeedValues[txtSeedValueKey]=self.SeedValues[txtSeedValueKey]+1
                    self.window[txtBKey].Update(value=self.SeedValues[txtSeedValueKey])
                else:
                    if self.SeedValues[txtSeedValueKey]>0: self.SeedValues[txtSeedValueKey]=self.SeedValues[txtSeedValueKey]-1
                    self.window[txtBKey].Update(value=self.SeedValues[txtSeedValueKey])
            if (time.time()-self.timer>0.3 and self.timerAux == True):
                self.window['siembra'].Update(data=self.get_img_data(self.paths[0], maxsize=(380,443), first=True))
                self.timerAux = False

        except Exception as e:
            if event in ('Cerrar', None):
                self.str2log("GUI Closed", 2)
                self.isOpen = False
                print(e)

# Debug

def main():
    gui = GUI()
    gui.begin()
    while gui.isOpen:
        gui.run()

if __name__ == '__main__':
    main()
