
        
/*
    Relação de camadas para destaques:
    Assentamento_Brasil - Asentamentos 
    nucleos_desertificacao - Nucleos de desertificação,
    UnidadesConservacao_S - Unidades de conservação  -> 'TipoUso' -> ["Proteção Integral", "Proteção integral",  "Uso Sustentável"]
    unidade_gerenc_RH_SNIRH_2020- Unidade de gerenciamento de recursos Hidricos 
    tis_poligonais_portarias -  Terras indígenas
    prioridade-conservacao - Prioridade de conservação (usar apenas Extremamente alta)
    florestaspublicas - Unidades de conservação
    areas_Quilombolas - áreas quilombolas
    macro_RH - Bacias hidrográficas 
    reserva da biosfera - 'zona' ->  ["nucleo","transicao","amortecimento"]
*/

var Legend = require('users/joaovsiqueira1/packages:Legend.js');
var Palettes = require('users/mapbiomas/modules:Palettes.js');
var paletteC8 = Palettes.get('classification8');

var lst_nameAsset = [
    'Assentamento_Brasil', "nucleos_desertificacao",
    "UnidadesConservacao_S", "unidade_gerenc_RH_SNIRH_2020", 
    'areas_Quilombolas', "macro_RH", "meso_RH", //'micro_RH', 
    'prioridade-conservacao', 'tis_poligonais_portarias', 
    "reserva_biosfera"
];
var camadasAtenc = [
    'prioridade-conservacao', 'reserva_biosfera',
    'UnidadesConservacao_S', 'macro_RH','meso_RH'
];
var nameCamada = '';
var lstTipoUso = [
    ["Proteção Integral", "Proteção integral"],  ["Uso Sustentável"]
];
var lstMacro = [
    "PARNAÍBA", "ATLÂNTICO NORDESTE ORIENTAL", 
    "SÃO FRANCISCO", "ATLÂNTICO LESTE"
];
var dictMeso ={
    "PARNAÍBA": ["Alto Parnaíba", "Médio Parnaíba", "Baixo Parnaíba"],
    "ATLÂNTICO NORDESTE ORIENTAL": [
        "Jaguaribe", "Litoral do Ceará", "Litoral do Rio Grande do Norte e Paraíba", 
        "Piancó-Piranhas-Açu", "Litoral de Pernambuco e Alagoas"],
    "SÃO FRANCISCO": ["Médio São Francisco", "Submédio São Francisco", "Baixo São Francisco"],
    "ATLÂNTICO LESTE": ["Contas", "Itapicuru/Paraguaçu", "Jequitinhonha/Pardo", "Vaza-Barris"]
}
var dictMesoSigla ={
    "PARNAÍBA": {
        "Alto Parnaíba": "AltoP", 
        "Médio Parnaíba": "MédioP", 
        "Baixo Parnaíba": "BaixoP"
    },
    "ATLÂNTICO NORDESTE ORIENTAL": {
        "Jaguaribe": "AtlaNO_Jag", 
        "Litoral do Ceará": "AtlaNO_LC", 
        "Litoral do Rio Grande do Norte e Paraíba": "AtlaNO_LRGNP", 
        "Piancó-Piranhas-Açu": "AtlaNO_PPA", 
        "Litoral de Pernambuco e Alagoas": "AtlaNO_LPA"
    },
    "SÃO FRANCISCO": {
        "Médio São Francisco": "MedioSF", 
        "Submédio São Francisco": "SubmedSF", 
        "Baixo São Francisco": "BaixoSF"
    },
    "ATLÂNTICO LESTE": {
        "Contas": "AtlaL_C", 
        "Itapicuru/Paraguaçu": "AtlaL_IP", 
        "Jequitinhonha/Pardo": "AtlaL_JP", 
        "Vaza-Barris": "AtlaL_VB"
    }
}


var param = {
    // 'inputAsset': 'projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1', 
    'inputAsset': 'projects/mapbiomas-workspace/COLECAO9/integracao',
    'assets' : {
        "Assentamento_Brasil" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Assentamento_Brasil",
        "BR_ESTADOS_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_ESTADOS_2022",
        "BR_Municipios_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Municipios_2022",
        "BR_Pais_2022" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/BR_Pais_2022",
        "Im_bioma_250" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/Im_bioma_250",
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
        // "UnidadesConservacao_S" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/UnidadesConservacao_S",
        "UnidadesConservacao_S" : "users/solkancengine17/shps_public/Unidades_consevacao_CNUC",
        "unidade_gerenc_RH_SNIRH_2020" : "projects/earthengine-legacy/assets/users/solkancengine17/shps_public/unidade_gerenc_RH_SNIRH_2020",
        "reserva_biosfera" : "projects/mapbiomas-workspace/AUXILIAR/RESERVA_BIOSFERA/caatinga-central-2019",
        "asset_semiarido2024": 'projects/mapbiomas-workspace/AUXILIAR/SemiArido_2024',
    },  
    'collection': '9.0', 
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORTcsv', 
    'lsClasses': [3,4,12,21,22,33,29],
};


