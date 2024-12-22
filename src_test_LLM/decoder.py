import random

from torch.nn import functional as F
import torch
from torch.nn.parameter import Parameter
import math
import os
path_dir = os.getcwd()

class ConvTransR(torch.nn.Module):
    def __init__(self, num_relations, embedding_dim, input_dropout=0, hidden_dropout=0, feature_map_dropout=0, channels=50, kernel_size=3, use_bias=True):
        super(ConvTransR, self).__init__()
        self.inp_drop = torch.nn.Dropout(input_dropout)
        self.hidden_drop = torch.nn.Dropout(hidden_dropout)
        self.feature_map_drop = torch.nn.Dropout(feature_map_dropout)
        self.loss = torch.nn.BCELoss()

        self.conv1 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))  # kernel size is odd, then padding = math.floor(kernel_size/2)
        self.bn0 = torch.nn.BatchNorm1d(2)
        self.bn1 = torch.nn.BatchNorm1d(channels)
        self.bn2 = torch.nn.BatchNorm1d(embedding_dim)
        self.register_parameter('b', Parameter(torch.zeros(num_relations)))
        self.fc = torch.nn.Linear(embedding_dim * channels, embedding_dim)


    def forward(self, embedding, emb_rel, triplets, nodes_id=None, mode="train", negative_rate=0):
        # e_embedded_all = [F.tanh(embedding_emb) for embedding_emb in embedding]
        # entity_index = [i for i in triplets[:, 0]]
        # assert (len(embedding) == triplets.size()[0])
        # for index, i in enumerate(e_embedded_all):
        #     if index == 0:
        #         e1_embedded = i[[index, 0]].unsqueeze(1)
        #         e2_embedded = i[[index, 2]].unsqueeze(1)
        #     else:
        #         e1_embedded = torch.concatenate((e1_embedded, i[[index, 0]].unsqueeze(1)), 0)
        #         e2_embedded = torch.concatenate((e2_embedded, i[[index, 0]].unsqueeze(1)), 0)

        e1_embedded_all = F.tanh(embedding) #Liu
        batch_size = len(triplets)
        # if mode=="train":
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)#Liu
        e2_embedded = e1_embedded_all[triplets[:, 2]].unsqueeze(1)#Liu
        # else:
        #     e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
        #     e2_embedded = e1_embedded_all[triplets[:, 2]].unsqueeze(1)
        stacked_inputs = torch.cat([e1_embedded, e2_embedded], 1)
        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)
        x = self.fc(x)
        x = self.hidden_drop(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = torch.mm(x, emb_rel.transpose(1, 0))
        return x


class ConvTransE(torch.nn.Module):
    def __init__(self, num_entities, embedding_dim, input_dropout=0, hidden_dropout=0, feature_map_dropout=0, channels=50, kernel_size=3, use_bias=True):

        super(ConvTransE, self).__init__()
        # 初始化relation embeddings
        # self.emb_rel = torch.nn.Embedding(num_relations, embedding_dim, padding_idx=0)

        self.inp_drop = torch.nn.Dropout(input_dropout)
        self.hidden_drop = torch.nn.Dropout(hidden_dropout)
        self.feature_map_drop = torch.nn.Dropout(feature_map_dropout)
        self.loss = torch.nn.BCELoss()

        self.conv1 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))  # kernel size is odd, then padding = math.floor(kernel_size/2)
        self.bn0 = torch.nn.BatchNorm1d(2)
        self.bn1 = torch.nn.BatchNorm1d(channels)
        self.bn2 = torch.nn.BatchNorm1d(embedding_dim)
        self.register_parameter('b', Parameter(torch.zeros(num_entities)))
        self.fc = torch.nn.Linear(embedding_dim * channels, embedding_dim)


    def forward(self, embedding, emb_rel, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):

        # e1_embedded_all = [F.tanh(embedding_emb) for embedding_emb in embedding]
        # entity_index = [i for i in triplets[:,0]]
        # assert (len(embedding) == triplets.size()[0])
        # for index, i in enumerate(e1_embedded_all):
        #     if index == 0:
        #         e1_embedded = i[[index,0]].unsqueeze(1)
        #     else:
        #         e1_embedded =torch.concatenate((e1_embedded,i[[index,0]].unsqueeze(1)),0)

        e1_embedded_all = F.tanh(embedding)
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1).cuda()
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)
        stacked_inputs = torch.cat([e1_embedded.view(rel_embedded.shape[0],-1,rel_embedded.shape[2]), rel_embedded], 1)
        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)
        x = self.fc(x)
        x = self.hidden_drop(x)
        if batch_size > 1:
            x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
        else:
            x = torch.mm(x, partial_embeding.transpose(1, 0))
        return x
    def forward_slow(self, embedding, emb_rel, triplets):

        e1_embedded_all = F.tanh(embedding)
        # e1_embedded_all = embedding
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
        # translate to sub space
        # e1_embedded = torch.matmul(e1_embedded, sub_trans)
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)
        stacked_inputs = torch.cat([e1_embedded, rel_embedded], 1)
        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)
        x = self.fc(x)
        x = self.hidden_drop(x)
        if batch_size > 1:
            x = self.bn2(x)
        x = F.relu(x)
        e2_embedded = e1_embedded_all[triplets[:, 2]]
        score = torch.sum(torch.mul(x, e2_embedded), dim=1)
        pred = score
        return pred
        
        

