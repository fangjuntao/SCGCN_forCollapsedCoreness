#!/bin/bash
k=40
b=20
CUDA_VISIBLE_DEVICES=0 python2 train_gcn_kcore.py \
 --batch_size 32 \
 --n_hid1 256 \
 --n_hid2 256 \
 --n_expert 256 \
 --att_hid 256 \
 --steps 200 \
 --learning_rate 1e-4 \
 --verbose True \
 --extra_feats 0 \
 --weight_decay 5e-3 \
 --normalization NormAdj \
 --dropout 0.5 \
 --input_data_folder ../data/fb \
 --b $b \
 --k $k \
 --model_dir gcnatt_kcore_fb_${k}_${b}.pt  > result_gcnatt_fb_${k}_${b}.txt

