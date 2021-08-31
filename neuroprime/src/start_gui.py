# -*- coding: utf-8 -*-

"""
Created on Sun Jun 17 16:29:25 2019

@author: nm.costa
"""

import subprocess
import tkinter as tk
import platform
import os
root= tk.Tk()


cwd=os.path.dirname(os.path.realpath(__file__))
batchs_path=os.path.join(cwd, 'batchs')

canvas1 = tk.Canvas(root, width = 350, height = 350)
canvas1.pack()

def start_pycorder():
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_pycorder.bat')], creationflags= subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
        pass

def start_pyff():
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_pyff_windows.bat')], creationflags= subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
        subprocess.call([os.path.join(batchs_path,'start_pyff_mac_os.command')], shell=True)

def start_lsl_actichamp(): #start actichamp app
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_lsl_actichamp.bat')], creationflags= subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
        pass

def start_lsl_bva_rda(): #start brainvison rda app
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_lsl_bva_rda.bat')], creationflags= subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
        pass

def start_gsr_hr(): #start james one app
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_gsr_hr_simulate.bat')], creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
        pass

def start_experiment():
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_bci_windows.bat')], creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
       pass

def start_simulation():
    if platform.system()=='Windows':
        subprocess.call([os.path.join(batchs_path,'start_bci_simulate.bat')], creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True)
    if platform.system()=='Darwin':
       pass

button1 = tk.Button(root, text='1.Prepare EEG APP (PYCORDER)',command=start_pycorder)
canvas1.create_window(170, 50, window=button1)
button2 = tk.Button(root, text='2.Start Presentation APP (PYFF)',command=start_pyff)
canvas1.create_window(170, 100, window=button2)
button3 = tk.Button (root, text='3.Start EEG Acquisition APP (LSL)',command=start_lsl_bva_rda)
canvas1.create_window(170, 150, window=button3)
button4 = tk.Button (root, text='4.Start GSR & HR Acquisition APP',command=start_gsr_hr)
canvas1.create_window(170, 200, window=button4)
button5 = tk.Button(root, text='5.Start experiment',command=start_experiment)
canvas1.create_window(170, 250, window=button5)
button6 = tk.Button(root, text='5.Simulate experiment(needs 2. and 4.)',command=start_simulation)
canvas1.create_window(170, 250, window=button6)
#button6 = tk.Button(root, text='999.Start experiment (SIMULATION)',command=start_simulation)
#canvas1.create_window(170, 300, window=button6)

root.mainloop()
