var bloqueiaAtualizacaoGrafico = false;
var palettes = require('users/mapbiomas/modules:Palettes.js');
var vis = {
    mosaico: {
        min: 0,
        max: 2000,
        bands: ['red_median', 'green_median', 'blue_median']
    },
    vismosaicoGEE: {
        'min': 0.001, 'max': 0.15,
        bands: ['red', 'green', 'blue']
    },
    map_class: {
        min: 0,
        max: 69,
        palette: palettes.get('classification9')
    }
}
var param = {
    // # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Gap-fill',
    // # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/POS-CLASS/Estavel',
    // # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatial',
    // 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Frequency',
    assetFilters_bef: 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Temporal',
    // # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/MergerV6',
    // # 'assetFilters': 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/Classifier/toExport',
    assetFilters: 'projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/POS-CLASS/Spatial',
    asset_Map : "projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1",
    asset_bacias: 'projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions',
    pontos_accuracy: 'projects/mapbiomas-workspace/VALIDACAO/mapbiomas_85k_col4_points_w_edge_and_edited_v1',
    asset_biomas_raster : 'projects/mapbiomas-workspace/AUXILIAR/biomas-raster-41',
    asset_bioma: 'projects/diegocosta/assets/lm_bioma_250',
    asset_mosaic: 'projects/nexgenmap/MapBiomas2/LANDSAT/BRAZIL/mosaics-2',  
    asset_collectionId: 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY',
    nyears: [
        '1985','1986','1987','1988','1989','1990','1991','1992','1993','1994',
        '1995','1996','1997','1998','1999','2000','2001','2002','2003','2004',
        '2005','2006','2007','2008','2009','2010','2011','2012','2013','2014',
        '2015','2016','2017','2018','2019','2020','2021','2022','2023','2024',
        '2025'
    ],
}


// --- ASSETS ---
var bacias = ee.FeatureCollection(param.asset_bacias);
// Caminho da coleção
var caatinga = ee.FeatureCollection(param.asset_bioma)
                 .filter(ee.Filter.eq('Bioma', 'Caatinga'))
print("metadados shp Caatinga ", caatinga);
var version = 5;
var janela = 3;
var name_asset_maps_bef = param.assetFilters_bef.split("/").slice(-1)[0];
var name_asset_maps = param.assetFilters.split("/").slice(-1)[0];
//// Carrega a coleção com imagens por bacia/ano
var colMapsBef = ee.ImageCollection(param.assetFilters_bef)
                        .filter(ee.Filter.eq('version', version + 1));
if (param.assetFilters_bef.indexOf('Temporal') > 0){
    colMapsBef = colMapsBef.filter(ee.Filter.eq('janela', janela));
    name_asset_maps_bef = name_asset_maps_bef + '_J' + janela;
}
var colMaps = ee.ImageCollection(param.assetFilters)
                        .filter(ee.Filter.eq('version', version));
if (param.assetFilters.indexOf('Temporal') > 0){
    colMaps = colMaps.filter(ee.Filter.eq('janela', 5));
}
print("show metadata of collection ", colMaps);



// Corrige os nomes das bandas removendo o prefixo numérico
var nomesCorretos = ee.List(param.nyears).map(function(ano) {
    return ee.String('classification_').cat(ee.Number(ano).format('%.0f'));
});

// var mapbiomas = imagemBandas.rename(nomesCorretos);
// print(mapbiomas, 'aa')

var mapbiomasCol9 = ee.Image(param.asset_Map);
var mosaicoCol9 = ee.ImageCollection(param.asset_mosaic);
var mosaicEE = ee.ImageCollection(param.asset_collectionId);


// --- INTERFACE ---
ui.root.clear();  // Remove o Map padrão

// Painel lateral (controles + gráficos)
var panel = ui.Panel({style: {width: '450px', stretch: 'vertical'}});
panel.add(ui.Label('Inspeção de Bacias - Caatinga', {fontWeight: 'bold', fontSize: '18px'}));

panel.add(ui.Label('Bacia Hidrográfica:'));
var selectBacia = ui.Select({
                  placeholder: 'Carregando...', 
                  style: {width: '100px'} 
            });
