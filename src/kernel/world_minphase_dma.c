// WORLD fused minimum-phase HLS client. Root-only temporary module; no DT/boot changes.
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/dma-mapping.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/miscdevice.h>
#include <linux/fs.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>
#include <linux/ktime.h>
#include "world_minphase_ioctl.h"

#define CTRL_BASE 0x43c70000
#define ARGS_BASE 0x43c80000
#define REGION_BYTES 0x10000
#define PLANE_BYTES (WORLD_MINPHASE_BINS * sizeof(float))
#define BUFFER_BYTES (3 * PLANE_BYTES)

static struct platform_device *pdev;
static void __iomem *ctrl_regs, *arg_regs;
static void *buffer;
static dma_addr_t buffer_dma;
static DEFINE_MUTEX(lock);
static bool failed;
static u64 calls, copy_in_ns, device_ns, copy_out_ns;

static int stats_get(char *text, const struct kernel_param *kp)
{
    int length;
    mutex_lock(&lock);
    length = scnprintf(text, PAGE_SIZE,
        "{\"calls\":%llu,\"copy_in_ns\":%llu,\"device_ns\":%llu,\"copy_out_ns\":%llu}\n",
        calls, copy_in_ns, device_ns, copy_out_ns);
    mutex_unlock(&lock);
    return length;
}
static const struct kernel_param_ops stats_ops = { .get = stats_get };
module_param_cb(stats, &stats_ops, NULL, 0444);

static void write_pointer(unsigned int offset, dma_addr_t address)
{
    writel(lower_32_bits(address), arg_regs + offset);
    writel(upper_32_bits(address), arg_regs + offset + 4);
}

static long process(struct file *file, unsigned int op, unsigned long arg)
{
    struct world_minphase_packet __user *packet = (void __user *)arg;
    float *input = buffer;
    float *output_re = input + WORLD_MINPHASE_BINS;
    float *output_im = output_re + WORLD_MINPHASE_BINS;
    dma_addr_t re_dma = buffer_dma + PLANE_BYTES;
    dma_addr_t im_dma = re_dma + PLANE_BYTES;
    u64 begin, copied, completed;
    u32 status;
    int rc;

    if (op != WORLD_MINPHASE_PROCESS) return -ENOTTY;
    if (mutex_lock_interruptible(&lock)) return -ERESTARTSYS;
    if (failed) { rc = -EIO; goto out; }
    begin = ktime_get_ns();
    if (copy_from_user(input, packet->input, PLANE_BYTES)) {
        rc = -EFAULT; goto out;
    }
    dma_wmb();
    copied = ktime_get_ns();
    write_pointer(0x10, buffer_dma);
    write_pointer(0x1c, re_dma);
    write_pointer(0x28, im_dma);
    // Clear a stale COR done bit, then start one transaction.
    readl(ctrl_regs);
    writel(1, ctrl_regs);
    rc = readl_poll_timeout(ctrl_regs, status, status & BIT(1), 0, 20000);
    if (rc) {
        pr_err("world_minphase: timeout ctrl=%08x\n", status);
        failed = true;
        rc = -EIO;
        goto out;
    }
    dma_rmb();
    completed = ktime_get_ns();
    if (copy_to_user(packet->output_re, output_re, PLANE_BYTES) ||
        copy_to_user(packet->output_im, output_im, PLANE_BYTES)) {
        rc = -EFAULT; goto out;
    }
    ++calls;
    copy_in_ns += copied - begin;
    device_ns += completed - copied;
    copy_out_ns += ktime_get_ns() - completed;
    rc = 0;
out:
    mutex_unlock(&lock);
    return rc;
}

static const struct file_operations fops = {
    .owner = THIS_MODULE, .unlocked_ioctl = process, .llseek = no_llseek,
};
static struct miscdevice misc = {
    .minor = MISC_DYNAMIC_MINOR, .name = "world_minphase", .mode = 0600,
    .fops = &fops,
};

static int __init start(void)
{
    int rc;
    if (!request_mem_region(CTRL_BASE, REGION_BYTES, "world_minphase_ctrl"))
        return -EBUSY;
    if (!request_mem_region(ARGS_BASE, REGION_BYTES, "world_minphase_args")) {
        rc = -EBUSY; goto ctrl_region;
    }
    ctrl_regs = ioremap(CTRL_BASE, REGION_BYTES);
    arg_regs = ioremap(ARGS_BASE, REGION_BYTES);
    if (!ctrl_regs || !arg_regs) { rc = -ENOMEM; goto mappings; }
    pdev = platform_device_register_simple("world-minphase-buffer", -1, NULL, 0);
    if (IS_ERR(pdev)) { rc = PTR_ERR(pdev); goto mappings; }
    rc = dma_coerce_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
    if (rc) goto device;
    buffer = dma_alloc_coherent(&pdev->dev, BUFFER_BYTES, &buffer_dma, GFP_KERNEL);
    if (!buffer) { rc = -ENOMEM; goto device; }
    // No MMIO access occurs before the first ioctl after the matching PL is loaded.
    rc = misc_register(&misc);
    if (!rc) return 0;
    dma_free_coherent(&pdev->dev, BUFFER_BYTES, buffer, buffer_dma);
device:
    platform_device_unregister(pdev);
mappings:
    if (arg_regs) iounmap(arg_regs);
    if (ctrl_regs) iounmap(ctrl_regs);
    release_mem_region(ARGS_BASE, REGION_BYTES);
ctrl_region:
    release_mem_region(CTRL_BASE, REGION_BYTES);
    return rc;
}

static void __exit stop(void)
{
    misc_deregister(&misc);
    dma_free_coherent(&pdev->dev, BUFFER_BYTES, buffer, buffer_dma);
    platform_device_unregister(pdev);
    iounmap(arg_regs);
    iounmap(ctrl_regs);
    release_mem_region(ARGS_BASE, REGION_BYTES);
    release_mem_region(CTRL_BASE, REGION_BYTES);
}
module_init(start);
module_exit(stop);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("WORLD fused minimum-phase coherent HLS client");
