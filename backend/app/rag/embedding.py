"""
向量化模型封装。
支持 HuggingFace 模型名或本地路径，通过 .env 配置切换。
使用 sentence-transformers 加载，首次运行自动下载缓存到 backend/models/embeddings/。
"""
import atexit
import gc
import os

import torch
from sentence_transformers import SentenceTransformer

from app.rag.config import RAGConfig

_model_instance = None


def _find_local_model_path(model_name: str, cache_dir: str) -> str | None:
    """在 HuggingFace 缓存目录中查找已下载的模型快照路径。"""
    safe_name = model_name.replace('/', '--')
    models_dir = os.path.join(cache_dir, f'models--{safe_name}')
    if not os.path.isdir(models_dir):
        return None
    snapshots_dir = os.path.join(models_dir, 'snapshots')
    if not os.path.isdir(snapshots_dir):
        return None
    for entry in os.listdir(snapshots_dir):
        snapshot_path = os.path.join(snapshots_dir, entry)
        has_config = os.path.exists(os.path.join(snapshot_path, 'config.json'))
        has_weights = any(
            os.path.exists(os.path.join(snapshot_path, name))
            for name in (
                'model.safetensors',
                'model.safetensors.index.json',
                'pytorch_model.bin',
                'pytorch_model.bin.index.json',
            )
        )
        if os.path.isdir(snapshot_path) and has_config and has_weights:
            return snapshot_path
    return None


class EmbeddingModel:
    """
    向量化模型单例封装。
    """

    def __new__(cls):
        global _model_instance
        if _model_instance is None:
            _model_instance = super().__new__(cls)
            _model_instance._init_model()
        return _model_instance

    def _init_model(self):
        model_name = RAGConfig.EMBEDDING_MODEL
        cache_dir = os.path.join(RAGConfig.MODEL_CACHE_DIR, 'embeddings')
        os.makedirs(cache_dir, exist_ok=True)

        local_path = _find_local_model_path(model_name, cache_dir)
        if local_path:
            print(f"使用本地模型：{local_path}")
            load_target = local_path
        else:
            print(f"正在加载向量化模型：{model_name} ...")
            load_target = model_name

        self.model = SentenceTransformer(
            load_target,
            device=RAGConfig.EMBEDDING_DEVICE,
            cache_folder=cache_dir
        )
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"模型加载完成，维度：{self.dimension}")

    def encode(self, texts: list[str] | str, batch_size: int = 32) -> list[list[float]]:
        """
        将文本编码为向量，自动做 L2 归一化以便余弦相似度计算。

        :param texts: 单条文本或文本列表
        :param batch_size: 批处理大小
        :return: 向量列表
        """
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=False
        )
        return embeddings.tolist()

    def unload(self) -> None:
        """显式卸载模型并释放显存/内存。"""
        global _model_instance
        if getattr(self, 'model', None) is not None:
            del self.model
            self.model = None
        _model_instance = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        print("向量化模型已卸载，显存已释放。")


def get_embedding_model() -> EmbeddingModel:
    """获取向量化模型单例。"""
    return EmbeddingModel()


def _cleanup_embedding_model() -> None:
    """程序退出时自动清理模型。"""
    global _model_instance
    if _model_instance is not None:
        _model_instance.unload()


atexit.register(_cleanup_embedding_model)
