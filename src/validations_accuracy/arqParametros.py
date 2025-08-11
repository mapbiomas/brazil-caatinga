lsPtos_limite_bioma = [ 
        [[-42.73681640625, -3.35988909487339],
          [-43.6376953125, -5.943899579425586],
          [-44.12109375, -8.68963906812765],
          [-44.49462890625, -9.947208977327021],
          [-43.57177734375, -10.379765224421455],
          [-43.57177734375, -13.111580118251648],
          [-43.48388671875, -14.477234210156505],
          [-44.14306640625, -14.200488387358332],
          [-44.3408203125, -14.477234210156505],
          [-44.560546875, -15.771109173575281],
          [-43.83544921875, -16.214674588248542],
          [-42.73681640625, -15.982453522973495],
          [-42.64892578125, -15.24178985596171],
          [-41.85791015625, -15.326571801420831],
          [-40.869140625, -15.135764354595798],
          [-40.078125, -14.455958231194025],
          [-39.8583984375, -13.517837674890671],
          [-40.166015625, -13.49647276575895],
          [-39.287109375, -12.768946439455942],
          [-38.16650390625, -12.27559889056172],
          [-37.68310546875, -11.845847044118482],
          [-37.0458984375, -10.35815140094367],
          [-36.474609375, -10.228437266155943],
          [-36.36474609375, -9.70905706861821],
          [-36.4306640625, -9.188870084473393],
          [-35.44189453125, -8.58102121564184],
          [-35.04638671875, -7.514980942395871],
          [-35.04638671875, -5.922044619883305],
          [-35.33203125, -5.025282908609298],
          [-36.36474609375, -4.93772427430248],
          [-37.50732421875, -4.54357027937176],
          [-38.82568359375, -3.3160183381615123],
          [-40.10009765625, -2.657737790139788],
          [-41.484375, -2.6357885741666065],
          [-42.47314453125, -3.3160183381615123]]
  ]

listaNameBacias = [
    #   '741','7421','7422','744','745','746','7491','7492','751','752',
    #   '753', '754',
      '755'
    #   ,'756','757','758','759','7621','7622','763',
    #   '764','765','766','767','771','772','773', '7741','7742','775',
    #   '776','777','778','76111','76116','7612','7613','7614','7615',
    #   '7616','7617','7618','7619'
]
# '732','743', '747',
# listaNameBacias = [     
# #         '741','749',
# #         '757','758','759','762','763','766','771',
# #         '772','773', '774', '775','776','777','778','76111','76116'        
# # ]
#listaNameBacias = [
#      '732','741','742','743','744', '745','746','747','751','752',
#      '753','754','755','756','757','758','759','762','763','765'                    
#]
# listaNameBacias = [      
#       '753','754','755','756','757','758','759','762','763','765'              
# ]

# listaNameBacias = ['766','767','771','772','773', '774', '775','776','777']
#listaNameBacias = ['7611','7612','7613','7614','7615', '7617','7618','7619']
# listaNameBacias = ['749']   

