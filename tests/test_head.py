import itertools
import unittest

import numpy as np
import torch
from pytorchvideo.models.head import ResNetBasicHead, create_res_basic_head
from torch import nn


class TestHeadHelper(unittest.TestCase):
    def setUp(self):
        super().setUp()
        torch.set_rng_state(torch.manual_seed(42).get_state())

    def test_build_simple_head(self):
        """
        Test simple ResNetBasicHead (without dropout and activation layers).
        """
        for input_dim, output_dim in itertools.product((4, 8), (4, 8, 16)):
            model = ResNetBasicHead(
                proj=nn.Linear(input_dim, output_dim), pool=nn.AdaptiveAvgPool3d(1)
            )

            # Test forwarding.
            for tensor in TestHeadHelper._get_inputs(input_dim=input_dim):
                if tensor.shape[1] != input_dim:
                    with self.assertRaises(RuntimeError):
                        out = model(tensor)
                    continue
                else:
                    out = model(tensor)

                input_shape = tensor.shape
                output_shape = out.shape
                output_shape_gt = (input_shape[0], output_dim)

                self.assertEqual(
                    output_shape,
                    output_shape_gt,
                    "Output shape {} is different from expected shape {}".format(
                        output_shape, output_shape_gt
                    ),
                )

    def test_build_complex_head(self):
        """
        Test complex ResNetBasicHead.
        """
        for input_dim, output_dim in itertools.product((4, 8), (4, 8, 16)):
            model = ResNetBasicHead(
                proj=nn.Linear(input_dim, output_dim),
                activation=nn.Softmax(),
                pool=nn.AdaptiveAvgPool3d(1),
                dropout=nn.Dropout(0.5),
            )

            # Test forwarding.
            for tensor in TestHeadHelper._get_inputs(input_dim=input_dim):
                if tensor.shape[1] != input_dim:
                    with self.assertRaises(Exception):
                        out = model(tensor)
                    continue

                out = model(tensor)

                input_shape = tensor.shape
                output_shape = out.shape
                output_shape_gt = (input_shape[0], output_dim)

                self.assertEqual(
                    output_shape,
                    output_shape_gt,
                    "Output shape {} is different from expected shape {}".format(
                        output_shape, output_shape_gt
                    ),
                )

    def test_build_default_head_with_callable(self):
        """
        Test default builder `create_res_basic_head`.
        """
        for (pool, activation) in itertools.product(
            (nn.AvgPool3d, nn.MaxPool3d, nn.AdaptiveAvgPool3d, None),
            (nn.ReLU, nn.Softmax, nn.Sigmoid, None),
        ):
            if activation is None:
                activation_model = None
            elif activation == nn.Softmax:
                activation_model = activation(dim=1)
            else:
                activation_model = activation()

            if pool is None:
                pool_model = None
            elif pool == nn.AdaptiveAvgPool3d:
                pool_model = pool(1)
            else:
                pool_model = pool(kernel_size=[5, 7, 7], stride=[1, 1, 1])

            model = create_res_basic_head(
                in_features=16,
                out_features=32,
                pool=pool,
                pool_kernel_size=(5, 7, 7),
                output_size=(1, 1, 1),
                dropout_rate=0.0,
                activation=activation,
            )
            model_gt = ResNetBasicHead(
                proj=nn.Linear(16, 32),
                activation=activation_model,
                pool=pool_model,
                dropout=None,
            )
            model.load_state_dict(
                model_gt.state_dict(), strict=True
            )  # explicitly use strict mode.

            # Test forwarding.
            for tensor in TestHeadHelper._get_inputs(input_dim=16):
                with torch.no_grad():
                    if tensor.shape[1] != 16:
                        with self.assertRaises(RuntimeError):
                            out = model(tensor)
                        continue
                    else:
                        out = model(tensor)
                        out_gt = model(tensor)
                self.assertEqual(
                    out.shape,
                    out_gt.shape,
                    "Output shape {} is different from expected shape {}".format(
                        out.shape, out_gt.shape
                    ),
                )
                self.assertTrue(np.allclose(out.numpy(), out_gt.numpy()))

    @staticmethod
    def _get_inputs(input_dim: int = 8) -> torch.tensor:
        """
        Provide different tensors as test cases.

        Yield:
            (torch.tensor): tensor as test case input.
        """
        # Prepare random tensor as test cases.
        shapes = (
            # Forward succeeded.
            (1, input_dim, 5, 7, 7),
            (2, input_dim, 5, 7, 7),
            (4, input_dim, 5, 7, 7),
            (4, input_dim, 5, 7, 7),
            (4, input_dim, 7, 7, 7),
            (4, input_dim, 7, 7, 14),
            (4, input_dim, 7, 14, 7),
            (4, input_dim, 7, 14, 14),
            # Forward failed.
            (8, input_dim * 2, 3, 7, 7),
            (8, input_dim * 4, 5, 7, 7),
        )
        for shape in shapes:
            yield torch.rand(shape)
