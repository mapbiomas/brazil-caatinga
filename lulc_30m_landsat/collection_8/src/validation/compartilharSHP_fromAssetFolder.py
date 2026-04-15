#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE SHARING ASSET FEATURES FROM ASSETR FOLDER
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''
import os
import ee 
import gee
import sys
from tqdm import tqdm
import arqParametros as arqParamet
import collections
collections.Callable = collections.abc.Callable

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

def gerenciador(conta):    
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    print("activando conta de >> {} <<".format(conta))        
    gee.switch_user(conta)
    gee.init()        
    gee.tasks(n= 2, return_list= True)        


def getPolygonsfromFolder(inputROIs):
    
    getlistPtos = ee.data.getList(inputROIs);   
    lstFeatsPtos = [];
    # print("getlistPtos ", getlistPtos);
    for idAsset in tqdm(getlistPtos):         
        path_ = idAsset.get('id')        
        name = path_.split('/')[-1]
        print('"{}" : "{}",'.format(name, path_))
        lstFeatsPtos.append(name)                
    
    print(lstFeatsPtos)
    return  lstFeatsPtos

# assetfolder = {'id': 'users/solkancengine17/shps_public'}
# assetfolder = {'id': 'users/CartasSol/gridsEcoReg90KM'}
assetfolder = {'id': 'users/CartasSol/gridsEcoRegV2'}
# gerenciador('solkanCengine')
gerenciador('solkan1201')

print("reading from => ", assetfolder['id'])
dictAnalista = {}

lstAssets = getPolygonsfromFolder(assetfolder)
# sys.exit()
for nameFeat in lstAssets:
    idAssetSHP = assetfolder['id'] + '/' + nameFeat
    # set permissão in the file Asset
    print("set full permissão in => ", idAssetSHP)
    comando = 'earthengine acl set public ' + idAssetSHP
    # comando = 'earthengine acl ch -u solkan1201@gmail.com:R ' + idAssetSHP
    os.system(comando)
    print("acessando a ", idAssetSHP)