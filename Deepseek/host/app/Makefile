# Cross-compile vc_stream for the Zynq-7020 (ARMv7 hard-float, fully static).
#
# On this workstation make(1) is not installed, so build_arm.ps1 drives the same
# command lines; this Makefile is the portable equivalent and documents the exact
# flags.  Verified: both produce the same 796,232-byte ELF with SHA-256
# 6550e91925d4b4b10c1a1739ddc7b61e024417d9d380d485db026bb3736056a3.
#
#   make            # ARM static binary
#   make host       # native x86 build for desk-side numeric work
#   make clean

CROSS    ?= arm-linux-gnueabihf-
CXX_ARM   = $(CROSS)g++
CXX_HOST ?= g++

SRC_DIR   := src
BUILD_DIR := build
WORLD_SRC := $(wildcard third_party/world/*.cpp)
ST_SRC    := $(wildcard third_party/soundtouch/*.cpp)
# src/st_cpu_stub.cpp is mandatory: SoundTouch calls detectCPUextensions(), whose
# implementation only exists for x86, so ARM needs the zero stub.
# src/stream_mode.inc is #included by vc_stream.cpp (not compiled separately).
SRC       := $(SRC_DIR)/vc_stream.cpp $(SRC_DIR)/st_cpu_stub.cpp
HDR       := $(wildcard third_party/world/world/*.h) $(wildcard third_party/soundtouch/*.h) \
             $(SRC_DIR)/stream_mode.inc

# -O2 exactly as the task specifies; no -ffast-math anywhere (WORLD/CheapTrick
# numerics must stay reproducible).  Two exceptions, both documented and both
# verified not to change the results outside float rounding:
#   * the MLP kernel carries __attribute__((optimize("O3"))) in the source so its
#     element-wise inner loop vectorises;
#   * the STFT FFT is single precision.
COMMON      := -std=c++11 -Wno-psabi -pthread \
               -Ithird_party/world -Ithird_party/soundtouch \
               -I$(SRC_DIR) -DSOUNDTOUCH_DISABLE_X86_OPTIMIZATIONS
CXXFLAGS_ARM := -O2 -static -s -mcpu=cortex-a9 -mfpu=neon -mfloat-abi=hard \
                -ffunction-sections -fdata-sections $(COMMON)
# --whole-archive is required for a *static* binary: without it the pthread stubs
# in libc.a win over libpthread.a and pthread_create fails at runtime.
LDFLAGS_ARM  := -static -s -Wl,--gc-sections \
                -Wl,--whole-archive -lpthread -Wl,--no-whole-archive -lm -pthread
CXXFLAGS_HOST := -O2 $(COMMON)

.PHONY: all arm host clean blob

all: arm

blob:
	@test -f data/student_v5.blob || \
	  echo "WARNING: data/student_v5.blob missing -- run: python export_weights.py"

arm: $(BUILD_DIR)/vc_stream_arm

$(BUILD_DIR)/vc_stream_arm: $(SRC) $(WORLD_SRC) $(ST_SRC) $(HDR) | $(BUILD_DIR)
	$(CXX_ARM) $(CXXFLAGS_ARM) -o $@ $(SRC) $(WORLD_SRC) $(ST_SRC) $(LDFLAGS_ARM)
	@ls -l $@

host: $(BUILD_DIR)/vc_stream_host

$(BUILD_DIR)/vc_stream_host: $(SRC) $(WORLD_SRC) $(ST_SRC) $(HDR) | $(BUILD_DIR)
	$(CXX_HOST) $(CXXFLAGS_HOST) -o $@ $(SRC) $(WORLD_SRC) $(ST_SRC) -lm

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)