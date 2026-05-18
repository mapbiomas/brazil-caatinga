# Land Use and Land Cover Mapping — Caatinga Biome (Sentinel-2, Collection 2)

This repository contains the complete workflow and scripts used for the annual mapping of land use and land cover in the Caatinga biome using **Sentinel-2** imagery at **10 m** spatial resolution. The process is based on remote sensing techniques, utilizing the **Google Earth Engine (GEE)** platform and **Machine Learning** algorithms, covering the time series from **2016 to 2023**.

The project is organized into six main stages: sample collection, feature selection, hyperparameter tuning, classification, post-classification filters, and validation.

## Methodological Flowchart

<p align="center">
  <img src="../figuras/Copia de fluxograma Col 9.0.png" alt="Fluxograma de processos da Coleção Sentinel 9.0" width="600"/>
</p>
<p align="center">Figure 1. Classification process flowchart for MapBiomas Caatinga — Sentinel-2 Collection 2 (2016–2023).</p>

## About Sentinel Collection 2

This is the second iteration of the 10 m Sentinel-2 LULC mapping for the Caatinga biome (Collection 9.0 of MapBiomas Brazil Sentinel). It builds upon Collection 1 by:

- Incorporating **normalized spectral ROI collection** for improved sample quality.
- Adding a **PAN (pansharpening) pipeline** variant for finer spatial discrimination.
- Expanding the **post-classification correction layer** (forest, campo, water, illumination).
- Including a full **validation module** (accuracy metrics and area calculation).
- Integrating a **preprocessing module** for mask construction and mosaic statistics.


## Classification Target Classes

Collection 2 maps **8 land cover/use classes** in the Caatinga biome:

| Code | Class                       |
|------|-----------------------------|
| 3    | Forest Formation            |
| 4    | Savanna Formation           |
| 12   | Grassland / Campestre       |
| 15   | Pasture                     |
| 18   | Agriculture (Mosaic)        |
| 21   | Mosaic of Agriculture       |
| 22   | Non-Vegetated Area          |
| 33   | Water Body                  |


## Workflow Stages

The workflow is organized into six major stages.

---

### 1. Sample Data Collection (`src/coletas`)

Collection of ROIs (Regions of Interest) from the 756-grid system based on **49 hydrographic basins**, extracting spectral information from Sentinel-2 annual mosaics. Multiple collection strategies are available:

- **Grid-based collection** — samples collected per 30 km grid cell, then merged per basin.
- **Normalized collection** — spectral values normalized to reduce mosaic radiometric variability.
- **PAN collection** — uses pansharpened bands for improved spatial resolution.
- **Region-based collection** — samples collected directly from larger hydrographic regions.

**Key scripts:**
* `colect_ROIs_fromGrade_with_Spectral_info.py` — standard grid-based ROI collection from Sentinel-2 mosaics (2016–2023).
* `colect_ROIs_fromGrade_with_Normalize_Spectral_info.py` / `V2` — normalized variant to reduce inter-annual radiometric drift.
* `colect_ROIs_with_Spectral_info_fromRegions.py` / `fromRegionsPan.py` — region-scale collection.
* `colect_ROIs_Normalize_Grade_with_Spectral_info_fromC8rois.py` — re-collects normalized ROIs seeded from Collection 8 reference samples.
* `recolect_ROIs_with_Spectral_info_fromC8rois.py` — re-collection pass targeting gaps from the previous collection.
* `merge_ROIs_from_grade_to_bacias.py` — merges grid ROIs into basin-level feature collections.
* `exportROIStoDrive.py` — exports ROIs as CSV to Google Drive for local processing.
* `search_rois_dont_saved_from_grade.py` / `Pan` — identifies grids with missing ROI assets.
* `make_feature_selection_RFECV.py` — runs RFECV locally on exported CSVs.
* `register_parameters.py` — registers collection parameters and progress.
* `Feature_Selection_ROIs_Caat.ipynb` — exploratory notebook for feature selection.


### 2. Feature Analysis and Variable Selection (`src/features`)

Identifies the most discriminative spectral bands and indices from the hundreds of available Sentinel-2 features.

- **RFECV** (Recursive Feature Elimination with Cross-Validation via `scikit-learn`) ranks variables by importance.
- Correlation filtering removes redundant features.
- Sample analysis notebooks explore class separability.

**Key scripts:**
* `Feature_Selection_ROIs_Caat.ipynb` — main RFECV notebook for feature selection.
* `analisys_ROIs_samples.ipynb` — exploratory analysis of ROI distributions and class separability.
* `analisys_ROIs_samplesScale.ipynb` — scale-specific analysis of sample quality.


### 3. Hyperparameter Tuning (`src/tuningHiperparameters`)

Systematic search for the best GTB (Gradient Tree Boost) and RF (Random Forest) classifier parameters per basin and year, using **HalvingGridSearchCV**.

**Key scripts:**
* `hyperpTuning_Halving_Grid_Search.py` — runs halving grid search over GTB parameters; saves best configuration to JSON.
* `testMulti_class_ROCcurve.py` — evaluates classifier performance with multi-class ROC curves.


