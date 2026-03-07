"""評価JSONの横断分析スクリプト"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import math

SCORE_AXES = [
    "concept_novelty",
    "core_mechanic_novelty",
    "mechanic_intuitiveness",
    "feasibility",
    "theme_concept_relevance",
    "theme_art_style_relevance",
    "design_coherence",
    "art_style_concept_coherence",
    "mechanic_art_style_coherence",
    "first_impression_hook",
    "elevator_pitch_clarity",
    "game_cycle_quality",
    "thematic_mechanic_unity",
    "game_feel",
    "risk_reward_depth",
    "overall_fun",
]

def load_evaluations(output_dirs: list[str]) -> list[dict]:
    evals = []
    for dir_path in output_dirs:
        d = Path(dir_path)
        for eval_file in sorted(d.glob("pitch_*/evaluation.json")):
            with open(eval_file) as f:
                data = json.load(f)
            # スコアが含まれているか確認
            if "overall_fun" not in data or data.get("overall_fun", 0) == 0:
                print(f"  [SKIP] {eval_file} (スコアなし)", file=sys.stderr)
                continue
            # テーマ情報をディレクトリ名から抽出
            topic = d.name.split("_", 2)[-1] if "_" in d.name else d.name
            data["_topic"] = topic
            data["_path"] = str(eval_file)
            evals.append(data)
    return evals

def compute_stats(evals: list[dict]) -> dict:
    axis_values = defaultdict(list)
    for ev in evals:
        for axis in SCORE_AXES:
            val = ev.get(axis, 0)
            if isinstance(val, (int, float)) and val > 0:
                axis_values[axis].append(val)

    stats = {}
    for axis in SCORE_AXES:
        vals = axis_values[axis]
        if not vals:
            stats[axis] = {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals) if len(vals) > 1 else 0
        std = math.sqrt(var)
        stats[axis] = {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": min(vals),
            "max": max(vals),
            "count": len(vals),
        }
    return stats

def compute_correlation(evals: list[dict]) -> list[tuple[str, str, float]]:
    """軸間のピアソン相関係数"""
    correlations = []
    for i, ax1 in enumerate(SCORE_AXES):
        for ax2 in SCORE_AXES[i+1:]:
            pairs = []
            for ev in evals:
                v1, v2 = ev.get(ax1, 0), ev.get(ax2, 0)
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)) and v1 > 0 and v2 > 0:
                    pairs.append((v1, v2))
            if len(pairs) < 3:
                continue
            x = [p[0] for p in pairs]
            y = [p[1] for p in pairs]
            mx, my = sum(x)/len(x), sum(y)/len(y)
            sx = math.sqrt(sum((xi-mx)**2 for xi in x)/len(x))
            sy = math.sqrt(sum((yi-my)**2 for yi in y)/len(y))
            if sx == 0 or sy == 0:
                continue
            cov = sum((xi-mx)*(yi-my) for xi, yi in zip(x, y)) / len(x)
            r = cov / (sx * sy)
            correlations.append((ax1, ax2, round(r, 3)))
    return sorted(correlations, key=lambda x: abs(x[2]), reverse=True)

def topic_analysis(evals: list[dict]) -> dict:
    topic_scores = defaultdict(list)
    for ev in evals:
        topic = ev["_topic"]
        scores = [ev.get(ax, 0) for ax in SCORE_AXES if isinstance(ev.get(ax, 0), (int, float)) and ev.get(ax, 0) > 0]
        if scores:
            topic_scores[topic].append({
                "title": ev.get("title", "無題"),
                "mean": round(sum(scores)/len(scores), 2),
                "overall_fun": ev.get("overall_fun", 0),
            })
    return dict(topic_scores)


def main():
    # 今回の8テーマの出力ディレクトリを検索
    output_root = Path("output")
    target_dirs = []
    target_topics = [
        "お題__孤独_",
        "猫カフェ経営シミュレーション",
        "時間が逆行する世界",
        "音だけで遊ぶゲーム",
        "地下迷宮の料理人",
        "植物 vs 機械",
        "100人同時かくれんぼ",
        "夢の中の郵便配達",
    ]

    for d in sorted(output_root.iterdir()):
        if d.is_dir():
            name = d.name
            for topic in target_topics:
                if topic in name and name.startswith("20260307"):
                    target_dirs.append(str(d))
                    break

    print(f"対象ディレクトリ: {len(target_dirs)}", file=sys.stderr)
    for d in target_dirs:
        print(f"  {d}", file=sys.stderr)

    evals = load_evaluations(target_dirs)
    print(f"有効な評価データ: {len(evals)} 件", file=sys.stderr)

    if not evals:
        print("評価データがありません", file=sys.stderr)
        sys.exit(1)

    # === 分析結果出力 ===
    result = {}

    # 1. スコア分布
    stats = compute_stats(evals)
    result["score_distribution"] = stats

    # 2. 軸間相関
    correlations = compute_correlation(evals)
    result["high_correlations"] = [
        {"axis1": ax1, "axis2": ax2, "r": r}
        for ax1, ax2, r in correlations[:15]
    ]

    # 3. テーマ別傾向
    result["topic_analysis"] = topic_analysis(evals)

    # 4. 全体サマリー
    all_means = [s["mean"] for s in stats.values() if s["count"] > 0]
    all_stds = [s["std"] for s in stats.values() if s["count"] > 0]
    result["overall"] = {
        "total_pitches": len(evals),
        "grand_mean": round(sum(all_means)/len(all_means), 2) if all_means else 0,
        "avg_std": round(sum(all_stds)/len(all_stds), 2) if all_stds else 0,
        "axes_with_low_discrimination": [
            ax for ax, s in stats.items() if s["std"] < 0.5 and s["count"] > 0
        ],
        "axes_with_high_mean": [
            ax for ax, s in stats.items() if s["mean"] > 7.0 and s["count"] > 0
        ],
        "axes_with_low_mean": [
            ax for ax, s in stats.items() if s["mean"] < 4.0 and s["count"] > 0
        ],
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
