#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''
import os
import ee 
import gee
import sys
import collections
collections.Callable = collections.abc.Callable

from pathlib import Path
pathparent = str(Path(os.getcwd()).parents[0])
sys.path.append(pathparent)
from configure_account_projects_ee import get_current_account, get_project_from_account
projAccount = get_current_account()
print(f"projetos selecionado >>> {projAccount} <<<")

try:
    ee.Initialize( project= projAccount)
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

# sys.setrecursionlimit(1000000000)

relatorios = open("relatorioTaskXContas.txt", 'a+')

param = {
    'cancelar' : False,
    'unicaconta': True,
    'numeroTask': 10,
    'numeroLimit': 9,
    'conta' : {
        '0': 'caatinga01',
        '1': 'caatinga02',
        '2': 'caatinga03',
        '3': 'caatinga04',
        '4': 'caatinga05',        
        '5': 'solkan1201',
        '6': 'solkanGeodatin',        
        # '7': 'diegoGmail',
        '8': 'superconta'
        # '6': 'diegoUEFS', 
        # '7': 'soltangalano',
        # '8': 'Rafael',
        # '9': 'solkanCengine',
        # '10': 'Nerivaldo',
        # '12': 'rodrigo',
        # '13': 'ellen',
        # '14': 'vinicius',   
    }
}

def gerenciador(cont):    
    #=====================================
    # gerenciador de contas para controlar 
    # processos task no gee   
    #=====================================
    numberofChange = [kk for kk in param['conta'].keys()]
    print(cont)
    print(numberofChange)
    
    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        projAccount = get_project_from_account(param['conta'][str(cont)])
        try:
            ee.Initialize(project= projAccount) # project='ee-cartassol'
            print('The Earth Engine package initialized successfully!')
        except ee.EEException as e:
            print('The Earth Engine package failed to initialize!') 

        gee.tasks(n= param['numeroTask'], return_list= True) 
        relatorios.write("Conta de: " + param['conta'][str(cont)] + '\n')

        tarefas = gee.tasks(
            n= param['numeroTask'],
            return_list= True)
        
        for lin in tarefas:            
            relatorios.write(str(lin) + '\n')
    
    elif cont > param['numeroLimit']:
        cont = 0
    cont += 1    
    return cont

if param['unicaconta']:
    cont = 6
    cont = gerenciador(cont)
    if param['cancelar']:
        gee.cancel(opentasks=True)
else:
    cont = 0
    for ii in range(0,param['numeroLimit']):        
        cont = gerenciador(ii)
        if param['cancelar']:
            gee.cancel(opentasks=True)
