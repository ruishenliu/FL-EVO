import torch.nn as nn
import math
import torch.nn.functional as F

class GRUCell(nn.Module):
    """
    An implementation of GRUCell.

    """

    def __init__(self, input_size, hidden_size, bias=True):
        super(GRUCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.bias = bias
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias)
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias)
        self.reset_gate = nn.Linear(hidden_size, hidden_size, bias=bias)
        self.reset_parameters()#所以这个是什么参数？

    def reset_parameters(self):
        std = 1.0 / math.sqrt(self.hidden_size)
        for w in self.parameters():
            w.data.uniform_(-std, std)

    def forward(self, x, hidden):
        x = x.view(-1, x.size(1))

        gate_x = self.x2h(x)
        gate_h = self.h2h(hidden)

        gate_x = gate_x.squeeze()
        gate_h = gate_h.squeeze()

        i_r, i_i, i_n = gate_x.chunk(3, 1)#Entity_Num X hidden_size*3 -->3*eneity_num*hidden*3/3
        h_r, h_i, h_n = gate_h.chunk(3, 1)


        resetgate = F.sigmoid(i_r + h_r)

        inputgate = F.sigmoid(i_i + h_i)

        newgate = F.tanh(i_n + (resetgate * h_n))



        hy = (1 - inputgate) * hidden + inputgate * newgate


        return hy
