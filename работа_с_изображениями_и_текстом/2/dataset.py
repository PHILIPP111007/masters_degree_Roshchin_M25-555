"""Datasets and dataloaders for the multimodal calorie regression project."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Tuple

import albumentations as A
import numpy as np
import pandas as pd
import torch
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer


def ingredient_mapping(ingredients_path: str | os.PathLike) -> Dict[str, str]:
    """Map technical IDs such as ingr_0000000001 to human-readable names."""
    ingredients = pd.read_csv(ingredients_path)
    mapping = {}
    for row in ingredients.itertuples(index=False):
        key = f"ingr_{int(row.id):010d}"
        mapping[key] = str(row.ingr)
    return mapping


def prepare_metadata(data_root: str | os.PathLike) -> pd.DataFrame:
    """Load metadata, replace ingredient IDs and attach image paths."""
    root = Path(data_root)
    dish = pd.read_csv(root / "dish.csv")
    mapping = ingredient_mapping(root / "ingredients.csv")

    def names_from_ids(value: object) -> str:
        tokens = [token for token in str(value).split(";") if token]
        return ", ".join(mapping.get(token, f"unknown ({token})") for token in tokens)

    dish["ingredient_text"] = dish["ingredients"].map(names_from_ids)
    dish["image_path"] = dish["dish_id"].map(
        lambda dish_id: str(root / "images" / str(dish_id) / "rgb.png")
    )
    dish["image_exists"] = dish["image_path"].map(os.path.isfile)
    return dish


def split_metadata(
    metadata: pd.DataFrame,
    val_size: float = 0.15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Use the provided train/test split and create a deterministic validation split."""
    usable = metadata[metadata["image_exists"]].copy()
    train_pool = usable[usable["split"].eq("train")].copy()
    test = usable[usable["split"].eq("test")].copy()

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(train_pool))
    val_count = max(1, int(round(len(train_pool) * val_size)))
    val_positions = order[:val_count]
    val = train_pool.iloc[val_positions].copy()
    train = train_pool.drop(val.index).copy()

    return (
        train.reset_index(drop=True),
        val.reset_index(drop=True),
        test.reset_index(drop=True),
    )


def make_transforms(image_size: int, train: bool) -> A.Compose:
    """Create train or deterministic evaluation image transforms."""
    operations = [A.Resize(image_size, image_size)]
    if train:
        operations.extend(
            [
                A.HorizontalFlip(p=0.5),
                A.ShiftScaleRotate(
                    shift_limit=0.06,
                    scale_limit=0.10,
                    rotate_limit=12,
                    border_mode=0,
                    p=0.5,
                ),
                A.RandomBrightnessContrast(p=0.3),
            ]
        )
    operations.extend(
        [
            A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            ToTensorV2(),
        ]
    )
    return A.Compose(operations)


class DishDataset(Dataset):
    """Multimodal dataset returning image, ingredients, mass and calorie target."""

    def __init__(
        self,
        frame: pd.DataFrame,
        tokenizer,
        image_size: int = 224,
        max_text_length: int = 64,
        mass_mean: float = 0.0,
        mass_std: float = 1.0,
        train: bool = False,
    ) -> None:
        self.frame = frame.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.transforms = make_transforms(image_size, train)
        self.max_text_length = max_text_length
        self.mass_mean = mass_mean
        self.mass_std = max(mass_std, 1e-6)

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> dict:
        row = self.frame.iloc[index]
        with Image.open(row["image_path"]) as image:
            image_array = np.asarray(image.convert("RGB"))
        image_tensor = self.transforms(image=image_array)["image"].float()

        encoded = self.tokenizer(
            row["ingredient_text"],
            max_length=self.max_text_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        mass = (float(row["total_mass"]) - self.mass_mean) / self.mass_std

        return {
            "image": image_tensor,
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "mass": torch.tensor([mass], dtype=torch.float32),
            "target": torch.tensor(float(row["total_calories"]), dtype=torch.float32),
            "dish_id": str(row["dish_id"]),
            "ingredient_text": str(row["ingredient_text"]),
            "image_path": str(row["image_path"]),
        }


def build_dataloaders(cfg: dict):
    """Build train/validation/test loaders and return metadata used for inference."""
    data_root = Path(cfg["data"]["root"])
    metadata = prepare_metadata(data_root)
    train_frame, val_frame, test_frame = split_metadata(
        metadata,
        val_size=float(cfg["data"].get("val_size", 0.15)),
        seed=int(cfg["seed"]),
    )
    tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["text_model"])
    mass_mean = float(train_frame["total_mass"].mean())
    mass_std = float(train_frame["total_mass"].std())

    common = {
        "tokenizer": tokenizer,
        "image_size": int(cfg["data"].get("image_size", 224)),
        "max_text_length": int(cfg["data"].get("max_text_length", 64)),
        "mass_mean": mass_mean,
        "mass_std": mass_std,
    }
    datasets = {
        "train": DishDataset(train_frame, train=True, **common),
        "validation": DishDataset(val_frame, train=False, **common),
        "test": DishDataset(test_frame, train=False, **common),
    }
    loader_kwargs = {
        "batch_size": int(cfg["training"].get("batch_size", 4)),
        "num_workers": int(cfg["training"].get("num_workers", 2)),
        "pin_memory": torch.cuda.is_available(),
        "persistent_workers": int(cfg["training"].get("num_workers", 2)) > 0,
    }
    loaders = {
        "train": DataLoader(datasets["train"], shuffle=True, **loader_kwargs),
        "validation": DataLoader(datasets["validation"], shuffle=False, **loader_kwargs),
        "test": DataLoader(datasets["test"], shuffle=False, **loader_kwargs),
    }
    info = {
        "metadata": metadata,
        "train_frame": train_frame,
        "validation_frame": val_frame,
        "test_frame": test_frame,
        "tokenizer": tokenizer,
        "mass_mean": mass_mean,
        "mass_std": mass_std,
    }
    return loaders, info
