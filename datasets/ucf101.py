import os
import pickle
import re

from dassl.data.datasets import DATASET_REGISTRY, Datum, DatasetBase
from dassl.utils import mkdir_if_missing

from .oxford_pets import OxfordPets

base_file_path = "/home/STU/lql/datasets/UCF101/UCF-101-midframes/ucf-101-base.text"
novel_file_path = "/home/STU/lql/datasets/UCF101/UCF-101-midframes/ucf-101-novel.text"

@DATASET_REGISTRY.register()
class UCF101(DatasetBase):

    dataset_dir = "UCF101"

    def __init__(self, cfg):
        #root = os.path.abspath(os.path.expanduser(cfg.DATASET.ROOT))
        root = cfg.DATASET.ROOT
        self.dataset_dir = os.path.join(root, self.dataset_dir)
        self.image_dir = os.path.join(self.dataset_dir, "UCF-101-midframes")
        self.split_path = os.path.join(self.dataset_dir, "split_zhou_UCF101.json")
        self.split_fewshot_dir = os.path.join(self.dataset_dir, "split_fewshot")
        mkdir_if_missing(self.split_fewshot_dir)

        if os.path.exists(self.split_path):
            train, val, test = OxfordPets.read_split(self.split_path, self.image_dir)
        else:
            cname2lab = {}
            filepath = os.path.join(self.dataset_dir, "ucfTrainTestlist/classInd.txt")
            with open(filepath, "r") as f:
                lines = f.readlines()
                for line in lines:
                    label, classname = line.strip().split(" ")
                    label = int(label) - 1  # conver to 0-based index
                    cname2lab[classname] = label

            trainval = self.read_data(cname2lab, "ucfTrainTestlist/trainlist01.txt")
            test = self.read_data(cname2lab, "ucfTrainTestlist/testlist01.txt")
            train, val = OxfordPets.split_trainval(trainval)
            OxfordPets.save_split(train, val, test, self.split_path, self.image_dir)

        num_shots = cfg.DATASET.NUM_SHOTS
        if num_shots >= 1:
            seed = cfg.SEED
            preprocessed = os.path.join(self.split_fewshot_dir, f"shot_{num_shots}-seed_{seed}.pkl")
            
            if os.path.exists(preprocessed):
                print(f"Loading preprocessed few-shot data from {preprocessed}")
                with open(preprocessed, "rb") as file:
                    data = pickle.load(file)
                    train, val = data["train"], data["val"]
            else:
                train = self.generate_fewshot_dataset(train, num_shots=num_shots)
                val = self.generate_fewshot_dataset(val, num_shots=min(num_shots, 4))
                data = {"train": train, "val": val}
                print(f"Saving preprocessed few-shot data to {preprocessed}")
                with open(preprocessed, "wb") as file:
                    pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

        subsample = cfg.DATASET.SUBSAMPLE_CLASSES
        train, val, test = OxfordPets.subsample_classes(train, val, test, subsample=subsample)


        cls_name = []
        for item in train:
            if item.classname not in cls_name:
                print("class name:", item.classname)
                print("class label: ", item.label)
                cls_name.append(item.classname)
        if subsample == "base":
            if not os.path.exists(base_file_path):
                with open(base_file_path, 'a') as file:
                    for item in cls_name:
                        if item == "face":
                            file.write("faces\n")
                        elif item == "leopard":
                            file.write("leopards\n")
                        elif item == "motorbike":
                            file.write("motorbikes\n")
                        elif item == "airplane":
                            file.write("airplanes\n")
                        else:
                            file.write(f'{item}\n')
            else:
                print("exits base class name")

        cls_name_novel = []
        for item in test:
            if item.classname not in cls_name_novel:
                #print("class name:", item.classname)
                cls_name_novel.append(item.classname)
            if subsample == "new":
                if not os.path.exists(novel_file_path):
                    print("crate novel class name!")
                    with open(novel_file_path, 'a') as file:
                        for item in cls_name:
                            file.write(f'{item}\n')
                else:
                    print("exits novel class name")



        super().__init__(train_x=train, val=val, test=test)

    def read_data(self, cname2lab, text_file):
        text_file = os.path.join(self.dataset_dir, text_file)
        items = []

        with open(text_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().split(" ")[0]  # trainlist: filename, label
                action, filename = line.split("/")
                label = cname2lab[action]

                elements = re.findall("[A-Z][^A-Z]*", action)
                renamed_action = "_".join(elements)

                filename = filename.replace(".avi", ".jpg")
                impath = os.path.join(self.image_dir, renamed_action, filename)

                item = Datum(impath=impath, label=label, classname=renamed_action)
                items.append(item)

        return items
