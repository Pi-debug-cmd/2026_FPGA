// gemm_dma.c - kernel module: contiguous DMA region for the gemm_s8 PL
// accelerator, exposed via /dev/gemm_dma. Userspace mapping is CACHED;
// cache maintenance is provided via explicit sync ioctls.
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/dma-mapping.h>
#include <linux/dma-map-ops.h>
#include <linux/uaccess.h>
#include <linux/ioctl.h>
#include <linux/slab.h>

#define GEMM_DMA_SIZE (8u * 1024u * 1024u)
#define GEMM_DMA_MAGIC 'G'
#define GEMM_DMA_GET_PHYS _IOR(GEMM_DMA_MAGIC, 1, unsigned long long)
#define GEMM_DMA_GET_SIZE _IOR(GEMM_DMA_MAGIC, 2, unsigned long long)

struct gemm_range_arg {
	unsigned long long off;
	unsigned long long size;
};
// CPU->PL: writeback/clean after CPU writes
#define GEMM_CACHE_CLEAN _IOW(GEMM_DMA_MAGIC, 3, struct gemm_range_arg)
// PL->CPU: invalidate before CPU reads
#define GEMM_CACHE_INV   _IOW(GEMM_DMA_MAGIC, 4, struct gemm_range_arg)

// ARM dma_map_ops (arch/arm/mm/dma-mapping.c), provides cache maintenance.
extern const struct dma_map_ops arm_dma_ops;

struct gemm_dma_dev {
	void            *cpu_addr;
	dma_addr_t       handle;
	size_t           size;
	struct device   *dev;
};

static struct gemm_dma_dev *gdev;
static u64 gemm_dma_mask = DMA_BIT_MASK(32);

static int gemm_dma_open(struct inode *inode, struct file *filp)
{
	filp->private_data = gdev;
	return 0;
}

static int gemm_dma_mmap(struct file *filp, struct vm_area_struct *vma)
{
	struct gemm_dma_dev *dev = filp->private_data;
	unsigned long off = vma->vm_pgoff << PAGE_SHIFT;
	unsigned long size = vma->vm_end - vma->vm_start;
	unsigned long pfn;

	if (off >= dev->size || size > dev->size - off)
		return -EINVAL;
	pfn = ((unsigned long)dev->handle >> PAGE_SHIFT) + vma->vm_pgoff;
	// Cached (normal RAM) mapping.
	return remap_pfn_range(vma, vma->vm_start, pfn, size,
	                       vma->vm_page_prot);
}

static long gemm_dma_ioctl(struct file *filp, unsigned int cmd,
                           unsigned long arg)
{
	struct gemm_dma_dev *dev = filp->private_data;
	unsigned long long val;
	struct gemm_range_arg ra;

	switch (cmd) {
	case GEMM_DMA_GET_PHYS:
		val = (unsigned long long)dev->handle;
		if (copy_to_user((void __user *)arg, &val, sizeof(val)))
			return -EFAULT;
		return 0;
	case GEMM_DMA_GET_SIZE:
		val = (unsigned long long)dev->size;
		if (copy_to_user((void __user *)arg, &val, sizeof(val)))
			return -EFAULT;
		return 0;
	case GEMM_CACHE_CLEAN:
	case GEMM_CACHE_INV:
		if (copy_from_user(&ra, (void __user *)arg, sizeof(ra)))
			return -EFAULT;
		if (ra.off >= dev->size || ra.size > dev->size - ra.off)
			return -EINVAL;
		if (cmd == GEMM_CACHE_CLEAN)
			arm_dma_ops.sync_single_for_device(
				dev->dev, (dma_addr_t)(dev->handle + ra.off),
				(size_t)ra.size, DMA_TO_DEVICE);
		else
			arm_dma_ops.sync_single_for_cpu(
				dev->dev, (dma_addr_t)(dev->handle + ra.off),
				(size_t)ra.size, DMA_FROM_DEVICE);
		return 0;
	default:
		return -ENOTTY;
	}
}

static const struct file_operations gemm_dma_fops = {
	.owner          = THIS_MODULE,
	.open           = gemm_dma_open,
	.mmap           = gemm_dma_mmap,
	.unlocked_ioctl = gemm_dma_ioctl,
};

static struct miscdevice gemm_dma_misc = {
	.minor = MISC_DYNAMIC_MINOR,
	.name  = "gemm_dma",
	.fops  = &gemm_dma_fops,
};

static int __init gemm_dma_init(void)
{
	int ret;
	struct device *d;

	gdev = kzalloc(sizeof(*gdev), GFP_KERNEL);
	if (!gdev)
		return -ENOMEM;
	gdev->size = GEMM_DMA_SIZE;

	ret = misc_register(&gemm_dma_misc);
	if (ret) {
		pr_err("gemm_dma: misc_register failed %d\n", ret);
		goto err_free;
	}
	d = gemm_dma_misc.this_device;
	d->dma_mask = &gemm_dma_mask;
	d->coherent_dma_mask = DMA_BIT_MASK(32);
	gdev->dev = d;

	gdev->cpu_addr = dma_alloc_coherent(d, gdev->size, &gdev->handle,
	                                    GFP_KERNEL);
	if (!gdev->cpu_addr) {
		pr_err("gemm_dma: dma_alloc_coherent failed\n");
		ret = -ENOMEM;
		goto err_misc;
	}

	pr_info("gemm_dma: %zu bytes @ phys 0x%llx (cpu %p)\n",
	        gdev->size, (unsigned long long)gdev->handle, gdev->cpu_addr);
	return 0;

err_misc:
	misc_deregister(&gemm_dma_misc);
err_free:
	kfree(gdev);
	gdev = NULL;
	return ret;
}

static void __exit gemm_dma_exit(void)
{
	dma_free_coherent(gdev->dev, gdev->size, gdev->cpu_addr, gdev->handle);
	misc_deregister(&gemm_dma_misc);
	kfree(gdev);
	gdev = NULL;
}

module_init(gemm_dma_init);
module_exit(gemm_dma_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("LLVC");
MODULE_DESCRIPTION("Contiguous DMA buffer (cached user mapping) for gemm_s8");