panel.add(selectBacia);
var cadena1 = 'Ano para visualização no mapa dos assets:';
var cadena2 = 'asset before: ' + name_asset_maps_bef; 
var cadena3 = 'asset courrent:  ' + name_asset_maps;
panel.add(ui.Label(cadena1));
panel.add(ui.Label(cadena2));
panel.add(ui.Label(cadena3));
var sliderAno = ui.Slider({
    min: 1985,
    max: 2024,
    value: 2024,
    step: 1,
    style: {width: '100%'}  // ou: {stretch: 'horizontal'}
});
panel.add(sliderAno);

var marcarBtn = ui.Button({
    label: '✔️ Marcar bacia para reclassificação',
    style: {stretch: 'horizontal', backgroundColor: '#ffd1dc'},
    onClick: marcarOuDesmarcarBacia
});
panel.add(marcarBtn);

var chartPanel = ui.Panel();
panel.add(chartPanel);

var panelGrafico = ui.Panel({style: {margin: '10px'}});

var listaMarcadas = [];
var marcadasPanel = ui.Panel([ui.Label('Bacias marcadas:')]);
panel.add(marcadasPanel);
var stylesWidget = {
    labels: {fontWeight: 'bold', textAlign: 'center'},
    controlsVis: {layerList: true, zoomControl: false, mapTypeControl: false},
    painel_comp: {stretch: 'horizontal', padding: '10px', border: '1px solid lightgray', margin: '10px 0'}
}


////// ----------------------------- BUILDING MAPAS ----------------------------
var mapAnt = ui.Map();
var mapAtual = ui.Map();
var mapPost = ui.Map();
ui.Map.Linker([mapAnt, mapAtual, mapPost]);

mapAnt.setControlVisibility(stylesWidget.controlsVis);
mapAtual.setControlVisibility(stylesWidget.controlsVis);
mapPost.setControlVisibility(stylesWidget.controlsVis);

//// ----------------------- building  Títulos dinâmicos --------------------------
var tituloAnt = ui.Label('Ano anterior:', stylesWidget.labels);
var tituloAtual = ui.Label('Ano selecionado:', stylesWidget.labels);
var tituloPost = ui.Label('Ano posterior:', stylesWidget.labels);

////----------------------  Painéis verticais com título + mapa ------
var painelAnt = ui.Panel({
                    widgets: [tituloAnt, mapAnt], 
                    layout: ui.Panel.Layout.Flow('vertical'), 
                    style: {stretch: 'both'}
                });
var painelAtual = ui.Panel({
                    widgets: [tituloAtual, mapAtual], 
                    layout: ui.Panel.Layout.Flow('vertical'), 
                    style: {stretch: 'both'}
                });
var painelPost = ui.Panel({
                    widgets: [tituloPost, mapPost], 
                    layout: ui.Panel.Layout.Flow('vertical'), 
                    style:{stretch: 'both'}
                });

//// -------------------------- building Painel com os três mapas lado a lado --------
var mapasHorizontal = ui.Panel({
                    widgets: [painelAnt, painelAtual, painelPost], 
                    layout: ui.Panel.Layout.Flow('horizontal'), 
                    style: {stretch: 'both'}
                });

//// --------- building Painel completo (esquerda: controles, direita: mapas) --------
var painelCompleto = ui.Panel({
                    widgets: [panel, mapasHorizontal],
                    layout: ui.Panel.Layout.Flow('horizontal'),
                    style: {stretch: 'both'}
                });
// --- Painel de comparação de versões ---
var painelComparacao = ui.Panel({ style: stylesWidget.painel_comp});
painelComparacao.add(ui.Label('Comparação entre versões de classificação para uma classe específica', {fontWeight: 'bold'}));

var colecaoInputs = [];
var classeInput = ui.Textbox({placeholder: 'Ex: 15 (Pastagem)'});

var adicionarInputBtn = ui.Button({
    label: '➕ Adicionar Coleção',
    onClick: function() {
        var input = ui.Textbox({placeholder: 'ID completo da ImageCollection'});
        colecaoInputs.push(input);
        painelColecoes.add(input);
    }
});

var painelColecoes = ui.Panel({layout: ui.Panel.Layout.flow('vertical')});
painelColecoes.add(ui.Label('Coleções:'));
painelColecoes.add(adicionarInputBtn);

var gerarBtn = ui.Button({
    label: '📊 Gerar Gráfico Comparativo',
    style: {stretch: 'horizontal', backgroundColor: '#d0f0d0'},
    onClick: gerarGraficoComparativo
});

