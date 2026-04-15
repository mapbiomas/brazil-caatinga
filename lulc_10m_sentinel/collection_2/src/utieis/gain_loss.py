import ee

ee.Initialize(project='mapbiomas-agua')

MONTH_ANALYZED = (2024,8)

POINTS = ee.FeatureCollection('projects/mapbiomas-agua/assets/localidades')

def __format_result(transitions, buffer_size_m):
  transition_areas = ee.List(transitions.get('groups'))

  def __reduce_to_dict(current_item: ee.Dictionary, result_dictionary: ee.Dictionary) -> ee.Dictionary:
    current_item = ee.Dictionary(current_item)
    result_dictionary = ee.Dictionary(result_dictionary)
    
    key = ee.Algorithms.String(current_item.get('transition'))
    value = current_item.get('sum')
    result_dictionary = result_dictionary.set(key, value)
    
    return result_dictionary

  transition_areas = transition_areas.iterate(
    lambda item, result_dictionary: __reduce_to_dict(item, result_dictionary),
    ee.Dictionary({'3': 0, '4': 0})
  )
  transition_areas = ee.Dictionary(transition_areas)

  loss_area = transition_areas.get('3') # water to no water transition area
  gain_area = transition_areas.get('4') # no water to water transition area

  feature = ee.Feature(None, {
    'name': transitions.get('identifica'),
    'buffer_size_km': ee.Number(buffer_size_m).divide(1000),
    'gain_area_ha': gain_area,
    'loss_area_ha': loss_area,
  })
  return feature

def compute_transitions_in_buffers(buffer_size_m):
  buffers = POINTS.map(lambda p: p.buffer(buffer_size_m))

  areas = transition_image_area.reduceRegions(
    collection=buffers,
    reducer=ee.Reducer.sum().group(1, 'transition'),
    scale=30,
  ).map(
    lambda transitions: __format_result(transitions, buffer_size_m)
  )

  return areas


water_collection = (
  ee.ImageCollection('projects/mapbiomas-workspace/TRANSVERSAIS/AGUA5-FT')
    .filter(ee.Filter.eq('version', '11'))
    .filter(ee.Filter.eq('cadence', 'monthly'))
)

years = water_collection.aggregate_array('year').distinct()
number_of_years = years.size().getInfo()

permanence_frequency = number_of_years // 2

water_collection_month = (
  water_collection
    .select(f'classification_{MONTH_ANALYZED[1]}')
)

frequency_image = water_collection_month.sum()

reference_image = frequency_image.gte(permanence_frequency)

month_image = (
  water_collection
    .filter(ee.Filter.eq('year', MONTH_ANALYZED[0]))
    .select(f'classification_{MONTH_ANALYZED[1]}')
    .mosaic()
)

initial_image = reference_image.unmask()
final_image = month_image.unmask()

transition_image = initial_image.add(final_image.add(1).multiply(2)).rename('transition')
# 3 -> Water to no water transition
# 4 -> No water to water transition

pixel_area_ha = ee.Image.pixelArea().divide(10000)

transition_image_area = pixel_area_ha.addBands(transition_image)

for buffer_size_km in range(2, 101, 2):
  buffer_size_m = buffer_size_km * 1000

  gain_loss_statistics = compute_transitions_in_buffers(buffer_size_m)

  ee.batch.Export.table.toDrive(
    collection=gain_loss_statistics,
    description=f'WATER GAIN LOSS {buffer_size_km}km {MONTH_ANALYZED[0]}-{MONTH_ANALYZED[1]}',
    folder='Mapbiomas Água',
    fileNamePrefix=f'water_gain_loss_{buffer_size_km}km_{MONTH_ANALYZED[0]}-{MONTH_ANALYZED[1]}',
    fileFormat='CSV',
    selectors=['name', 'buffer_size_km', 'gain_area_ha', 'loss_area_ha']
  ).start()


  













