from __future__ import annotations

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "pamm_native",
        [
            "cpp/src/pamm_core.cpp",
            "cpp/src/pybind_module.cpp",
        ],
        include_dirs=["include"],
        libraries=["z", "lzma"],
        cxx_std=20,
    )
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
