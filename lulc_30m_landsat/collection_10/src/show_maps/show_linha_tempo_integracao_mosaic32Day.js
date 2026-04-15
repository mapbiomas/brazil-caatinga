
var asset = 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification';
var assetft = 'projects/mapbiomas-brazil/assets/LAND-COVER/COLLECTION-10/INTEGRATION/classification-ft';
var asset_landsat = 'LANDSAT/COMPOSITES/C02/T1_L2_32DAY';
var version = '0-7'; 

// Mapa integrado base (sem filtros)
var integration = ee.ImageCollection(asset);
print(integration.aggregate_histogram('version'));
integration = integration.filter(ee.Filter.eq('version', version + '')).mosaic();

// Mapa integrado com todos os filtros
var integrationft = ee.ImageCollection(assetft);
print(integrationft.aggregate_histogram('version'));
integrationft = integrationft.filter(ee.Filter.eq('version', version + '-tra-3')).mosaic();
var mask_raster_bioma = integration.select('classification_2024').gt(0);
var bands = integration.bandNames();
var nyear = '2024';
var Palettes = require('users/mapbiomas/modules:Palettes.js');

var palette = Palettes.get('classification9');
var vis = {
    mapbiomas: {
          'bands': 'classification_2024',
          'min': 0,
          'max': 69,
          'palette': palette,
          'format': 'png'
    },
    vismosaicoGEE: {
        'min': 0.001, 'max': 0.15,
        bands: ['red', 'green', 'blue']
    },
};

integrationft = integrationft.select(bands);

var diff = integration.neq(integrationft).reduce(ee.Reducer.anyNonZero()).not().selfMask();
var mosaicEE = ee.ImageCollection(asset_landsat);

var dateStart = ee.Date.fromYMD(parseInt(nyear), 1, 1);
    var dateEnd = ee.Date.fromYMD(parseInt(nyear), 12, 31);
var mosGEEyy = mosaicEE.filter(ee.Filter.date(dateStart, dateEnd))
                                  .median().updateMask(mask_raster_bioma);

Map.addLayer(mosGEEyy, vis.vismosaicoGEE, 'mosEE_' + nyear);
Map.addLayer(integration, vis.mapbiomas, 'integracao', false);
Map.addLayer(integrationft, vis.mapbiomas, 'integracao + filtro silvicultura');
// Map.addLayer(diff, {min: 0, max:1, palette: '000000,000000', format:'png', opacity: 0.7})


/**
 * 
 */
