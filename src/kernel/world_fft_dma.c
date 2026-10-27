// WORLD floating FFT simple DMA. Root-only temporary module; no DT/boot changes.
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/dma-mapping.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>
#include "world_fft_ioctl.h"

#define DMA_BASE 0x40410000
#define BYTES ((2048 + 1) * sizeof(u64))
static struct platform_device *pdev;
static void __iomem *regs;
static void *tx, *rx;
static dma_addr_t tx_dma, rx_dma;
static DEFINE_MUTEX(lock);
static bool failed;

static long process(struct file *file, unsigned int op, unsigned long arg)
{
    u32 status;
    int rc;
    struct world_fft_request request;
    size_t bytes;
    if (op != WORLD_FFT_PROCESS) return -ENOTTY;
    if (copy_from_user(&request, (void __user *)arg, sizeof(request))) return -EFAULT;
    if ((request.n != 1024 && request.n != 2048) || request.forward > 1) return -EINVAL;
    bytes = request.n * sizeof(u64);
    if (mutex_lock_interruptible(&lock)) return -ERESTARTSYS;
    if (failed) { rc = -EIO; goto out; }
    ((u64 *)tx)[0] = (request.n == 1024 ? 10 : 11) | (request.forward << 8);
    if (copy_from_user((u64 *)tx + 1, u64_to_user_ptr(request.input), bytes)) {
        rc = -EFAULT; goto out;
    }
    dma_wmb();
    // Start receive before transmit. Clear old IOC/error flags (W1C).
    writel(0x7000, regs + 0x34);
    writel(0x7000, regs + 0x04);
    writel(1, regs + 0x30);
    writel(rx_dma, regs + 0x48);
    writel(bytes, regs + 0x58);
    writel(1, regs + 0x00);
    writel(tx_dma, regs + 0x18);
    writel(bytes + sizeof(u64), regs + 0x28);
    // 20 ms bounds a stalled FFT/DMA transaction. Failure requires PL reload.
    rc = readl_poll_timeout(regs + 0x34, status,
                            (status & 0x5070), 0, 20000);
    if (rc || (status & 0x5070) != 0x1000) goto fault;
    rc = readl_poll_timeout(regs + 0x04, status,
                            (status & 0x5070), 0, 20000);
    if (rc || (status & 0x5070) != 0x1000) goto fault;
    if (readl(regs + 0x58) != bytes) goto fault;
    dma_rmb();
    rc = copy_to_user(u64_to_user_ptr(request.output), rx, bytes) ? -EFAULT : 0;
    goto out;
fault:
    pr_err("world_fft: DMA fault tx=%08x rx=%08x\n",
           readl(regs + 4), readl(regs + 0x34));
    writel(4, regs);
    failed = true;
    rc = -EIO;
out:
    mutex_unlock(&lock);
    return rc;
}
static const struct file_operations fops = {
    .owner = THIS_MODULE, .unlocked_ioctl = process, .llseek = no_llseek,
};
static struct miscdevice misc = {
    .minor = MISC_DYNAMIC_MINOR, .name = "world_fft", .mode = 0600, .fops = &fops,
};
static int __init start(void)
{
    int rc;
    if (!request_mem_region(DMA_BASE, 0x10000, "world_fft")) return -EBUSY;
    regs = ioremap(DMA_BASE, 0x10000);
    if (!regs) { rc = -ENOMEM; goto region; }
    pdev = platform_device_register_simple("world-fft-buffer", -1, NULL, 0);
    if (IS_ERR(pdev)) { rc = PTR_ERR(pdev); goto mapping; }
    rc = dma_coerce_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
    if (rc) goto device;
    tx = dma_alloc_coherent(&pdev->dev, BYTES, &tx_dma, GFP_KERNEL);
    rx = dma_alloc_coherent(&pdev->dev, BYTES, &rx_dma, GFP_KERNEL);
    if (!tx || !rx) { rc = -ENOMEM; goto buffers; }
    // No register access until first ioctl, after the correct PL is loaded.
    rc = misc_register(&misc);
    if (!rc) return 0;
buffers:
    if (rx) dma_free_coherent(&pdev->dev, BYTES, rx, rx_dma);
    if (tx) dma_free_coherent(&pdev->dev, BYTES, tx, tx_dma);
device:
    platform_device_unregister(pdev);
mapping:
    iounmap(regs);
region:
    release_mem_region(DMA_BASE, 0x10000);
    return rc;
}
static void __exit stop(void)
{
    misc_deregister(&misc);
    if (!failed) writel(4, regs);
    dma_free_coherent(&pdev->dev, BYTES, rx, rx_dma);
    dma_free_coherent(&pdev->dev, BYTES, tx, tx_dma);
    platform_device_unregister(pdev);
    iounmap(regs);
    release_mem_region(DMA_BASE, 0x10000);
}
module_init(start);
module_exit(stop);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("WORLD 1024/2048 floating FFT coherent simple DMA client");
