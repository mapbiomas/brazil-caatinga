#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed May 22 12:01:42 2019
SCRIPT DE CLASSIFICACAO POR BACIA
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: Geodatin
"""
import ee
import numpy as np
import json 

ee.Initialize()

#============================================================
#========================METODOS=============================


#============================================================


##======================VARIAVEIS============================
assetPoints = 'users/rnvuefsppgm/Acuracia_Lapig'
assetCol4BaciaV3 = 'projects/mapbiomas-workspace/AMOSTRAS/col4/CAATINGA/ver3bacia'
dirout = '/home/gabriel/Dados/acuracia/'
pontos = ee.FeatureCollection(assetPoints)
ImgCol4BaciaV3 = ee.ImageCollection(assetCol4BaciaV3)

imgclassBaciaV3 = ee.Image(ImgCol4BaciaV3.mosaic())
anos =['1985','1986','1987','1988','1989','1990','1991','1992','1993','1994','1995','1996','1997','1998','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
 '2011','2012','2013','2014','2015','2016','2017', '2018']

#nome das possiveis classificacoes
antigo = ['Forma��o Florestal'
            , 'Forma��o Sav�nica'
            , 'Mangue'
            , 'Silvicultura'
            , 'Forma��o Campestre'
            , 'Outra Forma��o n�o Florestal'
            , 'Pastagem Cultivada'
            , 'Pastagem Natural'
            , 'Cultura Anual'
            , 'Cultura Perene'
            , 'Cultura Semi-Perene'
            , 'Infraestrutura Urbana'
            , 'Afloramento Rochoso'
            , 'Minera��o'
            , 'Apicum'
            , 'Rio, Lago e Oceano'
            , 'N�o Observado'
            , 'Outra �rea n�o Vegetada'
            , 'Praia e Duna'
            , 'Aquicultura']

#numeros para substituir os nomes das possiveis classificacoes
novo = [ 3, 4, 3, 3, 12, 12, 21, 12, 21, 21, 21, 22, 29, 22, 22, 33, 27, 22, 22, 33]

nameClasses = ["12","21","22","27","29","3","33","4"]
classes = map(lambda num: int(num), nameClasses)
salvar = list()

#cria matriz: ano x classe x classe
total_matrix = list()
total_accuracy = list()
total_kappa = list ()
#============================================================

for indice, ano in enumerate(anos):
    #nome da banda em que a imagem por ano esta
    aux = 'class_'+ano
    #nome da classificacao na imagem
    aux2 = 'classification_'+ano
    #renomeia a classificacao
    pontos = pontos.remap(antigo, novo, aux)
    
    #seleiona os pontos dos anos
    pontos_ano = pontos.select(['lat', 'lon', aux])
    imgclassBaciav3 = imgclassBaciaV3.select(aux2)
    
    #retorna os mesmos pontos que estavam na colecao que e passada, 
    #pois o metodo enxerga cada ponto como uma geometria
    pontosColetados = imgclassBaciav3.sampleRegions(**{
      'collection': pontos_ano,
      'properties': [aux],
      'scale': 30, 
      'geometries': True
    })
    
    
    
    #calcula matriz de erro enttre as bandas, sendo que cada banda, 
    #nesse caso, representa um ano
    errorMatrix_abs = pontosColetados.errorMatrix(aux, aux2, classes)
    #obtem kappa e acuracia
    acuracia = errorMatrix_abs.accuracy().getInfo()
    kappa = errorMatrix_abs.kappa().getInfo()
    errorMatrix_abs = errorMatrix_abs.getInfo()
    #salva nos vetores para salvar no computador
    total_matrix.append(errorMatrix_abs)
    total_kappa.append(kappa)
    total_accuracy.append(acuracia)
    salvar.append({ 'year':ano,
                   'data':{
                           'matrix':errorMatrix_abs,
                           'accuracy': acuracia,
                           'kappa': kappa
                           }
            })
    print('terminado '+str(ano)+', faltando '+str(len(anos)-(indice+1))+' anos...')
    

total_matrix=np.array(total_matrix)
json_data = json.dumps(salvar)
total_kappa = np.array(total_kappa)
total_accuracy = np.array(total_accuracy)

with open(dirout+'data.json', 'w') as f:
    f.write(json_data)
    f.close()

aux = np.array2string(total_matrix, precision=8, separator=',').replace('\n ', '')
with open(dirout+'matrix.txt', 'w') as k:
    k.write(aux)
    k.close()

np.savetxt(dirout+'accuracy.txt', total_accuracy, delimiter=',')
np.savetxt(dirout+'kappa.txt', total_kappa, delimiter=',')
