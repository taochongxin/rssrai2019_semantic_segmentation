import torch
import torch.nn as nn
from models.utils.utils import init_weights


class UnetConv2(nn.Module):
    def __init__(self, in_size, out_size, batchnorm=None, is_batchnorm=True, n=2, kernel_size=3, stride=1, padding=1):
        super(UnetConv2, self).__init__()
        self.n = n
        self.ks = kernel_size
        self.stride = stride
        self.padding = padding
        if is_batchnorm:
            for i in range(1, n+1):
                conv = nn.Sequential(nn.Conv2d(in_size, out_size, kernel_size, stride, padding),
                                     batchnorm(out_size),
                                     nn.ReLU(inplace=True),
                                     nn.Conv2d(out_size, out_size, kernel_size, stride, padding),
                                     batchnorm(out_size),
                                     nn.ReLU(inplace=True)
                                     )
                setattr(self, 'conv%d' % i, conv)
                in_size = out_size
        else:
            for i in range(1, n + 1):
                conv = nn.Sequential(nn.Conv2d(in_size, out_size, kernel_size, stride, padding),
                                     nn.ReLU(inplace=True))
                setattr(self, 'conv%d' % i, conv)
                in_size = out_size

        # initialise the blocks
        for m in self.modules():
            init_weights(m, init_type='kaiming')

    def forward(self, inputs):
        x = inputs
        for i in range(1, self.n+1):
            conv = getattr(self, 'conv%d' % i)
            x = conv(x)

        return x


class UnetUp(nn.Module):
    def __init__(self, in_size, out_size, is_deconv, n_concat=2):
        super(UnetUp, self).__init__()
        self.conv = UnetConv2(in_size+(n_concat-2)*out_size, out_size, is_batchnorm=False)
        if is_deconv:
            self.up = nn.ConvTranspose2d(in_size, out_size, kernel_size=2, stride=2, padding=0)
        else:
            self.up = nn.Sequential(
                 nn.UpsamplingBilinear2d(scale_factor=2),
                 nn.Conv2d(in_size, out_size, 1))
           
        # initialise the blocks
        for m in self.children():
            if m.__class__.__name__.find('unetConv2') != -1:
                continue
            init_weights(m, init_type='kaiming')

    def forward(self, high_feature, *low_feature):
        outputs0 = self.up(high_feature)
        for feature in low_feature:
            outputs0 = torch.cat([outputs0, feature], 1)
        return self.conv(outputs0)
