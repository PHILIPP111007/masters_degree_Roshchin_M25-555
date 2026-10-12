"""Model, training, evaluation and reproducibility utilities."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn as nn
import yaml
from torch.optim import AdamW
from transformers import AutoModel

from dataset import build_dataloaders


def load_config(config_path: str | Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def choose_device() -> torch.device:
    """Use CUDA only when the installed build supports the current GPU."""
    if not torch.cuda.is_available():
        return torch.device("cpu")
    capability = torch.cuda.get_device_capability()
    supported = set(torch.cuda.get_arch_list())
    requested = f"sm_{capability[0]}{capability[1]}"
    if requested not in supported:
        print(f"CUDA {requested} is unavailable in this PyTorch build. Using CPU.")
        return torch.device("cpu")
    return torch.device("cuda")


class MultimodalCalorieModel(nn.Module):
    """Image-text regression model with a normalized mass feature."""

    def __init__(self, cfg: dict) -> None:
        super().__init__()
        model_cfg = cfg["model"]
        self.image_encoder = timm.create_model(
            model_cfg["image_model"],
            pretrained=bool(model_cfg.get("pretrained", True)),
            num_classes=0,
            global_pool="avg",
        )
        self.text_encoder = AutoModel.from_pretrained(model_cfg["text_model"])
        image_dim = int(self.image_encoder.num_features)
        text_dim = int(self.text_encoder.config.hidden_size)
        fusion_dim = int(model_cfg.get("fusion_dim", 256))
        dropout = float(model_cfg.get("dropout", 0.2))

        self.image_projection = nn.Sequential(
            nn.Linear(image_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.text_projection = nn.Sequential(
            nn.Linear(text_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.mass_projection = nn.Sequential(
            nn.Linear(1, fusion_dim // 4),
            nn.LayerNorm(fusion_dim // 4),
            nn.GELU(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(fusion_dim * 2 + fusion_dim // 4, fusion_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim, 1),
        )

        if bool(model_cfg.get("freeze_encoders", False)):
            for parameter in self.image_encoder.parameters():
                parameter.requires_grad = False
            for parameter in self.text_encoder.parameters():
                parameter.requires_grad = False

    @staticmethod
    def masked_mean(hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        mask = attention_mask.unsqueeze(-1).to(hidden_states.dtype)
        summed = (hidden_states * mask).sum(dim=1)
        denominator = mask.sum(dim=1).clamp_min(1.0)
        return summed / denominator

    def forward(self, batch: dict) -> torch.Tensor:
        image_features = self.image_encoder(batch["image"])
        text_output = self.text_encoder(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
        )
        text_features = self.masked_mean(
            text_output.last_hidden_state,
            batch["attention_mask"],
        )
        image_features = self.image_projection(image_features)
        text_features = self.text_projection(text_features)
        mass_features = self.mass_projection(batch["mass"])
        fused = torch.cat([image_features, text_features, mass_features], dim=1)
        return self.classifier(fused).squeeze(1)


def trainable_parameters(model: nn.Module, name: str, lr: float) -> dict:
    parameters = [parameter for parameter in getattr(model, name).parameters() if parameter.requires_grad]
    return {"params": parameters, "lr": lr}


def make_optimizer(model: MultimodalCalorieModel, cfg: dict) -> AdamW:
    opt_cfg = cfg["training"]
    classifier_lr = float(opt_cfg.get("classifier_lr", 1e-4))
    groups = [
        trainable_parameters(model, "text_encoder", float(opt_cfg.get("text_lr", 1e-5))),
        trainable_parameters(model, "image_encoder", float(opt_cfg.get("image_lr", 1e-5))),
        trainable_parameters(model, "text_projection", classifier_lr),
        trainable_parameters(model, "image_projection", classifier_lr),
        trainable_parameters(model, "mass_projection", classifier_lr),
        trainable_parameters(model, "classifier", classifier_lr),
    ]
    groups = [group for group in groups if group["params"]]
    return AdamW(groups, weight_decay=float(opt_cfg.get("weight_decay", 1e-4)))


def move_batch(batch: dict, device: torch.device) -> dict:
    return {
        key: value.to(device, non_blocking=True) if torch.is_tensor(value) else value
        for key, value in batch.items()
    }


def regression_metrics(targets: list[float], predictions: list[float]) -> dict:
    y_true = np.asarray(targets, dtype=np.float64)
    y_pred = np.asarray(predictions, dtype=np.float64)
    errors = y_pred - y_true
    ss_res = float(np.square(errors).sum())
    ss_tot = float(np.square(y_true - y_true.mean()).sum())
    return {
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt(np.square(errors).mean())),
        "r2": float(1.0 - ss_res / ss_tot) if ss_tot else 0.0,
    }


def run_epoch(
    model: MultimodalCalorieModel,
    loader,
    criterion: nn.Module,
    device: torch.device,
    optimizer=None,
    scaler=None,
    amp: bool = True,
    grad_accumulation: int = 1,
) -> dict:
    training = optimizer is not None
    model.train(training)
    all_targets = []
    all_predictions = []
    total_loss = 0.0
    if training:
        optimizer.zero_grad(set_to_none=True)

    for step, batch in enumerate(loader):
        batch = move_batch(batch, device)
        with torch.cuda.amp.autocast(enabled=amp and device.type == "cuda"):
            predictions = model(batch)
            loss = criterion(predictions, batch["target"])
            scaled_loss = loss / grad_accumulation
        if training:
            if scaler is not None and scaler.is_enabled():
                scaler.scale(scaled_loss).backward()
            else:
                scaled_loss.backward()
            is_last_batch = step == len(loader) - 1
            if (step + 1) % grad_accumulation == 0 or is_last_batch:
                if scaler is not None and scaler.is_enabled():
                    scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                if scaler is not None and scaler.is_enabled():
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)

        batch_size = len(batch["target"])
        all_targets.extend(batch["target"].detach().cpu().tolist())
        all_predictions.extend(predictions.detach().float().cpu().tolist())
        total_loss += float(loss.detach().cpu()) * batch_size

    metrics = regression_metrics(all_targets, all_predictions)
    metrics["loss"] = total_loss / max(len(all_targets), 1)
    return metrics


def predict_loader(model, loader, device: torch.device) -> pd.DataFrame:
    model.eval()
    rows = []
    with torch.no_grad():
        for batch in loader:
            original_ids = batch["dish_id"]
            ingredient_text = batch["ingredient_text"]
            image_paths = batch["image_path"]
            batch = move_batch(batch, device)
            predictions = model(batch).detach().cpu().tolist()
            targets = batch["target"].detach().cpu().tolist()
            for dish_id, ingredients, image_path, target, prediction in zip(
                original_ids,
                ingredient_text,
                image_paths,
                targets,
                predictions,
            ):
                rows.append(
                    {
                        "dish_id": dish_id,
                        "ingredient_text": ingredients,
                        "image_path": image_path,
                        "actual_calories": float(target),
                        "predicted_calories": float(prediction),
                        "absolute_error": abs(float(prediction) - float(target)),
                    }
                )
    return pd.DataFrame(rows)


def train(config_path: str | Path) -> pd.DataFrame:
    """Train the model from a YAML config and save the best checkpoint."""
    cfg = load_config(config_path)
    seed_everything(int(cfg["seed"]))
    device = choose_device()
    loaders, info = build_dataloaders(cfg)
    model = MultimodalCalorieModel(cfg).to(device)
    criterion = nn.L1Loss()
    optimizer = make_optimizer(model, cfg)
    amp = bool(cfg["training"].get("amp", True)) and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=amp)
    epochs = int(cfg["training"].get("epochs", 10))
    grad_accumulation = int(cfg["training"].get("grad_accumulation", 1))
    checkpoint_path = Path(cfg["training"].get("checkpoint_path", "artifacts/best_model.pt"))
    history_path = Path(cfg["training"].get("history_path", "artifacts/history.csv"))
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    best_mae = float("inf")
    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        train_metrics = run_epoch(
            model,
            loaders["train"],
            criterion,
            device,
            optimizer=optimizer,
            scaler=scaler,
            amp=amp,
            grad_accumulation=grad_accumulation,
        )
        val_metrics = run_epoch(model, loaders["validation"], criterion, device, amp=amp)
        elapsed = time.perf_counter() - started
        row = {
            "epoch": epoch,
            "train_loss": train_metrics["loss"],
            "train_mae": train_metrics["mae"],
            "val_loss": val_metrics["loss"],
            "val_mae": val_metrics["mae"],
            "val_rmse": val_metrics["rmse"],
            "val_r2": val_metrics["r2"],
            "epoch_time_sec": elapsed,
        }
        history.append(row)
        history_df = pd.DataFrame(history)
        history_df.to_csv(history_path, index=False)
        print(
            f"epoch {epoch:02d}/{epochs} | "
            f"train MAE {row['train_mae']:.2f} | "
            f"val MAE {row['val_mae']:.2f} | "
            f"val RMSE {row['val_rmse']:.2f} | "
            f"val R2 {row['val_r2']:.3f} | {elapsed:.1f}s"
        )
        if row["val_mae"] < best_mae:
            best_mae = row["val_mae"]
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "config": cfg,
                    "epoch": epoch,
                    "best_val_mae": best_mae,
                    "mass_mean": info["mass_mean"],
                    "mass_std": info["mass_std"],
                },
                checkpoint_path,
            )
            print(f"saved best checkpoint: {checkpoint_path}")
    return pd.DataFrame(history)


def evaluate_checkpoint(config_path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Load the best checkpoint, run test inference and return predictions/metrics."""
    cfg = load_config(config_path)
    seed_everything(int(cfg["seed"]))
    device = choose_device()
    loaders, info = build_dataloaders(cfg)
    checkpoint_path = Path(cfg["training"].get("checkpoint_path", "artifacts/best_model.pt"))
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = MultimodalCalorieModel(cfg).to(device)
    model.load_state_dict(checkpoint["model_state"])
    predictions = predict_loader(model, loaders["test"], device)
    metrics = regression_metrics(
        predictions["actual_calories"].tolist(),
        predictions["predicted_calories"].tolist(),
    )
    predictions.to_csv("artifacts/test_predictions.csv", index=False)
    print(f"test MAE: {metrics['mae']:.2f}")
    print(f"test RMSE: {metrics['rmse']:.2f}")
    print(f"test R2: {metrics['r2']:.3f}")
    return predictions, metrics
