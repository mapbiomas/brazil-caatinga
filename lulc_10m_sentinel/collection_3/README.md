# dev_col2_Sentinel_MB
aqui é um repositorio para tratar o desenvolvimento da coleção Sentinel de Mapbiomas
# Land Use and Land Cover Mapping — Caatinga Biome (Sentinel-2, Collection 3)

This repository contains the complete workflow and scripts used for the annual mapping of land use and land cover in the Caatinga biome using **Sentinel-2** imagery at **10 m** spatial resolution. The process is based on remote sensing techniques, utilizing the **Google Earth Engine (GEE)** platform and **Machine Learning** algorithms, covering the time series from **2016 to 2025** (10 years).

The project is organized into six main stages: sample collection, feature selection, hyperparameter tuning, classification, post-classification filtering, and validation. This collection introduces significant improvements over Collection 2, including integration with **Google Satellite Embeddings**, an optimized local ML pipeline, an expanded post-classification filter sequence, and new area-correction tools.

## Methodological Flowchart

<p align="center">
  <img src="../figuras/Copia de fluxograma Col 9.0.png" alt="Fluxograma de processos da Coleção Sentinel" width="600"/>
</p>
<p align="center">Figure 1. General classification process flowchart for MapBiomas Caatinga — Sentinel-2 Collection 3 (2016–2025).</p>

## About Sentinel Collection 3

Collection 3 (corresponding to MapBiomas Brazil Sentinel Collection 3) builds upon Collection 2 with the following key advances:

