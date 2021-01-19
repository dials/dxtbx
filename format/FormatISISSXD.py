from __future__ import absolute_import, division, print_function
from sys import argv
import h5py
from dials.array_family import flex
from dxtbx.format.FormatNXTOFRAW import FormatNXTOFRAW
from dxtbx.format.FormatMultiImage import FormatMultiImage
from dxtbx.model import (
Beam,
Detector, 
Panel,
Goniometer,
Scan,
SimplePxMmStrategy)
from dxtbx.model.scan import ScanFactory
from dxtbx import IncorrectFormatError
import numpy as np

class FormatISISSXD(FormatNXTOFRAW):

    """
    Class to read NXTOFRAW files from the ISIS SXD
    (https://www.isis.stfc.ac.uk/Pages/sxd.aspx)

    """

    def __init__(self, image_file, **kwargs):
        super().__init__(image_file)
        if not FormatISISSXD.understand(image_file):
            raise IncorrectFormatError(self, image_file)
        self.nxs_file = self.open_file(image_file)
        self.detector = None
        self.raw_data = None

    def open_file(self, image_file):
        return h5py.File(image_file, "r")
        
    @staticmethod
    def understand(image_file):
        try:
            return FormatISISSXD.is_isissxd_file(image_file)
        except IOError:
            return False
 

    @staticmethod
    def is_isissxd_file(image_file):

        """
        Confirms if image_file is a NXTOFRAW format
        and from the SXD by confirming required fields
        are present and then checking the name attribute

        """

        def get_name(image_file):
               with h5py.File(image_file, "r") as handle:
                   return handle['/raw_data_1/name'][0].decode()
  
        if not FormatNXTOFRAW.understand(image_file):
            return False

        return get_name(image_file) == "SXD"

    def load_raw_data(self):
            
        def get_detector_idx_array(detector_number, image_size, idx_offset):
            total_pixels = image_size[0] * image_size[1]  
            min_range = (total_pixels * (detector_number - 1)) + (idx_offset* (detector_number-1))
            max_range = min_range + total_pixels
            return np.arange(min_range, max_range).reshape(image_size).T
                                                            
        raw_counts = self.nxs_file['raw_data_1']['detector_1']['counts'][:][0]
        num_panels = self._get_num_panels() 
        image_size = self._get_panel_size_in_px()
        
        # Index offset in SXD data 
        # See p24 of https://www.isis.stfc.ac.uk/Pages/sxd-user-guide6683.pdf
        idx_offset = 4

        num_images = self.get_num_images() 
        raw_data = []
                                                                            
        for i in range(1, num_panels + 1):
            idx_array = get_detector_idx_array(i, image_size, idx_offset)
            panel_array = np.zeros((idx_array.shape[0], idx_array.shape[1], num_images))
            for c_i, i in enumerate(idx_array):
                for c_j, j in enumerate(i):
                    panel_array[c_i, c_j, :] = raw_counts[j,:]
            flex_array = flex.double(np.ascontiguousarray(panel_array))
            flex_array.reshape(flex.grid(panel_array.shape))
            raw_data.append(flex_array)
                                                                                                                                                                
        return tuple(raw_data)

    def get_raw_data(self, index):
        if self.raw_data is None:
            self.raw_data = self.load_raw_data()

        raw_data_idx = []
        for i in self.raw_data:
            arr = i[:, :, index:index+1]
            arr.reshape(flex.grid(i.all()[0], i.all()[1]))
            raw_data_idx.append(arr)

        return tuple(raw_data_idx)


    def _get_detector(self):

        """
        Returns a  Detector instance with parameters taken from 

        """

        num_panels = self._get_num_panels() 
        panel_names = self._get_panel_names()
        panel_type = self._get_panel_type()
        image_size = self._get_panel_size_in_px()
        trusted_range = (-1, 100000)
        pixel_size = self._get_panel_pixel_size_in_mm()
        fast_axis = (1, 0, 0)
        slow_axis = (0, 1, 0)
        panel_origins = self._get_panel_origins()
        detector = Detector()
        root = detector.hierarchy()

        for i in range(num_panels):
            panel = root.add_panel()
            panel.set_type(panel_type)
            panel.set_name(panel_names[i])
            panel.set_image_size(image_size)
            panel.set_trusted_range(trusted_range)
            panel.set_pixel_size(pixel_size)
            panel.set_local_frame(fast_axis, slow_axis, panel_origins[i])
            #panel.set_px_mm_strategy(SimplePxMmStrategy)

        return detector

    """
    Hardcoded values not contained in the self.nxs_file are taken from
    https://doi.org/10.1107/S0021889806025921
    """

    def _get_time_channel_bins(self):
        return \
        self.nxs_file['raw_data_1']['instrument']['dae']['time_channels_1']['time_of_flight'][:]

    def _get_time_channels_in_seconds(self):
        bins = self._get_time_channel_bins()
        return [(bins[i] + bins[i+1])*.5*10**-6 for i in range(len(bins) - 1)]

    def _get_primary_flight_path_in_m(self):
        return 8.3

    def _get_num_panels(self):
        return 11

    def _get_panel_names(self):
        return ["%02d" % (i + 1) for i in range(11)]

    def _get_centroid_panel_l2_vals_in_m(self):
        return (.225, .225, .225, .225, .225, .225, .270, .270, .270, .270, .280)

    def _get_panel_origins(self):
        return (
            (48.9, -96.0, -217.9),
            (195.7, -96.0, -88.3),
            (195.7, -96.0, 110.4),
            (-48.9, -96.0, 217.9),
            (-195.7, -96.0, 88.3),
            (-229.2, -96.0, -146.8),
            (114.6, -258.8, -41.2),
            (28.7, -258.8, 115.9),
            (-114.6, -258.8, 41.2),
            (-28.7, -258.8, -115.9),
            (-29.6, -280.0, -90.8)
            )

    def _get_panel_l2_vals_in_m(self, pixel_size_in_mm, panel_size_in_px):
        centroid_l2_vals = self._get_centroid_panel_l2_vals_in_m()
        centroid = (panel_size_in_px[0]/2, panel_size_in_px[1]/2)

        panel = np.arange(-centroid[0],  centroid[1]).reshape(panel_size_in_px) 
        mm_x = pixel_size_in_mm[0]/1000.
        mm_y = pizel_size_in_mm[1]/1000.       

        for x in range(panel.shape[0]):
            for y in range(panel.shape[1]):
                panel[x,y] = np.sqrt(np.square(x * mm_x) + np.square(y * mm_y))        

        panels = [np.copy(panel) for i in range(len(centroid_l2_vals))]
        
        for p, panel in enumerate(panels):
            l2_val = centroid_l2_vals[p]
            for x in range(panel.shape[0]):
                for y in range(panel.shape[1]):
                    panel[x,y] = np.sqrt(np.square(l2_val) + np.square(panel[x,y]))

        return panels
            
    def _get_panel_longitude_in_deg(self):
        return (142.5, 90.0, 37.5, -37.5, -90.0, -142.5, 90.0, 0.0, -90.0, 180.0, 0.0)
           
    def get_num_images(self):
        return  len(self._get_time_channels_in_seconds())

    def get_beam(self, idx=None):
        return Beam() 

    def get_detector(self, idx=None):
        return self._get_detector() 

    def get_scan(self, idx=None):
        image_range = (1, self.get_num_images())
        exposure_times = 1
        oscillation = (0.0, 1.0)
        epochs = [i for i in range(self.get_num_images())]
        return ScanFactory.make_scan(image_range, exposure_times,
                                    oscillation, epochs) 

    def get_goniometer(self, idx=None):
        return Goniometer()

    def _get_panel_latitude_in_deg(self):
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -45.0, -45.0, -45.0, -45.0, -90.0)

    def _get_panel_size_in_px(self):
        return (64, 64)
    
    def _get_panel_pixel_size_in_mm(self):
        return (3, 3)

    def _get_panel_type(self):
        return "SENSOR_PAD"

    def _get_tof_wavelength_in_ang(self, L0, L, tof):
        h = 6.626E-34
        m_n = 1.675E-27
        return ((h * tof)/(m_n * (L0 + L)))*10**10

    def _get_pixel_wavelength_in_ang(self, x, y, tof, 
                                     L0, centroid_l, pixel_size_in_mm, panel_size_in_px):
        
        panel_centroid = (panel_size_in_px[0]/2., panel_size_in_px[1]/2.)
        rel_x = abs(x - panel_centroid[0]) * pixel_size_in_mm[0] *10**-3
        rel_y = abs(y - panel_centroid[1]) * pixel_size_in_mm[1] *10**-3
        rel_pos = np.sqrt(np.square(rel_x) + np.square(rel_y))
        rel_L = np.sqrt(np.square(rel_pos) + np.square(centroid_l))
        
        return self._get_tof_wavelength_in_ang(L0, rel_L, tof)


    def _get_raw_spectra_array(self):
        # Returns 2D array of (pixels, time_channels) for all 11 detectors
        return self.nxs_file['raw_data_1']['detector_1']['counts'][:][0]

    def _get_panel_images(self):

        """
        Returns a list of arrays (x_num_px, y_num_px, num_time_channels)
        for each panel, ordered from 1-11
        """
        raw_data = self._get_raw_spectra_array()

        # Panel positions are offset by 4 in raw_data array
        # See p24 of https://www.isis.stfc.ac.uk/Pages/sxd-user-guide6683.pdf
        panel_size = self._get_panel_size_in_px()
        total_px = panel_size[0] * panel_size[1]
        offsets =  [(((total_px * i) + (i*4)), ((total_px * (i+1)) + (i * 4))) for i in range(11)]
        panel_raw_data = [raw_data[i[0] : i[1], :] for i in offsets]
        
        # To match SXD2001 viewer, images must be transposed
        panel_size = self._get_panel_size_in_px()
        time_channel_size = len(self._get_time_channels_in_seconds())
        array_shape = (panel_size[0], panel_size[1], time_channel_size)
        return [np.transpose(i.reshape(array_shape), (1,0,2)) for i in panel_raw_data]

         
if __name__== "__main__":
    for arg in argv[1:]:
        print(FormatISISSXD.understand(arg))
