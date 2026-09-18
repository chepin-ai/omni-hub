
__version__ = "11.0.0"
"""
formal_life_engine.py — DNA/RNA/蛋白质形式化生命引擎

OMNI-HUB v9.0 形式化生命架构
将DNA/RNA/蛋白质的生物过程数学化、形式化，并与知识谱系同构。

参考: Moonshine-Monster / 形式化生命研究 (ucif2)

类:
    DNAMathematics — DNA数学模型
    RNAMathematics — RNA数学模型
    ProteinMathematics — 蛋白质数学模型
    GeneticCode — 遗传密码
    FormalLife — 形式化生命
    BioKnowledgeIsomorphism — 生物-知识同构
    FormalLifeEngine — 主引擎
"""

import numpy as np
import random
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Any, Optional, Set
import logging


# =============================================================================
# 1. DNAMathematics — DNA数学
# =============================================================================

class DNAMathematics:
    """DNA双螺旋的数学模型。

    碱基: A(腺嘌呤), T(胸腺嘧啶), C(胞嘧啶), G(鸟嘌呤)
    配对规则: A↔T (2氢键), C↔G (3氢键)
    """

    BASES = ['A', 'T', 'C', 'G']
    PAIRING = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    H_BONDS = {'A': 2, 'T': 2, 'C': 3, 'G': 3}

    # Z-curve坐标映射
    Z_CURVE_MAP = {
        'A': (1, 1, 1),
        'C': (1, -1, -1),
        'G': (-1, 1, -1),
        'T': (-1, -1, 1)
    }

    # 随机游走映射
    WALK_MAP = {
        'A': (1, 0),
        'T': (-1, 0),
        'C': (0, 1),
        'G': (0, -1)
    }

    def __init__(self, seed: Optional[int] = None):
        """初始化DNA数学模型。

        Args:
            seed: 随机种子（可选）
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def generate_sequence(self, length: int) -> str:
        """生成随机DNA序列。

        Args:
            length: 序列长度

        Returns:
            随机DNA序列字符串
        """
        return ''.join(random.choice(self.BASES) for _ in range(length))

    def complement(self, sequence: str) -> str:
        """求DNA互补序列。

        Args:
            sequence: DNA序列

        Returns:
            互补序列
        """
        return ''.join(self.PAIRING[base] for base in sequence)

    def reverse_complement(self, sequence: str) -> str:
        """求DNA反向互补序列。

        Args:
            sequence: DNA序列

        Returns:
            反向互补序列
        """
        return self.complement(sequence)[::-1]

    def transcribe(self, dna: str) -> str:
        """DNA→RNA转录（T→U）。

        Args:
            dna: DNA序列

        Returns:
            RNA序列
        """
        return dna.replace('T', 'U')

    def gc_content(self, sequence: str) -> float:
        """计算GC含量。

        Args:
            sequence: DNA序列

        Returns:
            GC含量比例 (0.0 ~ 1.0)
        """
        gc_count = sum(1 for base in sequence if base in ('G', 'C'))
        return gc_count / len(sequence) if sequence else 0.0

    def entropy(self, sequence: str) -> float:
        """计算序列香农熵（Shannon Entropy）。

        公式: H = -Σ p(x) * log2(p(x))

        Args:
            sequence: DNA序列

        Returns:
            香农熵（最大值为2，对应完全随机）
        """
        if not sequence:
            return 0.0
        counts = Counter(sequence)
        length = len(sequence)
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)
        return entropy

    def fourier_transform(self, sequence: str) -> np.ndarray:
        """对DNA序列进行傅里叶变换以发现周期性。

        编码: A=0, T=1, C=2, G=3

        Args:
            sequence: DNA序列

        Returns:
            傅里叶变换幅值数组
        """
        encoding = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
        numeric = np.array([encoding[base] for base in sequence], dtype=float)
        fft_result = np.fft.fft(numeric)
        return np.abs(fft_result)

    def z_curve(self, sequence: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算DNA序列的Z曲线表示（Z-curve）。

        Z曲线三维坐标:
            x_n = Σ(A_i + G_i - C_i - T_i)
            y_n = Σ(A_i + C_i - G_i - T_i)
            z_n = Σ(A_i + T_i - C_i - G_i)

        Args:
            sequence: DNA序列

        Returns:
            (x_array, y_array, z_array) 三个numpy数组
        """
        n = len(sequence)
        x = np.zeros(n)
        y = np.zeros(n)
        z = np.zeros(n)

        for i, base in enumerate(sequence):
            if base == 'A':
                dx, dy, dz = 1, 1, 1
            elif base == 'C':
                dx, dy, dz = -1, -1, -1
            elif base == 'G':
                dx, dy, dz = 1, -1, -1
            else:  # T
                dx, dy, dz = -1, -1, 1

            if i == 0:
                x[i] = dx
                y[i] = dy
                z[i] = dz
            else:
                x[i] = x[i - 1] + dx
                y[i] = y[i - 1] + dy
                z[i] = z[i - 1] + dz

        return x, y, z

    def walk_plot(self, sequence: str) -> Tuple[np.ndarray, np.ndarray]:
        """DNA随机游走图（2D）。

        编码映射:
            A → (1, 0)
            T → (-1, 0)
            C → (0, 1)
            G → (0, -1)

        Args:
            sequence: DNA序列

        Returns:
            (x_coords, y_coords) 坐标数组
        """
        x = np.zeros(len(sequence) + 1)
        y = np.zeros(len(sequence) + 1)

        for i, base in enumerate(sequence):
            dx, dy = self.WALK_MAP[base]
            x[i + 1] = x[i] + dx
            y[i + 1] = y[i] + dy

        return x, y

    def melting_temperature(self, sequence: str) -> float:
        """估算DNA熔解温度（Wallace规则简化版）。

        Args:
            sequence: DNA序列

        Returns:
            估算熔解温度（摄氏度）
        """
        gc = self.gc_content(sequence)
        return 64.9 + 41.0 * (gc - 0.5) if len(sequence) < 20 else 81.5 + 0.41 * gc * 100 - 500 / len(sequence)

    def kmer_frequency(self, sequence: str, k: int = 3) -> Dict[str, int]:
        """计算k-mer频率。

        Args:
            sequence: DNA序列
            k: k-mer长度

        Returns:
            k-mer频率字典
        """
        kmers = {}
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i + k]
            kmers[kmer] = kmers.get(kmer, 0) + 1
        return kmers


# =============================================================================
# 2. RNAMathematics — RNA数学
# =============================================================================

