#!/usr/bin/env python3
"""
T-0008 CND Verification Script
Verifies that a 46x46 tree metric matrix satisfies the Conditionally Negative Definite (CND) property.
"""

import numpy as np
from scipy.linalg import eigh
import os

np.random.seed(42)

N = 46

def generate_tree_metric_matrix(n, seed=42):
    """
    Generate a proper n-node tree metric matrix.
    Steps:
    1. Build a random tree with n nodes (using random parent assignments).
    2. Assign random positive edge weights.
    3. Compute pairwise distances as the unique path length between nodes.
    A proper tree metric is guaranteed to satisfy the 4-point condition and be CND.
    """
    rng = np.random.default_rng(seed)

    # Build a random tree: node 0 is root, each subsequent node picks a random parent
    parents = [None]  # root has no parent
    edge_weights = [0.0]  # dummy for root

    for i in range(1, n):
        parent = rng.integers(0, i)  # pick a parent from existing nodes
        parents.append(parent)
        weight = rng.uniform(0.5, 2.0)  # positive edge weight
        edge_weights.append(weight)

    # Precompute ancestors and distances to root for each node
    depth = [0.0] * n
    dist_to_root = [0.0] * n

    def compute_dist_to_root(node):
        if node == 0:
            return 0.0
        p = parents[node]
        return compute_dist_to_root(p) + edge_weights[node]

    for i in range(n):
        dist_to_root[i] = compute_dist_to_root(i)

    # Build adjacency list for LCA computation
    children = [[] for _ in range(n)]
    for i in range(1, n):
        children[parents[i]].append(i)

    # Compute depth (number of edges from root)
    def compute_depth(node, d):
        depth[node] = d
        for c in children[node]:
            compute_depth(c, d + 1)

    compute_depth(0, 0)

    # Binary lifting for LCA
    LOG = (n).bit_length()
    up = [[-1] * n for _ in range(LOG)]
    for i in range(n):
        up[0][i] = parents[i] if parents[i] is not None else -1

    for k in range(1, LOG):
        for i in range(n):
            if up[k - 1][i] != -1:
                up[k][i] = up[k - 1][up[k - 1][i]]
            else:
                up[k][i] = -1

    def lca(u, v):
        if depth[u] < depth[v]:
            u, v = v, u
        # Lift u up to same depth as v
        diff = depth[u] - depth[v]
        for k in range(LOG - 1, -1, -1):
            if diff >= (1 << k):
                u = up[k][u]
                diff -= (1 << k)
        if u == v:
            return u
        for k in range(LOG - 1, -1, -1):
            if up[k][u] != -1 and up[k][u] != up[k][v]:
                u = up[k][u]
                v = up[k][v]
        return parents[u]

    # Compute pairwise distances: d(u,v) = dist_to_root[u] + dist_to_root[v] - 2*dist_to_root[lca]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            ancestor = lca(i, j)
            d = dist_to_root[i] + dist_to_root[j] - 2 * dist_to_root[ancestor]
            D[i, j] = d
            D[j, i] = d

    return D


def check_four_point_condition(D, tol=1e-9):
    """
    Check the 4-point condition for tree metrics:
    For all distinct i,j,k,l: the two largest of
        D[i,j] + D[k,l], D[i,k] + D[j,l], D[i,l] + D[j,k]
    must be equal (up to tolerance).
    """
    n = D.shape[0]
    violations = 0
    max_violation = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for l in range(k + 1, n):
                    s1 = D[i, j] + D[k, l]
                    s2 = D[i, k] + D[j, l]
                    s3 = D[i, l] + D[j, k]
                    sums = sorted([s1, s2, s3])
                    diff = abs(sums[1] - sums[2])
                    max_violation = max(max_violation, diff)
                    if diff > tol:
                        violations += 1
    return violations, max_violation


def sample_cnd_check(D, n_samples=10000, seed=42):
    """
    Approximate CND check:
    Sample n_samples random vectors x with sum(x_i) = 0,
    and verify x^T D x <= 0 for all of them.
    """
    rng = np.random.default_rng(seed)
    n = D.shape[0]
    max_val = -np.inf
    all_nonpos = True

    for _ in range(n_samples):
        # Sample random vector, then center it (sum = 0)
        x = rng.standard_normal(n)
        x = x - x.mean()
        # Quadratic form
        val = x @ D @ x
        max_val = max(max_val, val)
        if val > 1e-8:  # small tolerance for numerical noise
            all_nonpos = False

    return all_nonpos, max_val


def check_psd_kernel(D, beta=1.0):
    """
    Check that exp(-beta * D) is positive semidefinite.
    For CND matrices, this should be PSD for all beta > 0.
    """
    K = np.exp(-beta * D)
    # Use eigh for symmetric matrices
    eigvals = eigh(K, eigvals_only=True)
    min_eig = eigvals.min()
    return min_eig >= -1e-8, min_eig


