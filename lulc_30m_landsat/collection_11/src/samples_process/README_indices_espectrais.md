# Índices Espectrais — MapBiomas Col11 / Caatinga

Referência dos índices espectrais utilizados no pipeline de classificação.  
Bandas de entrada: `blue`, `green`, `red`, `nir`, `swir1`, `swir2` (Landsat C02 T1 L2).

---

## Índices ativos na seleção de features (VC4)

| Sigla | Nome completo | Fórmula | Alvos principais | Referência | DOI |
|-------|--------------|---------|-----------------|-----------|-----|
| **NDVI** | Normalized Difference Vegetation Index | `(NIR − RED) / (NIR + RED)` | Biomassa verde, fitomassa, sazonalidade | Tucker (1979). *Remote Sensing of Environment*, 8(2), 127–150 | [10.1016/0034-4257(79)90013-0](https://doi.org/10.1016/0034-4257(79)90013-0) |
| **NDWI** | Normalized Difference Water Index | `(NIR − SWIR2) / (NIR + SWIR2)` | Teor de água na vegetação, estresse hídrico | Gao (1996). *Remote Sensing of Environment*, 58(3), 257–266 | [10.1016/S0034-4257(96)00067-3](https://doi.org/10.1016/S0034-4257(96)00067-3) |
| **NDTI** | Normalized Difference Tillage Index | `(SWIR1 − SWIR2) / (SWIR1 + SWIR2)` | Resíduos de cultivo, solo exposto, preparo do solo | Van Deventer et al. (1997). *Photogrammetric Engineering and Remote Sensing*, 63(1), 87–93 | N/A (PE&RS, sem DOI formal) |
| **GLI** | Green Leaf Index | `(2·green − red − blue) / (2·green + red + blue)` | Cobertura vegetal viva, pastagem, vegetação rasa | Louhaichi et al. (2001). *Geocarto International*, 16(1), 65–70 | [10.1080/10106040108542184](https://doi.org/10.1080/10106040108542184) |
| **AWEI** | Automated Water Extraction Index | `4·(green − SWIR2) − (0.25·NIR + 2.75·SWIR1)` | Corpos d'água, áreas úmidas, separação água/sombra | Feyisa et al. (2014). *Remote Sensing of Environment*, 140, 23–35 | [10.1016/j.rse.2013.08.029](https://doi.org/10.1016/j.rse.2013.08.029) |

---

## Índices usados em versões anteriores de features (desativados em VC4)

| Sigla | Nome completo | Fórmula | Alvos principais | Referência | DOI |
|-------|--------------|---------|-----------------|-----------|-----|
| **GCVI** | Green Chlorophyll Vegetation Index | `(NIR / green) − 1` | Clorofila foliar, saúde vegetal | Gitelson et al. (2003). *Journal of Plant Physiology*, 160(3), 271–282 | [10.1078/0176-1617-00887](https://doi.org/10.1078/0176-1617-00887) |
| **BSI** | Bare Soil Index | `((SWIR1−RED) − (NIR+BLUE)) / ((SWIR1+RED) + (NIR+BLUE))` | Solo exposto, degradação, desmatamento | Rikimaru et al. (2002). *Tropical Ecology*, 43(1), 39–47 | N/A |
| **BRBA** | Band Ratio for Built-up Area | `RED / SWIR1` | Áreas construídas, estradas, solo compactado | He et al. (2010). *Remote Sensing Letters*, 1(4), 213–221 | [10.1080/01431161003638343](https://doi.org/10.1080/01431161003638343) |
| **MBI** | Modified Bare-soil Index | `(SWIR1 − SWIR2 − NIR) / (SWIR1 + SWIR2 + NIR) + 0.5` | Solo exposto, áreas degradadas, mapeamento de solo nu | Rasul et al. (2018). *Remote Sensing*, 10(12), 1928 | [10.3390/rs10121928](https://doi.org/10.3390/rs10121928) |
| **UI** | Urban Index | `(SWIR2 − NIR) / (SWIR2 + NIR)` | Áreas urbanas, superfícies impermeáveis | Kawamura et al. (1996). *Int. Archives Photogrammetry & Remote Sensing*, 31, 321–326 | N/A (anais de congresso) |

---

## Demais índices presentes no dicionário `FORMULAS_INDICES_ESPECTRAIS`

| Sigla | Nome completo | Fórmula | Alvos principais | Referência | DOI |
|-------|--------------|---------|-----------------|-----------|-----|
| **NDBI** | Normalized Difference Built-up Index | `(SWIR1 − NIR) / (SWIR1 + NIR)` | Áreas construídas, superfícies impermeáveis | Zha et al. (2003). *International Journal of Remote Sensing*, 24(3), 583–594 | [10.1080/01431160304987](https://doi.org/10.1080/01431160304987) |
| **NDMI** | Normalized Difference Moisture Index | `(NIR − SWIR1) / (NIR + SWIR1)` | Umidade florestal, detecção de corte | Wilson & Sader (2002). *Remote Sensing of Environment*, 80(3), 385–396 | [10.1016/S0034-4257(01)00318-2](https://doi.org/10.1016/S0034-4257(01)00318-2) |
| **NBR** | Normalized Burn Ratio | `(NIR − SWIR1) / (NIR + SWIR1)` | Severidade de queimada, cicatrizes de fogo | Key & Benson (1999). *Proceedings Joint Fire Science Conference*, 2, 284 | N/A (relatório técnico USGS) |
| **EVI** | Enhanced Vegetation Index | `2.4·(NIR − RED) / (1 + NIR + RED)` | Dossel denso, florestas, redução de saturação | Huete et al. (2002). *Remote Sensing of Environment*, 83(1–2), 195–213 | [10.1016/S0034-4257(02)00096-2](https://doi.org/10.1016/S0034-4257(02)00096-2) |
| **EVI2** | Enhanced Vegetation Index 2 (duas bandas) | `2.4·(NIR − RED) / (1 + NIR + RED)` | Vegetação densa sem banda azul (Landsat) | Jiang et al. (2008). *Remote Sensing of Environment*, 112(10), 3833–3845 | [10.1016/j.rse.2008.06.006](https://doi.org/10.1016/j.rse.2008.06.006) |
| **SAVI** | Soil-Adjusted Vegetation Index | `1.5·(NIR − RED) / (NIR + RED + 0.5)` | Vegetação esparsa, Caatinga, cerrado aberto | Huete (1988). *Remote Sensing of Environment*, 25(3), 295–309 | [10.1016/0034-4257(88)90106-X](https://doi.org/10.1016/0034-4257(88)90106-X) |
| **OSAVI** | Optimized Soil-Adjusted Vegetation Index | `(NIR − RED) / (NIR + RED + 0.16)` | Vegetação com influência de solo (L otimizado) | Rondeaux et al. (1996). *Remote Sensing of Environment*, 55(2), 95–107 | [10.1016/0034-4257(95)00186-7](https://doi.org/10.1016/0034-4257(95)00186-7) |
| **GNDVI** | Green Normalized Difference Vegetation Index | `(NIR − GREEN) / (NIR + GREEN)` | Clorofila, dossel verde, senescência | Gitelson & Merzlyak (1996). *Journal of Plant Physiology*, 148(3–4), 494–500 | [10.1016/S0176-1617(96)80284-7](https://doi.org/10.1016/S0176-1617(96)80284-7) |
| **GCVI** | Green Chlorophyll Vegetation Index | `(NIR / GREEN) − 1` | Clorofila, saúde da cultura, biomassa | Gitelson et al. (2003). *Journal of Plant Physiology*, 160(3), 271–282 | [10.1078/0176-1617-00887](https://doi.org/10.1078/0176-1617-00887) |
| **LSWI** | Land Surface Water Index | `(NIR − SWIR1) / (NIR + SWIR1)` | Água foliar, fenologia, áreas alagadas | Xiao et al. (2004). *Remote Sensing of Environment*, 89(4), 519–534 | [10.1016/j.rse.2003.11.008](https://doi.org/10.1016/j.rse.2003.11.008) |
| **GVMI** | Global Vegetation Moisture Index | `((NIR+0.1) − (SWIR1+0.02)) / ((NIR+0.1) + (SWIR1+0.02))` | Conteúdo de água na vegetação, risco de incêndio | Ceccato et al. (2002). *Remote Sensing of Environment*, 82(2–3), 198–207 | [10.1016/S0034-4257(02)00036-6](https://doi.org/10.1016/S0034-4257(02)00036-6) |
| **PRI** | Photochemical Reflectance Index (banda larga) | `(GREEN − BLUE) / (GREEN + BLUE)` | Eficiência fotossintética, estresse luminoso | Peñuelas et al. (1994). *Remote Sensing of Environment*, 48(2), 135–146 | [10.1016/0034-4257(94)90136-8](https://doi.org/10.1016/0034-4257(94)90136-8) |
| **GEMI** | Global Environmental Monitoring Index | `η·(1 − 0.25·η) − (RED − 0.125)/(1 − RED)` com `η = (2·(NIR²−RED²)+1.5·NIR+0.5·RED)/(NIR+RED+0.5)` | Vegetação global, resistência à atmosfera | Pinty & Verstraete (1992). *Vegetatio*, 101(1), 15–20 | [10.1007/BF00031911](https://doi.org/10.1007/BF00031911) |
| **MSI** | Moisture Stress Index | `NIR / SWIR1` | Estresse hídrico foliar, déficit de água | Rock et al. (1986). *BioScience*, 36(7), 439–445 | [10.2307/1310339](https://doi.org/10.2307/1310339) |
| **DSWI5** | Disease-Water Stress Index 5 | `(NIR + GREEN) / (SWIR1 + RED)` | Estresse hídrico, doença em culturas | Apan et al. (2004). *International Journal of Remote Sensing*, 25(2), 489–498 | [10.1080/01431160310001618031](https://doi.org/10.1080/01431160310001618031) |
| **AVI** | Ashburn Vegetation Index | `(NIR·(1−RED)·(NIR−RED))^(1/3)` | Biomassa, cobertura vegetal densa | Ashburn (1979). *NASA JSC Technical Report*, 1, 96–102 | N/A (relatório técnico) |
| **AFVI** | Aerosol Free Vegetation Index | `(NIR − 0.5·SWIR2) / (NIR + 0.5·SWIR2)` | Vegetação com correção de aerossóis | Karnieli et al. (2001). *Remote Sensing of Environment*, 77(1), 10–21 | [10.1016/S0034-4257(01)00190-0](https://doi.org/10.1016/S0034-4257(01)00190-0) |
| **RATIO** | Ratio Vegetation Index | `NIR / RED` | Biomassa, separação solo/vegetação | Jordan (1969). *Ecology*, 50(4), 663–666 | [10.2307/1936256](https://doi.org/10.2307/1936256) |
| **RVI** | Reciprocal Vegetation Index | `RED / NIR` | Albedo, áreas degradadas (inverso do RATIO) | Pearson & Miller (1972). *Remote sensing of environment*, 8, 1–10 | N/A |
| **IIA** | Infrared Index of Albedo | `(GREEN − 4·NIR) / (GREEN + 4·NIR)` | Albedo, água, superfícies brilhantes | — | N/A |
| **SHAPE** | Spectral Shape Index | `(2·RED − GREEN − BLUE) / (GREEN − BLUE)` | Solo exposto, granulometria | — | N/A |
| **CVI** | Chlorophyll Vegetation Index | `NIR·(GREEN / BLUE²)` | Clorofila, concentração de pigmentos | Vincini et al. (2008). *Precision Agriculture*, 9(5), 303–319 | [10.1007/s11119-008-9075-z](https://doi.org/10.1007/s11119-008-9075-z) |

---

## Tasseled Cap (componentes usados como features)

| Componente | Fórmula resumida | Alvos |
|-----------|-----------------|-------|
| **Brightness** | `0.3037·B + 0.2793·G + 0.4743·R + 0.5585·NIR + 0.5082·SWIR1 + 0.1863·SWIR2` | Albedo do solo, áreas descobertas |
| **Wetness** | `0.1509·B + 0.1973·G + 0.3279·R + 0.3406·NIR + 0.7112·SWIR1 + 0.4572·SWIR2` | Umidade do solo e vegetação |

Coeficientes para Landsat 5 TM — Crist (1985). *Remote Sensing of Environment*, 17(3), 301–306.  
DOI: [10.1016/0034-4257(85)90102-6](https://doi.org/10.1016/0034-4257(85)90102-6)

---

## Notas

- Fórmulas completas no código: [`src/classification_process/arqParametros_class.py`](../classification_process/arqParametros_class.py) → `FORMULAS_INDICES_ESPECTRAIS`
- Bandas no contexto Landsat C02 T1 L2 pré-processado: `blue`≈B2, `green`≈B3, `red`≈B4, `nir`≈B5, `swir1`≈B6, `swir2`≈B7
- NDWI aqui se refere à versão **Gao (1996)** (NIR/SWIR2, teor de água na vegetação), **não** à versão McFeeters (1996) (GREEN/NIR, água livre)
- LSWI, NDMI e NBR (com SWIR1) possuem a mesma fórmula base; diferem no contexto ecológico de aplicação
