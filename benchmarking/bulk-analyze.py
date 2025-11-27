# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
import statistics
import json
from pathlib import Path

def main() -> None:
    log_dir = Path("logs")
    individual_results_by_model = {}
    for file in log_dir.glob("*.json"):
        with file.open() as f:
            data = json.load(f)
            if data["thinking"]:
                data["model"] += "-thinking"
            if data["model"] not in individual_results_by_model:
                individual_results_by_model[data["model"]] = []

            individual_results_by_model[data["model"]].append({
                                                                  "created_at": data["created_at"],
                                                                  "total_duration_ns": data["total_duration"],
                                                                  "load_duration_ns": data["load_duration"],
                                                                  "prompt_processing_duration_ns": data["prompt_eval_duration"],
                                                                  "response_generation_duration_ns": data["eval_duration"],
                                                                  "response_token_count": data["eval_count"],
                                                                  "prompt_token_count": data["prompt_eval_count"]
                                                              })

    # now, we get to process bulk
    overview_models = {}
    for model in individual_results_by_model.keys():
        overview_models[model] = {}
        # get statistics
        # avg, min, max, stdev for all key metrics
        metrics = [
            "total_duration_ns",
            "load_duration_ns",
            "prompt_processing_duration_ns",
            "response_generation_duration_ns",
            "response_token_count",
            "prompt_token_count"
        ]
        for metric in metrics:
            values = [entry[metric] for entry in individual_results_by_model[model]]
            overview_models[model][metric] = {
                "avg": statistics.mean(values),
                "median": statistics.median(values),
                "25th_percentile": statistics.quantiles(values, n=4)[0],
                "75th_percentile": statistics.quantiles(values, n=4)[2],
                "90th_percentile": statistics.quantiles(values, n=10)[8],
                "99th_percentile": statistics.quantiles(values, n=100)[98],
                "min": min(values),
                "max": max(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0
            }
        overview_models[model]["total_runs"] = len(individual_results_by_model[model])

    with open("results.json", "w") as f:
        json.dump({
                      "overview": {
                        "total_runs": sum(len(v) for v in individual_results_by_model.values()),
                        "total_duration_ns": sum(
                            entry["total_duration_ns"]
                            for entries in individual_results_by_model.values()
                            for entry in entries
                        ),
                        "models_evaluated": list(individual_results_by_model.keys()),
                        "tokens_processed": {
                            "prompt_tokens": sum(
                                entry["prompt_token_count"]
                                for entries in individual_results_by_model.values()
                                for entry in entries
                            ),
                            "response_tokens": sum(
                                entry["response_token_count"]
                                for entries in individual_results_by_model.values()
                                for entry in entries
                            )
                        },
                        "characters_processed": {
                            "prompt_characters": sum(
                                entry["prompt_token_count"] * 4
                                for entries in individual_results_by_model.values()
                                for entry in entries
                            ),
                            "response_characters": sum(
                                entry["response_token_count"] * 4
                                for entries in individual_results_by_model.values()
                                for entry in entries
                            )
                        }
                      },
                      "model_results": overview_models,
                      "individual": individual_results_by_model
                  }, f, indent=2)

if __name__ == "__main__":
    main()