allFeatures = [  
    'amp_evi2','amp_gv','amp_ndfi','amp_ndvi','amp_ndwi','amp_npv','amp_sefi','amp_soil',
    'amp_wefi','median_blue','median_blue_dry','median_blue_wet','median_cai','median_cai_dry',
    'median_cai_wet','median_cloud','median_evi2','median_evi2_dry','median_evi2_wet','median_fns',
    'median_fns_dry','median_fns_wet','median_gcvi','median_gcvi_dry','median_gcvi_wet','median_green',
    'median_green_dry','median_green_wet','median_gv','median_gvs','median_gvs_dry','median_gvs_wet',
    'median_hallcover','median_ndfi','median_ndfi_dry','median_ndfi_wet','median_ndvi','median_ndvi_dry',
    'median_ndvi_wet','median_ndwi','median_ndwi_dry','median_ndwi_wet','median_nir','median_nir_dry',
    'median_nir_wet','median_npv','median_pri','median_pri_dry','median_pri_wet','median_red','median_red_dry',
    'median_red_wet','median_savi','median_savi_dry','median_savi_wet','median_sefi','median_sefi_dry',
    'median_sefi_wet','median_shade','median_soil','median_swir1','median_swir1_dry','median_swir1_wet',
    'median_swir2','median_swir2_dry','median_swir2_wet','median_temp','median_wefi','median_wefi_dry',
    'median_wefi_wet','min_blue','min_green','min_nir','min_red','min_swir1','min_swir2','min_temp',
    'stdDev_blue','stdDev_cai','stdDev_cloud','stdDev_evi2','stdDev_fns','stdDev_gcvi','stdDev_green',
    'stdDev_gv','stdDev_gvs','stdDev_hallcover','stdDev_ndfi','stdDev_ndvi','stdDev_ndwi','stdDev_nir',
    'stdDev_npv','stdDev_pri','stdDev_red','stdDev_savi','stdDev_sefi','stdDev_shade','stdDev_soil',
    'stdDev_swir1','stdDev_swir2','stdDev_temp','stdDev_wefi'
]
            
      
allProperties = [  
    'amp_evi2','amp_gv','amp_ndfi','amp_ndvi','amp_ndwi','amp_npv','amp_sefi','amp_soil',
    'amp_wefi','median_blue','median_blue_dry','median_blue_wet','median_cai','median_cai_dry',
    'median_cai_wet','median_cloud','median_evi2','median_evi2_dry','median_evi2_wet','median_fns',
    'median_fns_dry','median_fns_wet','median_gcvi','median_gcvi_dry','median_gcvi_wet','median_green',
    'median_green_dry','median_green_wet','median_gv','median_gvs','median_gvs_dry','median_gvs_wet',
    'median_hallcover','median_ndfi','median_ndfi_dry','median_ndfi_wet','median_ndvi','median_ndvi_dry',
    'median_ndvi_wet','median_ndwi','median_ndwi_dry','median_ndwi_wet','median_nir','median_nir_dry',
    'median_nir_wet','median_npv','median_pri','median_pri_dry','median_pri_wet','median_red','median_red_dry',
    'median_red_wet','median_savi','median_savi_dry','median_savi_wet','median_sefi','median_sefi_dry',
    'median_sefi_wet','median_shade','median_soil','median_swir1','median_swir1_dry','median_swir1_wet',
    'median_swir2','median_swir2_dry','median_swir2_wet','median_temp','median_wefi','median_wefi_dry',
    'median_wefi_wet','min_blue','min_green','min_nir','min_red','min_swir1','min_swir2','min_temp',
    'stdDev_blue','stdDev_cai','stdDev_cloud','stdDev_evi2','stdDev_fns','stdDev_gcvi','stdDev_green',
    'stdDev_gv','stdDev_gvs','stdDev_hallcover','stdDev_ndfi','stdDev_ndvi','stdDev_ndwi','stdDev_nir',
    'stdDev_npv','stdDev_pri','stdDev_red','stdDev_savi','stdDev_sefi','stdDev_shade','stdDev_soil',
    'stdDev_swir1','stdDev_swir2','stdDev_temp','stdDev_wefi','year','class'
]
# https://code.earthengine.google.com/a7d6a5655537eb3efdee7509be3bd342
dictBaciasViz = {    
    '741': ["741","751","752","7421","7422"],
    '7421': ["741","744","754","7421","7422"],
    '7422': ["741","752","754","7421","7422"],
    # '743': ['744', '745', '747', '732', '743', '742', '741'],
    '744': ['7614', '7615', '7619', '7617', '744', '745', '746', '7421', '754'],
    '745': ["744","745","746"],
    '746': ["744","745","746","7619","7492","7491","7622"],
    # '747': ['746', '745', '747', '732', '743'],
    '7491' : ["746","7492","7491","7622"],
    '7492' : ["746","7492","7491"],
    '751': ["741","751","752","753"],
    '752': ["741","751","752","753","754","7422"],
    '753': ["751","752","753","754","755"], 
    '754': ['7612', '7613', '7614', '744', '7421', '7422','752', '753', '754', '756', '755'],
    '755': ["753","754","755","756","757"],
    '756': ["754","755","756","757","758","7612"],
    '757': ["755","756","757","758","759"],
    '758': ["756","757","758","759","76116","7612"],
    '759': ["757","758","759","76111","76116","771"],
    '7621': ["763","7622","7621","764"],
    '7622': ["746","763","7619","7491","7622","7621"],
    '763': ['763', '764', '765', '776','7618','7619','7741','7621', '7622'],
    '764': ["763","7621","764","765","767"],
    '765': ["763","764","765","766","767","776"],
    '766': ["765","766","767","776","777","778"],
    '767': ["764","765","766","767"],
    '771': ['759', '7611', '7616','771', '772', '773','7613', '7615'],
    '772': ["7616","7742","771","772","773","7615"],
    '773': ["7742","771","772","773","775"], 
    '7741': ["763","7618","7742","7741","775","776"], 
    '7742': ["7616","7618","7742","7741","772","773","775"], 
    '775': ["7742","7741","773","775","776","777"],
    '776': ["763","7741","765","766","775","776","777"],
    '777': ["766","775","776","777","778"],
    '778': ["766","777","778"],
    '7611': ['759', '7611', '771', '7612', '7613', '758',"76111","76116"],
    '76111': ["759","76111","76116","771"],
    '76116': ["758","759","76111","76116","771","7612","7613"],
    '7612': ["754","756","758","76116","7612","7613"],
    '7613': ["754","76116","771","7612","7613","7614","7615"],
    '7614': ["744","754","7613","7614","7615"],
    '7615': ['744',"7616","7617",'771','772','7613', '7614', '7615'],
    '7616': ["7616","7617","7618","7742","772","7615"], 
    '7617': ["744","7616","7617","7618","7619","7615"],
    '7618': ["763","7616","7617","7618","7619","7742","7741"],
    '7619': ["744","746","763","7617","7618","7619","7622"]
}


