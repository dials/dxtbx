from __future__ import absolute_import, division, print_function
from sys import argv
import h5py
from dxtbx.format.FormatNXTOFRAW import FormatNXTOFRAW
from dxtbx.model import Detector
from dxtbx import IncorrectFormatError

class FormatISISSXD(FormatNXTOFRAW):

    """
    Class to read NXTOFRAW files from the ISIS SXD
    (https://www.isis.stfc.ac.uk/Pages/sxd.aspx)

    """

    def __init__(self, image_file):
        super().__init__(self, image_file)
        if not FormatISISSXD.understand(image_file):
            raise IncorrectFormatError(self, image_file)
        self.nxs_file = self.open_file(image_file)

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


    def _get_detector(self):

        """
        Returns a  Detector instance with parameters taken from 

        """

        num_panels = 11
        panel_type = "coupled_scintillator_PSD"
        image_size = (64, 64)
        pixel_size = (3, 3)
        trusted_range(-1, 100000)



        detector = Detector()
        root = detector.hierarchy()

        for i in range(num_panels):
            panel = root.add_panel()
            panel.set_name("%02d" % i + 1)
            panel.set_type(panel_type)
            panel.set_raw_image_offset(img_offsets[i])
            panel.set_trusted_range(trusted_range)
            panel.set_pixel_size(pixel_size)

    """
    Hardcoded values not contained in the self.nxs_file are taken from
    https://doi.org/10.1107/S0021889806025921
    """

    def _get_time_channel_bins(self):
        return self.nxs_file['raw_data_1']['instrument']['dae']['time_channels_1']['time_of_flight'][:]

    def _get_time_channels_in_seconds(self):
        bins = self._get_time_channel_bins()
        return [(bins[i] + bins[i+1])*.5*10**-6 for i in range(len(bins) - 1)]

    def _get_primary_flight_path_in_metres(self):
        return 8.3

    def _get_num_panels(self):
        return 11

    def _get_panel_names(self):
        return ["%02d" % (i + 1) for i in range(11)]

    def _get_panel_l2_vals_in_metres(self):
        return (.225, .225, .225, .225, .225, .225, .270, .270, .270, .270, .280)

    def _get_panel_longitude_in_deg(self):
        return (142.5, 90.0, 37.5, -37.5, -90.0, -142.5, 90.0, 0.0, -90.0, 180.0, 0.0)
           
    def _get_panel_latitude_in_deg(self):
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -45.0, -45.0, -45.0, -45.0, -90.0)

    def _get_panel_size_in_pixels(self):
        return (64, 64)
    
    def _get_panel_pixel_size_in_mm(self):
        return (3, 3)

    def _get_panel_type(self):
        return "coupled_scintillator_PSD"

    def _get_wavelength_bins_in_ang(self, L0, L, time_channels):
        h = 6.626E-34
        m_n = 1.675E-27
        return [((h * i)/(m_n * (L0 + L)))*10**10 for i in time_channels]

    def _get_raw_spectra_array(self):
        # Returns 2D array of (pixels, time_channels) for all 11 detectors
        return self.nxs_file['raw_data_1']['detector_1']['counts'][:][0]

    def _get_panel_images(self):
        raw_data = self._get_raw_spectra_array()
        # Image positions are offset by 4 
        # See p24 of https://www.isis.stfc.ac.uk/Pages/sxd-user-guide6683.pdf
        offsets =  [(((4096 * i) + (i*4)), ((4096 * (i+1)) + (i * 4))) for i in range(11)]
        return [raw_data[i[0] : i[1], :].T for i in offsets]
         
if __name__== "__main__":
    for arg in argv[1:]:
        print(FormatISISSXD.understand(arg))
