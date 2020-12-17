from __future__ import absolute_import, division, print_function
from sys import argv
import h5py
from dxtbx.format.FormatNXTOFRAW import FormatNXTOFRAW, NXTOFRAWReader

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



if __name__== "__main__":
    for arg in argv[1:]:
        print(FormatISISSXD.understand(arg))
