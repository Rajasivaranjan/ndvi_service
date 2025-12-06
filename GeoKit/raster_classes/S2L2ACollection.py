from .EERasterBuilder import EERasterBuilder
import ee
import datetime


class S2L2ACompositeRaster(EERasterBuilder):
    """Sentinel 2 raster class that inherits time and geography attributes
     from the EarthEngineRaster class
    """

    def __init__(self, start: str, end: str, bands: list = None, cloud_filter: int = 60, cld_prb_thresh: int = 20,
                 nir_drk_thresh: float = 0.15, cld_prj_dist: float = 1, buffer: int = 50, reducer='median'
                 ):
        """
                Initialize the S2L2A_CompositeRaster object.

                Parameters:
                    start (str): Start date for image collection (format: 'YYYY-MM-DD').
                    end (str): End date for image collection (format: 'YYYY-MM-DD').
                    bands (list): List of Sentinel-2 bands to include.
                    cloud_filter (int): Maximum percentage of cloudy image to include.
                    cld_prb_thresh (int): Cloud probability threshold.
                    nir_drk_thresh (float): Threshold for dark NIR pixels.
                    cld_prj_dist (float): Distance for projecting cloud shadows.
                    buffer (int): Buffer size for dilating cloud-shadow mask.
                    reducer (str): Reducer function for composite calculation ('mean' or 'median').
                """
        super().__init__(start, end)
        self.instance_list.append(self)
        # RasterClass identifier code
        self.code = 'S2CR'
        # satellite scale
        self.scale = 10
        # continue here with subclass specifics
        self.collection = 'COPERNICUS/S2_SR_HARMONIZED'
        # included bands, defaults to rgb
        if not bands:
            bands = ['B2', 'B3', 'B4', 'B8']
        self.bands = bands
        # cloud filter parameters
        self.cloud_filter = cloud_filter
        self.cld_prb_thresh = cld_prb_thresh
        self.nir_drk_thresh = nir_drk_thresh
        self.cld_prj_dist = cld_prj_dist
        self.buffer = buffer
        # select reducer function
        self.reducer = reducer
        self.earliest_date = None
        self.band_ids = None

    def set_aoi(self, fc: ee.FeatureCollection, province: str = None):
        """ Sets the area of interest and triggers the actual computation of the raster class
        Inputs:
         fc: feature collection with one element, representing aoi
         province: name of province for storage purposes
        """
        super()._set_aoi(fc, province)
        # compute raster
        # self.earliest_date = self.get_collection_dates()
        self.image = self.compute_raster()
        self.band_ids = self.get_feature_identifiers()
        return self


    def get_s2_sr_cld_col(self):
        """ Import and filter S2 SR. Import and filter s2cloudless.
        Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
        Import and filter S2 SR """
        s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                     .filterBounds(self.aoi)
                     .filterDate(self.start, self.end)
                     .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', self.cloud_filter)))
        s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
                            .filterBounds(self.aoi)
                            .filterDate(self.start, self.end))
        return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
            'primary': s2_sr_col,
            'secondary': s2_cloudless_col,
            'condition': ee.Filter.equals(**{
                'leftField': 'system:index',
                'rightField': 'system:index'
            })
        }))

    def add_cloud_bands(self, img: ee.Image):
        """ Get s2cloudless image, subset the probability band.
        Condition s2cloudless by the probability threshold value.
        Add the cloud probability layer and cloud mask as image bands. """
        cld_prb = ee.Image(img.get('s2cloudless')).select('probability')
        is_cloud = cld_prb.gt(self.cld_prb_thresh).rename('clouds')
        return img.addBands(ee.Image([cld_prb, is_cloud]))

    def add_shadow_bands(self, img: ee.Image):
        """ To add shadow bands """
        # Identify water pixels from the SCL band.
        not_water = img.select('SCL').neq(6)
        # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
        SR_BAND_SCALE = 1e4
        dark_pixels = img.select('B8').lt(self.nir_drk_thresh * SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')
        # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
        shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))
        # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
        cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, self.cld_prj_dist * 10)
                    .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
                    .select('distance')
                    .mask()
                    .rename('cloud_transform'))

        # Identify the intersection of dark pixels with cloud shadow projection.
        shadows = cld_proj.multiply(dark_pixels).rename('shadows')
        # Add dark pixels, cloud projection, and identified shadows as image bands.
        return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

    def add_cld_shdw_mask(self, img):
        """ Add cloud shadow mask """
        # Add cloud component bands.
        img_cloud = self.add_cloud_bands(img)
        # Add cloud shadow component bands.
        img_cloud_shadow = self.add_shadow_bands(img_cloud)
        # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
        is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)
        # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
        # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
        is_cld_shdw = (is_cld_shdw.focal_min(2).focal_max(self.buffer * 2 / 20)
                       .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
                       .rename('cloudmask'))
        # Add the final cloud-shadow mask to the image.
        return img_cloud_shadow.addBands(is_cld_shdw)

    def apply_cld_shdw_mask(self, img):
        """ Apply cloud shadow mask """
        # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
        not_cld_shdw = img.select('cloudmask').Not()
        # Subset reflectance bands and update their masks, return the result.
        return img.select('B.*').updateMask(not_cld_shdw)

    def img_reproject(self, image: ee.Image):
        """
        Reproject an image to EPSG:4326 with a scale of 10.

        :param image: Image to be reprojected(ee.Image).
        :return: Reprojected image.
        """
        return image.reproject(crs='EPSG:4326', scale=10)

    def compute_raster(self):
        """ Computes the cloud-free composite raster and returns an ee.Image """

        s2_sr_cld_col = self.get_s2_sr_cld_col()
        s2_sr_cld_col = (s2_sr_cld_col.map(self.add_cld_shdw_mask)
                         .map(self.apply_cld_shdw_mask).map(self.img_reproject))
        if self.reducer == 'mean':
            s2_sr_image = s2_sr_cld_col.mean().divide(10000)
        elif self.reducer == 'median':
            s2_sr_image = s2_sr_cld_col.median().divide(10000)
        elif self.reducer == 'std_dev':
            s2_sr_image = s2_sr_cld_col.select(self.bands).reduce(ee.Reducer.stdDev()).divide(10000)
            tmp_bnd = s2_sr_image.bandNames().getInfo()
            s2_sr_image = s2_sr_image.select(tmp_bnd, self.bands)
        elif self.reducer == 'max':
            s2_sr_image = s2_sr_cld_col.max().divide(10000)
        elif self.reducer == 'min':
            s2_sr_image = s2_sr_cld_col.min().divide(10000)
        else:
            s2_sr_image = s2_sr_cld_col.median().divide(10000)
        return s2_sr_image.select(self.bands)

    def compute_collection(self):
        def scale_conversion(img):
            """Scale conversion function"""
            # Divide image by 10000 to scale
            scaled_img = img.divide(10000)
            # Copy properties from input image to output image
            scaled_img = scaled_img.copyProperties(img, img.propertyNames())
            return scaled_img

        s2_sr_cld_col = self.get_s2_sr_cld_col()
        s2_sr_cld_col = (s2_sr_cld_col.map(self.add_cld_shdw_mask)
                         .map(self.apply_cld_shdw_mask)).map(scale_conversion)
        return s2_sr_cld_col


