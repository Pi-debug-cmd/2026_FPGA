// Independent double-precision comparison over a wide negative dB range.
#include <algorithm>
#include <cmath>
#include <cstdio>

int main() {
  double absolute = 0, relative = 0;
  for (int i = 0; i <= 200000; ++i) {
    const double db = -600.0 * i / 200000;
    const double reference = std::pow(10.0, db / 20.0);
    const double candidate = std::exp((db / 20.0) * 2.302585092994045684);
    absolute = std::max(absolute, std::abs(candidate - reference));
    relative = std::max(relative, std::abs(candidate - reference) / reference);
  }
  std::printf("{\"range_db\":[-600,0],\"points\":200001,\"max_absolute_error\":%.17g,"
              "\"max_relative_error\":%.17g}\n", absolute, relative);
  return absolute > 2e-15 || relative > 2e-14;
}