def check_eigenvalues_centered(D):
    """
    Compute eigenvalues of the centered matrix.
    For a CND matrix, all non-zero eigenvalues should be negative.
    Centering: P D P where P = I - (1/n) 1 1^T
    """
    n = D.shape[0]
    P = np.eye(n) - np.ones((n, n)) / n
    centered = P @ D @ P
    eigvals = eigh(centered, eigvals_only=True)
    # Sort descending
    eigvals_sorted = np.sort(eigvals)[::-1]
    # Check that all non-zero eigenvalues are negative (or zero)
    # The matrix is rank at most n-1, so at least one zero eigenvalue
    tol = 1e-8
    non_zero_eigs = eigvals_sorted[np.abs(eigvals_sorted) > tol]
    all_negative = np.all(non_zero_eigs < 0)
    return all_negative, eigvals_sorted


def main():
    print("=== T-0008 CND Verification Script ===")
    print(f"Matrix size: {N}x{N}")
    print()

    # 1. Generate tree metric matrix from a proper random tree
    D = generate_tree_metric_matrix(N, seed=42)
    print("[1] Tree metric matrix generated (from proper random tree).")

    # 2. Verify 4-point condition (tree metric property)
    violations, max_viol = check_four_point_condition(D)
    print(f"[2] 4-point condition violations: {violations}")
    print(f"    Max violation: {max_viol:.6e}")

    # 3. CND check (sampled)
    cnd_pass, max_quad = sample_cnd_check(D, n_samples=10000, seed=42)
    print(f"[3] CND check (10,000 samples): {'PASS' if cnd_pass else 'FAIL'}")
    print(f"    Max x^T D x (sampled): {max_quad:.6e}")

    # 4. PSD kernel check
    psd_pass, min_eig_kernel = check_psd_kernel(D, beta=1.0)
    print(f"[4] PSD kernel check (beta=1.0): {'PASS' if psd_pass else 'FAIL'}")
    print(f"    Min eigenvalue of exp(-D): {min_eig_kernel:.6e}")

    # 5. Eigenvalue check (centered matrix)
    eig_pass, eigvals = check_eigenvalues_centered(D)
    print(f"[5] Eigenvalue check (centered): {'PASS' if eig_pass else 'FAIL'}")
    print(f"    Eigenvalues (centered, top 10):")
    for i in range(min(10, len(eigvals))):
        print(f"      lambda_{i}: {eigvals[i]:.6e}")
    print(f"    Number of near-zero eigenvalues: {np.sum(np.abs(eigvals) < 1e-8)}")

    # 6. Final verdict
    verdict = "PROVISIONALLY VERIFIED" if (cnd_pass and eig_pass and psd_pass) else "FAILED"
    print()
    print("=" * 50)
    print("=== T-0008 CND Verification Report ===")
    print(f"Matrix size: {N}x{N}")
    print(f"CND check (sampled): {'PASS' if cnd_pass else 'FAIL'}")
    print(f"Max x^T D x (sampled): {max_quad:.6e}")
    print(f"Eigenvalue check: {'PASS' if eig_pass else 'FAIL'}")
    print(f"PSD kernel check: {'PASS' if psd_pass else 'FAIL'}")
    print(f"=== VERDICT: {verdict} ===")
    print("=" * 50)

    # Save report
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hub")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "cnd_verification_report.txt")

    with open(report_path, "w") as f:
        f.write("=" * 50 + "\n")
        f.write("=== T-0008 CND Verification Report ===\n")
        f.write(f"Matrix size: {N}x{N}\n")
        f.write(f"CND check (sampled): {'PASS' if cnd_pass else 'FAIL'}\n")
        f.write(f"Max x^T D x (sampled): {max_quad:.6e}\n")
        f.write(f"Eigenvalue check: {'PASS' if eig_pass else 'FAIL'}\n")
        f.write(f"PSD kernel check: {'PASS' if psd_pass else 'FAIL'}\n")
        f.write(f"=== VERDICT: {verdict} ===\n")
        f.write("=" * 50 + "\n")
        f.write("\nDetailed results:\n")
        f.write(f"4-point condition violations: {violations}\n")
        f.write(f"Max 4-point violation: {max_viol:.6e}\n")
        f.write(f"Min eigenvalue of exp(-D): {min_eig_kernel:.6e}\n")
        f.write(f"Centered eigenvalues (top 10):\n")
        for i in range(min(10, len(eigvals))):
            f.write(f"  lambda_{i}: {eigvals[i]:.6e}\n")

    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
