# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.

import itertools
import unittest

import torch
from pytorchvideo.layers.convolutions import ConvReduce3D
from torch import nn


class TestConvReduce3D(unittest.TestCase):
    def setUp(self):
        super().setUp()
        torch.set_rng_state(torch.manual_seed(42).get_state())

    def test_create_stack_conv(self):
        """
        Test ConvReduce3D.
        """
        for input_dim, output_dim in itertools.product((2, 4), (4, 8, 16)):
            model = ConvReduce3D(
                in_channels=input_dim,
                out_channels=output_dim,
                kernel_size=((1, 1, 1), (3, 3, 3), (1, 3, 3)),
                stride=((1, 1, 1), (1, 1, 1), None),
                padding=((0, 0, 0), (1, 1, 1), (0, 1, 1)),
                dilation=((2, 2, 2), (1, 1, 1), None),
                groups=(1, 2, None),
                bias=(True, False, None),
            )
            model_gt_list = [
                nn.Conv3d(
                    in_channels=input_dim,
                    out_channels=output_dim,
                    kernel_size=(1, 1, 1),
                    stride=(1, 1, 1),
                    padding=(0, 0, 0),
                    dilation=(2, 2, 2),
                    groups=1,
                    bias=True,
                ),
                nn.Conv3d(
                    in_channels=input_dim,
                    out_channels=output_dim,
                    kernel_size=(3, 3, 3),
                    stride=(1, 1, 1),
                    padding=(1, 1, 1),
                    dilation=(1, 1, 1),
                    groups=2,
                    bias=False,
                ),
                nn.Conv3d(
                    in_channels=input_dim,
                    out_channels=output_dim,
                    kernel_size=(1, 3, 3),
                    padding=(0, 1, 1),
                ),
            ]
            model.convs[0].load_state_dict(
                model_gt_list[0].state_dict(), strict=True
            )  # explicitly use strict mode.
            model.convs[1].load_state_dict(
                model_gt_list[1].state_dict(), strict=True
            )  # explicitly use strict mode.
            model.convs[2].load_state_dict(
                model_gt_list[2].state_dict(), strict=True
            )  # explicitly use strict mode.

            # Test forwarding.
            for tensor in TestConvReduce3D._get_inputs(input_dim):
                if tensor.shape[1] != input_dim:
                    with self.assertRaises(RuntimeError):
                        output_tensor = model(tensor)
                    continue
                else:
                    output_tensor = model(tensor)
                    output_gt = []
                    for ind in range(3):
                        output_gt.append(model_gt_list[ind](tensor))
                    output_tensor_gt = torch.stack(output_gt, dim=0).sum(
                        dim=0, keepdim=False
                    )

                self.assertEqual(
                    output_tensor.shape,
                    output_tensor_gt.shape,
                    "Output shape {} is different from expected shape {}".format(
                        output_tensor.shape, output_tensor_gt.shape
                    ),
                )

    @staticmethod
    def _get_inputs(input_dim: int = 3) -> torch.tensor:
        """
        Provide different tensors as test cases.

        Yield:
            (torch.tensor): tensor as test case input.
        """
        # Prepare random tensor as test cases.
        shapes = (
            # Forward succeeded.
            (1, input_dim, 3, 7, 7),
            (1, input_dim, 5, 7, 7),
            (1, input_dim, 7, 7, 7),
            (2, input_dim, 3, 7, 7),
            (4, input_dim, 3, 7, 7),
            (8, input_dim, 3, 7, 7),
            (2, input_dim, 3, 7, 14),
            (2, input_dim, 3, 14, 7),
            (2, input_dim, 3, 14, 14),
            # Forward failed.
            (8, input_dim * 2, 3, 7, 7),
            (8, input_dim * 4, 5, 7, 7),
        )
        for shape in shapes:
            yield torch.rand(shape)
