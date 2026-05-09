import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class NucleiDataset(Dataset):
    def __init__(self, csv_file, image_size=256):
        self.df = pd.read_csv(csv_file)
        self.image_size = image_size

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        image_path = self.df.iloc[idx]["image_path"]
        mask_path = self.df.iloc[idx]["mask_path"]

        image = cv2.imread(image_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Failed to read image: {image_path}")
        if mask is None:
            raise ValueError(f"Failed to read mask: {mask_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image = cv2.resize(image, (self.image_size, self.image_size))
        mask = cv2.resize(mask, (self.image_size, self.image_size), interpolation=cv2.INTER_NEAREST)

        image = image.astype(np.float32) / 255.0
        mask = (mask > 0).astype(np.float32)

        image = np.transpose(image, (2, 0, 1))
        mask = np.expand_dims(mask, axis=0)

        image = torch.tensor(image, dtype=torch.float32)
        mask = torch.tensor(mask, dtype=torch.float32)

        return image, mask