bandas_PCA = [
    'soil_amp', 'gcvi_median', 'gcvi_median_dry', 'gcvi_median_wet', 'green_median',
    'green_median_dry', 'hallcover_median', 'ndfi_median_dry', 'ndvi_median', 'ndvi_median_wet',
    'nir_median_dry', 'nir_median_wet', 'red_median', 'red_median_dry', 'red_median_wet', 'sefi_median_dry', 
    'swir1_median_dry', 'swir2_median', 'swir2_median_dry', 'swir2_median_wet', 'green_min', 'nir_min', 'red_min',
    'swir1_min', 'swir2_min', 'blue_median_dry', 'gvs_median', 'ndvi_median_dry', 'savi_median', 'blue_min',
    'evi2_median', 'sefi_median', 'shade_median', 'soil_median', 'ndwi_median', 'nir_median', 'swir1_median',
    'sefi_stdDev', 'swir1_median_wet', 'blue_median', 'cai_median_dry', 'pri_median_wet', 'green_median_wet',
    'wefi_median', 'ndvi_stdDev', 'soil_stdDev', 'evi2_median_wet', 'savi_median_wet', 'ndvi_amp',
    'pri_median', 'evi2_stdDev', 'savi_stdDev', 'red_stdDev', 'gvs_median_dry', 'ndwi_median_dry', 'savi_median_dry',
    'gvs_median_wet', 'evi2_median_dry', 'gcvi_stdDev', 'ndfi_median', 'ndwi_median_wet',
    'pri_median_dry', 'cloud_median', 'wefi_median_wet', 'gv_stdDev', 'gv_amp', 'swir2_stdDev',
    'ndfi_median_wet', 'cai_stdDev', 'ndwi_stdDev', 'evi2_amp', 'wefi_stdDev'
]

ls_cartas = [
        'SA-23-Z-D', 'SA-24-Y-A', 'SA-24-Y-B', 'SA-24-Y-C', 'SA-24-Y-D',
        'SA-24-Z-C', 'SB-23-X-B', 'SB-23-X-D', 'SB-23-Z-B', 'SB-23-Z-C',
        'SB-23-Z-D', 'SB-24-V-A', 'SB-24-V-B', 'SB-24-V-C', 'SB-24-V-D',
        'SB-24-X-A', 'SB-24-X-B', 'SB-24-X-C', 'SB-24-X-D', 'SB-24-Y-A',
        'SB-24-Y-B', 'SB-24-Y-C', 'SB-24-Y-D', 'SB-24-Z-A', 'SB-24-Z-B',
        'SB-24-Z-C', 'SB-24-Z-D', 'SB-25-V-C', 'SB-25-Y-A', 'SB-25-Y-C',
        'SC-23-X-A', 'SC-23-X-B', 'SC-23-X-C', 'SC-23-X-D', 'SC-23-Z-A',
        'SC-23-Z-B', 'SC-23-Z-C', 'SC-23-Z-D', 'SC-24-V-A', 'SC-24-V-B',
        'SC-24-V-C', 'SC-24-V-D', 'SC-24-X-A', 'SC-24-X-B', 'SC-24-X-C',
        'SC-24-X-D', 'SC-24-Y-A', 'SC-24-Y-B', 'SC-24-Y-C', 'SC-24-Y-D',
        'SC-24-Z-A', 'SC-24-Z-B', 'SC-24-Z-C', 'SC-25-V-A', 'SD-23-X-A',
        'SD-23-X-B', 'SD-23-X-C', 'SD-23-X-D', 'SD-23-Y-D', 'SD-23-Z-A',
        'SD-23-Z-B', 'SD-23-Z-C', 'SD-23-Z-D', 'SD-24-V-A', 'SD-24-V-B',
        'SD-24-V-C', 'SD-24-V-D', 'SD-24-X-A', 'SD-24-Y-A', 'SD-24-Y-B',
        'SD-24-Y-C', 'SE-23-X-A', 'SE-23-X-B', 'SE-23-V-B', 'SE-23-Z-A',
        'SE-23-X-C', 'SE-23-X-D', 'SE-23-Z-B', 'SE-24-V-C', 'SC-25-V-C',
        'SC-24-Z-D', 'SD-24-X-C', 'SD-24-Z-C', 'SE-24-V-B', 'SD-24-Y-D',
        'SD-24-Z-A', 'SE-24-V-A', 'SD-23-Y-B', 'SD-23-V-D', 'SD-23-V-B',
        'SC-23-Y-D', 'SC-23-Y-B', 'SC-23-V-D', 'SC-23-V-B', 'SB-23-Y-D',
        'SB-23-Z-A', 'SC-23-V-C', 'SC-23-V-A', 'SC-23-Y-C', 'SD-23-Y-A',
        'SD-23-Y-C', 'SE-23-V-A'
    ]

