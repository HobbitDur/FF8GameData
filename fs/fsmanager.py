import glob
import os
import pathlib
from dataclasses import dataclass
from enum import Enum, auto
import lzss

from fs.lzs import Lzs


class FsFileType(Enum):
    MAIN = auto()
    MENU = auto()
    WORLD = auto()
    FIELD = auto()
    MAGIC = auto()
    BATTLE = auto()
    UNKNOWN = auto()

@dataclass
class FiSingleData:
        length_unpack_file: int
        packed_file_location: int
        compression_used: bool


class Archive:
    """
    An archive is a composition of 3 files: FS, FI and FL.
    The workflow to read is a follow:
    1) Create the archive with the path for each file (done by creating the class)
    2) Load the data (thus the data can be loaded only when needed) with load_data
    3) Analyse the archive (thus the data can be loaded but analysed at a later time, or unload after analysing) with analyse_data
    4) Retrieve the data with get_fs_data_analyzed
    Normally there is no need to retrieve other info, but if needed the fi and fl data can be retrieved
    """
    FILE_NAME_STR_LIST = ("main", "menu", "world", "field", "magic", "battle")
    FILE_NAME_LIST = (FsFileType.MAIN, FsFileType.MENU, FsFileType.WORLD, FsFileType.FIELD, FsFileType.MAGIC, FsFileType.BATTLE)
    OFFSET_SIZE = 4

    def __init__(self, fs_path: str, fi_path: str, fl_path: str):
        """
        The different path contains the name of the file
        """
        # Raw data
        self._fs_path = fs_path
        self._fi_path = fi_path
        self._fl_path = fl_path
        self._fs_data = bytearray()
        self._fi_data = bytearray()
        self._fl_data = []

        # Data analysed now
        self.name = pathlib.Path(fs_path).name.replace(".fs", "")
        if self.name not in self.FILE_NAME_STR_LIST:
            print(f"Unexpected name: {self.name}")
            self.type = FsFileType.UNKNOWN
        else:
            self.type = self.FILE_NAME_LIST[self.FILE_NAME_STR_LIST.index(self.name)]

        # Data analysed later
        self._file_name_list = []
        self._data_list = []
        self._fi_data_list = []
        self._nb_file = 0

    def __str__(self):
        loaded = False
        analysed = False
        if self._fl_data and self._fi_data and self._fs_data:
            loaded= True
        if self._file_name_list and self._nb_file > 0 and  self._fi_data_list and self._data_list:
            analysed= True
        return f"Archive(name:{self.name}, loaded:{loaded}, analysed:{analysed})"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_folder_and_name(cls, folder_path, name):
        return cls(os.path.join(folder_path, name + ".fs"), os.path.join(folder_path, name + ".fi"), os.path.join(folder_path, name + ".fl"))

    def load_data(self):
        """
        Read all data in memory
        No error management if the file path are invalid
        """
        with open(self._fs_path, "rb") as file:
            self._fs_data.extend(file.read())
        with open(self._fi_path, "rb") as file:
            self._fi_data.extend(file.read())
        with open(self._fl_path, "r", encoding="utf8") as file:
            self._fl_data = file.read().splitlines()

    def unload_data(self):
        """Removing the data from memory"""
        self._fs_data = bytearray()
        self._fi_data = bytearray()
        self._fl_data = bytearray()

    def analyse_data(self):
        """
        Analysing the data already loaded
        If no data have been loaded, the data is loaded on itself
        First the Fl file is analysed, then the Fi then the Fs
        """
        # Checking if data have been loaded previously
        if not self._fs_data or not self._fi_data or not self._fl_data:
            self.load_data()

        # For FL, the data is already a list of text
        self._file_name_list = self._fl_data
        self._nb_file = len(self._file_name_list)

        # FI analyse
        for current_offset in range(0, len(self._fi_data), 3*self.OFFSET_SIZE):
            length_unpack_file = int.from_bytes(self._fi_data[current_offset:current_offset +self.OFFSET_SIZE], byteorder="little")
            packed_file_location = int.from_bytes(self._fi_data[current_offset+self.OFFSET_SIZE:current_offset +self.OFFSET_SIZE*2], byteorder="little")
            compression_used = bool(int.from_bytes(self._fi_data[current_offset+self.OFFSET_SIZE*2:current_offset +self.OFFSET_SIZE*3], byteorder="little"))
            self._fi_data_list.append(FiSingleData(length_unpack_file, packed_file_location, compression_used))

        # FS analyse
        for i in range(self._nb_file):
            if i == self._nb_file - 1:
                end_data = len(self._fs_data)
            else:
                end_data = self._fi_data_list[i+1].packed_file_location
            start_data = self._fi_data_list[i].packed_file_location
            fs_data = self._fs_data[start_data:end_data]
            if self._fi_data_list[i].compression_used:
                #fs_data = lzss.decompress(bytes(fs_data))
                fs_data = Lzs.decode(fs_data)
                #fs_data = lzs_c.decode(fs_data)
                pass
            self._data_list.append(fs_data)

    def get_fs_data_analyzed(self)->list[bytearray]:
        """Get the FS data uncompressed"""
        return self._data_list
    def get_fi_data_analyzed(self)->list[FiSingleData]:
        return self._fi_data_list
    def get_fl_data_analyzed(self)->list[str]:
        return self._file_name_list


