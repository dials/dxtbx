from __future__ import absolute_import, division, print_function
from sys import argv
import h5py
from dxtbx.format.FormatNXTOFRAW import FormatNXTOFRAW, NXTOFRAWReader
from dxtbx.model import Detector

class FormatISISSXD(FormatNXTOFRAW):

    """
    Class to read NXTOFRAW files from the ISIS SXD
    (https://www.isis.stfc.ac.uk/Pages/sxd.aspx)

    """

    def __init__(self, image_file):
        super().__init__(self, image_file)
        
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
        https://doi.org/10.1107/S0021889806025921

        """

        num_panels = 11
        panel_type = "coupled_scintillator_PSD"
        image_size = (64, 64)
        pixel_size = (3, 3)
        longitude = (142.5, 90.0, 37.5, -37.5, -90.0, -142.5,
                    90.0, 0.0, -90.0, 180.0, 0.0)
        latitude = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    -45.0, -45.0, -45.0, -45.0, -90.0)
        l2 = (225, 225, 225, 225, 225, 225,
              270, 270, 270, 270, 280)
        trusted_range(-1, 100000)

        # Image positions are offset by 4 
        # See p24 of https://www.isis.stfc.ac.uk/Pages/sxd-user-guide6683.pdf
        img_offsets = [(((4096 * i) + (i*4)), ((4096 * (i+1)) + (i * 4))) for i in range(11)]


        detector = Detector()
        root = detector.hierarchy()

        for i in range(num_panels):
            panel = root.add_panel()
            panel.set_name("%02d" % i + 1)
            panel.set_type(panel_type)
            panel.set_raw_image_offset(img_offsets[i])
            panel.set_trusted_range(trusted_range)
            panel.set_pixel_size(pixel_size)
            
            

            

 


if __name__== "__main__":
    for arg in argv[1:]:
        print(FormatISISSXD.understand(arg))