dict_cartas_v1 = {
    '1985': [        'SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'    ],
    '1986': [        'SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'        ],
    '1987': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'    ],
    '1988': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'    ],
    '1989': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'    ],
    '1990': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B', 'SE-23-X-B'    ],
    '1991': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1992': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1993': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1994': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1995': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1996': ['SA-24-Y-B', 'SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1997': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1998': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '1999': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2000': [
        'SA-24-Y-A', 'SA-24-Y-B', 'SA-24-Y-C', 'SA-24-Y-D', 'SA-24-Z-C', 'SB-23-Z-B', 'SB-23-Z-C', 
        'SB-23-Z-D', 'SB-24-V-A', 'SB-24-V-B', 'SB-24-V-C', 'SB-24-V-D', 'SB-24-X-A', 'SB-24-X-B', 
        'SB-24-X-C', 'SB-24-X-D', 'SB-24-Y-A', 'SB-24-Y-B', 'SB-24-Y-C', 'SB-24-Y-D', 'SB-24-Z-A', 
        'SB-24-Z-B', 'SB-24-Z-C', 'SB-24-Z-D', 'SC-23-X-A', 'SC-23-X-B', 'SC-23-X-C', 'SC-23-X-D', 
        'SC-23-Z-A', 'SC-23-Z-B', 'SC-23-Z-C', 'SC-23-Z-D', 'SC-24-V-A', 'SC-24-V-B', 'SC-24-V-C', 
        'SC-24-V-D', 'SC-24-X-A', 'SC-24-X-C', 'SC-24-Y-A', 'SC-24-Y-B', 'SC-24-Y-C', 'SD-23-X-A', 
        'SD-23-X-B', 'SD-23-X-C', 'SD-23-X-D', 'SD-23-Y-D', 'SD-23-Z-A', 'SD-23-Z-B', 'SD-23-Z-C', 
        'SD-24-V-A', 'SE-23-V-B', 'SE-23-X-A'
    ],
    '2001': [
        'SA-24-Y-A', 'SA-24-Y-B', 'SA-24-Y-C', 'SA-24-Y-D', 'SA-24-Z-C', 'SB-23-Z-B', 'SB-23-Z-C', 
        'SB-23-Z-D', 'SB-24-V-A', 'SB-24-V-B', 'SB-24-V-C', 'SB-24-V-D', 'SB-24-X-A', 'SB-24-X-B', 
        'SB-24-X-C', 'SB-24-X-D', 'SB-24-Y-A', 'SB-24-Y-B', 'SB-24-Y-C', 'SB-24-Y-D', 'SB-24-Z-A', 
        'SB-24-Z-B', 'SB-24-Z-C', 'SB-24-Z-D', 'SC-23-X-A', 'SC-23-X-B', 'SC-23-X-C', 'SC-23-X-D', 
        'SC-23-Z-A', 'SC-23-Z-B', 'SC-23-Z-C', 'SC-23-Z-D', 'SC-24-V-A', 'SC-24-V-B', 'SC-24-V-C', 
        'SC-24-V-D', 'SC-24-X-A', 'SC-24-X-C', 'SC-24-Y-A', 'SC-24-Y-B', 'SC-24-Y-C', 'SD-23-X-A', 
        'SD-23-X-B', 'SD-23-X-C', 'SD-23-X-D', 'SD-23-Y-D', 'SD-23-Z-A', 'SD-23-Z-B', 'SD-23-Z-C', 
        'SD-24-V-A', 'SE-23-V-B', 'SE-23-X-A'
    ],
    '2002': [
        'SA-24-Y-A', 'SA-24-Y-B', 'SA-24-Y-C', 'SA-24-Y-D', 'SA-24-Z-C', 'SB-23-Z-B', 'SB-23-Z-C', 
        'SB-23-Z-D', 'SB-24-V-A', 'SB-24-V-B', 'SB-24-V-C', 'SB-24-V-D', 'SB-24-X-A', 'SB-24-X-B', 
        'SB-24-X-C', 'SB-24-X-D', 'SB-24-Y-A', 'SB-24-Y-B', 'SB-24-Y-C', 'SB-24-Y-D', 'SB-24-Z-A', 
        'SB-24-Z-B', 'SB-24-Z-C', 'SB-24-Z-D', 'SB-25-V-C', 'SB-25-Y-A', 'SB-25-Y-C', 'SC-23-X-A', 
        'SC-23-X-B', 'SC-23-X-C', 'SC-23-X-D', 'SC-23-Z-A', 'SC-23-Z-B', 'SC-23-Z-C', 'SC-23-Z-D', 
        'SC-24-V-A', 'SC-24-V-B', 'SC-24-V-C', 'SC-24-V-D', 'SC-24-X-A', 'SC-24-X-B', 'SC-24-X-C', 
        'SC-24-X-D', 'SC-24-Y-A', 'SC-24-Y-B', 'SC-24-Y-C', 'SC-24-Y-D', 'SC-24-Z-A', 'SC-24-Z-B', 
        'SC-24-Z-C', 'SC-25-V-A', 'SD-23-X-A', 'SD-23-X-B', 'SD-23-X-C', 'SD-23-X-D', 'SD-23-Y-D', 
        'SD-23-Z-A', 'SD-23-Z-B', 'SD-23-Z-C', 'SD-24-V-A', 'SD-24-V-B', 'SD-24-V-C', 'SD-24-V-D', 
        'SD-24-X-A', 'SD-24-Y-A', 'SD-24-Y-B', 'SD-24-Y-C', 'SE-23-V-B', 'SE-23-X-A'
    ],
    '2003': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2004': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2005': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2006': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2007': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2008': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2009': ['SC-23-Z-C', 'SC-25-V-A', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2010': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2011': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'    ],
    '2012': [
        'SA-24-Y-A', 'SA-24-Y-B', 'SA-24-Y-C', 'SA-24-Y-D', 'SA-24-Z-C', 'SB-23-Z-B', 'SB-23-Z-C', 
        'SB-23-Z-D', 'SB-24-V-A', 'SB-24-V-B', 'SB-24-V-C', 'SB-24-V-D', 'SB-24-X-A', 'SB-24-X-B', 
        'SB-24-X-C', 'SB-24-X-D', 'SB-24-Y-A', 'SB-24-Y-B', 'SB-24-Y-C', 'SB-24-Y-D', 'SB-24-Z-A', 
        'SB-24-Z-B', 'SB-24-Z-C', 'SB-24-Z-D', 'SB-25-V-C', 'SB-25-Y-A', 'SB-25-Y-C', 'SC-23-X-A', 
        'SC-23-X-B', 'SC-23-X-C', 'SC-23-X-D', 'SC-23-Z-A', 'SC-23-Z-B', 'SC-23-Z-C', 'SC-23-Z-D', 
        'SC-24-V-A', 'SC-24-V-B', 'SC-24-V-C', 'SC-24-V-D', 'SC-24-X-A', 'SC-24-X-B', 'SC-24-X-C', 
        'SC-24-X-D', 'SC-24-Y-A', 'SC-24-Y-B', 'SC-24-Y-C', 'SC-24-Y-D', 'SC-24-Z-A', 'SC-24-Z-B', 
        'SC-24-Z-C', 'SC-25-V-A', 'SD-23-X-A', 'SD-23-X-B', 'SD-23-X-C', 'SD-23-X-D', 'SD-23-Y-D', 
        'SD-23-Z-A', 'SD-23-Z-B', 'SD-23-Z-C', 'SD-23-Z-D', 'SD-24-V-A', 'SD-24-V-B', 'SD-24-V-C', 
        'SD-24-V-D', 'SD-24-X-A', 'SD-24-Y-A', 'SD-24-Y-B', 'SD-24-Y-C', 'SE-23-V-B', 'SE-23-X-A', 
        'SE-23-X-B'
    ],
    '2013': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2014': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2015': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2016': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2017': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2018': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2019': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B'],
    '2020': ['SC-23-Z-C', 'SD-23-X-A', 'SD-23-X-C', 'SD-23-Y-D', 'SE-23-V-B']
}