#include "pamm_core.hpp"

#include <lzma.h>
#include <zlib.h>

#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

std::uint32_t read_u32le(const std::vector<std::uint8_t>& in, std::size_t off) {
    return static_cast<std::uint32_t>(in[off]) |
           (static_cast<std::uint32_t>(in[off + 1]) << 8U) |
           (static_cast<std::uint32_t>(in[off + 2]) << 16U) |
           (static_cast<std::uint32_t>(in[off + 3]) << 24U);
}

void set_u32le(std::vector<std::uint8_t>& out, std::size_t off, std::uint32_t v) {
    out[off] = static_cast<std::uint8_t>(v & 0xFFU);
    out[off + 1] = static_cast<std::uint8_t>((v >> 8U) & 0xFFU);
    out[off + 2] = static_cast<std::uint8_t>((v >> 16U) & 0xFFU);
    out[off + 3] = static_cast<std::uint8_t>((v >> 24U) & 0xFFU);
}

void write_u32le(std::vector<std::uint8_t>& out, std::uint32_t v) {
    out.push_back(static_cast<std::uint8_t>(v & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((v >> 8U) & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((v >> 16U) & 0xFFU));
    out.push_back(static_cast<std::uint8_t>((v >> 24U) & 0xFFU));
}

std::vector<std::uint8_t> zlib_compress_level(const std::vector<std::uint8_t>& in, int level) {
    uLongf out_bound = compressBound(static_cast<uLong>(in.size()));
    std::vector<std::uint8_t> out;
    out.resize(4 + static_cast<std::size_t>(out_bound));
    set_u32le(out, 0, static_cast<std::uint32_t>(in.size()));

    uLongf actual = out_bound;
    int rc = compress2(
        reinterpret_cast<Bytef*>(out.data() + 4),
        &actual,
        reinterpret_cast<const Bytef*>(in.data()),
        static_cast<uLong>(in.size()),
        level);
    if (rc != Z_OK) {
        throw std::runtime_error("zlib compress failed");
    }
    out.resize(4 + static_cast<std::size_t>(actual));
    return out;
}

std::vector<std::uint8_t> zlib_decompress(const std::vector<std::uint8_t>& in) {
    if (in.size() < 4) {
        throw std::runtime_error("invalid zlib stream");
    }
    std::uint32_t raw_size = read_u32le(in, 0);
    std::vector<std::uint8_t> out(raw_size);
    uLongf actual = static_cast<uLongf>(raw_size);
    int rc = uncompress(
        reinterpret_cast<Bytef*>(out.data()),
        &actual,
        reinterpret_cast<const Bytef*>(in.data() + 4),
        static_cast<uLong>(in.size() - 4));
    if (rc != Z_OK || actual != raw_size) {
        throw std::runtime_error("zlib decompress failed");
    }
    return out;
}

std::vector<std::uint8_t> lzma_compress_preset(const std::vector<std::uint8_t>& in, std::uint32_t preset) {
    std::vector<std::uint8_t> out;
    std::size_t bound = static_cast<std::size_t>(lzma_stream_buffer_bound(in.size()));
    out.resize(4 + bound);
    set_u32le(out, 0, static_cast<std::uint32_t>(in.size()));

    std::size_t out_pos = 4;
    lzma_ret ret = lzma_easy_buffer_encode(
        preset,
        LZMA_CHECK_CRC64,
        nullptr,
        in.data(),
        in.size(),
        out.data(),
        &out_pos,
        out.size());
    if (ret != LZMA_OK) {
        throw std::runtime_error("lzma compress failed");
    }
    out.resize(out_pos);
    return out;
}

std::vector<std::uint8_t> lzma_decompress(const std::vector<std::uint8_t>& in) {
    if (in.size() < 4) {
        throw std::runtime_error("invalid lzma stream");
    }
    std::uint32_t raw_size = read_u32le(in, 0);
    std::vector<std::uint8_t> out(raw_size);

    std::size_t in_pos = 4;
    std::size_t out_pos = 0;
    std::uint64_t memlimit = std::numeric_limits<std::uint64_t>::max();
    uint32_t flags = 0;
    lzma_ret ret = lzma_stream_buffer_decode(
        &memlimit,
        flags,
        nullptr,
        in.data(),
        &in_pos,
        in.size(),
        out.data(),
        &out_pos,
        out.size());

    if (ret != LZMA_OK || out_pos != raw_size) {
        throw std::runtime_error("lzma decompress failed");
    }
    return out;
}

} // namespace

namespace pamm {

std::vector<std::uint8_t> normalize_text(const std::vector<std::uint8_t>& in) {
    return in;
}

std::vector<std::uint8_t> normalize_executable(const std::vector<std::uint8_t>& in) {
    std::vector<std::uint8_t> out = in;

    // Reversible 32-bit lane delta-XOR transform for address-heavy regions.
    for (std::size_t i = 4; i + 3 < out.size(); i += 4) {
        const std::uint32_t cur = static_cast<std::uint32_t>(in[i]) |
                                  (static_cast<std::uint32_t>(in[i + 1]) << 8U) |
                                  (static_cast<std::uint32_t>(in[i + 2]) << 16U) |
                                  (static_cast<std::uint32_t>(in[i + 3]) << 24U);
        const std::uint32_t prev = static_cast<std::uint32_t>(in[i - 4]) |
                                   (static_cast<std::uint32_t>(in[i - 3]) << 8U) |
                                   (static_cast<std::uint32_t>(in[i - 2]) << 16U) |
                                   (static_cast<std::uint32_t>(in[i - 1]) << 24U);
        const std::uint32_t d = cur ^ prev;
        out[i] = static_cast<std::uint8_t>(d & 0xFFU);
        out[i + 1] = static_cast<std::uint8_t>((d >> 8U) & 0xFFU);
        out[i + 2] = static_cast<std::uint8_t>((d >> 16U) & 0xFFU);
        out[i + 3] = static_cast<std::uint8_t>((d >> 24U) & 0xFFU);
    }

    return out;
}

std::vector<std::uint8_t> denormalize_executable(const std::vector<std::uint8_t>& in) {
    std::vector<std::uint8_t> out = in;
    for (std::size_t i = 4; i + 3 < out.size(); i += 4) {
        const std::uint32_t d = static_cast<std::uint32_t>(out[i]) |
                                (static_cast<std::uint32_t>(out[i + 1]) << 8U) |
                                (static_cast<std::uint32_t>(out[i + 2]) << 16U) |
                                (static_cast<std::uint32_t>(out[i + 3]) << 24U);
        const std::uint32_t prev = static_cast<std::uint32_t>(out[i - 4]) |
                                   (static_cast<std::uint32_t>(out[i - 3]) << 8U) |
                                   (static_cast<std::uint32_t>(out[i - 2]) << 16U) |
                                   (static_cast<std::uint32_t>(out[i - 1]) << 24U);
        const std::uint32_t cur = d ^ prev;
        out[i] = static_cast<std::uint8_t>(cur & 0xFFU);
        out[i + 1] = static_cast<std::uint8_t>((cur >> 8U) & 0xFFU);
        out[i + 2] = static_cast<std::uint8_t>((cur >> 16U) & 0xFFU);
        out[i + 3] = static_cast<std::uint8_t>((cur >> 24U) & 0xFFU);
    }
    return out;
}

std::vector<std::uint8_t> compress_engine_a(const std::vector<std::uint8_t>& in) {
    return zlib_compress_level(in, 6);
}

std::vector<std::uint8_t> decompress_engine_a(const std::vector<std::uint8_t>& in) {
    return zlib_decompress(in);
}

std::vector<std::uint8_t> compress_engine_b(const std::vector<std::uint8_t>& in) {
    return zlib_compress_level(in, 9);
}

std::vector<std::uint8_t> decompress_engine_b(const std::vector<std::uint8_t>& in) {
    return zlib_decompress(in);
}

std::vector<std::uint8_t> compress_engine_c(const std::vector<std::uint8_t>& in) {
    return lzma_compress_preset(in, 9U | LZMA_PRESET_EXTREME);
}

std::vector<std::uint8_t> decompress_engine_c(const std::vector<std::uint8_t>& in) {
    return lzma_decompress(in);
}

std::vector<std::uint8_t> compress_engine_n(const std::vector<std::uint8_t>& in) {
    std::vector<std::uint8_t> out;
    out.reserve(4 + in.size());
    write_u32le(out, static_cast<std::uint32_t>(in.size()));
    out.insert(out.end(), in.begin(), in.end());
    return out;
}

std::vector<std::uint8_t> decompress_engine_n(const std::vector<std::uint8_t>& in) {
    if (in.size() < 4) {
        throw std::runtime_error("invalid raw stream");
    }
    std::uint32_t raw_size = read_u32le(in, 0);
    if (in.size() - 4 != raw_size) {
        throw std::runtime_error("raw stream size mismatch");
    }
    return std::vector<std::uint8_t>(in.begin() + 4, in.end());
}

std::vector<std::uint8_t> compress_engine(const std::string& engine, const std::vector<std::uint8_t>& in) {
    if (engine == "A") return compress_engine_a(in);
    if (engine == "B") return compress_engine_b(in);
    if (engine == "C") return compress_engine_c(in);
    if (engine == "N") return compress_engine_n(in);
    throw std::runtime_error("unknown engine");
}

std::vector<std::uint8_t> decompress_engine(const std::string& engine, const std::vector<std::uint8_t>& in) {
    if (engine == "A") return decompress_engine_a(in);
    if (engine == "B") return decompress_engine_b(in);
    if (engine == "C") return decompress_engine_c(in);
    if (engine == "N") return decompress_engine_n(in);
    throw std::runtime_error("unknown engine");
}

std::pair<std::string, std::vector<std::uint8_t>> choose_best_engine(
    const std::vector<std::uint8_t>& in,
    bool fast_mode,
    bool high_entropy) {
    if (fast_mode) {
        return {"A", compress_engine_a(in)};
    }

    std::pair<std::string, std::vector<std::uint8_t>> best{"N", compress_engine_n(in)};

    auto try_engine = [&](const std::string& id) {
        auto out = compress_engine(id, in);
        if (out.size() < best.second.size()) {
            best = {id, std::move(out)};
        }
    };

    try_engine("A");
    try_engine("B");
    if (!high_entropy || in.size() < (16U * 1024U * 1024U)) {
        try_engine("C");
    }

    return best;
}

} // namespace pamm
