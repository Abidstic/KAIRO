import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
from models import Manager
from utils.bots import is_bot

class AdvancedEvaluation:
    """
    Comprehensive evaluation system for reviewer recommendation algorithms.
    Provides detailed metrics suitable for thesis-level analysis.
    """
    
    def __init__(self, manager: Manager):
        self.manager = manager
        self.ground_truth = self._build_ground_truth()
        
    def _build_ground_truth(self) -> Dict[int, set]:
        """Build ground truth from actual reviews."""
        ground_truth = {}
        for pr in self.manager.pull_requests_list:
            reviewers = {
                review.reviewer_username
                for review in self.manager.reviews_list
                if review.pull_number == pr.number
                and review.reviewer_username != pr.developer_username
                and not is_bot(review.reviewer_username)
            }
            if reviewers:
                ground_truth[pr.number] = reviewers
        return ground_truth
    
    def evaluate_algorithms(self, algorithm_results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Evaluate multiple algorithms and return comprehensive metrics
        
        Args:
            algorithm_results: Dict with algorithm_name -> {pr_number: {dev: score}}
            
        Returns:
            Dict with detailed evaluation metrics for each algorithm
        """
        print(f"\n{'='*70}")
        print("ADVANCED EVALUATION RESULTS")
        print(f"{'='*70}")
        
        if not algorithm_results:
            print("No algorithm results to evaluate.")
            return {}
        
        print(f"Ground truth: {len(self.ground_truth)} PRs with reviews")
        
        if not self.ground_truth:
            print("No ground truth available for evaluation.")
            return {}
        
        detailed_metrics = {}
        
        print(f"\n{'='*50}")
        print("ALGORITHM PERFORMANCE ANALYSIS")
        print(f"{'='*50}")
        
        for algo_name, algo_result in algorithm_results.items():
            print(f"\n--- {algo_name} Analysis ---")
            
            if not algo_result:
                print(f"  No results from {algo_name}")
                continue
            
            metrics = self._calculate_algorithm_metrics(algo_name, algo_result)
            detailed_metrics[algo_name] = metrics
            
            self._display_algorithm_analysis(algo_name, metrics, algo_result)
        
        if len(detailed_metrics) > 1:
            self._display_comparative_analysis(detailed_metrics)
            
            self._perform_statistical_testing(detailed_metrics)
        
        self._save_evaluation_results(detailed_metrics)
        
        return detailed_metrics
    
    def _calculate_algorithm_metrics(self, algo_name: str, algo_result: Dict) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a single algorithm"""
        
        total_prs_analyzed = len(algo_result)
        developers_recommended = len(set(dev for scores in algo_result.values() for dev in scores.keys()))
        
        all_scores = [score for scores in algo_result.values() for score in scores.values()]
        score_stats = {}
        if all_scores:
            score_stats = {
                'mean': np.mean(all_scores),
                'median': np.median(all_scores),
                'std': np.std(all_scores),
                'min': np.min(all_scores),
                'max': np.max(all_scores),
                'range': np.max(all_scores) - np.min(all_scores)
            }
        
        per_pr_metrics = {
            'mrr_scores': [],
            'ap_scores': [],
            'dcg_scores': [],
            'ndcg_scores': [],
            'precision_at_1': [],
            'precision_at_3': [],
            'precision_at_5': [],
            'precision_at_10': [],
            'recall_at_1': [],
            'recall_at_3': [],
            'recall_at_5': [],
            'recall_at_10': [],
            'f1_at_1': [],
            'f1_at_3': [],
            'f1_at_5': [],
            'f1_at_10': [],
            'hit_at_1': [],
            'hit_at_3': [],
            'hit_at_5': [],
            'hit_at_10': []
        }
        
        hits_at_k = {1: 0, 3: 0, 5: 0, 10: 0}
        reciprocal_ranks = []
        average_precisions = []
        dcg_scores = []
        ndcg_scores = []
        valid_prs = 0
        
        k_values = [1, 3, 5, 10]
        precision_at_k = {k: [] for k in k_values}
        recall_at_k = {k: [] for k in k_values}
        f1_at_k = {k: [] for k in k_values}
        ap_at_k = {k: [] for k in k_values}
        
        for pr_num, actual_reviewers in self.ground_truth.items():
            sorted_recs = sorted(
                algo_result.get(pr_num, {}).items(), key=lambda x: x[1], reverse=True
            )

            for k in k_values:
                top_k = [rec[0] for rec in sorted_recs[:k]]
                
                num_correct = len(set(top_k) & actual_reviewers)
                
                precision = num_correct / k if k > 0 else 0
                precision_at_k[k].append(precision)
                per_pr_metrics[f'precision_at_{k}'].append(precision)
                
                recall = num_correct / len(actual_reviewers) if actual_reviewers else 0
                recall_at_k[k].append(recall)
                per_pr_metrics[f'recall_at_{k}'].append(recall)
                
                if precision + recall > 0:
                    f1 = 2 * (precision * recall) / (precision + recall)
                else:
                    f1 = 0
                f1_at_k[k].append(f1)
                per_pr_metrics[f'f1_at_{k}'].append(f1)
                
                hit = 1 if num_correct > 0 else 0
                per_pr_metrics[f'hit_at_{k}'].append(hit)
                if hit:
                    hits_at_k[k] += 1
            
            mrr_for_this_pr = 0.0
            for rank, (rec_reviewer, _) in enumerate(sorted_recs, 1):
                if rec_reviewer in actual_reviewers:
                    mrr_for_this_pr = 1.0 / rank
                    break
            reciprocal_ranks.append(mrr_for_this_pr)
            per_pr_metrics['mrr_scores'].append(mrr_for_this_pr)
            
            relevant_ranks = []
            for rank, (rec_reviewer, _) in enumerate(sorted_recs, 1):
                if rec_reviewer in actual_reviewers:
                    relevant_ranks.append(rank)
            
            if relevant_ranks:
                precisions = []
                for i, rank in enumerate(relevant_ranks):
                    precision_at_rank = (i + 1) / rank
                    precisions.append(precision_at_rank)
                ap = np.mean(precisions)
            else:
                ap = 0.0
            average_precisions.append(ap)
            per_pr_metrics['ap_scores'].append(ap)
            
            for k in k_values:
                hits_so_far = 0
                ap_k_sum = 0.0
                for i, (rec_reviewer, _) in enumerate(sorted_recs[:k], 1):
                    if rec_reviewer in actual_reviewers:
                        hits_so_far += 1
                        ap_k_sum += hits_so_far / i
                ap_k = ap_k_sum / len(actual_reviewers)
                ap_at_k[k].append(ap_k)
                per_pr_metrics.setdefault(f'ap_at_{k}', []).append(ap_k)
            
            dcg = 0.0
            for rank, (rec_reviewer, score) in enumerate(sorted_recs[:10], 1):
                relevance = 1.0 if rec_reviewer in actual_reviewers else 0.0
                dcg += relevance / np.log2(rank + 1)
            dcg_scores.append(dcg)
            per_pr_metrics['dcg_scores'].append(dcg)
            
            num_relevant = min(len(actual_reviewers), 10)
            if num_relevant > 0:
                idcg = sum(1.0 / np.log2(rank + 1) for rank in range(1, num_relevant + 1))
                ndcg = dcg / idcg if idcg > 0 else 0
            else:
                ndcg = 0
            ndcg_scores.append(ndcg)
            per_pr_metrics['ndcg_scores'].append(ndcg)
            
            valid_prs += 1
        
        stability_metrics = {}
        if per_pr_metrics['mrr_scores']:
            mrr_scores = np.array(per_pr_metrics['mrr_scores'])
            stability_metrics = {
                'mrr': {
                    'q1': np.percentile(mrr_scores, 25),
                    'q3': np.percentile(mrr_scores, 75),
                    'iqr': np.percentile(mrr_scores, 75) - np.percentile(mrr_scores, 25),
                    'median': np.median(mrr_scores),
                    'std': np.std(mrr_scores),
                    'cv': np.std(mrr_scores) / np.mean(mrr_scores) if np.mean(mrr_scores) > 0 else 0
                }
            }
            
            for metric_name in ['ap_scores', 'precision_at_5', 'recall_at_5']:
                if per_pr_metrics[metric_name]:
                    scores = np.array(per_pr_metrics[metric_name])
                    stability_metrics[metric_name] = {
                        'q1': np.percentile(scores, 25),
                        'q3': np.percentile(scores, 75),
                        'iqr': np.percentile(scores, 75) - np.percentile(scores, 25),
                        'median': np.median(scores),
                        'std': np.std(scores)
                    }
        
        metrics = {
            'basic_stats': {
                'total_prs_analyzed': total_prs_analyzed,
                'developers_recommended': developers_recommended,
                'valid_prs': valid_prs,
                'coverage': valid_prs / len(self.ground_truth) if self.ground_truth else 0
            },
            'score_distribution': score_stats,
            'precision_metrics': {},
            'recall_metrics': {},
            'f1_metrics': {},
            'ranking_metrics': {},
            'stability_metrics': stability_metrics,
            'per_pr_scores': per_pr_metrics,
            'other_metrics': {}
        }
        
        if valid_prs > 0:
            for k in k_values:
                metrics['precision_metrics'][f'precision_at_{k}'] = np.mean(precision_at_k[k])
                metrics['precision_metrics'][f'hit_rate_at_{k}'] = hits_at_k[k] / valid_prs
            
            for k in k_values:
                metrics['recall_metrics'][f'recall_at_{k}'] = np.mean(recall_at_k[k])
            
            for k in k_values:
                metrics['f1_metrics'][f'f1_at_{k}'] = np.mean(f1_at_k[k])
            
            metrics['ranking_metrics']['mrr'] = np.mean(reciprocal_ranks)
            metrics['ranking_metrics']['map'] = np.mean(average_precisions)
            for k in k_values:
                metrics['ranking_metrics'][f'map_at_{k}'] = np.mean(ap_at_k[k])
            metrics['ranking_metrics']['avg_dcg'] = np.mean(dcg_scores)
            metrics['ranking_metrics']['avg_ndcg'] = np.mean(ndcg_scores)
            
            metrics['other_metrics']['successful_recommendations'] = sum(1 for rr in reciprocal_ranks if rr > 0)
            metrics['other_metrics']['recommendation_success_rate'] = metrics['other_metrics']['successful_recommendations'] / valid_prs
        
        return metrics
    
    def _display_algorithm_analysis(self, algo_name: str, metrics: Dict, algo_result: Dict):
        """Display detailed analysis for a single algorithm"""
        
        basic = metrics['basic_stats']
        precision = metrics['precision_metrics']
        recall = metrics['recall_metrics']
        f1 = metrics['f1_metrics']
        ranking = metrics['ranking_metrics']
        stability = metrics['stability_metrics']
        scores = metrics['score_distribution']
        other = metrics['other_metrics']
        
        print(f"\n  Basic statistics:")
        print(f"    PRs analyzed: {basic['total_prs_analyzed']}")
        print(f"    Valid PRs: {basic['valid_prs']}")
        print(f"    Coverage: {basic['coverage']:.4f}")
        print(f"    Unique developers: {basic['developers_recommended']}")
        
        if scores:
            print(f"\n  Score statistics:")
            print(f"    Mean: {scores['mean']:.4f}")
            print(f"    Median: {scores['median']:.4f}")
            print(f"    Std Dev: {scores['std']:.4f}")
            print(f"    Range: [{scores['min']:.4f}, {scores['max']:.4f}]")
        
        if precision and recall and f1:
            print(f"\n  📊 METRICS:")
            print(f"  {'k':<5} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Hit Rate':<12}")
            print(f"  {'-'*53}")
            for k in [1, 3, 5, 10]:
                p = precision.get(f'precision_at_{k}', 0)
                r = recall.get(f'recall_at_{k}', 0)
                f = f1.get(f'f1_at_{k}', 0)
                h = precision.get(f'hit_rate_at_{k}', 0)
                print(f"  {k:<5} {p:<12.4f} {r:<12.4f} {f:<12.4f} {h:<12.4f}")
        
        if ranking:
            print(f"\n  Ranking metrics:")
            if 'mrr' in ranking:
                print(f"    MRR: {ranking['mrr']:.4f}")
            if 'map' in ranking:
                print(f"    MAP: {ranking['map']:.4f}")
            for k in [1, 3, 5, 10]:
                if f'map_at_{k}' in ranking:
                    print(f"    MAP@{k}: {ranking[f'map_at_{k}']:.4f}")
            if 'avg_dcg' in ranking:
                print(f"    Avg DCG@10: {ranking['avg_dcg']:.4f}")
            if 'avg_ndcg' in ranking:
                print(f"    Avg NDCG@10: {ranking['avg_ndcg']:.4f}")
        
        if stability and 'mrr' in stability:
            print(f"\n  Stability metrics (MRR):")
            mrr_stability = stability['mrr']
            print(f"    Median: {mrr_stability['median']:.4f}")
            print(f"    Q1: {mrr_stability['q1']:.4f}")
            print(f"    Q3: {mrr_stability['q3']:.4f}")
            print(f"    IQR: {mrr_stability['iqr']:.4f}")
            print(f"    Std Dev: {mrr_stability['std']:.4f}")
            print(f"    CV: {mrr_stability['cv']:.4f}")
        
        if other:
            print(f"\n  Success metrics:")
            if 'recommendation_success_rate' in other:
                print(f"    Success Rate: {other['recommendation_success_rate']:.4f}")
    
    def _display_comparative_analysis(self, detailed_metrics: Dict):
        """Display comprehensive comparison between algorithms"""
        
        print(f"\n{'='*80}")
        print("DETAILED COMPARISON TABLE (CORRECTED)")
        print(f"{'='*80}")
        
        algorithms = list(detailed_metrics.keys())
        
        print(f"\n📊 Precision, Recall, F1-Score:")
        header = f"{'Algo':<12}{'P@1':<8}{'R@1':<8}{'F1@1':<8}{'P@5':<8}{'R@5':<8}{'F1@5':<8}{'MRR':<8}{'MAP':<8}"
        print(header)
        print("-" * len(header))
        
        for algo_name in algorithms:
            metrics = detailed_metrics[algo_name]
            p = metrics['precision_metrics']
            r = metrics['recall_metrics']
            f = metrics['f1_metrics']
            rank = metrics['ranking_metrics']
            
            row = f"{algo_name:<12}"
            row += f"{p.get('precision_at_1', 0):<8.4f}"
            row += f"{r.get('recall_at_1', 0):<8.4f}"
            row += f"{f.get('f1_at_1', 0):<8.4f}"
            row += f"{p.get('precision_at_5', 0):<8.4f}"
            row += f"{r.get('recall_at_5', 0):<8.4f}"
            row += f"{f.get('f1_at_5', 0):<8.4f}"
            row += f"{rank.get('mrr', 0):<8.4f}"
            row += f"{rank.get('map', 0):<8.4f}"
            print(row)
        
        print(f"\n📈 Stability Analysis (MRR):")
        header = f"{'Algo':<12}{'Median':<10}{'IQR':<10}{'Std Dev':<10}{'CV':<10}"
        print(header)
        print("-" * len(header))
        
        for algo_name in algorithms:
            metrics = detailed_metrics[algo_name]
            if 'stability_metrics' in metrics and 'mrr' in metrics['stability_metrics']:
                stab = metrics['stability_metrics']['mrr']
                row = f"{algo_name:<12}"
                row += f"{stab['median']:<10.4f}"
                row += f"{stab['iqr']:<10.4f}"
                row += f"{stab['std']:<10.4f}"
                row += f"{stab['cv']:<10.4f}"
                print(row)
        
        self._display_rankings(detailed_metrics)
        
        self._display_performance_insights(detailed_metrics)
    
    def _display_rankings(self, detailed_metrics: Dict):
        """Display algorithm rankings by different metrics"""
        print(f"\n{'='*40}")
        print("ALGORITHM RANKINGS")
        print(f"{'='*40}")
        
        ranking_metrics = [
            ('MRR', 'ranking_metrics', 'mrr'),
            ('MAP', 'ranking_metrics', 'map'),
            ('MAP@3', 'ranking_metrics', 'map_at_3'),
            ('Precision@5', 'precision_metrics', 'precision_at_5'),
            ('Recall@5', 'recall_metrics', 'recall_at_5'),
            ('F1@5', 'f1_metrics', 'f1_at_5'),
            ('NDCG@10', 'ranking_metrics', 'avg_ndcg')
        ]
        
        for metric_name, category, key in ranking_metrics:
            print(f"\nRanking by {metric_name}:")
            ranked = sorted(
                detailed_metrics.items(), 
                key=lambda x: x[1].get(category, {}).get(key, 0), 
                reverse=True
            )
            for rank, (algo_name, metrics) in enumerate(ranked, 1):
                value = metrics.get(category, {}).get(key, 0)
                print(f"  {rank}. {algo_name}: {value:.4f}")
    
    def _display_performance_insights(self, detailed_metrics: Dict):
        """Display performance insights and best performers"""
        print(f"\n{'='*40}")
        print("PERFORMANCE INSIGHTS")
        print(f"{'='*40}")
        
        best_mrr = max(detailed_metrics.items(), key=lambda x: x[1]['ranking_metrics'].get('mrr', 0))
        best_map = max(detailed_metrics.items(), key=lambda x: x[1]['ranking_metrics'].get('map', 0))
        best_f1_5 = max(detailed_metrics.items(), key=lambda x: x[1]['f1_metrics'].get('f1_at_5', 0))
        
        stable_algos = [
            (name, metrics['stability_metrics']['mrr']['iqr'])
            for name, metrics in detailed_metrics.items()
            if 'stability_metrics' in metrics and 'mrr' in metrics['stability_metrics']
        ]
        if stable_algos:
            most_stable = min(stable_algos, key=lambda x: x[1])
        
        print(f"\n🏆 Best Performers:")
        print(f"  Best MRR: {best_mrr[0]} ({best_mrr[1]['ranking_metrics'].get('mrr', 0):.4f})")
        print(f"  Best MAP: {best_map[0]} ({best_map[1]['ranking_metrics'].get('map', 0):.4f})")
        print(f"  Best F1@5: {best_f1_5[0]} ({best_f1_5[1]['f1_metrics'].get('f1_at_5', 0):.4f})")
        if stable_algos:
            print(f"  Most Stable: {most_stable[0]} (IQR: {most_stable[1]:.4f})")
        
        mrr_scores = [metrics['ranking_metrics'].get('mrr', 0) for metrics in detailed_metrics.values()]
        if len(mrr_scores) > 1:
            mrr_range = max(mrr_scores) - min(mrr_scores)
            max_mrr = max(mrr_scores)
            if max_mrr > 0:
                print(f"\n📊 Performance Spread:")
                print(f"  MRR Range: {mrr_range:.4f}")
                print(f"  Relative Difference: {(mrr_range/max_mrr*100):.1f}%")
    
    def _perform_statistical_testing(self, detailed_metrics: Dict):
        """
        Perform statistical significance testing
        
        Uses Friedman test + post-hoc Nemenyi test
        """
        print(f"\n{'='*60}")
        print("STATISTICAL SIGNIFICANCE TESTING")
        print(f"{'='*60}")
        
        try:
            from scipy import stats
            from scipy.stats import friedmanchisquare
            
            algorithms = list(detailed_metrics.keys())
            per_pr_scores = {}
            
            min_length = float('inf')
            for algo_name in algorithms:
                if 'per_pr_scores' in detailed_metrics[algo_name]:
                    scores = detailed_metrics[algo_name]['per_pr_scores']['mrr_scores']
                    per_pr_scores[algo_name] = scores
                    min_length = min(min_length, len(scores))
            
            if len(per_pr_scores) < 2:
                print("⚠️ Need at least 2 algorithms for statistical testing")
                return
            
            aligned_scores = []
            for algo_name in algorithms:
                if algo_name in per_pr_scores:
                    aligned_scores.append(per_pr_scores[algo_name][:min_length])
            
            if len(aligned_scores) >= 2 and min_length >= 10:
                statistic, p_value = friedmanchisquare(*aligned_scores)
                
                print(f"\n📊 Friedman Test (MRR):")
                print(f"  Chi-square statistic: {statistic:.4f}")
                print(f"  p-value: {p_value:.6f}")
                
                if p_value < 0.05:
                    print(f"  ✅ Significant difference found (p < 0.05)")
                    print(f"  Recommendation: Perform post-hoc Nemenyi test")
                else:
                    print(f"  ❌ No significant difference (p >= 0.05)")
                
                print(f"\n📊 Pairwise Wilcoxon Signed-Rank Tests:")
                for i in range(len(algorithms)):
                    for j in range(i+1, len(algorithms)):
                        algo1 = algorithms[i]
                        algo2 = algorithms[j]
                        
                        if algo1 in per_pr_scores and algo2 in per_pr_scores:
                            scores1 = per_pr_scores[algo1][:min_length]
                            scores2 = per_pr_scores[algo2][:min_length]
                            
                            stat, p = stats.wilcoxon(scores1, scores2)
                            
                            sig = "✅" if p < 0.05 else "❌"
                            print(f"  {algo1} vs {algo2}: p={p:.6f} {sig}")
            
            else:
                print("⚠️ Not enough data for statistical testing")
                print(f"   Need at least 10 PRs, have {min_length}")
                
        except ImportError:
            print("⚠️ scipy not installed - cannot perform statistical tests")
            print("   Install with: pip install scipy")
        except Exception as e:
            print(f"⚠️ Error in statistical testing: {e}")
    
    def _save_evaluation_results(self, detailed_metrics: Dict):
        """Save evaluation results to files for thesis analysis"""
        
        results_dir = "evaluation_results"
        os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.manager.project
        
        metrics_file = f"{results_dir}/{project_name}_advanced_metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            json_metrics = self._convert_numpy_types(detailed_metrics)
            json.dump(json_metrics, f, indent=2)
        
        try:
            import pandas as pd
            
            csv_data = []
            for algo_name, metrics in detailed_metrics.items():
                row = {'Algorithm': algo_name}
                
                row.update({f"basic_{k}": v for k, v in metrics['basic_stats'].items()})
                
                row.update({f"precision_{k}": v for k, v in metrics['precision_metrics'].items()})
                
                row.update({f"recall_{k}": v for k, v in metrics['recall_metrics'].items()})
                
                row.update({f"f1_{k}": v for k, v in metrics['f1_metrics'].items()})
                
                row.update({f"ranking_{k}": v for k, v in metrics['ranking_metrics'].items()})
                
                if metrics['stability_metrics'] and 'mrr' in metrics['stability_metrics']:
                    for stat, value in metrics['stability_metrics']['mrr'].items():
                        row[f'stability_mrr_{stat}'] = value
                
                row.update({f"other_{k}": v for k, v in metrics['other_metrics'].items()})
                
                if metrics['score_distribution']:
                    row.update({f"score_{k}": v for k, v in metrics['score_distribution'].items()})
                
                csv_data.append(row)
            
            df = pd.DataFrame(csv_data)
            csv_file = f"{results_dir}/{project_name}_advanced_summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            
            print(f"\n💾 Results saved:")
            print(f"  Detailed JSON: {metrics_file}")
            print(f"  Summary CSV: {csv_file}")
            
        except ImportError:
            print(f"\n💾 Results saved:")
            print(f"  Detailed JSON: {metrics_file}")
            print("  (CSV export requires pandas - install with: pip install pandas)")
        
        return metrics_file
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to regular Python types for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj


def run_advanced_evaluation(manager: Manager, algorithm_results: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Convenience function to run advanced evaluation
    
    Args:
        manager: The data manager
        algorithm_results: Dict with algorithm_name -> {pr_number: {dev: score}}
        
    Returns:
        Dict with detailed evaluation metrics
        
    Example usage:
        results = run_advanced_evaluation(manager, {
            'CF': cf_results,
            'RF': rf_results,
            'KUREC': kurec_results
        })
    """
    evaluator = AdvancedEvaluation(manager)
    return evaluator.evaluate_algorithms(algorithm_results)