painelComparacao.add(painelColecoes);
painelComparacao.add(ui.Label('Classe (ex: 15):'));
painelComparacao.add(classeInput);
painelComparacao.add(gerarBtn);
panel.add(painelComparacao); // Adiciona ao painel lateral
panel.add(panelGrafico);  // ✅ Agora no fim, depois de tudo


function gerarGraficoComparativo() {
    // ⛔️ Impede atualização automática durante o processamento
    bloqueiaAtualizacaoGrafico = true;  

    var classeStr = classeInput.getValue();
    var classe = parseInt(classeStr);
    if (isNaN(classe)) {
        ui.alert('Classe inválida');
        bloqueiaAtualizacaoGrafico = false;  // Libera se ocorrer erro
        return;
    }

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4', selectBacia.getValue()));
    var anos = ee.List.sequence(1985, 2025);

    // Apenas limpa o painel de comparação (não mexe no gráfico de série temporal)
    panelGrafico.clear();
    panelGrafico.add(ui.Label('🔄 Processando comparações...'));

  var colecoes = colecaoInputs
    .map(function(input) {
      var id = input.getValue();
      if (!id) return null;
      return {id: id, ic: ee.ImageCollection(id)};
    })
    .filter(function(obj) { return obj !== null; });

  var resultadosRestantes = colecoes.length;
  var todosResultados = [];

  colecoes.forEach(function(colecao) {
    var id = colecao.id;
    var ic = colecao.ic;

    var imagens = anos.map(function(ano) {
      var nome = ee.String('classification_').cat(ee.Number(ano).format('%d'));
      return ic.select(nome).max().eq(classe)
        .multiply(ee.Image.pixelArea().divide(10000))
        .rename('area')
        .reduceRegion({
          reducer: ee.Reducer.sum(),
          geometry: bacia.geometry(),
          scale: 30,
          maxPixels: 1e13
        }).get('area');
    });

    ee.List(imagens).evaluate(function(valores) {
      todosResultados.push({id: id, dados: valores});
      resultadosRestantes--;

      if (resultadosRestantes === 0) {
        // ✅ Todos os dados foram processados — agora gera o gráfico
        panelGrafico.clear();
        var header = ['Ano'].concat(todosResultados.map(function(v) { return v.id; }));
        var linhas = [header];

        for (var i = 0; i < 40; i++) {
          var linha = [1985 + i];
          todosResultados.forEach(function(v) {
            linha.push((v.dados && v.dados[i]) ? v.dados[i] : 0);
          });
          linhas.push(linha);
        }

        var chart = ui.Chart(linhas)
          .setChartType('LineChart')
          .setOptions({
            title: 'Comparação entre versões - Classe ' + classe,
            hAxis: {title: 'Ano'},
            vAxis: {title: 'Área (ha)'},
            lineWidth: 2,
            pointSize: 3
          });

        panelGrafico.add(chart);

        // ✅ Libera após tudo estar desenhado
        ui.util.debounce(function() {
          bloqueiaAtualizacaoGrafico = false;
        }, 300)();
      }
    });
  });
}



// Adiciona à interface
ui.root.add(painelCompleto);

// --- Preenchimento da lista de bacias ---
bacias.aggregate_array('nunivotto4').evaluate(
    function(codigos) {
        var opcoes = codigos.map(function(c) {
            return {label: String(c), value: c};
        });
        selectBacia.items().reset(opcoes);
        selectBacia.setValue('751');
});

function marcarOuDesmarcarBacia() {
    var codigo = selectBacia.getValue();
    if (!codigo) return;

    var index = listaMarcadas.indexOf(codigo);
    if (index > -1) {
        listaMarcadas.splice(index, 1);
        atualizarListaMarcadas();
    } else {
        listaMarcadas.push(codigo);
        atualizarListaMarcadas();
    }
}

function atualizarListaMarcadas() {
    marcadasPanel.clear();
    marcadasPanel.add(ui.Label('Bacias marcadas:'));
    listaMarcadas.forEach(
        function(codigo) {
            marcadasPanel.add(ui.Label('• Bacia ' + codigo));
    });
}

// Arrays para rastrear camadas adicionadas
var camadasAnt = [];
var camadasAtual = [];
var camadasPost = [];