class ConvTransE2(torch.nn.Module):
    def __init__(self, num_entities, embedding_dim, input_dropout=0, hidden_dropout=0, feature_map_dropout=0, channels=50, kernel_size=3, use_bias=True):

        super(ConvTransE2, self).__init__()
        # 初始化relation embeddings
        # self.emb_rel = torch.nn.Embedding(num_relations, embedding_dim, padding_idx=0)

        self.inp_drop = torch.nn.Dropout(input_dropout)
        self.hidden_drop = torch.nn.Dropout(hidden_dropout)
        self.feature_map_drop = torch.nn.Dropout(feature_map_dropout)
        self.feature_map_drop2 = torch.nn.Dropout(feature_map_dropout)
        self.loss = torch.nn.BCELoss()

        self.conv1 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))  # kernel size is odd, then padding = math.floor(kernel_size/2)
        self.bn0 = torch.nn.BatchNorm1d(2)
        self.bn1 = torch.nn.BatchNorm1d(channels)
        
        self.conv2 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))  # kernel size is odd, then padding = math.floor(kernel_size/2)
        self.bn00 = torch.nn.BatchNorm1d(2)
        self.bn11 = torch.nn.BatchNorm1d(channels)
        
        
        
        self.bn2 = torch.nn.BatchNorm1d(embedding_dim*2)
        self.register_parameter('b', Parameter(torch.zeros(num_entities)))
        self.fc = torch.nn.Linear(embedding_dim * channels*2, 2*embedding_dim)


    def forward(self, embedding, emb_rel, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):

        e1_embedded_all = F.tanh(embedding)
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)
        e1_embedded = e1_embedded.view(rel_embedded.shape[0],-1,rel_embedded.shape[2])
        stacked_inputs = torch.cat([torch.unsqueeze(e1_embedded[:,0,:],1), rel_embedded], 1)
        stacked_inputs2 = torch.cat([torch.unsqueeze(e1_embedded[:,1,:],1), rel_embedded], 1)

        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)

        stacked_inputs2 = self.bn00(stacked_inputs2)
        x2 = self.inp_drop(stacked_inputs2)
        x2 = self.conv2(x2)
        x2 = self.bn11(x2)
        x2 = F.relu(x2)
        x2 = self.feature_map_drop2(x2)
        x2 = x2.view(batch_size, -1)

        x = torch.cat((x, x2), 1)

        x = self.fc(x)
        x = self.hidden_drop(x)
        if batch_size > 1:
            x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
        else:
            x = torch.mm(x, partial_embeding.transpose(1, 0))
        return x
    def forward_slow(self, embedding, emb_rel, triplets):

        e1_embedded_all = F.tanh(embedding)
        # e1_embedded_all = embedding
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
        # translate to sub space
        # e1_embedded = torch.matmul(e1_embedded, sub_trans)
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)
        stacked_inputs = torch.cat([e1_embedded, rel_embedded], 1)
        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)
        x = self.fc(x)
        x = self.hidden_drop(x)
        if batch_size > 1:
            x = self.bn2(x)
        x = F.relu(x)
        e2_embedded = e1_embedded_all[triplets[:, 2]]
        score = torch.sum(torch.mul(x, e2_embedded), dim=1)
        pred = score
        return pred