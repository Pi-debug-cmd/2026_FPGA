// PCM16 DMA client with optional v2 ratio and DSP-reset control.
#include <linux/completion.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/dmaengine.h>
#include <linux/dma-mapping.h>
#include <linux/fs.h>
#include <linux/jiffies.h>
#include <linux/kref.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include "pitch_dma_ioctl.h"

#define BUFFER_BYTES (PITCH_DMA_MAX_FRAMES * sizeof(s32))
struct pitch_proxy {
    struct miscdevice misc;
    struct kref refs;
    struct mutex lock;
    struct dma_chan *tx, *rx;
    void *input, *output;
    dma_addr_t input_dma, output_dma;
    void __iomem *control;
    bool online, failed, opened, configured;
};

static void proxy_free(struct kref *ref)
{
    kfree(container_of(ref, struct pitch_proxy, refs));
}

static void transfer_complete(void *completion)
{
    complete(completion);
}

static int proxy_open(struct inode *inode, struct file *file)
{
    struct pitch_proxy *p = container_of(file->private_data, struct pitch_proxy, misc);
    if (mutex_lock_interruptible(&p->lock))
        return -ERESTARTSYS;
    if (!p->online || p->opened) {
        int error = p->online ? -EBUSY : -ENODEV;
        mutex_unlock(&p->lock);
        return error;
    }
    p->opened = true;
    kref_get(&p->refs);
    mutex_unlock(&p->lock);
    file->private_data = p;
    return 0;
}

static int proxy_close(struct inode *inode, struct file *file)
{
    struct pitch_proxy *p = file->private_data;
    mutex_lock(&p->lock);
    p->opened = false;
    mutex_unlock(&p->lock);
    kref_put(&p->refs, proxy_free);
    return 0;
}