function atualizarInterface() {  
    if (bloqueiaAtualizacaoGrafico) return;
    
    // Limpa gráfico de comparação se existir
    var panelChildren = panel.widgets();
    for (var i = panelChildren.length - 1; i >= 0; i--) {
        var child = panelChildren.get(i);
        if (child && child.style && child.style().margin === '10px') {
            panel.remove(child);
        }
    }
    //------  Remove camadas antigas com segurança -----------
    camadasAnt.forEach(function(layer) { mapAnt.layers().remove(layer); });
    camadasAtual.forEach(function(layer) { mapAtual.layers().remove(layer); });
    camadasPost.forEach(function(layer) { mapPost.layers().remove(layer); });
    camadasAnt = [];
    camadasAtual = [];
    camadasPost = [];

    chartPanel.clear();
    chartPanel.add(ui.Label('🔄 Carregando gráficos...', {color: 'gray'}));

    var bacia_selected = selectBacia.getValue();
    var anoMapa = sliderAno.getValue();
    if (!bacia_selected) return;

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4', bacia_selected));
    var raster_bacia = bacia.map(function(feat){return feat.set('id_codigo', 1)});
    raster_bacia = raster_bacia.reduceToImage(['id_codigo'], ee.Reducer.first());

    var mapa_bacia = colMaps.filter(ee.Filter.eq('id_bacias', bacia_selected)).first();
    print("show metadata of map by bacia " + bacia_selected, mapa_bacia);
    var mapa_baciaBef = colMapsBef.filter(ee.Filter.eq('id_bacias', bacia_selected)).first();
    print("show metadata of map by bacia versão anterior " + bacia_selected, mapa_baciaBef);


    // -----  Define os anos vizinhos com limite------------
    var anosLocais = [
            Math.max(1985, anoMapa - 1),
            anoMapa,
            Math.min(2025, anoMapa + 1)
    ];

    // Atualiza os títulos acima dos mapas
    tituloAnt.setValue('Ano anterior: ' + anosLocais[0]);
    tituloAtual.setValue('Ano selecionado: ' + anosLocais[1]);
    tituloPost.setValue('Ano posterior: ' + anosLocais[2]);

    var maps = [mapAnt, mapAtual, mapPost];
    var listasCamadas = [camadasAnt, camadasAtual, camadasPost];

    anosLocais.forEach(function(ano, i) {
        var map = maps[i];
        var listaCamadas = listasCamadas[i];
        var mapYearCol9 = null;
        var mosaico = null;
        var maps_year = null;
        if (ano < 2025){
            maps_year = mapa_bacia.select(['classification_' + ano]).updateMask(raster_bacia);
            mosaico = mosaicoCol9.filter(ee.Filter.eq('year', ano)).mosaic().updateMask(raster_bacia);
        }else{
            maps_year = mapa_bacia.select(['classification_2024']).updateMask(raster_bacia);
             mosaico = mosaicoCol9.filter(ee.Filter.eq('year', 2024)).mosaic().updateMask(raster_bacia);
        }
        var maps_year_bef = mapa_baciaBef.select(['classification_' + ano]).updateMask(raster_bacia);
        if (ano < 2024){
            mapYearCol9 = mapbiomasCol9.select(['classification_' + ano]).updateMask(raster_bacia);
        }else{
            mapYearCol9 = mapbiomasCol9.select(['classification_2023']).updateMask(raster_bacia);
        }
        
        var dateStart = ee.Date.fromYMD(parseInt(ano), 1, 1);
        var dateEnd = ee.Date.fromYMD(parseInt(ano), 12, 31);
        var mosGEEyy = mosaicEE.filter(ee.Filter.date(dateStart, dateEnd)).median().updateMask(raster_bacia);

        if (i === 1) {
            map.centerObject(bacia, 9);
        }

        // Criar camadas explicitamente
        //var layerBacia = ui.Map.Layer(bacia, {color: 'red'}, 'Bacia ' + bacia_selected);
        var layerMosaico = ui.Map.Layer(mosaico, vis.mosaico, 'Mosaico ' + ano, false);
        var layerMosEE = ui.Map.Layer(mosGEEyy, vis.vismosaicoGEE, 'Mosaico EE' + ano);
        var layerCol90 = ui.Map.Layer(mapYearCol9, vis.map_class, 'Col90 ' + ano, false )
        var layerUsoBef = ui.Map.Layer(maps_year_bef, vis.map_class, 'Map Bef' + ano, false);
        var layerUso = ui.Map.Layer(maps_year, vis.map_class, 'Map ' + ano);

        //map.layers().add(layerBacia);
        map.layers().add(layerMosaico);
        map.layers().add(layerMosEE);
        map.layers().add(layerCol90);
        map.layers().add(layerUsoBef);
        map.layers().add(layerUso);

        listaCamadas.push(layerMosaico, layerMosEE, layerCol90, layerUsoBef, layerUso);
    });

    // Análise temporal por classe
    var anos = ee.List.sequence(1985, 2025);
    var listaResultados = [];
    var mapa_area = mapa_baciaBef ;//mapa_bacia
    param.nyears.forEach(
        function(anoNum) {
        var nomeBanda = 'classification_' + anoNum;
        var imagem = ee.Image.cat(
                                ee.Image.pixelArea().divide(10000).rename('area'),
                                mapa_area.select([nomeBanda])   
                            );
        var nreducer =  ee.Reducer.sum().group({ groupField: 1, groupName: 'class'})
        var stats = imagem.reduceRegion({
            reducer: nreducer,
            geometry: bacia.geometry(),
            scale: 30,
            maxPixels: 1e13
        });

        stats.evaluate(function(result) {
            var grupos = result && result.groups ? result.groups : [];
            listaResultados.push({ano: anoNum, grupos: grupos});

        if (listaResultados.length === param.nyears.length) {
            // ✅ CORREÇÃO: ordenar resultados por ano
            listaResultados.sort(function(a, b) {
                            return a.ano - b.ano;
                    });

                chartPanel.clear();
                gerarGrafico(listaResultados);
                exibirAcuracia(bacia_selected);
                panelGrafico.clear(); // <- limpeza correta no fim

            };
      });
    });

}


