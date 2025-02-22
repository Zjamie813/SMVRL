import os.path as op
from typing import List

from utils.iotools import read_json
from .bases import BaseDataset
import numpy as np

class RSTPReid(BaseDataset):
    """
    RSTPReid

    Reference:
    DSSL: Deep Surroundings-person Separation Learning for Text-based Person Retrieval MM 21

    URL: http://arxiv.org/abs/2109.05534

    Dataset statistics:
    # identities: 4101 
    """
    dataset_dir = 'RSTPReid'

    def __init__(self, root='', verbose=True):
        super(RSTPReid, self).__init__()
        self.dataset_dir = op.join(root, self.dataset_dir)
        self.img_dir = op.join(self.dataset_dir, 'imgs/')

        self.anno_path = op.join(self.dataset_dir, 'data_captions.json')
        self._check_before_run()

        # 修改分隔数据集部分
        self.train_annos = read_json(op.join(self.dataset_dir, 'train_same_id_data.json'))
        self.test_annos = read_json(op.join(self.dataset_dir, 'test_same_id_data.json'))
        self.val_annos = read_json(op.join(self.dataset_dir, 'val_same_id_data.json'))
        # self.train_annos, self.test_annos, self.val_annos = self._split_anno(self.anno_path)

        self.train, self.train_id_container = self._process_anno(self.train_annos, training=True)
        self.test, self.test_id_container = self._process_anno(self.test_annos)
        self.val, self.val_id_container = self._process_anno(self.val_annos)

        if verbose:
            self.logger.info("=> RSTPReid Images and Captions are loaded")
            self.show_dataset_info()


    def _split_anno(self, anno_path: str):
        train_annos, test_annos, val_annos = [], [], []
        annos = read_json(anno_path)
        for anno in annos:
            if anno['split'] == 'train':
                train_annos.append(anno)
            elif anno['split'] == 'test':
                test_annos.append(anno)
            else:
                val_annos.append(anno)
        return train_annos, test_annos, val_annos

  
    def _process_anno(self, annos: List[dict], training=False):
        pid_container = set()
        if training:
            dataset = []
            image_id = 0
            for anno in annos:
                pid = int(anno['id'])
                pid_container.add(pid)
                img_path = op.join(self.img_dir, anno['img_path'])
                captions = anno['captions'] # caption list
                # 增加same id index
                same_id_index_list = anno["same_id_index"]
                for caption in captions:
                    # 随机选取另一个视角图片，先不保证随机视角是否与当前视角相同
                    same_id_index = same_id_index_list[np.random.randint(len(same_id_index_list))]
                    anno_idx, cap_idx = same_id_index.split('-')
                    anno_idx = int(anno_idx)
                    cap_idx = int(cap_idx)
                    cr_img_path = op.join(self.img_dir, annos[anno_idx]['img_path'])
                    cr_caption = annos[anno_idx]['captions'][cap_idx]
                    assert pid == annos[anno_idx]['id']  # 检索是否是同一个ID
                    dataset.append((pid, image_id, img_path, caption, cr_img_path, cr_caption))
                    # dataset.append((pid, image_id, img_path, caption))
                image_id += 1
            for idx, pid in enumerate(pid_container):
                # check pid begin from 0 and no break
                assert idx == pid, f"idx: {idx} and pid: {pid} are not match"
            return dataset, pid_container
        else:
            dataset = {}
            img_paths = []
            captions = []
            image_pids = []
            caption_pids = []
            for anno in annos:
                pid = int(anno['id'])
                pid_container.add(pid)
                img_path = op.join(self.img_dir, anno['img_path'])
                img_paths.append(img_path)
                image_pids.append(pid)
                caption_list = anno['captions'] # caption list
                for caption in caption_list:
                    captions.append(caption)
                    caption_pids.append(pid)
            dataset = {
                "image_pids": image_pids,
                "img_paths": img_paths,
                "caption_pids": caption_pids,
                "captions": captions
            }
            return dataset, pid_container


    def _check_before_run(self):
        """Check if all files are available before going deeper"""
        if not op.exists(self.dataset_dir):
            raise RuntimeError("'{}' is not available".format(self.dataset_dir))
        if not op.exists(self.img_dir):
            raise RuntimeError("'{}' is not available".format(self.img_dir))
        if not op.exists(self.anno_path):
            raise RuntimeError("'{}' is not available".format(self.anno_path))
