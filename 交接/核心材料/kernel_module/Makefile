obj-m += gemm_dma.o
ccflags-y += -march=armv7-a -mtune=cortex-a9

# Cross toolchain (Vivado 2018.3), POSIX paths for MSYS build
CROSS_COMPILE ?= /d/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-
KDIR ?= /d/Tools_FPGA/workspace/voice_conversion_zynq7020/kernel_src

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=arm CROSS_COMPILE=$(CROSS_COMPILE) modules

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=arm CROSS_COMPILE=$(CROSS_COMPILE) clean