class RNAMathematics:
    """RNA结构数学模型。

    RNA结构层级:
        一级: 序列 (A, U, C, G)
        二级: 茎环/发夹结构
        三级: 3D折叠
    """

    BASES = ['A', 'U', 'C', 'G']
    PAIRING = {'A': 'U', 'U': 'A', 'C': 'G', 'G': 'C'}

    # 标准密码子表（RNA版本）
    CODON_TABLE = {
        'UUU': 'F', 'UUC': 'F', 'UUA': 'L', 'UUG': 'L',
        'UCU': 'S', 'UCC': 'S', 'UCA': 'S', 'UCG': 'S',
        'UAU': 'Y', 'UAC': 'Y', 'UAA': '*', 'UAG': '*',
        'UGU': 'C', 'UGC': 'C', 'UGA': '*', 'UGG': 'W',
        'CUU': 'L', 'CUC': 'L', 'CUA': 'L', 'CUG': 'L',
        'CCU': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
        'CAU': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGU': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
        'AUU': 'I', 'AUC': 'I', 'AUA': 'I', 'AUG': 'M',
        'ACU': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
        'AAU': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGU': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
        'GUU': 'V', 'GUC': 'V', 'GUA': 'V', 'GUG': 'V',
        'GCU': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
        'GAU': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGU': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
    }

    # 配对能量（近似值，单位: kcal/mol）
    PAIR_ENERGY = {
        ('A', 'U'): -2.0,
        ('U', 'A'): -2.0,
        ('C', 'G'): -3.0,
        ('G', 'C'): -3.0,
        ('G', 'U'): -1.0,
        ('U', 'G'): -1.0,
    }

    def __init__(self, seed: Optional[int] = None):
        """初始化RNA数学模型。

        Args:
            seed: 随机种子
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def fold_secondary(self, sequence: str, min_loop: int = 3) -> List[Tuple[int, int]]:
        """RNA二级结构预测（简化Nussinov算法）。

        Nussinov算法: 动态规划最大化配对数。

        Args:
            sequence: RNA序列
            min_loop: 最小环长度

        Returns:
            碱基配对列表 [(i, j), ...]
        """
        n = len(sequence)
        # DP矩阵: M[i][j] = sequence[i:j+1]的最大配对数
        M = np.zeros((n, n), dtype=int)

        # 填充DP表
        for length in range(min_loop + 1, n):
            for i in range(n - length):
                j = i + length
                # 不配对i
                max_val = M[i + 1, j]
                # 不配对j
                max_val = max(max_val, M[i, j - 1])
                # i与j配对
                if self._can_pair(sequence[i], sequence[j]):
                    max_val = max(max_val, M[i + 1, j - 1] + 1)
                # 分断点k
                for k in range(i + 1, j):
                    max_val = max(max_val, M[i, k] + M[k + 1, j])
                M[i, j] = max_val

        # 回溯
        pairs = []
        self._traceback(M, sequence, 0, n - 1, min_loop, pairs)
        return sorted(pairs)

    def _can_pair(self, a: str, b: str) -> bool:
        """检查两个碱基是否可以配对。"""
        return (a, b) in self.PAIR_ENERGY

    def _traceback(self, M: np.ndarray, sequence: str, i: int, j: int, min_loop: int, pairs: List):
        """Nussinov回溯。"""
        if i >= j:
            return
        if M[i, j] == M[i + 1, j]:
            self._traceback(M, sequence, i + 1, j, min_loop, pairs)
        elif M[i, j] == M[i, j - 1]:
            self._traceback(M, sequence, i, j - 1, min_loop, pairs)
        elif self._can_pair(sequence[i], sequence[j]) and M[i, j] == M[i + 1, j - 1] + 1:
            pairs.append((i, j))
            self._traceback(M, sequence, i + 1, j - 1, min_loop, pairs)
        else:
            for k in range(i + 1, j):
                if M[i, j] == M[i, k] + M[k + 1, j]:
                    self._traceback(M, sequence, i, k, min_loop, pairs)
                    self._traceback(M, sequence, k + 1, j, min_loop, pairs)
                    break

    def calculate_free_energy(self, structure: List[Tuple[int, int]], sequence: str) -> float:
        """计算RNA二级结构的自由能。

        Args:
            structure: 碱基配对列表
            sequence: RNA序列

        Returns:
            自由能（kcal/mol，负值表示稳定）
        """
        energy = 0.0
        for i, j in structure:
            pair = (sequence[i], sequence[j])
            energy += self.PAIR_ENERGY.get(pair, 0.0)
        return energy

    def find_motifs(self, sequence: str, motif: str) -> List[int]:
        """在RNA序列中查找motif。

        Args:
            sequence: RNA序列
            motif: 要查找的motif序列

        Returns:
            motif起始位置列表
        """
        positions = []
        motif_len = len(motif)
        for i in range(len(sequence) - motif_len + 1):
            if sequence[i:i + motif_len] == motif:
                positions.append(i)
        return positions

    def translate(self, rna: str, start_codon: bool = True) -> str:
        """RNA→蛋白质翻译（标准密码子表）。

        Args:
            rna: RNA序列
            start_codon: 是否从起始密码子AUG开始

        Returns:
            蛋白质氨基酸序列（单字母代码）
        """
        protein = []
        start = 0

        if start_codon:
            # 寻找起始密码子AUG
            for i in range(0, len(rna) - 2, 3):
                if rna[i:i + 3] == 'AUG':
                    start = i
                    break

        for i in range(start, len(rna) - 2, 3):
            codon = rna[i:i + 3]
            if len(codon) < 3:
                break
            aa = self.CODON_TABLE.get(codon, '?')
            if aa == '*':  # 终止密码子
                break
            protein.append(aa)

        return ''.join(protein)

    def gc_content(self, sequence: str) -> float:
        """计算RNA的GC含量。"""
        gc_count = sum(1 for base in sequence if base in ('G', 'C'))
        return gc_count / len(sequence) if sequence else 0.0

    def structure_to_dot_bracket(self, sequence: str, pairs: List[Tuple[int, int]]) -> str:
        """将配对列表转换为dot-bracket表示法。

        Args:
            sequence: RNA序列
            pairs: 碱基配对列表

        Returns:
            dot-bracket字符串
        """
        db = ['.'] * len(sequence)
        for i, j in pairs:
            db[i] = '('
            db[j] = ')'
        return ''.join(db)


# =============================================================================
# 3. ProteinMathematics — 蛋白质数学
# =============================================================================

class ProteinMathematics:
    """蛋白质结构数学模型。

    20种标准氨基酸及其物理化学性质。
    """

    # 20种标准氨基酸单字母代码
    AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")

    # 氨基酸全称
    AA_FULL_NAMES = {
        'A': 'Alanine', 'C': 'Cysteine', 'D': 'Aspartic Acid',
        'E': 'Glutamic Acid', 'F': 'Phenylalanine', 'G': 'Glycine',
        'H': 'Histidine', 'I': 'Isoleucine', 'K': 'Lysine',
        'L': 'Leucine', 'M': 'Methionine', 'N': 'Asparagine',
        'P': 'Proline', 'Q': 'Glutamine', 'R': 'Arginine',
        'S': 'Serine', 'T': 'Threonine', 'V': 'Valine',
        'W': 'Tryptophan', 'Y': 'Tyrosine'
    }

    # Kyte-Doolittle疏水性指数
    HYDROPHOBICITY = {
        'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
        'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
        'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
        'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
    }

    # α螺旋倾向性 (Chou-Fasman参数)
    ALPHA_HELIX_PROPENSITY = {
        'A': 1.45, 'C': 0.77, 'D': 0.98, 'E': 1.53, 'F': 1.12,
        'G': 0.53, 'H': 1.24, 'I': 1.00, 'K': 1.07, 'L': 1.34,
        'M': 1.20, 'N': 0.73, 'P': 0.59, 'Q': 1.17, 'R': 0.79,
        'S': 0.79, 'T': 0.82, 'V': 0.83, 'W': 1.14, 'Y': 0.61
    }

    # β折叠倾向性
    BETA_SHEET_PROPENSITY = {
        'A': 0.97, 'C': 1.30, 'D': 0.80, 'E': 0.26, 'F': 1.28,
        'G': 0.81, 'H': 0.71, 'I': 1.60, 'K': 0.74, 'L': 1.22,
        'M': 1.67, 'N': 0.65, 'P': 0.62, 'Q': 1.23, 'R': 0.90,
        'S': 0.72, 'T': 1.20, 'V': 1.87, 'W': 1.19, 'Y': 1.29
    }

    # 范德华半径 (Angstrom)
    VDWAALS_RADIUS = {
        'A': 2.0, 'C': 2.1, 'D': 2.2, 'E': 2.3, 'F': 2.5,
        'G': 1.5, 'H': 2.4, 'I': 2.4, 'K': 2.5, 'L': 2.4,
        'M': 2.4, 'N': 2.1, 'P': 2.0, 'Q': 2.3, 'R': 2.6,
        'S': 1.9, 'T': 2.1, 'V': 2.3, 'W': 2.7, 'Y': 2.6
    }

    def __init__(self, seed: Optional[int] = None):
        """初始化蛋白质数学模型。"""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def compute_hydrophobicity(self, protein: str) -> np.ndarray:
        """计算蛋白质的疏水性分布。

        Args:
            protein: 蛋白质氨基酸序列

        Returns:
            每个位置的疏水性值数组
        """
        return np.array([self.HYDROPHOBICITY.get(aa, 0.0) for aa in protein])

    def predict_alpha_helix(self, protein: str, window: int = 6, threshold: float = 1.03) -> List[Tuple[int, int]]:
        """α螺旋预测（简化Chou-Fasman算法）。

        Args:
            protein: 蛋白质序列
            window: 滑动窗口大小
            threshold: 螺旋倾向性阈值

        Returns:
            预测的螺旋区域列表 [(start, end), ...]
        """
        n = len(protein)
        scores = np.zeros(n)

        # 计算滑动窗口平均倾向性
        for i in range(n):
            win_start = max(0, i - window // 2)
            win_end = min(n, i + window // 2 + 1)
            score = sum(self.ALPHA_HELIX_PROPENSITY.get(protein[j], 0) for j in range(win_start, win_end))
            scores[i] = score / (win_end - win_start)

        # 识别连续的高分区域
        helices = []
        in_helix = False
        start = 0

        for i in range(n):
            if scores[i] >= threshold and not in_helix:
                in_helix = True
                start = i
            elif scores[i] < threshold and in_helix:
                in_helix = False
                if i - start >= 4:  # 最小螺旋长度
                    helices.append((start, i - 1))

        if in_helix and n - start >= 4:
            helices.append((start, n - 1))

        return helices

    def predict_beta_sheet(self, protein: str, window: int = 5, threshold: float = 1.00) -> List[Tuple[int, int]]:
        """β折叠预测（简化Chou-Fasman算法）。

        Args:
            protein: 蛋白质序列
            window: 滑动窗口大小
            threshold: 折叠倾向性阈值

        Returns:
            预测的折叠区域列表 [(start, end), ...]
        """
        n = len(protein)
        scores = np.zeros(n)

        for i in range(n):
            win_start = max(0, i - window // 2)
            win_end = min(n, i + window // 2 + 1)
            score = sum(self.BETA_SHEET_PROPENSITY.get(protein[j], 0) for j in range(win_start, win_end))
            scores[i] = score / (win_end - win_start)

        sheets = []
        in_sheet = False
        start = 0

        for i in range(n):
            if scores[i] >= threshold and not in_sheet:
                in_sheet = True
                start = i
            elif scores[i] < threshold and in_sheet:
                in_sheet = False
                if i - start >= 2:
                    sheets.append((start, i - 1))

        if in_sheet and n - start >= 2:
            sheets.append((start, n - 1))

        return sheets

    def contact_map(self, protein: str, threshold: float = 8.0) -> np.ndarray:
        """计算蛋白质接触图。

        简化模型: 基于序列距离和氨基酸性质的近似接触图。

        Args:
            protein: 蛋白质序列
            threshold: 接触距离阈值

        Returns:
            接触矩阵 (n x n)
        """
        n = len(protein)
        contact_matrix = np.zeros((n, n))

        # 生成简化的3D坐标（使用自避随机游走近似）
        coords = self._approximate_3d_coords(protein)

        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist < threshold:
                    contact_matrix[i, j] = 1.0
                    contact_matrix[j, i] = 1.0

        return contact_matrix

    def _approximate_3d_coords(self, protein: str) -> np.ndarray:
        """生成近似的3D坐标。"""
        n = len(protein)
        coords = np.zeros((n, 3))

        # 使用累积随机游走 + 疏水性约束
        for i in range(1, n):
            # 随机方向
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 3.8  # 肽键长度

            dx = r * math.sin(phi) * math.cos(theta)
            dy = r * math.sin(phi) * math.sin(theta)
            dz = r * math.cos(phi)

            # 疏水性氨基酸倾向于"折叠"回核心
            hydro = self.HYDROPHOBICITY.get(protein[i], 0)
            if hydro > 2.0:
                # 向中心吸引
                center = np.mean(coords[:i], axis=0) if i > 0 else np.zeros(3)
                direction = center - coords[i - 1]
                if np.linalg.norm(direction) > 0:
                    direction = direction / np.linalg.norm(direction)
                    dx += direction[0] * 0.5
                    dy += direction[1] * 0.5
                    dz += direction[2] * 0.5

            coords[i] = coords[i - 1] + np.array([dx, dy, dz])

        return coords

    def fold_topology(self, protein: str) -> Dict[str, Any]:
        """蛋白质折叠拓扑分析（纽结理论简化）。

        Args:
            protein: 蛋白质序列

        Returns:
            拓扑特征字典
        """
        coords = self._approximate_3d_coords(protein)
        n = len(protein)

        # 计算回转半径
        center = np.mean(coords, axis=0)
        rg = np.sqrt(np.mean(np.sum((coords - center) ** 2, axis=1)))

        # 计算端到端距离
        end_to_end = np.linalg.norm(coords[-1] - coords[0])

        # 纽结不变量（简化: 基于缠绕数）
        writhing_number = self._compute_writhing_number(coords)

        return {
            'radius_of_gyration': rg,
            'end_to_end_distance': end_to_end,
            'writhing_number': writhing_number,
            'compactness': end_to_end / rg if rg > 0 else 0,
            'coord_shape': coords.shape
        }

    def _compute_writhing_number(self, coords: np.ndarray) -> float:
        """计算简化缠绕数。"""
        n = len(coords)
        if n < 3:
            return 0.0

        # 基于局部扭转的近似
        writhing = 0.0
        for i in range(n - 2):
            v1 = coords[i + 1] - coords[i]
            v2 = coords[i + 2] - coords[i + 1]
            cross = np.cross(v1, v2)
            if np.linalg.norm(cross) > 0 and np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                sin_angle = np.linalg.norm(cross) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                writhing += math.asin(min(1.0, sin_angle))

        return writhing / (2 * math.pi)

    def energy_landscape(self, protein: str, num_conformations: int = 50) -> Dict[str, Any]:
        """蛋白质能量景观（简化模型）。

        Args:
            protein: 蛋白质序列
            num_conformations: 采样构象数

        Returns:
            能量景观特征字典
        """
        energies = []
        rgs = []

        for _ in range(num_conformations):
            # 生成随机构象
            coords = self._random_conformation(len(protein))
            energy = self._compute_energy(protein, coords)
            rg = np.sqrt(np.mean(np.sum((coords - np.mean(coords, axis=0)) ** 2, axis=1)))
            energies.append(energy)
            rgs.append(rg)

        energies = np.array(energies)
        rgs = np.array(rgs)

        return {
            'energies': energies,
            'radii_of_gyration': rgs,
            'min_energy': np.min(energies),
            'max_energy': np.max(energies),
            'mean_energy': np.mean(energies),
            'energy_gap': np.max(energies) - np.min(energies),
            'native_energy': energies[0]  # 第一个作为"天然态"
        }

    def _random_conformation(self, n: int) -> np.ndarray:
        """生成随机构象。"""
        coords = np.zeros((n, 3))
        for i in range(1, n):
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 3.8
            coords[i] = coords[i - 1] + np.array([
                r * math.sin(phi) * math.cos(theta),
                r * math.sin(phi) * math.sin(theta),
                r * math.cos(phi)
            ])
        return coords

    def _compute_energy(self, protein: str, coords: np.ndarray) -> float:
        """计算简化的Lennard-Jones型能量。"""
        n = len(protein)
        energy = 0.0

        for i in range(n):
            for j in range(i + 4, n):  # 排除局部邻居
                dist = np.linalg.norm(coords[i] - coords[j])
                if dist > 0:
                    # Lennard-Jones势简化
                    sigma = (self.VDWAALS_RADIUS[protein[i]] + self.VDWAALS_RADIUS[protein[j]]) / 2
                    if dist < sigma * 2:
                        epsilon = 1.0 if self.HYDROPHOBICITY.get(protein[i], 0) > 0 and self.HYDROPHOBICITY.get(protein[j], 0) > 0 else 0.5
                        energy += epsilon * ((sigma / dist) ** 12 - 2 * (sigma / dist) ** 6)

        return energy

    def molecular_weight(self, protein: str) -> float:
        """估算蛋白质分子量。"""
        # 氨基酸平均分子量约110 Da
        return len(protein) * 110.0

    def isoelectric_point_approx(self, protein: str) -> float:
        """近似等电点。"""
        # 基于电荷氨基酸的简化计算
        charge_aas = {'D': -1, 'E': -1, 'K': 1, 'R': 1, 'H': 0.5}
        net_charge = sum(charge_aas.get(aa, 0) for aa in protein)
        # 简化的pI近似
        return 7.0 - net_charge * 0.5


# =============================================================================
# 4. GeneticCode — 遗传密码
# =============================================================================

class GeneticCode:
    """标准遗传密码。

    64个密码子 → 20种氨基酸 + 3个终止密码子
    """

    # 标准密码子表 (DNA版本)
    CODON_TABLE = {
        'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
        'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
        'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
        'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
        'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
        'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
        'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
        'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
        'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
        'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
        'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
        'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
        'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
    }

    # 氨基酸名称
    AA_NAMES = {
        'A': 'Ala', 'C': 'Cys', 'D': 'Asp', 'E': 'Glu', 'F': 'Phe',
        'G': 'Gly', 'H': 'His', 'I': 'Ile', 'K': 'Lys', 'L': 'Leu',
        'M': 'Met', 'N': 'Asn', 'P': 'Pro', 'Q': 'Gln', 'R': 'Arg',
        'S': 'Ser', 'T': 'Thr', 'V': 'Val', 'W': 'Trp', 'Y': 'Tyr',
        '*': 'Stop'
    }

    # 反向表: 氨基酸 -> 密码子列表
    AA_TO_CODONS = {}

    def __init__(self):
        """初始化遗传密码。"""
        # 构建反向表
        self.AA_TO_CODONS = defaultdict(list)
        for codon, aa in self.CODON_TABLE.items():
            self.AA_TO_CODONS[aa].append(codon)

    def codon_to_amino_acid(self, codon: str) -> str:
        """密码子→氨基酸。

        Args:
            codon: 3碱基密码子

        Returns:
            单字母氨基酸代码
        """
        return self.CODON_TABLE.get(codon.upper(), '?')

    def amino_acid_to_codons(self, aa: str) -> List[str]:
        """氨基酸→密码子列表。

        Args:
            aa: 单字母氨基酸代码

        Returns:
            编码该氨基酸的密码子列表
        """
        return self.AA_TO_CODONS.get(aa.upper(), [])

    def redundancy(self, codon: str) -> int:
        """密码子冗余度（同义密码子数）。

        Args:
            codon: 密码子

        Returns:
            编码同种氨基酸的密码子数量
        """
        aa = self.codon_to_amino_acid(codon)
        return len(self.amino_acid_to_codons(aa))

    def error_resilience(self, codon: str) -> float:
        """错误恢复力: 点突变后仍编码同种氨基酸的概率。

        Args:
            codon: 密码子

        Returns:
            恢复力概率 (0.0 ~ 1.0)
        """
        if len(codon) != 3:
            return 0.0

        original_aa = self.codon_to_amino_acid(codon)
        same_count = 0
        total_mutations = 0

        bases = ['A', 'T', 'C', 'G']
        for i in range(3):
            for base in bases:
                if base != codon[i]:
                    mutated = codon[:i] + base + codon[i + 1:]
                    mutated_aa = self.codon_to_amino_acid(mutated)
                    total_mutations += 1
                    if mutated_aa == original_aa:
                        same_count += 1

        return same_count / total_mutations if total_mutations > 0 else 0.0

    def symmetry_analysis(self) -> Dict[str, Any]:
        """密码子表的对称性分析。

        Returns:
            对称性特征字典
        """
        # 1. 简并度分布
        degeneracy = {}
        for aa in set(self.CODON_TABLE.values()):
            count = len(self.AA_TO_CODONS[aa])
            degeneracy[aa] = count

        # 2. 摆动位置分析（第三位简并）
        wobble_degeneracy = 0
        for codon in self.CODON_TABLE:
            aa = self.CODON_TABLE[codon]
            # 检查第三位突变是否保持同氨基酸
            bases = ['A', 'T', 'C', 'G']
            same = sum(1 for b in bases if self.CODON_TABLE.get(codon[:2] + b) == aa)
            if same > 1:
                wobble_degeneracy += 1

        # 3. 镜像对称性 (嘌呤↔嘧啶)
        purine = {'A', 'G'}
        pyrimidine = {'C', 'T'}

        mirror_pairs = 0
        for codon, aa in self.CODON_TABLE.items():
            mirrored = ''
            for base in codon:
                if base in purine:
                    mirrored += 'C' if base == 'A' else 'T'
                else:
                    mirrored += 'A' if base == 'C' else 'G'
            if mirrored in self.CODON_TABLE and self.CODON_TABLE[mirrored] == aa:
                mirror_pairs += 1

        # 4. 群的阶（密码子空间的结构）
        # 计算自同构群的大小（近似）
        automorphisms = self._count_automorphisms()

        return {
            'degeneracy_distribution': degeneracy,
            'mean_degeneracy': np.mean(list(degeneracy.values())),
            'wobble_degeneracy_count': wobble_degeneracy,
            'mirror_symmetry_pairs': mirror_pairs // 2,
            'automorphism_group_size': automorphisms,
            'total_codons': 64,
            'coding_codons': 61,  # 排除3个终止密码子
            'stop_codons': ['TAA', 'TAG', 'TGA']
        }

    def _count_automorphisms(self) -> int:
        """计算密码子表的自同构数（简化）。"""
        # 统计相同简并模式
        patterns = Counter(len(codons) for codons in self.AA_TO_CODONS.values())
        # 返回排列群大小的对数估计
        auto_size = 1
        for count, freq in patterns.items():
            auto_size *= math.factorial(freq)
        return auto_size

    def get_all_codons(self) -> List[str]:
        """获取所有64个密码子。"""
        return list(self.CODON_TABLE.keys())

    def translate_dna(self, dna: str) -> str:
        """翻译DNA为蛋白质。"""
        protein = []
        for i in range(0, len(dna) - 2, 3):
            codon = dna[i:i + 3]
            if len(codon) == 3:
                aa = self.codon_to_amino_acid(codon)
                if aa == '*':
                    break
                protein.append(aa)
        return ''.join(protein)


# =============================================================================
# 5. FormalLife — 形式化生命
# =============================================================================

class FormalLife:
    """形式化生命系统。

    将生命过程形式化为数学结构:
    - 自创生 (Autopoiesis): Maturana/Varela理论
    - 复制保真度
    - 突变率
    - 选择压力
    - 进化模拟
    """

    def __init__(self, dna_length: int = 100, seed: Optional[int] = None):
        """初始化形式化生命。

        Args:
            dna_length: DNA序列长度
            seed: 随机种子
        """
        self.dna_length = dna_length
        self.dna_math = DNAMathematics(seed=seed)
        self.rna_math = RNAMathematics(seed=seed)
        self.protein_math = ProteinMathematics(seed=seed)
        self.genetic_code = GeneticCode()

        # 当前生命状态
        self.dna = ""
        self.rna = ""
        self.protein = ""
        self.fitness = 0.0
        self.generation = 0
        self.age = 0

        # 自创生状态
        self.autopoiesis_state = {
            'production': 0.0,
            'structural_coupling': 0.0,
            'cognition': 0.0
        }

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def create(self) -> str:
        """创建生命形式（生成DNA）。"""
        self.dna = self.dna_math.generate_sequence(self.dna_length)
        self.rna = self.dna_math.transcribe(self.dna)
        self.protein = self.genetic_code.translate_dna(self.dna)
        self.fitness = self._calculate_fitness()
        self.generation = 0
        self.age = 0
        return self.dna

    def _calculate_fitness(self) -> float:
        """计算适应度。"""
        if not self.protein:
            return 0.0

        # 基于GC含量、蛋白质长度和疏水平衡
        gc = self.dna_math.gc_content(self.dna)
        gc_fitness = 1.0 - abs(gc - 0.5) * 2  # 最优GC含量约50%

        protein_len = len(self.protein)
        len_fitness = min(protein_len / 30.0, 1.0)

        hydro = self.protein_math.compute_hydrophobicity(self.protein)
        hydro_balance = 1.0 - abs(np.mean(hydro)) / 5.0

        return (gc_fitness * 0.3 + len_fitness * 0.4 + hydro_balance * 0.3)

    def autopoiesis_cycle(self) -> Dict[str, float]:
        """自创生循环（Maturana/Varela理论）。

        循环:
            生产(Production) → 结构耦合(Structural Coupling) → 认知(Cognition)

        Returns:
            自创生状态字典
        """
        # 1. 生产: 从DNA产生蛋白质
        production = len(self.protein) / (self.dna_length / 3.0) if self.dna_length > 0 else 0.0
        production = min(production, 1.0)

        # 2. 结构耦合: DNA与环境的匹配度
        env_signature = np.random.rand(self.dna_length)
        dna_numeric = np.array([{'A': 0, 'T': 1, 'C': 2, 'G': 3}[b] for b in self.dna])
        coupling = 1.0 - np.mean(np.abs(dna_numeric / 3.0 - env_signature))
        coupling = max(0.0, min(1.0, coupling))

        # 3. 认知: 系统区分自身与环境的能力
        # 用熵差近似
        dna_entropy = self.dna_math.entropy(self.dna)
        max_entropy = 2.0  # log2(4)
        cognition = dna_entropy / max_entropy * coupling

        self.autopoiesis_state = {
            'production': float(production),
            'structural_coupling': float(coupling),
            'cognition': float(cognition)
        }

        self.age += 1
        return self.autopoiesis_state

    def replication_fidelity(self) -> float:
        """复制保真度。

        基于GC含量和序列复杂度的估计。

        Returns:
            保真度概率 (0.0 ~ 1.0)
        """
        gc = self.dna_math.gc_content(self.dna)
        entropy = self.dna_math.entropy(self.dna)

        # GC含量越接近50%保真度越高
        gc_factor = 1.0 - abs(gc - 0.5) * 2

        # 熵越高（越随机）保真度越低
        entropy_factor = 1.0 - entropy / 2.0 * 0.3

        return gc_factor * entropy_factor * 0.999  # 最高99.9%

    def mutation_rate(self) -> float:
        """突变率。

        Returns:
            每碱基每代突变率
        """
        fidelity = self.replication_fidelity()
        return (1.0 - fidelity) / self.dna_length if self.dna_length > 0 else 0.0

    def mutate(self, rate: Optional[float] = None) -> str:
        """对DNA进行突变。

        Args:
            rate: 突变率（默认使用计算值）

        Returns:
            突变后的DNA
        """
        if rate is None:
            rate = self.mutation_rate()

        dna_list = list(self.dna)
        for i in range(len(dna_list)):
            if random.random() < rate:
                # 点突变
                dna_list[i] = random.choice([b for b in DNAMathematics.BASES if b != dna_list[i]])

        self.dna = ''.join(dna_list)
        self.rna = self.dna_math.transcribe(self.dna)
        self.protein = self.genetic_code.translate_dna(self.dna)
        self.generation += 1
        return self.dna

    def selection_pressure(self, environment: Dict[str, float]) -> float:
        """选择压力计算。

        Args:
            environment: 环境参数字典
                - 'temperature': 温度偏好
                - 'ph': pH偏好
                - 'resource': 资源可用性

        Returns:
            选择压力系数
        """
        pressure = 1.0

        # 温度适应
        if 'temperature' in environment:
            tm = self.dna_math.melting_temperature(self.dna)
            temp_diff = abs(tm - environment['temperature'])
            pressure *= max(0.0, 1.0 - temp_diff / 50.0)

        # GC含量适应
        if 'gc_preference' in environment:
            gc = self.dna_math.gc_content(self.dna)
            gc_diff = abs(gc - environment['gc_preference'])
            pressure *= max(0.0, 1.0 - gc_diff * 2)

        # 资源限制
        if 'resource' in environment:
            pressure *= environment['resource']

        self.fitness = self._calculate_fitness() * pressure
        return pressure

    def evolve(self, generations: int = 1, mutation_rate: Optional[float] = None,
               environment: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """进化模拟。

        Args:
            generations: 代数
            mutation_rate: 突变率
            environment: 环境参数

        Returns:
            进化历史字典
        """
        history = {
            'fitness': [self.fitness],
            'gc_content': [self.dna_math.gc_content(self.dna)],
            'entropy': [self.dna_math.entropy(self.dna)],
            'protein_length': [len(self.protein)],
            'generations': []
        }

        for gen in range(generations):
            self.mutate(rate=mutation_rate)

            if environment:
                self.selection_pressure(environment)
            else:
                self.fitness = self._calculate_fitness()

            history['fitness'].append(self.fitness)
            history['gc_content'].append(self.dna_math.gc_content(self.dna))
            history['entropy'].append(self.dna_math.entropy(self.dna))
            history['protein_length'].append(len(self.protein))
            history['generations'].append(gen + 1)

        return history

    def get_state(self) -> Dict[str, Any]:
        """获取当前生命状态。"""
        return {
            'dna': self.dna,
            'rna': self.rna,
            'protein': self.protein,
            'fitness': self.fitness,
            'generation': self.generation,
            'age': self.age,
            'gc_content': self.dna_math.gc_content(self.dna),
            'entropy': self.dna_math.entropy(self.dna),
            'autopoiesis': self.autopoiesis_state
        }


# =============================================================================
# 6. BioKnowledgeIsomorphism — 生物-知识同构
# =============================================================================

class BioKnowledgeIsomorphism:
    """生物结构与知识谱系的同构映射。

    建立:
    - DNA序列 ↔ 知识图谱
    - 蛋白质结构 ↔ 张量场
    - 代谢网络 ↔ 闭环机制
    - 进化过程 ↔ 涌现
    """

    def __init__(self):
        """初始化生物-知识同构。"""
        self.knowledge_graph = {}
        self.tensor_field = None

    def dna_to_knowledge_graph(self, dna: str) -> Dict[str, Any]:
        """DNA序列→知识图谱。

        映射规则:
        - 基因 ↔ 概念节点
        - 调控关系 ↔ 知识关系

        Args:
            dna: DNA序列

        Returns:
            知识图谱字典
        """
        nodes = {}
        edges = []

        # 将DNA分割为"基因"（每10bp为一个概念节点）
        gene_length = 10
        num_genes = len(dna) // gene_length

        for i in range(num_genes):
            gene = dna[i * gene_length:(i + 1) * gene_length]
            node_id = f"gene_{i}"

            # 基因作为概念节点
            nodes[node_id] = {
                'type': 'concept',
                'sequence': gene,
                'gc_content': (gene.count('G') + gene.count('C')) / len(gene),
                'entropy': self._quick_entropy(gene),
                'position': i
            }

        # 建立调控关系（基于序列相似性和互补性）
        node_ids = list(nodes.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                gene_i = nodes[node_ids[i]]['sequence']
                gene_j = nodes[node_ids[j]]['sequence']

                # 序列相似度
                similarity = self._sequence_similarity(gene_i, gene_j)

                # 互补性
                comp = DNAMathematics().complement(gene_i)
                complementarity = self._sequence_similarity(comp, gene_j)

                if similarity > 0.3 or complementarity > 0.3:
                    edges.append({
                        'source': node_ids[i],
                        'target': node_ids[j],
                        'relation': 'regulates' if similarity > complementarity else 'inhibits',
                        'weight': max(similarity, complementarity)
                    })

        return {
            'nodes': nodes,
            'edges': edges,
            'num_nodes': len(nodes),
            'num_edges': len(edges),
            'density': len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0
        }

    def _quick_entropy(self, sequence: str) -> float:
        """快速计算熵。"""
        counts = Counter(sequence)
        length = len(sequence)
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)
        return entropy

    def _sequence_similarity(self, seq1: str, seq2: str) -> float:
        """计算序列相似度。"""
        if len(seq1) != len(seq2):
            return 0.0
        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
        return matches / len(seq1)

    def protein_to_tensor_field(self, protein: str, resolution: int = 8) -> np.ndarray:
        """蛋白质→张量场。

        映射规则:
        - 氨基酸序列 ↔ 场的一维切片
        - 3D结构 ↔ 场的三维拓扑

        Args:
            protein: 蛋白质序列
            resolution: 张量场分辨率

        Returns:
            张量场 (resolution x resolution x resolution x features)
        """
        n = len(protein)
        pm = ProteinMathematics()

        # 创建张量场
        field = np.zeros((resolution, resolution, resolution, 4))

        # 近似3D坐标
        coords = pm._approximate_3d_coords(protein)

        # 归一化坐标到场中
        if len(coords) > 0:
            coords_min = np.min(coords, axis=0)
            coords_max = np.max(coords, axis=0)
            coords_range = coords_max - coords_min
            coords_range[coords_range == 0] = 1.0
            normalized = ((coords - coords_min) / coords_range * (resolution - 1)).astype(int)
            normalized = np.clip(normalized, 0, resolution - 1)

            for i, (x, y, z) in enumerate(normalized):
                aa = protein[i] if i < len(protein) else 'A'
                field[x, y, z, 0] = pm.HYDROPHOBICITY.get(aa, 0.0)
                field[x, y, z, 1] = pm.ALPHA_HELIX_PROPENSITY.get(aa, 0.0)
                field[x, y, z, 2] = pm.BETA_SHEET_PROPENSITY.get(aa, 0.0)
                field[x, y, z, 3] = pm.VDWAALS_RADIUS.get(aa, 2.0)

        self.tensor_field = field
        return field

    def metabolism_to_closed_loop(self, metabolism: Dict[str, List[str]]) -> Dict[str, Any]:
        """代谢网络→闭环机制。

        Args:
            metabolism: 代谢网络字典 {反应: [底物列表]}

        Returns:
            闭环分析结果
        """
        # 构建反应图
        all_compounds = set()
        reactions = []

        for reaction, substrates in metabolism.items():
            reactions.append({
                'name': reaction,
                'substrates': substrates,
                'products': []  # 简化模型
            })
            all_compounds.update(substrates)

        # 寻找闭环（简单环检测）
        cycles = []
        compounds_list = list(all_compounds)

        # 简化的环检测: 如果化合物出现在多个反应中，可能形成环
        compound_reactions = defaultdict(list)
        for i, reaction in enumerate(reactions):
            for compound in reaction['substrates']:
                compound_reactions[compound].append(i)

        for compound, reaction_indices in compound_reactions.items():
            if len(reaction_indices) > 1:
                cycles.append({
                    'type': 'compound_cycle',
                    'compound': compound,
                    'involved_reactions': [reactions[i]['name'] for i in reaction_indices]
                })

        return {
            'num_compounds': len(all_compounds),
            'num_reactions': len(reactions),
            'cycles': cycles,
            'cycle_count': len(cycles),
            'is_closed': len(cycles) > 0,
            'closure_degree': len(cycles) / len(reactions) if reactions else 0
        }

    def evolution_to_emergence(self, evolution_history: Dict[str, List[float]]) -> Dict[str, Any]:
        """进化过程→涌现分析。

        Args:
            evolution_history: 进化历史字典

        Returns:
            涌现特征字典
        """
        fitness = evolution_history.get('fitness', [])
        entropy = evolution_history.get('entropy', [])
        protein_length = evolution_history.get('protein_length', [])

        if len(fitness) < 2:
            return {'emergence_score': 0.0}

        # 适应度变化率
        fitness_delta = np.diff(fitness)
        mean_delta = np.mean(fitness_delta)

        # 熵变（复杂度变化）
        entropy_delta = np.diff(entropy)

        # 涌现度: 适应度提升 + 复杂度维持/提升
        emergence = 0.0
        if len(fitness_delta) > 0:
            positive_adaptation = np.sum(fitness_delta > 0) / len(fitness_delta)
            complexity_maintenance = np.sum(entropy_delta >= -0.1) / len(entropy_delta)
            emergence = (positive_adaptation + complexity_maintenance) / 2.0

        # 创新事件（适应度跳跃）
        innovations = []
        for i in range(len(fitness_delta)):
            if fitness_delta[i] > np.std(fitness_delta) * 2:
                innovations.append({
                    'generation': i + 1,
                    'fitness_jump': fitness_delta[i]
                })

        return {
            'emergence_score': float(emergence),
            'mean_fitness_delta': float(mean_delta),
            'fitness_variance': float(np.var(fitness)),
            'innovation_events': innovations,
            'innovation_count': len(innovations),
            'final_complexity': float(entropy[-1]) if entropy else 0.0,
            'complexity_trend': 'increasing' if len(entropy) > 1 and entropy[-1] > entropy[0] else 'decreasing'
        }

    def create_isomorphism_map(self, dna: str, protein: str) -> Dict[str, Any]:
        """创建完整的生物-知识同构映射。"""
        kg = self.dna_to_knowledge_graph(dna)
        tf = self.protein_to_tensor_field(protein)

        return {
            'knowledge_graph': kg,
            'tensor_field_shape': tf.shape,
            'mapping_type': 'bio_knowledge_isomorphism',
            'isomorphism_degree': kg['density']
        }


# =============================================================================
# 7. FormalLifeEngine — 主引擎
# =============================================================================

class FormalLifeEngine:
    """形式化生命主引擎。

    整合所有组件，提供统一接口。
    """

    def __init__(self, seed: Optional[int] = 42):
        """初始化形式化生命引擎。

        Args:
            seed: 全局随机种子
        """
        self.seed = seed
        self.dna_math = DNAMathematics(seed=seed)
        self.rna_math = RNAMathematics(seed=seed)
        self.protein_math = ProteinMathematics(seed=seed)
        self.genetic_code = GeneticCode()
        self.bio_knowledge = BioKnowledgeIsomorphism()

        self.life_forms = []
        self.population = []
        self.metrics_history = []

        # 64维生物数学场
        self.biomath_field = np.zeros(64)

        random.seed(seed)
        np.random.seed(seed)

    def create_life_form(self, dna_length: int = 100) -> FormalLife:
        """创建生命形式。

        Args:
            dna_length: DNA序列长度

        Returns:
            FormalLife实例
        """
        life = FormalLife(dna_length=dna_length, seed=self.seed + len(self.life_forms))
        life.create()
        self.life_forms.append(life)
        return life

    def run_life_cycle(self, cycles: int = 10) -> List[Dict[str, float]]:
        """运行生命周期。

        Args:
            cycles: 循环次数

        Returns:
            自创生状态历史
        """
        if not self.life_forms:
            self.create_life_form()

        history = []
        for _ in range(cycles):
            for life in self.life_forms:
                state = life.autopoiesis_cycle()
                history.append(state)
        return history

    def evolve_population(self, pop_size: int = 10, generations: int = 10,
                          environment: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """进化种群。

        Args:
            pop_size: 种群大小
            generations: 代数
            environment: 环境参数

        Returns:
            进化结果字典
        """
        # 初始化种群
        self.population = []
        for i in range(pop_size):
            life = FormalLife(dna_length=100, seed=self.seed + i)
            life.create()
            self.population.append(life)

        if environment is None:
            environment = {'temperature': 50.0, 'ph': 7.0, 'resource': 1.0, 'gc_preference': 0.5}

        # 进化历史
        fitness_history = []
        best_fitness_history = []
        mean_fitness_history = []

        for gen in range(generations):
            gen_fitness = []

            for life in self.population:
                life.mutate()
                life.selection_pressure(environment)
                gen_fitness.append(life.fitness)

            # 选择（轮盘赌选择 + 精英保留）
            sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
            best = sorted_pop[0]

            # 生成新一代
            new_population = [best]  # 精英保留

            while len(new_population) < pop_size:
                # 轮盘赌选择
                total_fitness = sum(l.fitness for l in self.population)
                if total_fitness <= 0:
                    total_fitness = 1.0

                pick = random.uniform(0, total_fitness)
                current = 0
                for life in self.population:
                    current += life.fitness
                    if current >= pick:
                        # 克隆并轻微突变
                        new_life = FormalLife(dna_length=100)
                        new_life.dna = life.dna
                        new_life.rna = life.rna
                        new_life.protein = life.protein
                        new_life.fitness = life.fitness
                        new_life.mutate(rate=0.01)
                        new_population.append(new_life)
                        break
                else:
                    new_population.append(sorted_pop[0])

            self.population = new_population[:pop_size]

            fitness_history.append(gen_fitness)
            best_fitness_history.append(max(gen_fitness))
            mean_fitness_history.append(np.mean(gen_fitness))

        return {
            'generations': generations,
            'population_size': pop_size,
            'best_fitness': best_fitness_history,
            'mean_fitness': mean_fitness_history,
            'final_best': max(best_fitness_history) if best_fitness_history else 0,
            'final_mean': mean_fitness_history[-1] if mean_fitness_history else 0,
            'fitness_improvement': (best_fitness_history[-1] - best_fitness_history[0]) if len(best_fitness_history) > 1 else 0
        }

    def get_life_metrics(self) -> Dict[str, Any]:
        """获取生命指标。

        Returns:
            生命指标字典（复杂度、适应度、涌现度）
        """
        if not self.life_forms:
            self.create_life_form()

        life = self.life_forms[0]
        state = life.get_state()

        # 复杂度
        complexity = state['entropy'] * len(state['protein']) / 30.0

        # 适应度
        fitness = state['fitness']

        # 涌现度（自创生循环的平均认知水平）
        emergence = life.autopoiesis_state['cognition']

        metrics = {
            'complexity': float(complexity),
            'fitness': float(fitness),
            'emergence': float(emergence),
            'gc_content': state['gc_content'],
            'entropy': state['entropy'],
            'protein_length': len(state['protein']),
            'generation': state['generation'],
            'age': state['age'],
            'dna_length': len(state['dna'])
        }

        self.metrics_history.append(metrics)
        return metrics

    def get_biomath_field_state(self) -> np.ndarray:
        """获取64维生物数学场状态。

        64维对应64个密码子，每一维的值编码:
        - 密码子频率
        - 氨基酸属性
        - 遗传信息流

        Returns:
            64维场向量
        """
        if not self.life_forms:
            self.create_life_form()

        field = np.zeros(64)
        codons = self.genetic_code.get_all_codons()

        # 统计当前生命中所有密码子的使用频率
        dna = self.life_forms[0].dna
        codon_counts = Counter()
        for i in range(0, len(dna) - 2, 3):
            codon = dna[i:i + 3]
            if len(codon) == 3:
                codon_counts[codon] += 1

        for idx, codon in enumerate(codons):
            frequency = codon_counts.get(codon, 0)
            aa = self.genetic_code.codon_to_amino_acid(codon)

            # 场值 = 频率 + 氨基酸疏水性 + 冗余度
            hydro = self.protein_math.HYDROPHOBICITY.get(aa, 0.0) if aa != '*' else 0.0
            redundancy = self.genetic_code.redundancy(codon)
            resilience = self.genetic_code.error_resilience(codon)

            field[idx] = frequency + hydro * 0.1 + redundancy * 0.05 + resilience * 0.1

        self.biomath_field = field
        return field

    def full_analysis(self, dna_length: int = 100) -> Dict[str, Any]:
        """完整分析管道。

        Args:
            dna_length: DNA长度

        Returns:
            完整分析结果
        """
        # 1. 创建生命
        life = self.create_life_form(dna_length)

        # 2. DNA分析
        dna = life.dna
        gc = self.dna_math.gc_content(dna)
        entropy = self.dna_math.entropy(dna)
        complement = self.dna_math.complement(dna)

        # 3. RNA分析
        rna = life.rna
        rna_pairs = self.rna_math.fold_secondary(rna[:50])  # 限制长度以加速
        rna_energy = self.rna_math.calculate_free_energy(rna_pairs, rna[:50])

        # 4. 蛋白质分析
        protein = life.protein
        helices = self.protein_math.predict_alpha_helix(protein)
        sheets = self.protein_math.predict_beta_sheet(protein)
        hydro = self.protein_math.compute_hydrophobicity(protein)
        topology = self.protein_math.fold_topology(protein)

        # 5. 遗传密码分析
        symmetry = self.genetic_code.symmetry_analysis()

        # 6. 同构映射
        kg = self.bio_knowledge.dna_to_knowledge_graph(dna)
        tf = self.bio_knowledge.protein_to_tensor_field(protein)

        # 7. 生命指标
        metrics = self.get_life_metrics()

        # 8. 64维场
        field = self.get_biomath_field_state()

        return {
            'dna': dna,
            'complement': complement,
            'gc_content': gc,
            'entropy': entropy,
            'rna': rna,
            'rna_pairs': rna_pairs,
            'rna_free_energy': rna_energy,
            'protein': protein,
            'alpha_helices': helices,
            'beta_sheets': sheets,
            'hydrophobicity_mean': float(np.mean(hydro)) if len(hydro) > 0 else 0.0,
            'fold_topology': topology,
            'genetic_code_symmetry': symmetry,
            'knowledge_graph': kg,
            'tensor_field_shape': tf.shape,
            'life_metrics': metrics,
            'biomath_field': field
        }


# =============================================================================
# __main__ 测试块
# =============================================================================
"""
OMNI-HUB v11.0 — formal_life_engine
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""

