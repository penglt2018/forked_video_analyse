from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize(['/home/mllabs/edward/edward_workspace/video_analyse/model/right_back/pos_recog_model.py']))
