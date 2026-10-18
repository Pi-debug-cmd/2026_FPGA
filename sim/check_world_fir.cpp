// Test adapter for independent NumPy comparison of streaming conversion.
#include <cstdio>
#include <cstring>
#include <io.h>
#include <fcntl.h>
#include "../src/ps/world_stream_fir.h"
int main(int argc, char **argv) {
  if (argc != 2 || (strcmp(argv[1], "down") && strcmp(argv[1], "up"))) return 2;
  _setmode(0, _O_BINARY); _setmode(1, _O_BINARY);
  Fir filter; InterpolateFir interpolate; double sample; int index = 0;
  while (fread(&sample, sizeof(sample), 1, stdin) == 1) {
    if (!strcmp(argv[1], "down")) {
      double value = filter.Step(sample, !(index % 2));
      if (!(index++ % 2)) fwrite(&value, sizeof(value), 1, stdout);
    } else {
      double pair[2]; interpolate.Step(sample, pair);
      fwrite(pair, sizeof(double), 2, stdout);
    }
  }
  return ferror(stdin) || fflush(stdout) ? 3 : 0;
}