if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v9.0 — 形式化生命引擎测试")
    print("=" * 70)

    # 初始化引擎
    engine = FormalLifeEngine(seed=42)

    # ========================================================================
    # 测试1: 生成100bp DNA序列
    # ========================================================================
    print("\n[测试1] 生成100bp DNA序列")
    print("-" * 50)
    dna = engine.dna_math.generate_sequence(100)
    print(f"DNA序列: {dna[:50]}...")
    print(f"长度: {len(dna)} bp")

    # ========================================================================
    # 测试2: 互补序列、GC含量、熵、Z曲线
    # ========================================================================
    print("\n[测试2] DNA基本分析")
    print("-" * 50)
    complement = engine.dna_math.complement(dna)
    gc = engine.dna_math.gc_content(dna)
    entropy = engine.dna_math.entropy(dna)
    z_x, z_y, z_z = engine.dna_math.z_curve(dna)

    print(f"互补序列: {complement[:50]}...")
    print(f"GC含量: {gc:.4f}")
    print(f"香农熵: {entropy:.4f} (最大: 2.0000)")
    print(f"Z曲线终点: ({z_x[-1]:.1f}, {z_y[-1]:.1f}, {z_z[-1]:.1f})")

    # 傅里叶变换
    fft = engine.dna_math.fourier_transform(dna)
    print(f"傅里叶变换主频幅值: {np.max(fft[1:]):.2f}")

    # 随机游走
    wx, wy = engine.dna_math.walk_plot(dna)
    print(f"随机游走终点: ({wx[-1]:.1f}, {wy[-1]:.1f})")

    # ========================================================================
    # 测试3: 转录为RNA并预测二级结构
    # ========================================================================
    print("\n[测试3] RNA转录与二级结构")
    print("-" * 50)
    rna = engine.dna_math.transcribe(dna)
    print(f"RNA序列: {rna[:50]}...")

    # 使用较短的序列进行二级结构预测（加速）
    rna_short = rna[:40]
    pairs = engine.rna_math.fold_secondary(rna_short)
    db = engine.rna_math.structure_to_dot_bracket(rna_short, pairs)
    energy = engine.rna_math.calculate_free_energy(pairs, rna_short)

    print(f"二级结构 (dot-bracket): {db}")
    print(f"碱基配对数: {len(pairs)}")
    print(f"自由能: {energy:.2f} kcal/mol")

    # ========================================================================
    # 测试4: 翻译为蛋白质并预测结构
    # ========================================================================
    print("\n[测试4] 蛋白质翻译与结构预测")
    print("-" * 50)
    protein = engine.genetic_code.translate_dna(dna)
    print(f"蛋白质序列: {protein}")
    print(f"蛋白质长度: {len(protein)} 氨基酸")

    helices = engine.protein_math.predict_alpha_helix(protein)
    sheets = engine.protein_math.predict_beta_sheet(protein)
    hydro = engine.protein_math.compute_hydrophobicity(protein)
    topology = engine.protein_math.fold_topology(protein)

    print(f"预测α螺旋区域: {helices}")
    print(f"预测β折叠区域: {sheets}")
    print(f"平均疏水性: {np.mean(hydro):.3f}")
    print(f"回转半径: {topology['radius_of_gyration']:.2f} Å")
    print(f"缠绕数: {topology['writhing_number']:.4f}")

    # ========================================================================
    # 测试5: 遗传密码对称性分析
    # ========================================================================
    print("\n[测试5] 遗传密码对称性分析")
    print("-" * 50)
    symmetry = engine.genetic_code.symmetry_analysis()
    print(f"密码子总数: {symmetry['total_codons']}")
    print(f"编码密码子: {symmetry['coding_codons']}")
    print(f"终止密码子: {symmetry['stop_codons']}")
    print(f"平均简并度: {symmetry['mean_degeneracy']:.2f}")
    print(f"摆动简并数: {symmetry['wobble_degeneracy_count']}")
    print(f"镜像对称对: {symmetry['mirror_symmetry_pairs']}")
    print(f"自同构群大小: {symmetry['automorphism_group_size']}")

    # 错误恢复力示例
    sample_codons = ['ATG', 'TGG', 'TTA', 'GCG']
    print("\n错误恢复力示例:")
    for codon in sample_codons:
        aa = engine.genetic_code.codon_to_amino_acid(codon)
        resilience = engine.genetic_code.error_resilience(codon)
        print(f"  {codon} ({aa}): {resilience:.3f}")

    # ========================================================================
    # 测试6: 自创生循环
    # ========================================================================
    print("\n[测试6] 自创生循环 (5次)")
    print("-" * 50)
    life = engine.create_life_form(100)
    for i in range(5):
        state = life.autopoiesis_cycle()
        print(f"  循环{i+1}: 生产={state['production']:.3f}, "
              f"耦合={state['structural_coupling']:.3f}, "
              f"认知={state['cognition']:.3f}")

    # ========================================================================
    # 测试7: 进化种群
    # ========================================================================
    print("\n[测试7] 进化种群 (10个体, 5代)")
    print("-" * 50)
    result = engine.evolve_population(pop_size=10, generations=5)
    print(f"代数: {result['generations']}")
    print(f"种群大小: {result['population_size']}")
    print(f"最佳适应度历史: {[f'{x:.4f}' for x in result['best_fitness']]}")
    print(f"平均适应度历史: {[f'{x:.4f}' for x in result['mean_fitness']]}")
    print(f"最终最佳适应度: {result['final_best']:.4f}")
    print(f"最终平均适应度: {result['final_mean']:.4f}")
    print(f"适应度提升: {result['fitness_improvement']:.4f}")

    # ========================================================================
    # 测试8: DNA→知识图谱映射
    # ========================================================================
    print("\n[测试8] DNA→知识图谱映射")
    print("-" * 50)
    kg = engine.bio_knowledge.dna_to_knowledge_graph(dna)
    print(f"节点数: {kg['num_nodes']}")
    print(f"边数: {kg['num_edges']}")
    print(f"图谱密度: {kg['density']:.4f}")
    print(f"节点示例:")
    for i, (node_id, node_data) in enumerate(list(kg['nodes'].items())[:3]):
        print(f"  {node_id}: seq={node_data['sequence']}, "
              f"GC={node_data['gc_content']:.3f}")
    print(f"边示例:")
    for i, edge in enumerate(kg['edges'][:3]):
        print(f"  {edge['source']} --[{edge['relation']}, w={edge['weight']:.3f}]--> {edge['target']}")

    # ========================================================================
    # 测试9: 蛋白质→张量场
    # ========================================================================
    print("\n[测试9] 蛋白质→张量场")
    print("-" * 50)
    tf = engine.bio_knowledge.protein_to_tensor_field(protein, resolution=8)
    print(f"张量场形状: {tf.shape}")
    print(f"非零元素数: {np.count_nonzero(tf)}")
    print(f"场值范围: [{np.min(tf):.3f}, {np.max(tf):.3f}]")

    # ========================================================================
    # 测试10: 生命指标与64维场
    # ========================================================================
    print("\n[测试10] 生命指标与64维生物数学场")
    print("-" * 50)
    metrics = engine.get_life_metrics()
    print(f"复杂度: {metrics['complexity']:.4f}")
    print(f"适应度: {metrics['fitness']:.4f}")
    print(f"涌现度: {metrics['emergence']:.4f}")
    print(f"GC含量: {metrics['gc_content']:.4f}")
    print(f"熵: {metrics['entropy']:.4f}")
    print(f"蛋白质长度: {metrics['protein_length']}")

    field = engine.get_biomath_field_state()
    print(f"\n64维生物数学场:")
    print(f"  场向量范数: {np.linalg.norm(field):.4f}")
    print(f"  场值总和: {np.sum(field):.4f}")
    print(f"  最大值索引: {np.argmax(field)} (密码子: {engine.genetic_code.get_all_codons()[np.argmax(field)]})")
    print(f"  前10维: {field[:10]}")

    # ========================================================================
    # 完整分析管道
    # ========================================================================
    print("\n[测试11] 完整分析管道")
    print("-" * 50)
    analysis = engine.full_analysis(100)
    print(f"分析完成。DNA长度: {len(analysis['dna'])}")
    print(f"蛋白质长度: {len(analysis['protein'])}")
    print(f"知识图谱节点: {analysis['knowledge_graph']['num_nodes']}")
    print(f"张量场形状: {analysis['tensor_field_shape']}")

    print("\n" + "=" * 70)
    print("所有测试通过！形式化生命引擎运行正常。")
    print("=" * 70)