### 4. Classification (`src/classification`)

Generates the land cover map for each basin and year using trained GTB or RF classifiers on GEE, loading the selected features and optimized hyperparameters from previous stages.

**Source imagery:** `projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3`

**Key scripts:**
* `process_clasification.py` — main classification script (GTB on GEE, per basin per year).
* `process_clasification_mod.py` — modified variant with additional spectral index computation.
* `process_clasification_modV2.py` — further refinement with updated class mapping.
* `analisesBaciascomFaltas.js` — GEE script to identify basins with missing classification results.
* `dictBetterModelpmtSet.json` — best hyperparameter sets per basin.
* `dictCodsBasin49reg.json` — basin code reference dictionary.


### 5. Post-Classification Filters (`src/filters`)

Applies thematic corrections to the raw classification to remove spectral confusion artifacts and temporal inconsistencies.

| Script | Correction applied |
|--------|--------------------|
| `filtersTemporal_step3.py` | Temporal sliding-window filter (step 3) |
| `reclassFillGaps.py` | Reclassifies pixels and fills remaining gaps |
| `filterNaturalWindows.js` | GEE helper for visual inspection of filter windows |


### 6. Validation (`src/validation`)

Assesses map quality through accuracy metrics and area estimation.

**Accuracy:**
* `accuracy_modificado.py` — calculates overall accuracy, producer's accuracy, and user's accuracy from validation points.
* `getCSVsPointstoAccGlobarlBacia.py` — downloads per-basin accuracy validation CSVs from GEE.
* `newsMetrics_AccuracySamples.py` — computes new accuracy metrics including F1-score and kappa coefficient.

**Area:**
* `calculoAreaV3.py` — computes per-class mapped areas per basin per year.
* `join_tables_Basin_areas_by_Model_Vers.py` — joins area tables across basins and versions.
* `revisar_tabelas_areas.py` — audits area calculation results.


### Additional Modules

**Preprocessing (`src/prepocessing_data`):**
* `buildin_maskstoSamples.py` — builds pixel masks to guide sample collection.
* `masksOfPixelsbySamples.py` — derives per-sample mask layers.
* `save_statisticsMosaic.py` — saves mosaic statistics per basin to GEE.

**Visualization (`src/showmaps`):**
* `showClassification_bacias.js` — GEE map viewer for classified basins.
* `reviewer_estradas_mapsVersS2.js` — road overlay reviewer.
* `poligonsVariationIlumination.js` — visualizes illumination variation polygons.

**Utilities (`src/utieis`):**
* `changedirAsset.js` / `.py` — bulk moves/renames GEE assets.
* `deletfilesFOLDERs.py` / `deletfilinAssetv2.py` — batch deletes GEE assets.
* `exportarclassFinaltoMapbiomasJo_emergV2.py` — exports final classification to MapBiomas integration format.
* `getStatbyBasinbyClass.py` / `get_stattiscglobal.py` — generates per-class statistics.
* `joinAllFeatReg.py` — joins feature tables across regions.
* `makedictIDsReg.py` — builds basin ID dictionaries.
* `revisarTasksXconta.py` — monitors GEE task distribution across accounts.


## Repository Structure

```
lulc_10m_sentinel/collection_2/
├── README.md
├── LICENSE
└── src/
    ├── configure_account_projects_ee.py    # GEE account/project manager
    │
    ├── coletas/                            # Stage 1 — ROI Collection
    ├── features/                           # Stage 2 — Feature Selection
    ├── tuningHiperparameters/              # Stage 3 — Hyperparameter Tuning
    ├── classification/                     # Stage 4 — Classification
    ├── filters/                            # Stage 5 — Post-Classification Filters
    ├── validation/
    │   ├── accuracy/                       # Stage 6 — Accuracy Assessment
    │   └── area/                           # Stage 6 — Area Estimation
    ├── prepocessing_data/                  # Mask and mosaic statistics
    ├── showmaps/                           # GEE visualization
    ├── utieis/                             # Utility scripts
    ├── app/                                # Validation app
    │   └── appVal.py
    └── dados/
        └── featuresSet/                    # Selected feature sets per basin
```


## Main Data Assets (GEE)

| Asset | Description |
|-------|-------------|
| `projects/mapbiomas-mosaics/assets/SENTINEL/BRAZIL/mosaics-3` | Sentinel-2 annual mosaics (2016–2023) |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta1` | ROIs — collection pass 1 |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/ROIs/coleta2` | ROIs — collection pass 2 |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/S2/Classifier/ClassVX` | Raw classification output |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/masks/mask_pixels_toSample` | Sampling exclusion masks |
| `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1` | MapBiomas Collection 9 reference |
| `projects/mapbiomas-workspace/AMOSTRAS/col9/CAATINGA/bacias_hidrografica_caatinga_49_regions` | 49 hydrographic basin boundaries |


## Dependencies

* Python 3.x
* `earthengine-api`
* `scikit-learn`
* `pandas`, `numpy`
* `tqdm`
* `gee` (local GEE utility wrapper)


## License

Distributed under **GPLv2**. Produced by **Geodatin — Dados e Geoinformação**.