function gerarGrafico(resultado) {
    if (!resultado || resultado.length === 0) {
        chartPanel.add(ui.Label('Sem dados disponíveis.'));
        return;
    }

    var tabela = {};
    var anos = [];

    resultado.forEach(function(f) {
          var ano = f.ano;
          anos.push(ano);
          var grupos = f.grupos || [];
          var presentes = {};
  
          grupos.forEach(
              function(g) {
                  var classe = g.hasOwnProperty('class') ? g.class :
                              g.hasOwnProperty('group') ? g.group : undefined;
                  var area = g.sum;
                  if (classe === undefined || area === undefined) return;
                  var chave = String(classe);
                  if (!tabela[chave]) tabela[chave] = [];
                  tabela[chave].push(area);
                  presentes[chave] = true;
          });
  
          Object.keys(tabela).forEach(function(classe) {
              if (!presentes[classe]) tabela[classe].push(0);
          });
      });

      var classesOrdenadas = Object.keys(tabela).filter(
                function(c) {
                  var lista = tabela[c];
                  return (
                      c !== null && c !== undefined && !isNaN(Number(c)) &&
                      Array.isArray(lista) && lista.length === anos.length &&
                      lista.some(function(v) { return typeof v === 'number' && isFinite(v); })
                  );
                }).map(Number)
                .sort(function(a, b) { return a - b; });

      if (classesOrdenadas.length === 0) {
          chartPanel.add(ui.Label('Sem classes válidas para o gráfico.'));
          return;
      }

      var header = ['Ano'].concat(classesOrdenadas.map(String));
      var dados = [header];
      anos.forEach(function(ano, i) {
          var linha = [ano];
          classesOrdenadas.forEach(function(classe) {
          linha.push(tabela[classe][i]);
          });
          dados.push(linha);
      });

    var paletaClass8 = palettes.get('classification9');
    var cores = classesOrdenadas.map(function(classe) {
        return paletaClass8[parseInt(classe)] || '#000000';
    });

    var chart = ui.Chart(dados)
      .setChartType('LineChart')
      .setOptions({
          title: 'Série Temporal - Área por Classe (ha)',
          hAxis: {title: 'Ano'},
          vAxis: {title: 'Área (ha)'},
          curveType: 'function',
          lineWidth: 2,
          pointSize: 3,
          series: cores.map(function(cor) { return {color: cor}; })
      });
    chartPanel.add(chart);
}

