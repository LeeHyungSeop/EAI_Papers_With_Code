import sys
sys.path.append("..")
from architecture2 import VGG16_BN
from utils import rgb_to_yuv, loadValDataset, testAccuracy, getPrunedNetwork, showNewPrunedModel
import torch.nn as nn
import torch.nn.utils.prune as prune
import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.transforms import ToTensor
import kornia
import matplotlib.pyplot as plt
import numpy as np
from pytorch_model_summary import summary
from torch.nn.parameter import Parameter
import copy
import pickle

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
print(f"Using {device} device")

# load best model's parameter
model = VGG16_BN()
checkpoint = torch.load('../vgg16_baseline_exp1/checkpoint/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model = model.to(device)        

# conv1 ~ conv13까지 돌며 각각 10, 20, 30, 40, 50, 60, 70, 80, 90, 95% pruning 후 accuracy 측정
filters_pruned_away_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95] # (%)
layer = 0
val_loader, tesize = loadValDataset()
top1_acc_list = {}
top5_acc_list = {}

for param in model.modules() :
    if isinstance(param, torch.nn.Conv2d) :
        top1_acc_list[layer] = []
        top5_acc_list[layer] = []
        print(f"="*40, f" conv{layer+1} ", "="*40)
        
        for pruned_rate in filters_pruned_away_list :
            model_copy = copy.deepcopy(model)
            num_prune_channels = round(param.weight.data.shape[0] * pruned_rate / 100)
            print(f"\n----- pruned rate : {pruned_rate}%, #pruned channels : {num_prune_channels} -----")
            
            # new_pruned_model architecture
            new_pruned_model = getPrunedNetwork(model_copy, layer, num_prune_channels)
            showNewPrunedModel(new_pruned_model)
            
            # Top-1 accuracy, Top-5 accuracy
            # print conv, pruned rate, #pruned channels
            print("\t"*20, f"[conv{layer+1}] pruned rate : {pruned_rate}%, #pruned channels : {num_prune_channels}")
            top1_acc, top5_acc = testAccuracy(new_pruned_model, val_loader)
            top1_acc_list[layer].append(top1_acc)
            top5_acc_list[layer].append(top5_acc)

        layer += 1
        
# save accuracy using pickle
with open('../Figure2/b/top1_acc_list.pkl', 'wb') as f :
    pickle.dump(top1_acc_list, f)
with open('../Figure2/b/top5_acc_list.pkl', 'wb') as f :
    pickle.dump(top5_acc_list, f)    