var Chart = {

    options: {
        'title': 'Inspector',
        'legend': 'none',
        'chartArea': {
            left: 30,
            right: 2,
        },
        'titleTextStyle': {
            color: '#ffffff',
            fontSize: 10,
            bold: true,
            italic: false
        },
        'tooltip': {
            textStyle: {
                fontSize: 10,
            },
            // isHtml: true
        },
        'backgroundColor': '#21242E',
        'pointSize': 6,
        'crosshair': {
            trigger: 'both',
            orientation: 'vertical',
            focused: {
                color: '#dddddd'
            }
        },
        'hAxis': {
            // title: 'Date', //muda isso aqui
            slantedTextAngle: 90,
            slantedText: true,
            textStyle: {
                color: '#ffffff',
                fontSize: 8,
                fontName: 'Arial',
                bold: false,
                italic: false
            },
            titleTextStyle: {
                color: '#ffffff',
                fontSize: 10,
                fontName: 'Arial',
                bold: true,
                italic: false
            },
            viewWindow: {
                max: 40,
                min: 0
            },
            gridlines: {
                color: '#21242E',
                interval: 1
            },
            minorGridlines: {
                color: '#21242E'
            }
        },
        'vAxis': {
            title: 'Class', // muda isso aqui
            textStyle: {
                color: '#ffffff',
                fontSize: 10,
                bold: false,
                italic: false
            },
            titleTextStyle: {
                color: '#ffffff',
                fontSize: 10,
                bold: false,
                italic: false
            },
            viewWindow: {
                max: 50,
                min: 0
            },
            gridlines: {
                color: '#21242E',
                interval: 2
            },
            minorGridlines: {
                color: '#21242E'
            }
        },
        'lineWidth': 0,
        // 'width': '300px',
        'height': '150px',
        'margin': '0px 0px 0px 0px',
        'series': {
            0: { color: '#21242E' }
        },

    },

    assets: {
        image: null,
        imagef: null
    },

    data: {
        image: null,
        imagef: null,
        point: null
    },

    legend: {
        0: { 'color': palette[0], 'name': 'Ausência de dados' },
        3: { 'color': palette[3], 'name': 'Formação Florestal' },
        4: { 'color': palette[4], 'name': 'Formação Savânica' },
        5: { 'color': palette[5], 'name': 'Mangue' },
        49: { 'color': palette[49], 'name': 'Restinga Florestal' },
        11: { 'color': palette[11], 'name': 'Área Úmida Natural não Florestal' },
        12: { 'color': palette[12], 'name': 'Formação Campestre' },
        32: { 'color': palette[32], 'name': 'Apicum' },
        29: { 'color': palette[29], 'name': 'Afloramento Rochoso' },
        50: { 'color': palette[50], 'name': 'Restinga Herbácea/Arbustiva' },
        13: { 'color': palette[13], 'name': 'Outra Formação não Florestal' },
        18: { 'color': palette[18], 'name': 'Agricultura' },
        39: { 'color': palette[39], 'name': 'Soja' },
        20: { 'color': palette[20], 'name': 'Cana' },
        40: { 'color': palette[40], 'name': 'Arroz' },
        62: { 'color': palette[62], 'name': 'Algodão' },
        41: { 'color': palette[41], 'name': 'Outras Lavouras Temporárias' },
        46: { 'color': palette[46], 'name': 'Café' },
        47: { 'color': palette[47], 'name': 'Citrus' },
        48: { 'color': palette[48], 'name': 'Outras Lavaouras Perenes' },
        9: { 'color': palette[9], 'name': 'Silvicultura' },
        15: { 'color': palette[15], 'name': 'Pastagem' },
        21: { 'color': palette[21], 'name': 'Mosaico de Usos, Áreas abandonadas' },
        22: { 'color': palette[22], 'name': 'Área não Vegetada' },
        23: { 'color': palette[23], 'name': 'Praia e Duna' },
        24: { 'color': palette[24], 'name': 'Infraestrutura Urbana' },
        30: { 'color': palette[30], 'name': 'Mineração' },
        25: { 'color': palette[25], 'name': 'Outra Área não Vegetada' },
        33: { 'color': palette[33], 'name': 'Rio, Lago e Oceano' },
        31: { 'color': palette[31], 'name': 'Aquicultura' },

    },

    loadData: function () {
        Chart.data.image = integration;
        Chart.data.imagef = integrationft;
    },

    init: function () {
        Chart.loadData();
        Chart.ui.init();
    },

    getSamplePoint: function (image, points) {

        var sample = image.sampleRegions({
            'collection': points,
            'scale': 30,
            'geometries': true
        });

        return sample;
    },

    ui: {

        init: function () {

            Chart.ui.form.init();
            Chart.ui.activateMapOnClick();

        },

        activateMapOnClick: function () {

            Map.onClick(
                function (coords) {
                    var point = ee.Geometry.Point(coords.lon, coords.lat);

                    var bandNames = Chart.data.image.bandNames();

                    var newBandNames = bandNames.map(
                        function (bandName) {
                            var name = ee.String(ee.List(ee.String(bandName).split('_')).get(1));

                            return name;
                        }
                    );

                    var image = Chart.data.image.select(bandNames, newBandNames);
                    var imagef = Chart.data.imagef.select(bandNames, newBandNames);

                    Chart.ui.inspect(Chart.ui.form.chartInspectorf, imagef, point, 1.0);
                    Chart.ui.inspect(Chart.ui.form.chartInspector, image, point, 1.0);
                }
            );

            Map.style().set('cursor', 'crosshair');
        },

        refreshGraph: function (chart, sample, opacity) {

            sample.evaluate(
                function (featureCollection) {

                    if (featureCollection !== null) {
                        // print(featureCollection.features);

                        var pixels = featureCollection.features.map(
                            function (features) {
                                return features.properties;
                            }
                        );

                        var bands = Object.getOwnPropertyNames(pixels[0]);

                        // Add class value
                        var dataTable = bands.map(
                            function (band) {
                                var value = pixels.map(
                                    function (pixel) {
                                        return pixel[band];
                                    }
                                );

                                return [band].concat(value);
                            }
                        );

                        // Add point style and tooltip
                        dataTable = dataTable.map(
                            function (point) {
                                var color = Chart.legend[point[1]].color;
                                var name = Chart.legend[point[1]].name;
                                var value = String(point[1]);

                                var style = 'point {size: 4; fill-color: ' + color + '; opacity: ' + opacity + '}';
                                var tooltip = 'year: ' + point[0] + ', class: [' + value + '] ' + name;

                                return point.concat(style).concat(tooltip);
                            }
                        );

                        var headers = [
                            'serie',
                            'id',
                            { 'type': 'string', 'role': 'style' },
                            { 'type': 'string', 'role': 'tooltip' }
                        ];

                        dataTable = [headers].concat(dataTable);

                        chart.setDataTable(dataTable);

                    }
                }
            );
        },

        refreshMap: function () {

            var pointLayer = Map.layers().filter(
                function (layer) {
                    return layer.get('name') === 'Point';
                }
            );

            if (pointLayer.length > 0) {
                Map.remove(pointLayer[0]);
                Map.addLayer(Chart.data.point, { color: 'red' }, 'Point');
            } else {
                Map.addLayer(Chart.data.point, { color: 'red' }, 'Point');
            }

        },

        inspect: function (chart, image, point, opacity) {
            print(point)
            // aqui pode fazer outras coisas além de atualizar o gráfico
            Chart.data.point = Chart.getSamplePoint(image, ee.FeatureCollection(point));

            Chart.ui.refreshMap(Chart.data.point);
            Chart.ui.refreshGraph(chart, Chart.data.point, opacity);

        },

        form: {

            init: function () {

                Chart.ui.form.panelChart.add(Chart.ui.form.chartInspector);
                Chart.ui.form.panelChart.add(Chart.ui.form.chartInspectorf);

                Chart.options.title = 'Integrated';
                Chart.ui.form.chartInspector.setOptions(Chart.options);

                Chart.options.title = 'Integrated - ft';
                Chart.ui.form.chartInspectorf.setOptions(Chart.options);

                // Chart.ui.form.chartInspector.onClick(
                //     function (xValue, yValue, seriesName) {
                //         print(xValue, yValue, seriesName);
                //     }
                // );

                Map.add(Chart.ui.form.panelChart);
            },

            panelChart: ui.Panel({
                'layout': ui.Panel.Layout.flow('vertical'),
                'style': {
                    'width': '450px',
                    // 'height': '200px',
                    'position': 'bottom-right',
                    'margin': '0px 0px 0px 0px',
                    'padding': '0px',
                    'backgroundColor': '#21242E'
                },
            }),

            chartInspector: ui.Chart([
                ['Serie', ''],
                ['', -1000], // número menor que o mínimo para não aparecer no gráfico na inicialização
            ]),

            chartInspectorf: ui.Chart([
                ['Serie', ''],
                ['', -1000], // número menor que o mínimo para não aparecer no gráfico na inicialização
            ])
        }
    }
};

Chart.init();