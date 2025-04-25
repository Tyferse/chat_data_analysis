import json

import torch

from v1.config import eval_interval, epochs, learn_rate
from .model import GPTLanguageModel
from .utils import current_time, estimate_loss, get_batch


def model_training(update: bool) -> None:
    """
    Trains or updates a GPTLanguageModel using pre-loaded data.

    This function either initializes a new model or loads an existing model
    based on the `update` parameter.
    It then trains the model using the AdamW optimizer on the training
    and validation data sets.
    Finally the trained model is saved.
    
    Args:
        update (bool): Boolean flag to indicate whether to update an existing model.
    """
    torch.autograd.set_detect_anomaly(True)
    
    # LOAD DATA --------------------------------------------------------

    train_data = torch.load("assets/output/train.pt")
    valid_data = torch.load("assets/output/valid.pt")
    train_data = torch.cat([train_data, valid_data])

    with open("assets/output/vocab.txt", "r", encoding="utf-8") as f:
        vocab = json.loads(f.read())

    # INITIALIZE / LOAD MODEL ------------------------------------------

    if update:
        try:
            model = torch.load("assets/models/model.pt")
            print("Loaded existing model to continue training.")
        except FileNotFoundError:
            print("No existing model found. Initializing a new model.")
            model = GPTLanguageModel(vocab_size=len(vocab))
    else:
        print("Initializing a new model.")
        model = GPTLanguageModel(vocab_size=len(vocab))
    
    # initialize optimizer
    model = model.cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learn_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.2, patience=2)

    # number of model parameters
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters to be optimized: {n_params}\n", )

    # MODEL TRAINING ---------------------------------------------------
    
    try:
        for i in range(epochs):
            train_loss = estimate_loss(model, train_data)
            valid_loss = estimate_loss(model, valid_data)
            scheduler.step(train_loss)
            
            time = current_time()
            print(f"{time} | epoch {i}: train loss {train_loss:.4f}, "
                  f"valid loss {valid_loss:.4f}, "
                  f"lr {scheduler.get_last_lr()[0]:.6f}")
            
            for _ in range(eval_interval):
                # sample batch of data
                x_batch, y_batch = get_batch(train_data)
                x_batch, y_batch = x_batch.to('cuda'), y_batch.to('cuda')
                
                # evaluate the loss
                logits, loss = model(x_batch, y_batch)
                # print(logits)
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
        else:
            train_loss = estimate_loss(model, train_data)
            valid_loss = estimate_loss(model, valid_data)
            
            time = current_time()
            print(f"{time} | epoch {epochs}: train loss {train_loss:.4f}, "
                  f"valid loss {valid_loss:.4f}, "
                  f"lr {optimizer.param_groups[0]['lr']:.6f}")
            
            # # Make graph of model's architecture
            # if i == eval_interval:
            #     (make_dot(logits,
            #               params=dict(model.named_parameters()),
            #               show_attrs=True, show_saved=True)
            #      .render('graph1', 'nnviz', format='png'))
    finally:
        torch.save(model, "assets/models/model.pt")
        print("Model saved")