static long proxy_ioctl(struct file *file, unsigned int command, unsigned long argument)
{
    struct pitch_proxy *p = file->private_data;
    struct pitch_dma_request request;
    struct dma_async_tx_descriptor *tx, *rx;
    dma_cookie_t tx_cookie, rx_cookie;
    DECLARE_COMPLETION_ONSTACK(tx_done);
    DECLARE_COMPLETION_ONSTACK(rx_done);
    size_t bytes;
    void __user *samples;
    int result;

    if (command == PITCH_DMA_CONFIGURE) {
        struct pitch_dma_config config;
        if (copy_from_user(&config, (void __user *)argument, sizeof(config)))
            return -EFAULT;
        if (config.reserved || config.ratio_q16 < 32768 || config.ratio_q16 > 131072)
            return -EINVAL;
        if (mutex_lock_interruptible(&p->lock))
            return -ERESTARTSYS;
        if (!p->online || p->failed)
            result = p->online ? -EIO : -ENODEV;
        else if (!p->control)
            result = -EOPNOTSUPP;
        else {
            /* AXI GPIO: channel1=ratio, channel2=active-low DSP reset. */
            writel(0, p->control + 0x8);
            readl(p->control + 0x8);
            udelay(1);
            writel(config.ratio_q16, p->control);
            writel(1, p->control + 0x8);
            readl(p->control + 0x8);
            /* 2048 clear clocks at the verified 100MHz, with margin. */
            udelay(50);
            p->configured = true;
            result = 0;
        }
        mutex_unlock(&p->lock);
        return result;
    }
    if (command != PITCH_DMA_PROCESS)
        return -ENOTTY;
    if (copy_from_user(&request, (void __user *)argument, sizeof(request)))
        return -EFAULT;
    if (!request.frames || request.frames > PITCH_DMA_MAX_FRAMES)
        return -EINVAL;
    samples = (void __user *)(unsigned long)request.samples_user_address;
    bytes = request.frames * sizeof(s32);
    if (mutex_lock_interruptible(&p->lock))
        return -ERESTARTSYS;
    if (!p->online || p->failed) {
        result = p->online ? -EIO : -ENODEV;
        goto unlock;
    }
    if (!p->configured) {
        result = -EINVAL;
        goto unlock;
    }
    if (copy_from_user(p->input, samples, bytes)) {
        result = -EFAULT;
        goto unlock;
    }
    rx = dmaengine_prep_slave_single(p->rx, p->output_dma, bytes,
            DMA_DEV_TO_MEM, DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
    tx = dmaengine_prep_slave_single(p->tx, p->input_dma, bytes,
            DMA_MEM_TO_DEV, DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
    if (!rx || !tx) {
        result = -EIO;
        goto fault;
    }
    rx->callback = transfer_complete;
    rx->callback_param = &rx_done;
    tx->callback = transfer_complete;
    tx->callback_param = &tx_done;
    rx_cookie = dmaengine_submit(rx);
    tx_cookie = dmaengine_submit(tx);
    if (dma_submit_error(rx_cookie) || dma_submit_error(tx_cookie)) {
        result = -EIO;
        goto fault;
    }
    /* Receive is armed before transmit to avoid blocking the AXI stream. */
    dma_wmb();
    dma_async_issue_pending(p->rx);
    dma_async_issue_pending(p->tx);
    if (!wait_for_completion_timeout(&rx_done, HZ) ||
        !wait_for_completion_timeout(&tx_done, HZ)) {
        result = -ETIMEDOUT;
        goto fault;
    }
    if (dma_async_is_tx_complete(p->rx, rx_cookie, NULL, NULL) != DMA_COMPLETE ||
        dma_async_is_tx_complete(p->tx, tx_cookie, NULL, NULL) != DMA_COMPLETE) {
        result = -EIO;
        goto fault;
    }
    dma_rmb();
    result = copy_to_user(samples, p->output, bytes) ? -EFAULT : 0;
    goto unlock;
fault:
    dmaengine_terminate_sync(p->tx);
    dmaengine_terminate_sync(p->rx);
    /* DSP-only reset cannot guarantee recovery of a failed DMA transaction. */
    p->failed = true;
unlock:
    mutex_unlock(&p->lock);
    return result;
}

static const struct file_operations proxy_fops = {
    .owner = THIS_MODULE, .open = proxy_open, .release = proxy_close,
    .unlocked_ioctl = proxy_ioctl, .llseek = no_llseek,
};

static void release_dma(struct pitch_proxy *p)
{
    if (p->tx) {
        dmaengine_terminate_sync(p->tx);
        if (p->input)
            dma_free_coherent(p->tx->device->dev, BUFFER_BYTES, p->input, p->input_dma);
        dma_release_channel(p->tx);
    }
    if (p->rx) {
        dmaengine_terminate_sync(p->rx);
        if (p->output)
            dma_free_coherent(p->rx->device->dev, BUFFER_BYTES, p->output, p->output_dma);
        dma_release_channel(p->rx);
    }
}

static int proxy_probe(struct platform_device *pdev)
{
    struct pitch_proxy *p = kzalloc(sizeof(*p), GFP_KERNEL);
    int error;
    if (!p)
        return -ENOMEM;
    kref_init(&p->refs);
    mutex_init(&p->lock);
    if (of_device_is_compatible(pdev->dev.of_node, "codex,pitch-dma-proxy-v2")) {
        p->control = devm_platform_ioremap_resource(pdev, 0);
        if (IS_ERR(p->control)) {
            error = PTR_ERR(p->control);
            p->control = NULL;
            goto fail;
        }
    }
    p->configured = !p->control;
    p->tx = dma_request_chan(&pdev->dev, "tx");
    if (IS_ERR(p->tx)) {
        error = PTR_ERR(p->tx);
        p->tx = NULL;
        goto fail;
    }
    p->rx = dma_request_chan(&pdev->dev, "rx");
    if (IS_ERR(p->rx)) {
        error = PTR_ERR(p->rx);
        p->rx = NULL;
        goto fail;
    }
    p->input = dma_alloc_coherent(p->tx->device->dev, BUFFER_BYTES, &p->input_dma, GFP_KERNEL);
    p->output = dma_alloc_coherent(p->rx->device->dev, BUFFER_BYTES, &p->output_dma, GFP_KERNEL);
    if (!p->input || !p->output) {
        error = -ENOMEM;
        goto fail;
    }
    p->misc.minor = MISC_DYNAMIC_MINOR;
    p->misc.name = "pitch_dma";
    p->misc.mode = 0600;
    p->misc.fops = &proxy_fops;
    p->misc.parent = &pdev->dev;
    p->online = true;
    error = misc_register(&p->misc);
    if (error)
        goto fail;
    platform_set_drvdata(pdev, p);
    return 0;
fail:
    release_dma(p);
    kref_put(&p->refs, proxy_free);
    return error;
}

static int proxy_remove(struct platform_device *pdev)
{
    struct pitch_proxy *p = platform_get_drvdata(pdev);
    misc_deregister(&p->misc);
    mutex_lock(&p->lock);
    p->online = false;
    release_dma(p);
    mutex_unlock(&p->lock);
    /* Existing open descriptors retain state and return ENODEV after removal. */
    kref_put(&p->refs, proxy_free);
    return 0;
}

static const struct of_device_id proxy_match[] = {
    { .compatible = "codex,pitch-dma-proxy" },
    { .compatible = "codex,pitch-dma-proxy-v2" }, {},
};
MODULE_DEVICE_TABLE(of, proxy_match);
static struct platform_driver proxy_driver = {
    .probe = proxy_probe, .remove = proxy_remove,
    .driver = { .name = "pitch-dma-proxy", .of_match_table = proxy_match },
};
module_platform_driver(proxy_driver);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("PCM16 AXI DMA client with optional ratio and DSP reset");
