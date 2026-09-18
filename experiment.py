
__version__ = "11.0.0"
"""
OMNI-HUB v11.0 — experiment
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
"""
OMNI-HUB v4.0 - Full Experiment
100 beats, 11 voices counterpoint composition
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from cantus_firmus import CantusFirmus
from counterpoint_engine import (
    CounterpointEngine, CounterpointVisualizer, 
    CounterpointValidator, ConsonanceCalculator
)
import numpy as np
import time
import logging


def run_experiment():
    logger.info("=" * 80)
    logger.info("OMNI-HUB v4.0 - Counterpoint Engine Full Experiment")
    logger.info("=" * 80)
    logger.info("\nConfiguration:")
    logger.info(f"  Measures: 100 beats")
    logger.info(f"  Voices: 11 (including 1 QGL voice)")
    logger.info(f"  Key: C Major")
    logger.info(f"  Seed: 42")
    
    start_time = time.time()
    
    # Step 1: Generate Cantus Firmus
    logger.info("\n[1/6] Generating Cantus Firmus...")
    cf = CantusFirmus(key_center=60, scale_type='major', seed=42)
    cf.generate(length=100)
    logger.info(f"  CF Length: {len(cf)} beats")
    logger.info(f"  CF Range: {cf.get_range()} semitones")
    logger.info(f"  CF Climax: beat {cf.get_climax()[0]}, pitch {cf.get_climax()[1]}")
    logger.info(f"  CF Melody: {cf.melody[:20]}...")
    
    # Step 2: Create Counterpoint Engine
    logger.info("\n[2/6] Creating Counterpoint Engine (11 voices)...")
    engine = CounterpointEngine(cantus_firmus=cf, n_voices=11, seed=42)
    logger.info(f"  Voices: {[v.name for v in engine.voices]}")
    logger.info(f"  QGL Voice: {engine.voices[-1].name} (index {engine.qgl_voice_idx})")
    
    # Step 3: Compose
    logger.info("\n[3/6] Composing counterpoint...")
    score = engine.compose(measures=100)
    logger.info(f"  Score shape: {len(score)} beats x {len(score[0])} voices")
    
    # Step 4: Evaluate
    logger.info("\n[4/6] Evaluating counterpoint quality...")
    results = engine.evaluate()
    
    logger.info(f"\n  === Evaluation Results ===")
    logger.info(f"  Contrary Motion Ratio:  {results['contrary_ratio']:.4f}")
    logger.info(f"  Oblique Motion Ratio:   {results['oblique_ratio']:.4f}")
    logger.info(f"  Similar Motion Ratio:   {results['similar_ratio']:.4f}")
    logger.info(f"  Parallel Violations:    {results['parallel_violations']}")
    logger.info(f"  Richness (Entropy):     {results['richness']:.4f}")
    logger.info(f"  Independence:           {results['independence']:.4f}")
    logger.info(f"  Harmony Score:          {results['harmony']:.4f}")
    logger.info(f"  QGL Silence Effect:     {results['qgl_silence_effect']:.4f}")
    logger.info(f"  Unison Violations:      {results['unison_violations']}")
    logger.info(f"  Mean Tension:           {results['mean_tension']:.4f}")
    logger.info(f"  Max Tension:            {results['max_tension']:.4f}")
    logger.info(f"  Tension Variance:       {results['tension_variance']:.4f}")
    logger.info(f"  Overall Score:          {results['overall']:.4f}")
    
    # Step 5: Validate
    logger.info("\n[5/6] Running validation...")
    validator = CounterpointValidator(engine)
    validation = validator.validate_all()
    
    logger.info(f"\n  === Validation Results ===")
    pv = validation['parallel_validation']
    logger.info(f"  Parallel Fifths:    {pv['parallel_fifths']} {'PASS' if pv['parallel_fifths']==0 else 'FAIL'}")
    logger.info(f"  Parallel Octaves:   {pv['parallel_octaves']} {'PASS' if pv['parallel_octaves']==0 else 'FAIL'}")
    
    vl = validation['voice_leading']
    logger.info(f"  Voice Leading:      {vl['overall_score']:.4f} {'PASS' if vl['passed'] else 'FAIL'}")
    
    cs = validation['consonance']
    logger.info(f"  Consonance:         {cs['mean_harmony']:.4f} {'PASS' if cs['passed'] else 'FAIL'}")
    
    qgl = validation['qgl']
    logger.info(f"  QGL Active Ratio:   {qgl.get('active_ratio', 0):.4f}")
    logger.info(f"  QGL Silence Effect: {qgl.get('silence_effect', 0):.4f}")
    logger.info(f"  QGL Validation:     {'PASS' if qgl['passed'] else 'FAIL'}")
    
    ind = validation['independence']
    logger.info(f"  Independence:       {ind['independence_score']:.4f} {'PASS' if ind['passed'] else 'FAIL'}")
    
    # Step 6: Visualize
    logger.info("\n[6/6] Generating visualizations...")
    viz = CounterpointVisualizer(engine)
    
    viz_dir = os.path.join(os.path.dirname(__file__), 'viz')
    os.makedirs(viz_dir, exist_ok=True)
    
    logger.info("  -> Plotting polyphonic score...")
    viz.plot_score(save_path=os.path.join(viz_dir, '01_polyphonic_score.png'))
    
    logger.info("  -> Plotting consonance matrix...")
    viz.plot_consonance_matrix(beat=0, save_path=os.path.join(viz_dir, '02_consonance_matrix_beat0.png'))
    viz.plot_consonance_matrix(beat=25, save_path=os.path.join(viz_dir, '02_consonance_matrix_beat25.png'))
    viz.plot_consonance_matrix(beat=50, save_path=os.path.join(viz_dir, '02_consonance_matrix_beat50.png'))
    
    logger.info("  -> Plotting voice independence...")
    viz.plot_voice_independence(save_path=os.path.join(viz_dir, '03_voice_independence.png'))
    
    logger.info("  -> Plotting tension curve...")
    viz.plot_tension_curve(save_path=os.path.join(viz_dir, '04_tension_curve.png'))
    
    logger.info("  -> Plotting QGL negative space...")
    viz.plot_qgl_negative_space(save_path=os.path.join(viz_dir, '05_qgl_negative_space.png'))
    
    logger.info("  -> Plotting interval distribution...")
    viz.plot_interval_distribution(save_path=os.path.join(viz_dir, '06_interval_distribution.png'))
    
    # Additional: correlation heatmap over time
    logger.info("  -> Plotting temporal correlation...")
    _plot_temporal_correlation(engine, save_path=os.path.join(viz_dir, '07_temporal_correlation.png'))
    
    # Generate report
    logger.info("\n[7/7] Generating report...")
    report = validator.generate_report()
    report_path = os.path.join(os.path.dirname(__file__), 'experiment_report.txt')
    with open(report_path, 'w') as f:
        f.write(report)
        f.write(f"\n\n{'='*80}\n")
        f.write("DETAILED EVALUATION METRICS\n")
        f.write(f"{'='*80}\n")
        for key, value in results.items():
            f.write(f"{key}: {value:.6f}\n")
    
        logger.error(f"File operation failed: {e}")
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"Experiment completed in {elapsed:.2f} seconds")
    logger.info(f"{'='*80}")
    logger.info(f"\nOutput files:")
    logger.info(f"  Core:  /mnt/agents/output/OMNI-HUB/core/cantus_firmus.py")
    logger.info(f"  Core:  /mnt/agents/output/OMNI-HUB/core/counterpoint_engine.py")
    logger.info(f"  Viz:   /mnt/agents/output/OMNI-HUB/viz/")
    logger.info(f"  Report: {report_path}")
    
    return results, validation


