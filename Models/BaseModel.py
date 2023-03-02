from abc import ABC
from typing import Optional

import torch
import torcheval.metrics.metric
from torch.optim.lr_scheduler import _LRScheduler
from torch.utils.data import DataLoader
from tqdm import tqdm


class BaseModel(ABC):
    def __init__(self):
        pass

    def save_model():
        pass

    @staticmethod
    def train_model(
        model: torch.nn.Module,
        train_loader: DataLoader,
        validation_loader: DataLoader,
        loss_fn: torch.nn,
        optimizer: torch.optim.Optimizer,
        metric: torcheval.metrics.Metric,
        num_epochs: Optional[int] = 5,
        device: Optional[torch.device] = torch.device("mps"),
        scheduler: Optional[_LRScheduler] = None,
    ) -> None:
        """
        Perform model training

        Args:
            model: torch.nn.Module
                Pytorch model for training
            train_loader: DataLoader
                Data loader for training set
            validation_loader: DataLoader
                Data loader for validation set
            loss_fn: torch.nn
                Predefined loss function
            num_epochs: Optional[int]
                Number of epochs to train
            device: Optional[torch.device]
                Device to perform calculation
            scheduler: Optional[Any]
                Scheduler to adjust learning rate per epoch

        Returns:
            None
        """
        running_loss = 0.0
        avg_loss = 0.0
        len_of_data = len(train_loader)
        for epoch in range(num_epochs):
            model.train()
            loop = tqdm(
                enumerate(train_loader), leave=False, total=len_of_data
            )
            running_loss = 0.0
            for batch_indx, (input, labels) in loop:
                input, labels = input.to(device), labels.to(device)

                optimizer.zero_grad()

                out = model(input)

                loss = loss_fn(out, labels)
                loss.backward()
                """
                Equal to
                torch.nn.functional.softmax(out, dim=1).max(dim=1).indices
                """
                out = torch.max(out, dim=1).indices
                metric.update(out, labels)

                optimizer.step()

                loop.set_description(f"Epoch [{epoch+1}/{num_epochs}]")
                loop.set_postfix(loss=loss.item())

                running_loss += loss.item()

            avg_loss = running_loss / (batch_indx + 1)
            train_f1_score = metric.compute()
            metric.reset()
            if scheduler:
                scheduler.step()

            # Evaluation phase
            model.eval()
            running_vloss = 0.0
            with torch.no_grad():
                for vbatch_indx, (vinputs, vlabels) in enumerate(
                    validation_loader
                ):
                    vinputs, vlabels = vinputs.to(device), vlabels.to(device)
                    voutputs = model(vinputs)
                    vloss = loss_fn(voutputs, vlabels)

                    voutputs = torch.max(voutputs, dim=1).indices
                    metric.update(voutputs, vlabels)
                    running_vloss += vloss
                avg_vloss = running_vloss / (vbatch_indx + 1)
            valid_f1_score = metric.compute()
            print(
                f"LOSS: train {avg_loss} / valid {avg_vloss} \
                \nF1_score: train {train_f1_score} / valid {valid_f1_score}"
            )
            metric.reset()