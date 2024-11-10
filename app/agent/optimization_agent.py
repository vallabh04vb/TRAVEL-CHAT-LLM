class OptimizationAgent:
    def optimize_path(self, itinerary, budget):
        # Logic to optimize based on the budget
        optimized_itinerary = []
        total_cost = 0
        taxi_cost_per_segment = 15

        for stop in itinerary:
            if total_cost + taxi_cost_per_segment <= budget:
                stop["transport"] = "taxi"
                total_cost += taxi_cost_per_segment
            else:
                stop["transport"] = "walk"
            optimized_itinerary.append(stop)

        return {"itinerary": optimized_itinerary, "total_cost": total_cost}
