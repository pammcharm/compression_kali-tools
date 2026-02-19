#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace pamm {

std::vector<std::uint8_t> normalize_text(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> normalize_executable(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> denormalize_executable(const std::vector<std::uint8_t>& in);

std::vector<std::uint8_t> compress_engine_a(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> decompress_engine_a(const std::vector<std::uint8_t>& in);

std::vector<std::uint8_t> compress_engine_b(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> decompress_engine_b(const std::vector<std::uint8_t>& in);

std::vector<std::uint8_t> compress_engine_c(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> decompress_engine_c(const std::vector<std::uint8_t>& in);

std::vector<std::uint8_t> compress_engine_n(const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> decompress_engine_n(const std::vector<std::uint8_t>& in);

std::vector<std::uint8_t> compress_engine(const std::string& engine, const std::vector<std::uint8_t>& in);
std::vector<std::uint8_t> decompress_engine(const std::string& engine, const std::vector<std::uint8_t>& in);

std::pair<std::string, std::vector<std::uint8_t>> choose_best_engine(
    const std::vector<std::uint8_t>& in,
    bool fast_mode,
    bool high_entropy);

} // namespace pamm
