import numpy as np
import torch
import torch.nn as nn

from transformers import CLIPConfig, PreTrainedModel
from transformers.configuration_utils import PretrainedConfig


class StableDiffusionSafetyCheckerDummy(PreTrainedModel):
    def __init__(self):
        super().__init__(PretrainedConfig())
        self.dummy_nn = torch.nn.Linear(1, 1)

    @torch.no_grad()
    def forward(self, clip_input, images):
        return images, False

    @torch.no_grad()
    def forward_onnx(self, clip_input: torch.FloatTensor, images: torch.FloatTensor):
        return images, False