def _plot_temporal_correlation(engine, save_path):
    """绘制随时间变化的相关系数"""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 6))
    
    n_beats = len(engine.score_history)
    n_voices = len(engine.voices)
    
    # 计算滑动窗口的相关系数
    window = 8
    time_points = []
    mean_corrs = []
    
    for t in range(window, n_beats):
        series = []
        for v_idx in range(n_voices):
            s = [engine.score_history[b][v_idx] for b in range(t - window, t)]
            series.append(s)
        
        corr = np.corrcoef(series)
        total = 0
        count = 0
        for i in range(n_voices):
            for j in range(i + 1, n_voices):
                total += abs(corr[i, j])
                count += 1
        
        time_points.append(t)
        mean_corrs.append(total / count if count > 0 else 0)
    
    ax.plot(time_points, mean_corrs, 'b-', linewidth=1.5)
    ax.axhline(y=0.3, color='r', linestyle='--', alpha=0.5, label='Threshold (0.3)')
    ax.fill_between(time_points, mean_corrs, alpha=0.3)
    
    ax.set_xlabel('Beat', fontsize=12)
    ax.set_ylabel('Mean Absolute Correlation', fontsize=12)
    ax.set_title('Temporal Voice Correlation\n(Sliding Window = 8 beats)', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    results, validation = run_experiment()
