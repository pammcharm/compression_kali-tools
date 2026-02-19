#include "pamm_core.hpp"

#include <pybind11/pybind11.h>

#include <cstdint>
#include <string>
#include <vector>

namespace py = pybind11;

namespace {

std::vector<std::uint8_t> to_vec(const py::bytes& b) {
    std::string s = b;
    return std::vector<std::uint8_t>(s.begin(), s.end());
}

py::bytes to_bytes(const std::vector<std::uint8_t>& v) {
    return py::bytes(reinterpret_cast<const char*>(v.data()), v.size());
}

} // namespace

PYBIND11_MODULE(pamm_native, m) {
    m.doc() = "PAMM native compression and normalization backend";

    m.def("compress_engine", [](const std::string& engine, const py::bytes& data) {
        return to_bytes(pamm::compress_engine(engine, to_vec(data)));
    });

    m.def("decompress_engine", [](const std::string& engine, const py::bytes& data) {
        return to_bytes(pamm::decompress_engine(engine, to_vec(data)));
    });

    m.def("normalize_block", [](const py::bytes& data, const std::string& file_type) {
        auto in = to_vec(data);
        if (file_type == "pe-executable" || file_type == "elf-executable" || file_type == "mach-o") {
            return to_bytes(pamm::normalize_executable(in));
        }
        return to_bytes(in);
    });

    m.def("denormalize_block", [](const py::bytes& data, const std::string& file_type) {
        auto in = to_vec(data);
        if (file_type == "pe-executable" || file_type == "elf-executable" || file_type == "mach-o") {
            return to_bytes(pamm::denormalize_executable(in));
        }
        return to_bytes(in);
    });

    m.def("choose_best_engine", [](const py::bytes& data, bool fast_mode, bool high_entropy) -> py::tuple {
        auto best = pamm::choose_best_engine(to_vec(data), fast_mode, high_entropy);
        return py::make_tuple(best.first, to_bytes(best.second));
    });
}