- **Google Satellite Embedding integration** (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`) — deep learning spatial features augment the traditional spectral indices for improved class discrimination.
- **Optimized feature selection pipeline** — replaces the original RFECV with a `HistGradientBoostingClassifier` + permutation importance approach that is 5–15× faster and uses significantly less RAM.
- **Optimized hyperparameter tuning** — uses `HalvingGridSearchCV` with `HistGradientBoostingClassifier` for faster local search.
- **Supervised sample cleaning** (`supervisionado_down_samples_cleaning_GE.py`) — applies GEE-based supervised cleaning to remove outlier samples per basin.
- **Expanded 7-step post-classification filter pipeline** — detailed gap-fill, temporal, spatial, and frequency filters matching the Landsat Collection 11 methodology.
- **Area correction tools** (`ferramentas/`) — polygon-based corrections for specific biome contexts (rocky outcrops, forest boundaries, anthropic polygons).
- **Detailed validation module** — per-basin and global accuracy with confusion matrix analysis.


## Classification Target Classes

Collection 3 maps **7 land cover/use classes** in the Caatinga biome:

| Code | Class                       |
|------|-----------------------------|
| 3    | Forest Formation            |
| 4    | Savanna Formation           |
| 12   | Grassland / Campestre       |
| 15   | Pasture                     |
| 18   | Agriculture (Mosaic)        |
| 22   | Non-Vegetated Area          |
| 33   | Water Body                  |


## Workflow Stages

---

### 1. Sample Data Collection (`src/coletas`)

Collection of ROIs (Regions of Interest) from the 756-grid system based on **49 hydrographic basins**, using Sentinel-2 annual mosaics. Collection 3 adds re-collection from Collection 10 reference samples and a supervised GEE-based cleaning step.

**Key scripts:**
* `colect_ROIs_Normalize_Grade_with_Spectral_info_fromC10rois.py` — re-collects normalized Sentinel-2 spectral ROIs using Collection 10 (`assetMapbiomas100`) reference pixels as seed locations, ensuring temporal consistency with the Landsat series.
* `merge_ROIs_from_grade_to_bacias.py` — merges grid-level ROIs into basin-level feature collections.
* `exportROIStoDrive.py` — exports ROIs as CSV to Google Drive for local processing.
* `down_samples_cleaning.py` — downsamples and cleans ROIs to reduce class imbalance before feature selection.
* `filter_downsamples.py` — applies spectral-outlier filtering to the downsampled ROI set.
* `supervisionado_down_samples_cleaning_GE.py` — supervised GEE-based cleaning that removes per-class outlier samples using spectral statistics computed directly on the mosaic.
* `view_distibution_class.py` — visualizes class distribution across basins to guide re-collection decisions.
* `getstatisticsMosaic.js` — GEE script to compute mosaic statistics per basin.
* `knowMosaic.js` — GEE inspection script for mosaic quality assessment.
* `dict_lst_distribuition_class_by_basin.json` — class distribution statistics per basin.
* `lista_gride_with_failsYearSaved2.csv` — list of grids with missing year assets.


### 2. Feature Analysis and Variable Selection (`src/features`)

Identifies the most discriminative spectral features from the full Sentinel-2 + embedding feature space.

**Collection 3 uses an optimized two-stage pipeline:**

1. **Pre-filtering:** `VarianceThreshold` + `SelectKBest` (F-test, top-100) reduce the feature space before the computationally expensive ranking step.
2. **Importance ranking:** `HistGradientBoostingClassifier` fitted on the pre-filtered set; `permutation_importance` (5 bootstrap repetitions) ranks features. The top 60 are kept.
3. **Final RFECV:** a lightweight RFECV with `StratifiedKFold` validates the selected subset.

This replaces the original `GradientBoostingClassifier`-based RFECV, achieving **5–15× speedup** and ~50% RAM reduction via `float32` data loading.

**Key scripts:**
* `featureselection_functions_otimizada.py` — optimized feature selection pipeline (HistGradientBoostingClassifier + permutation importance).
* `featureselection_functionsV2.py` — original RFECV-based implementation (reference).
* `RFE.py` — standalone RFE utility.
* `filtroOutlierAmostrasv2.py` — removes spectral outliers from the ROI dataset before feature selection.
* `get_vizinhos_representativos.py` — selects representative neighbor samples per class to improve coverage in spatially sparse classes.
* `getlist_FS_otimizadas_byBasin.py` — batch execution of the optimized feature selection per basin.
* `testePipeline.py` — test harness for the feature selection pipeline.
* `new_metodologia_feature_selection.ipynb` — exploratory notebook documenting the new methodology.
* `dict_lst_features_by_basin.json` — output: selected feature list per basin.


### 3. Hyperparameter Tuning (`src/tuningHiperparameters`)

Systematic optimization of GTB classifier parameters per basin and year using **HalvingGridSearchCV**.

Collection 3 introduces an **optimized tuning script** that:
- Uses `HistGradientBoostingClassifier` (native C implementation, 10× faster than sklearn GTB).
- Applies stratified subsampling (20% of data) for rapid search.
- Exports per-basin best-parameter sets and ROC curve visualizations.

**Key scripts:**
* `hyperpTuning_Halving_Grid_Search_otimizada.py` — optimized halving grid search with HistGradientBoosting, StandardScaler pipeline, and seaborn ROC visualization.
* `hyperpTuning_Halving_Grid_Search.py` — standard variant (reference).
* `testMulti_class_ROCcurve.py` — multi-class ROC curve evaluation.


### 4. Classification (`src/classification`)

Generates the land cover map for each basin and year using trained GTB classifiers on GEE. The script loads the selected features and optimized hyperparameters from previous stages and classifies the Sentinel-2 mosaic.

**Source imagery:**
- `projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3` (primary)
- `projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3` (secondary)
- `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (embedding features)

**Output:** `projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/Classifier/ClassifyV2`

**Key scripts:**
* `classificacao_NotN_newBasin_Float_col10_probVC2.py` — main GEE classification script; applies GTB per basin per year with per-class probability output. Uses cleaned ROIs from `col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_clean`.
* `arqParametros.py` — basin list, GEE asset paths, classifier parameters, and class remapping dictionary.
* `convert_img_toImageBands.py` — converts multiband classification images to individual year band images for downstream processing.
* `debugar_classification_process.ipynb` — step-by-step debug notebook for classification.
* `registros/lsBaciasClassifyfeitasv_1.txt` — log of completed basin classifications.


### 5. Post-Classification Filters (`src/filters`)

A structured 5-step pipeline removes temporal and spatial noise from the raw classification. The pipeline mirrors the Landsat Collection 11 methodology adapted for the 10-year Sentinel-2 series.

```
ClassifyV2 (raw GTB output)
         │
         ▼  filtersGapFill_step1A.py              ── STEP 1: Fill missing pixels
         │
         ▼  filtersNaturalTemporal_step2A.py      ── STEP 2A: Natural temporal filter
         │
         ▼  filtersAntropicTemporal_step2B.py     ── STEP 2B: Anthropic temporal filter
         │
         ▼  filtersSpatial_AllClass_step3A.py     ── STEP 3A: Spatial filter (all classes)
         │
         ▼  filtersSpatial_By_Cover_step3A.py     ── STEP 3B: Spatial filter (by cover)
         │
         ▼  filtersFrequency_step4A.py            ── STEP 4: Frequency-based stabilization
         │
         ▼  filtersTemporalCC.py                  ── STEP 5: Final temporal filter
    POS-CLASS/TemporalCC  ← FINAL PRODUCT
```

| Step | Script | What it does |
|------|--------|-------------|
| 1 | `filtersGapFill_step1A.py` | Fills null pixels (cloud gaps) using backward-fill from Sentinel-2 series |
| 2A | `filtersNaturalTemporal_step2A.py` | Sliding-window filter to correct 1–3 year anomalies in natural classes |
| 2B | `filtersAntropicTemporal_step2B.py` | Sliding-window filter to correct isolated natural pixels in anthropic areas |
| 3A | `filtersSpatial_AllClass_step3A.py` | Replaces isolated pixels (< 12 connected) with the mode of a 9×9 neighborhood |
| 3B | `filtersSpatial_By_Cover_step3A.py` | Class-pair-specific spatial filter (mode / min depending on context) |
| 4 | `filtersFrequency_step4A.py` | Stabilizes permanently natural pixels across the full 10-year series |
| 5 | `filtersTemporalCC.py` | Final 3-year window to remove residual 1-year anomalies |

Additional filter parameter file:
* `arqParametros.py` — assets, class remapping dictionaries, and basin list for filter scripts.
* `applyFilterSpatialCorregido.js` — GEE helper to visually inspect spatial filter output.


### 6. Area Correction Tools (`src/ferramentas`)

New in Collection 3: specialized polygon-based corrections applied after the filter pipeline to fix known systematic errors in specific landscape contexts.

| Script | Purpose |
|--------|---------|
| `apply_areas_correcao_Afloramento.py` | Corrects rocky outcrop (class 29) boundaries using reference polygons |
| `apply_areas_correcao_florest.py` | Corrects forest formation boundaries in transition zones |
| `apply_areas_correction_Polygon.py` | Generic polygon-area correction for user-defined ROIs |
| `apply_areas_dif_years_inic.py` | Applies differential corrections for initial years (2016–2018) |
| `apply_areas_Fl_Ant_correction_Polygon.py` | Forest/anthropic boundary correction using polygon masks |
| `exportarclassFinaltoMapbiomasJo_emergV2.py` | Exports final classification to MapBiomas integration format |
| `export_mapFV_10metros.py` | Exports final vegetation fraction map at 10 m resolution |
| `process_merger_layer.py` | Merges multiple correction layers into a single final product |


### 7. Validation (`src/validations`)

**Accuracy assessment:**
* `getCSVsPointstoAccGlobarlBacia.py` — downloads per-basin validation point CSVs from GEE.
* `joinAlltables_PointsAcc_Basin.py` — joins accuracy tables across all basins into a global table.
* `joinAlltables_PointsAcc_ColBef.py` — cross-collection accuracy comparison (Col3 vs. previous collection).
* `joinMatrixConfutionbyBasin.py` — joins per-basin confusion matrices and computes global metrics.
* `newsMetrics_AccuracySamples.py` — computes overall accuracy, F1-score, kappa, and per-class user/producer accuracy.

**Area estimation:**
* `calculoAreaV3.py` — computes per-class mapped areas per basin per year.


### Additional Modules

**Preprocessing (`src/preprocessing_data`):**
* `analises_exploratoria_embdding.js` — GEE exploratory analysis of Google Satellite Embedding bands per class.

**Visualization (`src/show_layers`):**
* `show_map_sentinel.js` — displays annual Sentinel-2 classification layers.
* `show_filtere_compare.js` — side-by-side comparison of pre- and post-filter maps.
* `inspeccionar_filters.js` — step-by-step filter inspection on GEE.
* `comparar_col10_vs_mapS2.js` — spatial comparison between Landsat Col10 and Sentinel-2 products.
* `show_layer_mosaic.js` — visualizes Sentinel-2 mosaic layers.

**Utilities (`src/utieis_scripts`):**
* `changedirAsset.py` — bulk moves/renames GEE assets.
* `deletfilesFOLDERs.py` / `deletfilinAssetv2.py` — batch deletes GEE assets.
* `revisarTasksXconta.py` — monitors GEE task distribution across accounts.

**Shared utility (`src/gee_tools.py`):**
Centralized GEE helper functions (mosaic loading, spectral index computation, asset management) shared across all scripts in this collection.


## Repository Structure

```
lulc_10m_sentinel/collection_3/
├── README.md
├── LICENSE
└── src/
    ├── configure_account_projects_ee.py     # GEE account/project manager
    ├── gee_tools.py                          # shared GEE utility functions
    │
    ├── coletas/                              # Stage 1 — ROI Collection
    ├── features/                             # Stage 2 — Feature Selection
    ├── tuningHiperparameters/                # Stage 3 — Hyperparameter Tuning
    ├── classification/                       # Stage 4 — Classification
    │   └── registros/
    ├── filters/                              # Stage 5 — Post-Classification Filters
    ├── ferramentas/                          # Stage 6 — Area Correction Tools
    ├── validations/
    │   ├── accuracy/                         # Stage 7 — Accuracy Assessment
    │   └── areas/                            # Stage 7 — Area Estimation
    ├── preprocessing_data/                   # Mosaic analysis and preprocessing
    ├── show_layers/                          # GEE visualization scripts
    └── utieis_scripts/                       # Utility scripts
```


## Main Data Assets (GEE)

| Asset | Description |
|-------|-------------|
| `projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3` | Sentinel-2 annual mosaics (2016–2025, primary) |
| `projects/nexgenmap/MapBiomas2/SENTINEL/mosaics-3` | Sentinel-2 annual mosaics (secondary) |
| `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` | Google Satellite Embedding annual features |
| `projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/ROIs/ROIs_merged_Indall_v3_clean` | Cleaned ROIs for training |
| `projects/mapbiomas-workspace/AMOSTRAS/col10/CAATINGA/S2/Classifier/ClassifyV2` | Raw classification output |
| `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1` | MapBiomas Collection 9 reference |
| `projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_integration_v2` | MapBiomas Collection 10 reference |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions` | 49 hydrographic basin boundaries |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/basegrade30KMCaatinga` | 756-cell 30 km grid |


## Dependencies

* Python 3.x
* `earthengine-api`
* `scikit-learn` (HistGradientBoostingClassifier, RFECV, HalvingGridSearchCV)
* `pandas`, `numpy`
* `tqdm`, `joblib`, `psutil`
* `seaborn`, `matplotlib`
* `gee_tools.py` (local utility module)


## License

Distributed under **GPLv2**. Produced by **Geodatin — Dados e Geoinformação**.