function exibirAcuracia(idBacia) {
    var pontosVal = ee.FeatureCollection(param.pontos_accuracy);

    var legenda_dict = ee.Dictionary({
            'FORMAÇÃO FLORESTAL': 3, 'FORMAÇÃO SAVÂNICA': 4, 'MANGUE': 3,
            'FLORESTA ALAGÁVEL': 3, 'FLORESTA INUNDÁVEL': 3, 'FLORESTA PLANTADA': 3,
            'RESTINGA ARBÓREA': 12, 'CAMPO ALAGADO E ÁREA PANTANOSA': 12,
            'FORMAÇÃO CAMPESTRE': 12, 'OUTRA FORMAÇÃO NÃO FLORESTAL': 12,
            'APICUM': 22, 'AFLORAMENTO ROCHOSO': 29, 'RESTINGA HERBÁCEA': 12,
            'PASTAGEM': 21, 'AGRICULTURA': 21, 'LAVOURA TEMPORÁRIA': 21, 'SOJA': 21,
            'CANA': 21, 'ARROZ': 21, 'ALGODÃO': 21, 'OUTRAS LAVOURAS TEMPORÁRIAS': 21,
            'LAVOURA PERENE': 21, 'CAFÉ': 21, 'CITRUS': 21, 'DENDÊ': 21,
            'OUTRAS LAVOURAS PERENES': 21, 'SILVICULTURA': 21, 'MOSAICO DE USOS': 21,
            'PRAIA, DUNA E AREAL': 22, 'PRAIA E DUNA': 22, 'ÁREA URBANIZADA': 22,
            'VEGETAÇÃO URBANA': 22, 'INFRAESTRUTURA URBANA': 22, 'MINERAÇÃO': 22,
            'OUTRAS ÁREAS NÃO VEGETADAS': 22, 'OUTRA ÁREA NÃO VEGETADA': 22,
            'CORPO D’ÁGUA': 33, 'RIO, LAGO E OCEANO': 33, 'AQUICULTURA': 33,
            'NÃO OBSERVADO': 27
    });

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4',  idBacia));
    var anos = param.nyears.slice(0, 38);

    var linhas = [['Ano', 'Acurácia']];
    var total = anos.length;
    var concluídos = 0;

    chartPanel.add(ui.Label('✅ Calculando acurácia global por ano...'));

    anos.forEach(function(ano) {
        var campo = 'CLASS_' + ano;
        var nomeBanda = 'classification_' + ano;
        var bacia_selected = selectBacia.getValue();;
        var pontosAno = pontosVal.filterBounds(bacia.geometry())
                            .filter(ee.Filter.notNull([campo]))
                            // ⛔️ remove valores em branco
                            .filter(ee.Filter.neq(campo, ''));  

        var pontosConvertidos = pontosAno.map(
            function(f) {
                    var classeNome = ee.String(f.get(campo)).trim();

                    // Correção de codificações quebradas
                    classeNome = classeNome
                        .replace('FORMAÇ��O FLORESTAL', 'FORMAÇÃO FLORESTAL');

                    var classeCod = legenda_dict.get(classeNome);
                    return ee.Algorithms.If(classeCod, f.set('classe_ref', classeCod), null);
             }).filter(ee.Filter.notNull(['classe_ref']));
        // mecher aqui 
        var imagem = colMaps.filter(ee.Filter.eq('id_bacias', bacia_selected)).first().select([nomeBanda]);

        var amostras = imagem.sampleRegions({
                                collection: pontosConvertidos,
                                properties: ['classe_ref'],
                                scale: 30,
                                geometries: false
                            });

        var matriz = amostras.errorMatrix('classe_ref', nomeBanda);
        var acc = matriz.accuracy();

        acc.evaluate(function(valor) {
            concluídos++;
            if (valor !== null && valor !== undefined && isFinite(valor)) {
                linhas.push([ano, valor]);
            }

            if (concluídos === total) {
                var header = linhas.shift();
                var ordenado = linhas.sort(function(a, b) {
                    return a[0] - b[0];
                });
                ordenado.unshift(header);

                if (ordenado.length <= 1) {
                    chartPanel.add(ui.Label('⚠️ Nenhum dado de acurácia disponível.'));
                } else {
                    var grafico = ui.Chart(ordenado)
                        .setChartType('ScatterChart')
                        .setOptions({
                            title: 'Acurácia Global por Ano',
                            hAxis: { title: 'Ano' },
                            vAxis: { title: 'Acurácia' },
                            pointSize: 4,
                            lineWidth: 2
                        });
                    chartPanel.add(grafico); // ✅ Adiciona abaixo do gráfico de área
                }
            }
        });
  });
}




// --- EVENTOS ---
selectBacia.onChange(function(valor) {
    if (!bloqueiaAtualizacaoGrafico) {
        atualizarInterface();
    }
});
sliderAno.onChange(atualizarAnoVisualizado); // ✅ Apenas atualiza os mapas

