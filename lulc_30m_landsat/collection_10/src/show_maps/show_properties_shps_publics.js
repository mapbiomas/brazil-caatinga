
var param = {    
    "Assentamento_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
    "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
    "br_estados_raster": 'projects/mapbiomas-workspace/AUXILIAR/estados-2016-raster',
    "br_estados_shp": 'projects/mapbiomas-workspace/AUXILIAR/estados-2017',
    "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
    "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
    "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
    'vetor_biomas_250': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'biomas_250_rasters': 'projects/mapbiomas-workspace/AUXILIAR/RASTER/Bioma250mil',
    "Sigef_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sigef_Brasil",
    "Sistema_Costeiro_Marinho" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Sistema_Costeiro_Marinho",
    "aapd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/aapd",
    "areas_Quilombolas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/areas_Quilombolas",
    "buffer_pts_energias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/buffer_pts_energias",
    "energias-dissolve-aneel" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/energias-dissolve-aneel",
    "florestaspublicas" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/florestaspublicas",
    "imovel_certificado_SNCI_br" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/imovel_certificado_SNCI_br",
    "macro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/macro_RH",
    "meso_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/meso_RH",
    "micro_RH" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/micro_RH",
    "pnrh_asd" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_asd",
    "prioridade-conservacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/prioridade-conservacao-caatinga-ibama",
    "tis_poligonais_portarias" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/tis_poligonais_portarias",
    "transposicao-cbhsf" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/transposicao-cbhsf",
    "nucleos_desertificacao" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/pnrh_nucleos_desertificacao",
    "UnidadesConservacao_S" : "users/solkancengine17/shps_public/Unidades_consevacao_CNUC",
    "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
    "reserva_biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
    "semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    'semiarido' : 'users/mapbiomascaatinga04/semiarido_rec',
    "irrigacao": 'projects/ee-mapbiomascaatinga04/assets/polos_irrigaaco_atlas',
    "energiasE": 'projects/ee-mapbiomascaatinga04/assets/energias_renovaveis',
    "bacia_sao_francisco" : 'users/solkancengine17/shps_public/bacia_sao_francisco',
    "matopiba": 'projects/mapbiomas-fogo/assets/territories/matopiba'
}
var shp_semiarido = ee.FeatureCollection(param['semiarido2024']).geometry();
Map.addLayer(shp_semiarido, {}, "semiarido");
var lst_nameAsset = [
    'Assentamento_Brasil', 
    "nucleos_desertificacao",
    "UnidadesConservacao_S", 
    'areas_Quilombolas', 
    "macro_RH", 
    "meso_RH", 
    'prioridade-conservacao', 
    'tis_poligonais_portarias', 
    "reserva_biosfera",
    'matopiba',
    "energiasE",
    "transposicao-cbhsf"
];                          
var dict_Macro = {
    "102": "TOCANTINS-ARAGUAIA",
    "103": "ATLÂNTICO NORDESTE OCIDENTAL",
    "104": "PARNAÍBA",
    "105": "ATLÂNTICO NORDESTE ORIENTAL",
    "106": "SÃO FRANCISCO",
    "107": "ATLÂNTICO LESTE",
    "108": "ATLÂNTICO SUDESTE"
}
var dict_Meso = {
    "10213": " Alto Tocantins",
    "10317": " Itapecuru",
    "10420": " Alto Parnaíba",
    "10419": " Médio Parnaíba",
    "10418": " Baixo Parnaíba",
    "10522": " Jaguaribe",
    "10521": " Litoral do Ceará",
    "10524": "Litoral do Rio Grande do Norte e Paraíba",
    "10523": " Piancó-Piranhas-Açu",
    "10525": " Litoral de Pernambuco e Alagoas",
    "10628": " Médio São Francisco",
    "10627": " Submédio São Francisco",
    "10629": " Alto São Francisco",
    "10626": " Baixo São Francisco",
    "10732": " Contas",
    "10731": " Itapicuru/Paraguaçu",
    "10734": " Itanhém/Mucuri/São Mateus",
    "10733": " Jequitinhonha/Pardo",
    "10730": " Vaza-Barris",
    "10836": " Jucu/Itapemirim/Itabapoana",
    "10835": " Doce"
}

lst_nameAsset.forEach(
    function(key_dict){
        var feat_tmp = ee.FeatureCollection(param[key_dict]).filterBounds(shp_semiarido);
        print(" ======= " + key_dict + " ====== ");
        print(feat_tmp.limit(3));
        print(feat_tmp.size());
        if (key_dict == "UnidadesConservacao_S"){
            print(feat_tmp.aggregate_histogram('grupo'));
        }
        if (key_dict == "macro_RH"){
            lstCod = feat_tmp.reduceColumns(ee.Reducer.toList(2), ['cd_macroRH', 'nm_macroRH']).get('list');
            print(lstCod);
            print(feat_tmp.aggregate_histogram('nm_macroRH'));
        }
        if (key_dict == "meso_RH"){
            lstCod = feat_tmp.reduceColumns(ee.Reducer.toList(2), ['cd_mesoRH', 'nm_mesoRH']).get('list');
            print(lstCod);
            print(feat_tmp.aggregate_histogram('nm_mesoRH'));
        }
        if (key_dict == "reserva_biosfera"){
            print(feat_tmp.aggregate_histogram('zona'));
        }
        if (key_dict == "prioridade-conservacao"){
            print(feat_tmp.aggregate_histogram('import_bio'));
        }
        if (key_dict == "bacia_sao_francisco"){
            print(feat_tmp.aggregate_histogram(''));
        }
        Map.addLayer(feat_tmp, {}, key_dict, false);
    }
)