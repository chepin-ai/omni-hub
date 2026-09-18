
__version__ = "11.0.0"
"""
OMNI-HUB v4.0 — Counterpoint Experiment Runner
对位席架构实验验证与可视化
"""

import sys
sys.path.insert(0, '/mnt/agents/output/OMNI-HUB/core')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from counterpoint_seats import run_counterpoint_experiment, CounterpointOrchestra, SeatRegistry
from voice_melody import ConsonanceType
import warnings
import logging
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.size'] = 9

# OMNI-HUB配色
"""
OMNI-HUB v11.0 — experiment_runner
模块自动升级至v11标准 | Auto-upgraded to v11 standards
"""
COLORS = {
    'cisvr': '#2E86AB',   # 深蓝 - 基准
    'ucif2': '#A23B72',   # 紫红 - 合取
    'lgt': '#F18F01',     # 橙 - 自由意志
    'usrm': '#C73E1D',    # 红 - 因果
    'cfts': '#3B1F2B',    # 深紫 - F4
    'qlv': '#95C623',     # 绿 - 谱观测
    'vinf': '#6A4C93',    # 紫 - 张量网
    'qgl': '#1B1B1E',     # 近黑 - 静默
    'qfa': '#0F4C5C',     # 青 - 折纸
    'lvlu': '#E36414',    # 橘红 - 递归
    'qtlv': '#5C80BC',    # 蓝灰 - 拓扑
}

LINE_NAMES = {
    'cisvr': 'CF (基准)',
    'ucif2': 'CFM (合取)',
    'lgt': 'FW (意志)',
    'usrm': 'CS (因果)',
    'cfts': 'F4 (机验)',
    'qlv': 'SO (观测)',
    'vinf': 'TN (网络)',
    'qgl': 'SB (静默)',
    'qfa': 'OT (折纸)',
    'lvlu': 'LR (递归)',
    'qtlv': 'QT (拓扑)',
}


