import os, sys

import pandas as pd

from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
import torch.nn.functional as Func
from torch.utils.data import DataLoader, TensorDataset
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
# Only this extra line of code is required to use oneDNN Graph
torch.jit.enable_onednn_fusion(True)
torch.autograd.detect_anomaly = False
torch.autograd.profiler.emit_nvtx = False 
torch.autograd.profiler.profile = False
torch.autograd.gradcheck = False
torch.autograd.gradgradcheck = False

base_DIR = "C:/Users/pansr/Documents/NBA/"

data_DIR = base_DIR + "data/rapm/"
misc_DIR = base_DIR + "data/misc/"
model_path = base_DIR + "data/models/"
pbp_DIR = base_DIR + "data/pbpdata/"
fig_DIR = base_DIR + "figs/analysis/"

dfw = pd.read_parquet(data_DIR + "NBA_rapm_possessions_odds_2017_2024.parquet")

# random seed
rr = 11

X = dfw[['margin', 'spread', 'secs']].values
y = dfw['win'].values

X = dfw[['margin', 'spread', 'secs']].values
y = dfw['win'].values

# sample the data
test_gid = dfw['gid'].sample(frac=0.8, random_state=rr).to_list()
dfw11 = dfw[dfw['gid'].isin(test_gid)]
# dfw12 = dfw11.query("secs <=120")
# for i in range(4):
#     dfw11  = pd.concat([dfw11,dfw12])
dfw1 = dfw11
dfw2 = dfw[dfw['gid'].isin(test_gid)]

# scale the data
scaler = MinMaxScaler()
smodel = scaler.fit(X)
Xs = smodel.transform(X)
X_train =  smodel.transform(dfw1[['margin', 'spread', 'secs']].values)
y_train = dfw1['win'].values
X_test =  smodel.transform(dfw2[['margin', 'spread', 'secs']].values)
y_test = dfw2['win'].values

# convert to tensors
inputs = torch.FloatTensor(Xs)
labels = torch.FloatTensor(y).unsqueeze(1)
X_train = torch.FloatTensor(X_train)
X_test = torch.FloatTensor(X_test)
y_train = torch.FloatTensor(y_train).unsqueeze(1)
y_test = torch.FloatTensor(y_test).unsqueeze(1)


# Create DataLoader for efficient batching
bs=8
dataset = TensorDataset(inputs, labels)
batch_size = int(len(dataset)/bs)+1
num_epochs = 50

def try_weights_dist(rank, world_size):
    torch.manual_seed(rr)
    # Distributed
    dist.init_process_group("gloo", rank=rank, world_size=world_size, init_method='env://')
    # Initialize the model
    h1=12
    h2=12
    model1 = nn.Sequential(
        nn.Linear(3,h1),
        nn.ReLU(),
        nn.Linear(h1,h2),
        nn.ReLU(),
        nn.Linear(h2,1),
        nn.Sigmoid()
    )
    
    # construct DDP model
    print(f"pre_init:{rank}")
    model = DDP(model1, device_ids=[rank])
    print(f"pos_init:{rank}")
    # loss function
    criterion = nn.BCELoss()
    # optimizer = torch.optim.RMSprop(model.parameters(),lr=1e-3)
    optimizer = torch.optim.Adam(model.parameters(),lr=1e-3)
    batch_size = batch_size
    sampler = DistributedSampler(dataset,num_replicas=world_size,rank=rank)
    dataloader = DataLoader(dataset, batch_size=batch_size, sampler=sampler)
    for epoch in range(num_epochs,desc="epochs"):
        model.train()
        for i, batch in enumerate(dataloader):
            inputs_batch,labels_batch = batch
            for param in model.parameters():
                param.grad = None
            outputs = model(inputs_batch)
            loss = criterion(outputs, labels_batch)
            loss.backward()
            optimizer.step()
            # if i % 10 == 0:
            print(f'Epoch {epoch}/{num_epochs}, Loss: {loss.item()}')

def main():
    world_size = 1
    mp.spawn(
        try_weights_dist,
        args=(world_size,),
        nprocs=world_size,
        join=True,
        daemon=True,
    )
    print("Success")

if __name__=="__main__":
    # Environment variables which need to be
    # set when using c10d's default "env"
    # initialization mode.
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = "29500"
    os.environ["USE_LIBUV"] = "0"
    main()