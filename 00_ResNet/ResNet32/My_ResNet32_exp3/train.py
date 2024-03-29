import torch
import torch.optim as optim
from torch.optim import lr_scheduler
import torch.nn as nn
import sys
sys.path.append("/home/hslee/Desktop/Embedded_AI/PyTorch_Tutorials/02_ResNet")
from utils import getCifar10, kaimingHeInitialization, testAccuracy
from architecture_ReLU_BN import MyResNet32_ReLU_BN
import pickle

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"device: {device}")

# Load the CIFAR10 data.
mini_batch_size = 128
train_loader, val_loader, test_loader, trainset, _, _ = getCifar10(mini_batch_size=mini_batch_size)

# Define the ResNet32 model.
model = MyResNet32_ReLU_BN()
model = model.to(device)
model.apply(kaimingHeInitialization)

# hyper parameters
## learning rate
lr = 0.1
## momentum
momentum = 0.9
## weight decay
L2 = 0.0001
# the number of iterations at 1 epoch
num_iters = (len(trainset) // mini_batch_size) + 1
print(f"num_iters at 1 epoch: {num_iters}")
epochs = 64000 // num_iters
# 32k, 48k iter = ?, ? epochs
print(f"32k iteration : {32000 // num_iters} epochs")
print(f"48k iteration : {48000 // num_iters} epochs")
print(f"64k iteration : {epochs} epochs")
## optimizer
## scheduler
## loss function
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=L2)        

# 125 epoch, 187 epoch lr decay
lr_decay = lr_scheduler.MultiStepLR(optimizer, milestones=[90, 136], gamma=0.1, verbose=True)

# train
train_loss_list = []
train_acc_list = []
val_loss_list = []
val_acc_list = []
for epoch in range(1, epochs+1):
    model.train().to(device)
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    train_acc = 0
    print(f"Epoch [{epoch}/{epochs}]")
    for i, (inputs, labels) in enumerate(train_loader, 0):
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        _, predicted = outputs.max(1)
        train_total += labels.size(0)
        train_correct += predicted.eq(labels).sum().item()
        
    train_loss = train_loss / len(train_loader)
    train_loss_list.append(train_loss)
    train_acc = 100 * train_correct / train_total
    train_acc_list.append(train_acc)
    
    model.eval().to(device)
    val_loss = 0.0
    val_correct = 0
    val_total = 0
    val_acc = 0
    with torch.no_grad():
        for i, (inputs, labels) in enumerate(val_loader, 0):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            val_loss += loss.item()
            _, predicted = outputs.max(1)
            val_total += labels.size(0)
            val_correct += predicted.eq(labels).sum().item()
            
    val_loss = val_loss / len(val_loader)
    val_loss_list.append(val_loss)
    val_acc = 100 * val_correct / val_total
    val_acc_list.append(val_acc)
    lr_decay.step()
    
    print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
    print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
    # save best model
    if val_acc == max(val_acc_list):
        torch.save(model.state_dict(), './checkpoint/best_model.pth')
        print(f"Best model is saved at {epoch} epoch. Val Acc: {val_acc:.4f}")
    print()

# save the log using pickle
with open('./log/train_loss_list.pkl', 'wb') as f:
    pickle.dump(train_loss_list, f)
with open('./log/train_acc_list.pkl', 'wb') as f:
    pickle.dump(train_acc_list, f)        
with open('./log/val_loss_list.pkl', 'wb') as f:
    pickle.dump(val_loss_list, f)
with open('./log/val_acc_list.pkl', 'wb') as f:
    pickle.dump(val_acc_list, f)
        
# test the best model
checkpoint = torch.load('./checkpoint/best_model.pth')
model.load_state_dict(checkpoint)
top1_acc, top5_acc = testAccuracy(model, test_loader)
print(f"Top-1 accuracy : {top1_acc:.2f}%, Top-5 accuracy : {top5_acc:.2f}%")
# save the accuracy using pickle
with open('./log/top1_acc.pkl', 'wb') as f:
    pickle.dump(top1_acc, f)
with open('./log/top5_acc.pkl', 'wb') as f:
    pickle.dump(top5_acc, f)