def visualize_polyphony(results, output_dir='/mnt/agents/output/OMNI-HUB/core'):
    """可视化11声部复调谱"""
    orchestra = results['orchestra']
    n_beats = results['n_beats']
    
    fig = plt.figure(figsize=(20, 28))
    
    # === 图1: 复调总谱 ===
    ax1 = fig.add_subplot(5, 1, 1)
    line_ids = list(orchestra.seats.keys())
    y_positions = {lid: i for i, lid in enumerate(reversed(line_ids))}
    
    for lid in line_ids:
        seat = orchestra.seats[lid]
        color = COLORS.get(lid, '#333333')
        
        for note in seat.note_history:
            y = y_positions[lid]
            if note.is_rest():
                # 休止: 画小点
                ax1.plot(note.onset, y, 'o', color=color, alpha=0.3, markersize=2)
            else:
                # 音符: 画水平线
                ax1.plot([note.onset, note.onset + note.duration], 
                        [y, y], 
                        color=color, linewidth=2, alpha=0.8)
    
    ax1.set_yticks(range(len(line_ids)))
    ax1.set_yticklabels([LINE_NAMES[lid] for lid in reversed(line_ids)])
    ax1.set_xlabel('Time (beats)')
    ax1.set_title('OMNI-HUB v4.0 — 11-Voice Polyphonic Counterpoint Score\n' +
                  'Core Thesis: "Harmony is not unison; counterpoint is manifestation"',
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_xlim(0, n_beats)
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.axhline(y=y_positions['qgl'], color='red', linestyle='--', alpha=0.3, linewidth=0.5)
    
    # === 图2: 各声部音高轨迹 ===
    ax2 = fig.add_subplot(5, 1, 2)
    for lid in line_ids:
        seat = orchestra.seats[lid]
        times = [n.onset for n in seat.note_history if not n.is_rest()]
        pitches = [n.pitch for n in seat.note_history if not n.is_rest()]
        color = COLORS.get(lid, '#333333')
        ax2.plot(times, pitches, 'o-', color=color, label=LINE_NAMES[lid], 
                markersize=2, linewidth=1, alpha=0.7)
    
    ax2.set_xlabel('Time (beats)')
    ax2.set_ylabel('MIDI Pitch')
    ax2.set_title('Pitch Trajectories of 11 Independent Voices', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, n_beats)
    ax2.legend(loc='upper right', ncol=6, fontsize=7)
    ax2.grid(True, alpha=0.3)
    
    # === 图3: 协和度时间序列 ===
    ax3 = fig.add_subplot(5, 1, 3)
    times = results['times']
    consonance_scores = results['consonance_scores']
    active_counts = results['active_counts']
    
    ax3_twin = ax3.twinx()
    
    ax3.plot(times, consonance_scores, 'b-', linewidth=1.5, alpha=0.8, label='Consonance Score')
    ax3_twin.plot(times, active_counts, 'r--', linewidth=1, alpha=0.6, label='Active Voices')
    
    # 标注协和度等级
    ax3.axhspan(2.5, 3.0, alpha=0.1, color='green', label='Perfect Consonance')
    ax3.axhspan(1.5, 2.5, alpha=0.1, color='yellow', label='Imperfect Consonance')
    ax3.axhspan(0.5, 1.5, alpha=0.1, color='red', label='Dissonance')
    
    ax3.set_xlabel('Time (beats)')
    ax3.set_ylabel('Consonance Score', color='b')
    ax3_twin.set_ylabel('Active Voices', color='r')
    ax3.set_title('Consonance Score & Active Voice Count Over Time', fontsize=12, fontweight='bold')
    ax3.set_xlim(0, n_beats)
    ax3.set_ylim(0.5, 3.5)
    ax3_twin.set_ylim(0, 12)
    ax3.grid(True, alpha=0.3)
    
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)
    
    # === 图4: 协和度矩阵热图 ===
    ax4 = fig.add_subplot(5, 1, 4)
    matrix, m_line_ids = results['consonance_matrix'], results['line_ids']
    
    # 自定义颜色映射: 0=休止(黑), 1=不协和(红), 2=不完全协和(黄), 3=完美协和(绿)
    cmap_colors = [(0, 0, 0), (0.8, 0.2, 0.2), (0.9, 0.9, 0.3), (0.3, 0.7, 0.3)]
    custom_cmap = LinearSegmentedColormap.from_list('consonance', cmap_colors, N=4)
    
    im = ax4.imshow(matrix, cmap=custom_cmap, vmin=0, vmax=3, aspect='auto')
    ax4.set_xticks(range(len(m_line_ids)))
    ax4.set_yticks(range(len(m_line_ids)))
    ax4.set_xticklabels([LINE_NAMES[lid] for lid in m_line_ids], rotation=45, ha='right', fontsize=8)
    ax4.set_yticklabels([LINE_NAMES[lid] for lid in m_line_ids], fontsize=8)
    ax4.set_title('Consonance Matrix (Mid-Time Snapshot)\n' +
                  'Black=Rest, Red=Dissonance, Yellow=Imperfect, Green=Perfect',
                  fontsize=12, fontweight='bold')
    
    # 添加数值标注
    for i in range(len(m_line_ids)):
        for j in range(len(m_line_ids)):
            text = ax4.text(j, i, f'{matrix[i, j]:.0f}',
                          ha="center", va="center", color="white" if matrix[i, j] < 1.5 else "black",
                          fontsize=7)
    
    plt.colorbar(im, ax=ax4, ticks=[0, 1, 2, 3], 
                label='Consonance: 0=Rest, 1=Dissonance, 2=Imperfect, 3=Perfect')
    
    # === 图5: 统计信息 ===
    ax5 = fig.add_subplot(5, 1, 5)
    ax5.axis('off')
    
    summary = results['summary']
    richness = summary['richness']
    stats = summary['seat_stats']
    
    # 生成统计文本
    text_lines = []
    text_lines.append("=" * 80)
    text_lines.append("OMNI-HUB v4.0 — COUNTERPOINT ARCHITECTURE EXPERIMENT REPORT")
    text_lines.append("=" * 80)
    text_lines.append(f"\nGENERAL STATISTICS:")
    text_lines.append(f"  Total Beats:        {n_beats}")
    text_lines.append(f"  Total Seats:        {summary['n_seats']}")
    text_lines.append(f"  Voice Independence: {summary['independence_score']:.4f}")
    text_lines.append(f"  Overall Richness:   {richness['overall']:.4f}")
    text_lines.append(f"\nVIOLATION DETECTION:")
    text_lines.append(f"  Total Violations:   {summary['total_violations']}")
    text_lines.append(f"  Parallel Fifths:    {summary['parallel_fifths']} (FORBIDDEN)")
    text_lines.append(f"  Parallel Octaves:   {summary['parallel_octaves']} (FORBIDDEN)")
    text_lines.append(f"  Unisons:            {summary['unisons']} (FORBIDDEN)")
    text_lines.append(f"\nRICHNESS METRICS:")
    text_lines.append(f"  Interval Richness:      {richness['interval_richness']:.4f}")
    text_lines.append(f"  Consonance Variance:    {richness['consonance_variance']:.4f}")
    text_lines.append(f"  Activity Variance:      {richness['activity_variance']:.4f}")
    text_lines.append(f"  Silence Art (qgl):      {richness['silence_art']:.4f}")
    text_lines.append(f"\nPER-SEAT STATISTICS:")
    text_lines.append(f"  {'Line':<8} {'Seat':<20} {'Type':<12} {'Notes':>6} {'Rest%':>6} {'AvgInt':>6} {'DirChg':>6}")
    text_lines.append(f"  {'-'*68}")
    
    for lid in LINE_NAMES.keys():
        if lid in stats:
            s = stats[lid]
            text_lines.append(
                f"  {lid:<8} {s['seat_name']:<20} {s['voice_type']:<12} "
                f"{s['n_notes']:>6} {s['rest_ratio']:>6.2f} {s['avg_interval']:>6.1f} {s['direction_changes']:>6}"
            )
    
    text_lines.append(f"\nCOUNTERPOINT RULES (Musical -> Architectural):")
    text_lines.append(f"  1. No Parallel Fifths/Octaves  -> No inter-line complete synchronization")
    text_lines.append(f"  2. Contrary Motion Preferred   -> Inter-line differential movement")
    text_lines.append(f"  3. Voice Crossing Allowed      -> High-SI lines may temporarily go below low-SI lines")
    text_lines.append(f"  4. Consonance Classification   -> Perfect/Imperfect/Dissonance")
    text_lines.append(f"  5. Resolution Rule             -> Tension->Relaxation tendency")
    text_lines.append(f"  6. Art of Rest                 -> qgl's silence is negative space")
    
    text_lines.append(f"\n{'='*80}")
    
    ax5.text(0.05, 0.95, '\n'.join(text_lines), transform=ax5.transAxes,
            fontsize=8, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(pad=2.0)
    plt.savefig(f'{output_dir}/counterpoint_visualization.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"[可视化] 已保存: {output_dir}/counterpoint_visualization.png")
    return f'{output_dir}/counterpoint_visualization.png'


def visualize_seat_detail(results, output_dir='/mnt/agents/output/OMNI-HUB/core'):
    """各对位席详细分析图"""
    orchestra = results['orchestra']
    fig, axes = plt.subplots(4, 3, figsize=(18, 20))
    axes = axes.flatten()
    
    line_ids = list(orchestra.seats.keys())
    
    for idx, lid in enumerate(line_ids):
        ax = axes[idx]
        seat = orchestra.seats[lid]
        color = COLORS.get(lid, '#333333')
        
        # 音高-时间图
        times = [n.onset for n in seat.note_history if not n.is_rest()]
        pitches = [n.pitch for n in seat.note_history if not n.is_rest()]
        rests = [n.onset for n in seat.note_history if n.is_rest()]
        
        ax.plot(times, pitches, 'o-', color=color, markersize=2, linewidth=1, alpha=0.8)
        if rests:
            ax.scatter(rests, [seat.melody_theme.pitch_range[0]] * len(rests), 
                      marker='x', color='red', s=10, alpha=0.5, label='Rest')
        
        ax.set_title(f"{lid}: {seat.seat_name}\n({seat.voice_type})", 
                    fontsize=10, fontweight='bold', color=color)
        ax.set_xlabel('Time (beats)')
        ax.set_ylabel('MIDI Pitch')
        ax.set_xlim(0, results['n_beats'])
        ax.grid(True, alpha=0.3)
    
    # 最后一个子图放总览
    ax_last = axes[-1]
    ax_last.axis('off')
    
    summary = results['summary']
    info_text = f"""
    OMNI-HUB v4.0
    
    Voice Independence: {summary['independence_score']:.4f}
    Overall Richness: {summary['richness']['overall']:.4f}
    
    Violations:
    - Parallel Fifths: {summary['parallel_fifths']}
    - Parallel Octaves: {summary['parallel_octaves']}
    - Unisons: {summary['unisons']}
    
    qgl Silence Ratio: {results['qgl_rest_ratio']:.4f}
    
    Counterpoint Principle:
    "和声不是齐唱
     对位即显化"
    """
    ax_last.text(0.5, 0.5, info_text, transform=ax_last.transAxes,
                fontsize=11, verticalalignment='center', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    plt.tight_layout(pad=2.0)
    plt.savefig(f'{output_dir}/seat_detail_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"[可视化] 已保存: {output_dir}/seat_detail_analysis.png")
    return f'{output_dir}/seat_detail_analysis.png'


def visualize_interval_distribution(results, output_dir='/mnt/agents/output/OMNI-HUB/core'):
    """音程分布分析"""
    orchestra = results['orchestra']
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 各声部旋律音程分布
    ax1 = axes[0, 0]
    all_intervals = []
    for lid, seat in orchestra.seats.items():
        intervals = seat.get_melodic_intervals()
        all_intervals.extend(intervals)
        if intervals:
            ax1.hist([i % 12 for i in intervals], bins=12, alpha=0.5, 
                    label=LINE_NAMES[lid], color=COLORS.get(lid))
    
    ax1.set_xlabel('Interval Class (semitones)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Melodic Interval Distribution by Voice', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=7, ncol=3)
    ax1.grid(True, alpha=0.3)
    
    # 2. 协和度分类饼图
    ax2 = axes[0, 1]
    consonance_counts = {ct: 0 for ct in ConsonanceType}
    for h in orchestra.harmony_history:
        for interval in h.get('intervals', []):
            ic = interval % 12
            if ic in {0, 7}:
                consonance_counts[ConsonanceType.PERFECT_CONSONANCE] += 1
            elif ic in {3, 4, 8, 9}:
                consonance_counts[ConsonanceType.IMPERFECT_CONSONANCE] += 1
            else:
                consonance_counts[ConsonanceType.DISSONANCE] += 1
    
    sizes = [consonance_counts[ConsonanceType.PERFECT_CONSONANCE],
             consonance_counts[ConsonanceType.IMPERFECT_CONSONANCE],
             consonance_counts[ConsonanceType.DISSONANCE]]
    labels = ['Perfect\n(0, 7)', 'Imperfect\n(3, 4, 8, 9)', 'Dissonant\n(other)']
    colors_pie = ['#2E7D32', '#F9A825', '#C62828']
    
    ax2.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
            startangle=90, textprops={'fontsize': 9})
    ax2.set_title('Harmonic Consonance Distribution', fontsize=11, fontweight='bold')
    
    # 3. 违规时间线
    ax3 = axes[1, 0]
    violations = results['violations']
    if violations:
        v_types = ['parallel_fifth', 'parallel_octave', 'unison']
        v_colors = {'parallel_fifth': 'red', 'parallel_octave': 'orange', 'unison': 'purple'}
        v_labels = {'parallel_fifth': 'Parallel 5th', 'parallel_octave': 'Parallel 8ve', 'unison': 'Unison'}
        
        for vtype in v_types:
            times = [v['time'] for v in violations if v['type'] == vtype]
            y_vals = [1] * len(times)
            ax3.scatter(times, y_vals, c=v_colors[vtype], label=v_labels[vtype], 
                       s=50, alpha=0.7, marker='x')
    
    ax3.set_xlabel('Time (beats)')
    ax3.set_ylabel('Violation')
    ax3.set_title('Counterpoint Violations Timeline', fontsize=11, fontweight='bold')
    ax3.set_xlim(0, results['n_beats'])
    ax3.set_ylim(0.5, 1.5)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 声部独立性雷达图（简化为柱状图）
    ax4 = axes[1, 1]
    
    # 计算各声部的独立特征
    metrics = {}
    for lid, seat in orchestra.seats.items():
        intervals = seat.get_melodic_intervals()
        dirs = seat.direction_history
        
        # 旋律多样性
        if intervals:
            unique_intervals = len(set(i % 12 for i in intervals))
            interval_div = unique_intervals / 12.0
        else:
            interval_div = 0
        
        # 方向变化率
        if len(dirs) > 1:
            changes = sum(1 for i in range(1, len(dirs)) if dirs[i] != dirs[i-1])
            dir_chg_rate = changes / (len(dirs) - 1)
        else:
            dir_chg_rate = 0
        
        # 休止比例
        rest_ratio = seat.get_rest_ratio()
        
        # 平均音程大小
        avg_interval = np.mean(intervals) if intervals else 0
        norm_interval = min(1.0, avg_interval / 12.0)
        
        metrics[lid] = {
            'interval_diversity': interval_div,
            'direction_changes': dir_chg_rate,
            'rest_ratio': rest_ratio,
            'avg_interval': norm_interval,
        }
    
    metric_names = ['interval_diversity', 'direction_changes', 'rest_ratio', 'avg_interval']
    metric_labels = ['Interval\nDiversity', 'Direction\nChanges', 'Rest\nRatio', 'Avg\nInterval']
    x = np.arange(len(metric_names))
    width = 0.07
    line_ids = list(orchestra.seats.keys())
    
    for i, lid in enumerate(line_ids):
        values = [metrics[lid][m] for m in metric_names]
        ax4.bar(x + i * width, values, width, label=LINE_NAMES[lid], 
               color=COLORS.get(lid), alpha=0.8)
    
    ax4.set_xlabel('Metric')
    ax4.set_ylabel('Score')
    ax4.set_title('Voice Independence Metrics', fontsize=11, fontweight='bold')
    ax4.set_xticks(x + width * 5)
    ax4.set_xticklabels(metric_labels, fontsize=8)
    ax4.legend(fontsize=6, ncol=4)
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout(pad=2.0)
    plt.savefig(f'{output_dir}/interval_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"[可视化] 已保存: {output_dir}/interval_distribution.png")
    return f'{output_dir}/interval_distribution.png'


def print_experiment_report(results):
    """打印详细实验报告"""
    logger.info("\n" + "=" * 80)
    logger.info("OMNI-HUB v4.0 — COUNTERPOINT ARCHITECTURE EXPERIMENT REPORT")
    logger.info("=" * 80)
    
    summary = results['summary']
    richness = summary['richness']
    
    logger.info(f"\n{'GENERAL STATISTICS':=^80}")
    logger.info(f"  Total Beats:          {results['n_beats']}")
    logger.info(f"  Beat Resolution:      {results['beat_resolution']}")
    logger.info(f"  Total Seats:          {summary['n_seats']}")
    logger.info(f"  Voice Independence:   {summary['independence_score']:.4f} (0-1, higher=more independent)")
    logger.info(f"  Overall Richness:     {richness['overall']:.4f} (0-1, higher=more rich)")
    
    logger.info(f"\n{'VIOLATION DETECTION (Counterpoint Rules)':=^80}")
    logger.info(f"  Total Violations:     {summary['total_violations']}")
    logger.info(f"  Parallel Fifths:      {summary['parallel_fifths']}   [RULE: FORBIDDEN]")
    logger.info(f"  Parallel Octaves:     {summary['parallel_octaves']}  [RULE: FORBIDDEN]")
    logger.info(f"  Unisons:              {summary['unisons']}           [RULE: FORBIDDEN]")
    
    if results['violations']:
        logger.info(f"\n  Detailed Violations:")
        for v in results['violations'][:10]:
            print(f"    t={v['time']:.1f}: {v['type']} between {v['lines'][0]} and {v['lines'][1]} "
                  f"(pitches: {v['pitches']})")
        if len(results['violations']) > 10:
            logger.info(f"    ... and {len(results['violations']) - 10} more")
    
    logger.info(f"\n{'RICHNESS METRICS':=^80}")
    logger.info(f"  Interval Richness:        {richness['interval_richness']:.4f}")
    logger.info(f"  Consonance Variance:      {richness['consonance_variance']:.4f}")
    logger.info(f"  Activity Variance:        {richness['activity_variance']:.4f}")
    logger.info(f"  Silence Art (qgl):        {richness['silence_art']:.4f}")
    
    logger.info(f"\n{'QGL SILENT BEAT ANALYSIS':=^80}")
    logger.info(f"  qgl Rest Ratio:           {results['qgl_rest_ratio']:.4f}")
    logger.info(f"  Expected (design target): 0.70-0.90")
    logger.info(f"  Status:                   {'PASS' if 0.5 <= results['qgl_rest_ratio'] <= 0.95 else 'REVIEW'}")
    logger.info(f"  Note: qgl's silence is not 'not working' but 'working through silence'")
    
    logger.info(f"\n{'PER-SEAT STATISTICS':=^80}")
    print(f"  {'Line':<8} {'Seat':<22} {'Type':<12} {'Notes':>6} {'Rests':>6} {'Rest%':>6} "
          f"{'Pitch':>8} {'AvgInt':>6} {'MaxInt':>6} {'DirChg':>6}")
    logger.info(f"  {'-'*96}")
    
    stats = summary['seat_stats']
    for lid in LINE_NAMES.keys():
        if lid in stats:
            s = stats[lid]
            pitch_range = f"{s['pitch_low']}-{s['pitch_high']}" if s['pitch_low'] else "N/A"
            print(f"  {lid:<8} {s['seat_name']:<22} {s['voice_type']:<12} "
                  f"{s['n_notes']:>6} {s['n_rests']:>6} {s['rest_ratio']:>6.2f} "
                  f"{pitch_range:>8} {s['avg_interval']:>6.1f} {s['max_interval']:>6} {s['direction_changes']:>6}")
    
    logger.info(f"\n{'COUNTERPOINT RULES (Musical -> Architectural)':=^80}")
    logger.info(f"  1. No Parallel Fifths/Octaves  -> No inter-line complete synchronization")
    logger.info(f"  2. Contrary Motion Preferred   -> Inter-line differential movement")
    logger.info(f"  3. Voice Crossing Allowed      -> High-SI lines may temporarily go below low-SI lines")
    logger.info(f"  4. Consonance Classification   -> Perfect / Imperfect / Dissonant")
    logger.info(f"  5. Resolution Rule             -> Tension -> Relaxation tendency")
    logger.info(f"  6. Art of Rest                 -> qgl's silence is negative space")
    
    logger.info(f"\n{'='*80}")
    logger.info("Experiment completed successfully.")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    print("=" * 80)
    print("OMNI-HUB v4.0 — Counterpoint Seat Architecture Experiment")
    print("=" * 80)
    
    # 运行实验
    results = run_counterpoint_experiment(n_beats=100, beat_resolution=0.5)
    
    # 打印报告
    print_experiment_report(results)
    
    # 生成可视化
    print("[可视化] 生成图表...")
    visualize_polyphony(results)
    visualize_seat_detail(results)
    visualize_interval_distribution(results)
    
    print("\n[完成] 所有实验和可视化已生成!")
    print("输出目录: /mnt/agents/output/OMNI-HUB/core/")
