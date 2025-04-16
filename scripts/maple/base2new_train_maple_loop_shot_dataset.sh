#!/bin/bash

#cd ../..

# custom config
#DATA="/path/to/dataset/folder"
DATA="/home/tiggers/mydisk/lql/datasets"
TRAINER=MaPLe

# DATASET=$1
SEED=$1

CFG=vit_b16_c2_ep5_batch4_2ctx
#SHOTS=( 1 2 4 8 16 -1)
SHOTS_LIST=(16)
#cifar100 cub dtd fgvc_aircraft food101 oxford_flowers oxford_pets
DATASET_LIST=(cifar10)
#SHOTS=2

for DATASET in "${DATASET_LIST[@]}"
do
    for SHOTS in "${SHOTS_LIST[@]}"
    do
        DIR=output/base2new/train_base/${DATASET}/shots_${SHOTS}/${TRAINER}/${CFG}/seed${SEED}
        if [ -d "$DIR" ]; then
            echo "Results are available in ${DIR}. Resuming..."
            CUDA_VISIBLE_DEVICES=1 python train.py \
            --root ${DATA} \
            --seed ${SEED} \
            --trainer ${TRAINER} \
            --dataset-config-file configs/datasets/${DATASET}.yaml \
            --config-file configs/trainers/${TRAINER}/${CFG}.yaml \
            --output-dir ${DIR} \
            DATASET.NUM_SHOTS ${SHOTS} \
            DATASET.SUBSAMPLE_CLASSES all
        else
            echo "Run this job and save the output to ${DIR}"
            CUDA_VISIBLE_DEVICES=1 python train.py \
            --root ${DATA} \
            --seed ${SEED} \
            --trainer ${TRAINER} \
            --dataset-config-file configs/datasets/${DATASET}.yaml \
            --config-file configs/trainers/${TRAINER}/${CFG}.yaml \
            --output-dir ${DIR} \
            DATASET.NUM_SHOTS ${SHOTS} \
            DATASET.SUBSAMPLE_CLASSES all
        fi
    done
done