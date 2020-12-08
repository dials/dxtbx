import h5py
from dxtbx.format.FormatHDF5 import FormatHDF5

class FormatNXTOFRAW(FormatHDF5):

    """
    Class to read NXTOFRAW files as defined in
    https://www.nexusformat.org/TOFRaw.html
    """

    @staticmethod
    def understand(image_file):
        try:
            return is_nxtofraw_file(image_file)
        except IOError:
            return False

    @staticmethod
    def is_nxtofraw_file(image_file):

        """
        Confirms if image_file conforms to NXTOFRAW format
        by checking if required_fields are present with reasonable values.

        """

        def field_in_file(field, image_file):

            def field_in_file_recursive(field, nxs_obj):
                if field in nxs_obj.name.split("/"):
                    return True
                else:
                    if isinstance(nxs_obj, h5py.Group):
                        for i in nxs_obj.values():
                            if field_in_file_recursive(field, i):
                                return True
                    return False

            for i in image_file.values():
                if field_in_file_recursive(field, i):
                    return True
            return False
                

        def required_fields_present(required_fields, image_file):
            for i in required_fields:
                if not field_in_field(i, image_file):
                    return False
            return True