var yyear = '2023';
var limiteReg = 'Caatinga';
var limiteGeo = null;
var mapCol9 = ee.ImageCollection(param.inputAsset).filter(ee.Filter.eq('version', '0-24')).mosaic();

// var lstRed = mapCol8.reduceColumns(ee.Reducer.toList(), ['version']).get('list');
// print("lista de versões ", ee.List(lstRed).distinct());

if (limiteReg == 'Caatinga'){
    limiteGeo = ee.FeatureCollection(param.assets["Im_bioma_250"]).filter("CD_Bioma == 2");
    print("limite a Caatinga ", limiteGeo);
    var rasterLimit = ee.Image(param.assets["biomas_250_rasters"]).eq(2);
}else{
    limiteGeo = ee.FeatureCollection(param.assets["asset_semiarido2024"])
    print("limite a Semiarido ", limiteGeo);
    limiteReg = 'Semiarido';
}


function intersectGeometrywithLimit(feat){
    return feat.intersection(limiteGeo.geometry())
}

Map.addLayer(ee.Image.constant(1), {palette: 'white'}, 'base');
Map.addLayer(ee.Image.constant(1), {palette: 'black'}, 'base-black');

mapCol9 = mapCol9.clip(limiteGeo.geometry());
var mapYear = mapCol9.select('classification_' + yyear)
Map.addLayer(mapYear, { format: 'png', palette: paletteC8, min: 0, max: 62 }, 'mapbiomas c8');

// Paint all the polygon edges with the same number and width, display.
var shpCaat = ee.Image().byte().paint({
  featureCollection: limiteGeo,
  color: 1,
  width: 3
});
Map.addLayer(shpCaat, {palette: 'red'}, limiteReg);

var lstProp = []
lst_nameAsset.forEach(function(nameAsset){
    var shp_tmp = ee.FeatureCollection(param.assets[nameAsset])
                    .filterBounds(limiteGeo.geometry())
                    .map(intersectGeometrywithLimit);
    print(" => " + nameAsset, shp_tmp.first().propertyNames());
    print("features ", shp_tmp)
    shp_tmp = ee.FeatureCollection(shp_tmp);
    if (nameAsset == 'prioridade-conservacao'){
        // print(ee.List(shp_tmp.reduceColumns(ee.Reducer.toList(),['import_bio']).get('list')).distinct())
        shp_tmp = shp_tmp.filter(ee.Filter.eq('import_bio', "Extremamente Alta"));
        print("filtrado por prioridade ", shp_tmp);
        Map.addLayer(shp_tmp, {}, nameAsset, false);
    }
    if (nameAsset == 'reserva_biosfera'){
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(), ['zona']).get('list');
        print("reserva da biosfera ", ee.List(lstProp).distinct());
    }
    if (nameAsset == 'UnidadesConservacao_S'){
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(), ['TipoUso']).get('list');
        print("Unidades de conservação ", ee.List(lstProp).distinct());
        lstTipoUso.forEach(
            function (typeUso) {
                var shp_tmp_uso = shp_tmp.filter(ee.Filter.inList('TipoUso', typeUso));
                nameCamada = nameAsset + "_" + typeUso[0]
                Map.addLayer(shp_tmp_uso, {}, nameCamada, false);
            })
    }
    if (nameAsset == 'macro_RH'){
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(), ['nm_macroRH']).get('list');
        print("Macro Região Hidrografica ", ee.List(lstProp).distinct());
        lstMacro.forEach(function(nmmacro){
            var shp_tmp_macro = shp_tmp.filter(ee.Filter.eq('nm_macroRH', nmmacro));
            nameCamada = nameAsset + "_" + nmmacro
            Map.addLayer(shp_tmp_macro, {}, nameCamada, false);
        })
    }
    if (nameAsset == 'meso_RH'){
        lstProp = shp_tmp.reduceColumns(ee.Reducer.toList(2), ['nm_macroRH', 'nm_mesoRH']).get('list');
        print("Meso Região Hidrografica ", ee.List(lstProp).distinct());
        lstMacro.forEach(function(nmmacro){
            var lstMesoRH = dictMeso[nmmacro]
            lstMesoRH.forEach(function(nmmeso){
                var shp_tmp_meso = shp_tmp.filter(ee.Filter.eq('nm_mesoRH', nmmeso));
                nameCamada = nameAsset + "_" + dictMesoSigla[nmmacro][nmmeso]
                Map.addLayer(shp_tmp_meso, {}, nameCamada, false);
            })
            
        })
    }
    if (camadasAtenc.indexOf(nameAsset) == '-1'){
        Map.addLayer(shp_tmp, {}, nameAsset, false);
    }
    var mapaRed = mapYear.clip(shp_tmp.geometry());
    Map.addLayer(mapaRed, { format: 'png', palette: paletteC8, min: 0, max: 62 }, nameAsset, false);
})
