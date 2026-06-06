import numpy as np
import torch
import random

def set_all_seeds(seed=42, torch_seed=1234):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(torch_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(torch_seed)
