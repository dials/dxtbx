from __future__ import absolute_import, division, print_function
import h5py
from sys import argv
from dxtbx.format.FormatHDF5 import FormatHDF5

class FormatNXTOFRAW(FormatHDF5):

    """
    Class to read NXTOFRAW files as defined in
    https://www.nexusformat.org/TOFRaw.html

    See also 
    https://manual.nexusformat.org/classes/applications/NXtofraw.html

    """

    def __init__(self, image_file):
        self.reader = NXTOFRAWReader(image_file)
        self.detector = self.reader.get_detector()

    @staticmethod
    def understand(image_file):
        try:
            return FormatNXTOFRAW.is_nxtofraw_file(image_file)
        except IOError:
            return False

    @staticmethod
    def is_nxtofraw_file(image_file):

        """
        Confirms if image_file conforms to NXTOFRAW format
        by checking if required_fields are present

        """

        required_fields = ["detector_1"]

        def required_fields_present(required_fields, image_file):
            with h5py.File(image_file, "r") as handle:
                for i in required_fields:
                    if not NXTOFRAWReader.field_in_file(i, handle):
                        return False
                return True


        if not FormatHDF5.understand(image_file):
            return False

        return required_fields_present(required_fields, image_file)



class NXTOFRAWReader:

    """
    Class to hold NXTOFRAW files in memory
    and convert NXTOFRAW values to formats useful for FormatNXTOFRAW
    """
    
    def __init__(self, nxs_filename):
        self.nxs_filename = nxs_filename
        self.nxs_file = self.open_nxs_file(nxs_filename)

    def open_nxs_file(self, nxs_file):
        return h5py.File(nxs_file, "r")

    @staticmethod
    def field_in_file(field, nxs_file):

        def field_in_file_recursive(field, nxs_obj):
            if field in nxs_obj.name.split("/"):
                return True
            else:
                if isinstance(nxs_obj, h5py.Group):
                    for i in nxs_obj.values():
                        if field_in_file_recursive(field, i):
                            return True
                return False

        for i in nxs_file.values():
            if field_in_file_recursive(field, i):
                return True
        return False

    def get_detector(self):
        return self.nxs_file['/raw_data_1/detector_1']

    def get_name(self):
        return nxs_file['/raw_data_1/name'][0].decode()


if __name__== "__main__":
    for arg in argv[1:]:
        print(FormatNXTOFRAW.understand(arg))
