import ee
import geopandas as gpd
import pandas as pd

class ZonalStats:
    def __init__(self, img_col, fc, bands, reducer, scale=10):
        self.img_col = img_col
        self.fc = fc
        self.bands = bands
        self.stats = reducer
        self.scale = scale

        if self.stats == 'mean':
            self.reducer = ee.Reducer.mean()
        elif self.stats == 'max':
            self.reducer = ee.Reducer.max()
        elif self.stats == 'median':
            self.reducer = ee.Reducer.median()
        elif self.stats == 'min':
            self.reducer = ee.Reducer.min()
        elif self.stats == 'mode':
            self.reducer = ee.Reducer.mode()
        elif self.stats == 'stdDev':
            self.reducer = ee.Reducer.stdDev()
        elif self.stats == 'var':
            self.reducer = ee.Reducer.variance()
        elif self.stats == 'sum':
            self.reducer = ee.Reducer.sum()


        if len(self.bands) == 1:
            self.reducer = self.reducer.setOutputs(self.bands)

    def get_zonal_stats(self, image):
        # Select bands from the image
        image = image.select(self.bands)

        # Compute zonal statistics
        def get_zonal_stats(image):
            def add_metadata(feature):
                # Function to handle missing values and add metadata
                def handle_missing(band_name):
                    value = ee.List([feature.get(band_name), -999]).reduce(ee.Reducer.firstNonNull())
                    return value

                # Set metadata
                metadata = {
                    'imageID': image.id(),
                    'Date': ee.Date(image.get('system:time_start')).format('dd-MM-YYYY')
                    # 'OrbitNumber': image.get('relativeOrbitNumber_start')
                }
                    # Add metadata and handle missing values for each band
                for band_name in self.bands:
                    metadata[band_name] = handle_missing(band_name)

                return feature.set(metadata)

            return image.reduceRegions(
                collection=self.fc,
                reducer=self.reducer,
                scale=self.scale
            ).map(add_metadata)

        stats = get_zonal_stats(image)

        return stats

    def ee_to_geopandas(self, ee_object):
        col_size = ee_object.size().getInfo()
        chunk_size = 5000
        chunks = range(0, col_size, chunk_size)

        all_features = []
        for start_index in chunks:
            subset_col = ee.FeatureCollection(ee_object.toList(chunk_size, start_index))
            try:
                collection = subset_col.getInfo()
                features = collection.get("features", [])
                temp_gdf = gpd.GeoDataFrame.from_features(features)

                if 'id' not in temp_gdf.columns:
                    temp_gdf['id'] = [f['id'] for f in features]

                all_features.append(temp_gdf)
            except Exception as e:
                raise ValueError(f"Error fetching features at index {start_index}: {e}")

        return pd.concat(all_features, ignore_index=True)

    def execute(self):
        stats = self.img_col.map(self.get_zonal_stats).flatten()
        df = self.ee_to_geopandas(stats)
        return df