class FsManager:
    """
    The FsManager is a class that manage a list of archive.
    The aim is to provide an easy-to-use abstract of a list of archive
    It is totally possible to manager his own list as the Archive class works on its own.
    """
    def __init__(self, folder_path=None):
        self._archive_list = []
        if folder_path:
            self.preload_all_archive_in_folder(folder_path)

    def __str__(self):
        return_str = ""
        for archive in self._archive_list:
            return_str += str(archive) + "\n"
        return return_str

    def __repr__(self):
        return self.__str__()

    def preload_all_archive_by_default_name(self, folder_path:str):
        for file_name in Archive.FILE_NAME_STR_LIST:
            self._archive_list.append(Archive.from_folder_and_name(folder_path, file_name))

    def preload_all_archive_in_folder(self, folder_path:str):
        fs_file_in_folder = glob.glob(os.path.join(folder_path, "*.fs"))
        for fs_file in fs_file_in_folder:
            if os.path.exists(fs_file.replace(".fs", ".fi")):
                if os.path.exists(fs_file.replace(".fs", ".fl")):
                    file_name = pathlib.Path(fs_file).name.replace(".fs", "")
                    self._archive_list.append(Archive.from_folder_and_name(folder_path, file_name))
                else:
                    print(f"File {fs_file.replace(".fs", ".fl")} doesn't exist")
            else:
                print(f"File {fs_file.replace(".fs", ".fi")} doesn't exist")

    def load_all_archive(self):
        for archive in self._archive_list:
            archive.load_data()

    def unload_all_archive(self):
        for archive in self._archive_list:
            archive.unload_data()

    def load_archive_by_name(self, name):
        self.get_archive_by_name(name).load_data()

    def analyse_archive_by_name(self, name):
        self.get_archive_by_name(name).analyse_data()

    def get_data_by_name(self, name:str):
        self.get_archive_by_name(name).get_fs_data_analyzed()

    def get_archive_by_name(self, name:str) -> Archive:
        for archive in self._archive_list:
            if archive.name == name:
                return archive


if __name__ == "__main__":
    # Create the fsManager
    fs_manager = FsManager()

    # Now do the full workflow:
    # 1. Preload (means reading the folder to find the different files)
    fs_manager.preload_all_archive_in_folder(os.path.join("..", "FsTester"))
    # 2. Load (means reading the data, which take memory and time)
    fs_manager.load_all_archive()
    # 3. Analyse (means analysing the data previously loaded, take time)
    fs_manager.analyse_archive_by_name("magic")

    # Retrieving as an example the archive for magic
    archive_magic = fs_manager.get_archive_by_name("magic")
    archive_fs_data = archive_magic.get_fs_data_analyzed()
    archive_fi_data = archive_magic.get_fi_data_analyzed()
    archive_fl_data = archive_magic.get_fl_data_analyzed()

    # Printing the first info for magic
    print(f"Fl path: {archive_fl_data[0]}")
    print(f"Fi archive data: {archive_fi_data[0]}")
    print(f"Fi archive data: {archive_fi_data[1]}")
    print(f"Fi archive data: {archive_fi_data[2]}")
    print(f"Fs hex: {archive_fs_data[0].hex(" ")}")
    print(f"Len hex: {len(archive_fs_data[0])}")
    print(f"Len hex: {len(archive_fs_data[1])}")

    # Print the fs manager, which will show all the archive loaded
    #print(fs_manager)