function atualizarAnoVisualizado() {
    var bacia_selected = selectBacia.getValue();
    var anoMapa = sliderAno.getValue();
    if (!bacia_selected) return;

    var bacia = bacias.filter(ee.Filter.eq('nunivotto4', bacia_selected));
    var raster_bacia = bacia.map(function(feat){return feat.set('id_codigo', 1)});
    raster_bacia = raster_bacia.reduceToImage(['id_codigo'], ee.Reducer.first());
    
    var mapa_bacia = colMaps.filter(ee.Filter.eq('id_bacias', bacia_selected)).first();
    print("show metadata of map by bacia " + bacia_selected, mapa_bacia);
    var mapa_baciaBef = colMapsBef.filter(ee.Filter.eq('id_bacias', bacia_selected)).first();
    print("show metadata of map by bacia versão anterior " + bacia_selected, mapa_baciaBef);

    var anosLocais = [
        Math.max(1985, anoMapa - 1),
        anoMapa,
        Math.min(2025, anoMapa + 1)
    ];

    tituloAnt.setValue('Ano anterior: ' + anosLocais[0]);
    tituloAtual.setValue('Ano selecionado: ' + anosLocais[1]);
    tituloPost.setValue('Ano posterior: ' + anosLocais[2]);

    // Limpa camadas anteriores
    camadasAnt.forEach(function(layer) { mapAnt.layers().remove(layer); });
    camadasAtual.forEach(function(layer) { mapAtual.layers().remove(layer); });
    camadasPost.forEach(function(layer) { mapPost.layers().remove(layer); });
    camadasAnt = [];
    camadasAtual = [];
    camadasPost = [];

    var maps = [mapAnt, mapAtual, mapPost];
    var listasCamadas = [camadasAnt, camadasAtual, camadasPost];

    anosLocais.forEach(function(ano, i) {
        var map = maps[i];
        var listaCamadas = listasCamadas[i];

        var mapYearCol9 = null;
        var mosaico = null;
        var maps_year = null;
        if (ano < 2025){
            maps_year = mapa_bacia.select(['classification_' + ano]).updateMask(raster_bacia);
            mosaico = mosaicoCol9.filter(ee.Filter.eq('year', ano)).mosaic().updateMask(raster_bacia);
        }else{
            maps_year = mapa_bacia.select(['classification_2024']).updateMask(raster_bacia);
             mosaico = mosaicoCol9.filter(ee.Filter.eq('year', 2024)).mosaic().updateMask(raster_bacia);
        }
        var maps_year_bef = mapa_baciaBef.select(['classification_' + ano]).updateMask(raster_bacia);
        if (ano < 2024){
            mapYearCol9 = mapbiomasCol9.select(['classification_' + ano]).updateMask(raster_bacia);
        }else{
            mapYearCol9 = mapbiomasCol9.select(['classification_2023']).updateMask(raster_bacia);
        }
        
        var dateStart = ee.Date.fromYMD(parseInt(ano), 1, 1);
        var dateEnd = ee.Date.fromYMD(parseInt(ano), 12, 31);
        var mosGEEyy = mosaicEE.filter(ee.Filter.date(dateStart, dateEnd)).median().updateMask(raster_bacia);

        if (i === 1) {
            map.centerObject(bacia, 9);
        }

        // Criar camadas explicitamente
        //var layerBacia = ui.Map.Layer(bacia, {color: 'red'}, 'Bacia ' + bacia_selected);
        var layerMosaico = ui.Map.Layer(mosaico, vis.mosaico, 'Mosaico ' + ano, false);
        var layerMosEE = ui.Map.Layer(mosGEEyy, vis.vismosaicoGEE, 'Mosaico EE' + ano);
        var layerCol90 = ui.Map.Layer(mapYearCol9, vis.map_class, 'Col90 ' + ano, false )
        var layerUsoBef = ui.Map.Layer(maps_year_bef, vis.map_class, 'Map Bef' + ano, false);
        var layerUso = ui.Map.Layer(maps_year, vis.map_class, 'Map ' + ano);

        //map.layers().add(layerBacia);
        map.layers().add(layerMosaico);
        map.layers().add(layerMosEE);
        map.layers().add(layerCol90);
        map.layers().add(layerUsoBef);
        map.layers().add(layerUso);

        listaCamadas.push(layerMosaico, layerMosEE, layerCol90, layerUsoBef, layerUso);
    });
}