class S2L2ACollection(S2L2ACompositeRaster):
    """Class for handling collections of Sentinel-2 images within a specified time range and area of interest."""
    def __init__(self, start: str, end: str, aoi, bands: list = None, cloud_filter: int = 60, cld_prb_thresh: int = 20,
                 nir_drk_thresh: float = 0.15, cld_prj_dist: float = 1, buffer: int = 50):
        """
                Initialize the S2L2A_collection object.

                Parameters:
                    start (str): Start date for image collection (format: 'YYYY-MM-DD').
                    end (str): End date for image collection (format: 'YYYY-MM-DD').
                    aoi (ee.FeatureCollection): Area of interest.
                    bands (list): List of Sentinel-2 bands to include.
                    cloud_filter (int): Maximum percentage of cloudy image to include.
                    cld_prb_thresh (int): Cloud probability threshold.
                    nir_drk_thresh (float): Threshold for dark NIR pixels.
                    cld_prj_dist (float): Distance for projecting cloud shadows.
                    buffer (int): Buffer size for dilating cloud-shadow mask.
                """
        super().__init__(start, end, bands, cloud_filter, cld_prb_thresh, nir_drk_thresh, cld_prj_dist, buffer)
        self.start = start
        self.end = end
        self.aoi = aoi
        # included bands, defaults to rgb
        if not bands:
            bands = ['B2', 'B3', 'B4', 'B8']
        self.bands = bands
        # cloud filter parameters
        self.cloud_filter = cloud_filter
        self.cld_prb_thresh = cld_prb_thresh
        self.nir_drk_thresh = nir_drk_thresh
        self.cld_prj_dist = cld_prj_dist
        self.buffer = buffer
        # select reducer function
        self.col = self.compute_collection().select(self.bands)

