from statistics import mean

import numpy as np
import logging
import streamlit as st
from numpy.ma.extras import average

class Generator:
    def __init__(self, seed=None):
        self.random = np.random.default_rng(seed)

    def erlang_interarrival(self, shape, mean, size=1):
        scale = mean / shape
        return self.random.gamma(shape, scale, size=size)

    def uniform_duration(self, low, high, size=1):
        return self.random.uniform(low, high, size=size)


class AdvertisementGenerator:
    def __init__(self):
        pass

    def generate_ads(self, time, erlang_shape=2, erlang_mean=20, duration_low=2.5, duration_high=3.5, seed=None):
        generator = Generator(seed)
        max_time = time * 60
        ads = []
        current_time = 0

        while True:
            interarrival = generator.erlang_interarrival(erlang_shape, erlang_mean, 1)[0]
            duration = generator.uniform_duration(duration_low, duration_high, 1)[0]
            new_time = current_time + interarrival

            if new_time + duration > max_time:
                break

            ads.append(Advertisement(len(ads), new_time, duration))
            current_time = new_time

        return ads


class Element:
    def __init__(self, index):
        self.index = index

    def __str__(self):
        return f'Element {self.index}'


class Advertisement(Element):
    def __init__(self, index, arrival_time, duration):
        super().__init__(index)
        self.arrival_time = arrival_time
        self.duration = duration

    def __str__(self):
        return f'Ad {self.index} at {self.arrival_time}; Duration: {self.duration}'




class Queue:
    def __init__(self, hours, percent):
        self.hours = hours
        self.percent = percent
        self.breaks = []
        self.ads = []
        self.ads_not_ran = 1

    def do_stats(self):
        total_immediately_added = 0
        total_not_immediately_added = 0
        total_full_addition = 0
        total_partial_addition = 0

        for ad_break in self.breaks:
            total_immediately_added += sum(1 for ad in ad_break.get('ads', []) if ad.get('immediately_added'))
            total_not_immediately_added += sum(1 for ad in ad_break.get('ads', []) if not ad.get('immediately_added'))
            total_full_addition += sum(1 for ad in ad_break.get('ads', []) if ad.get('full_addition'))
            total_partial_addition += sum(1 for ad in ad_break.get('ads', []) if not ad.get('full_addition'))

        return {
            "not_added": self.ads_not_ran,
            "immediately_added": total_immediately_added,
            "not_immediately_added": total_not_immediately_added,
            "full_addition": total_full_addition,
            "partial_addition": total_partial_addition
        }


    def create_breaks(self, num_breaks):
        total_duration = self.hours * 60
        break_duration = (self.hours*self.percent * 60) / num_breaks
        interval_duration = (total_duration - (num_breaks * break_duration)) / (num_breaks + 1)

        self.breaks = [
            {
                "start": interval_duration * (i + 1),
                "end": interval_duration * (i + 1) + break_duration,
                "duration": break_duration,
                "ads": [],
                "current_time": interval_duration * (i + 1),
            }
            for i in range(num_breaks)
        ]

    def add_ad(self, ad):
        remaining_duration = ad.duration
        ad_window_start = ad.arrival_time
        ad_window_end = ad.arrival_time + 4 * 60

        for ad_break in self.breaks:
            proposed_start = ad_break['current_time']
            proposed_end = proposed_start + remaining_duration

            if ad_window_start <= proposed_start < ad_window_end and ad_window_start < proposed_end <= ad_window_end:
                available_time = ad_break['duration'] - sum(a['duration'] for a in ad_break['ads'])

                if available_time > 0:
                    time_to_add = min(remaining_duration, available_time)
                    immediately_added = (ad.arrival_time // 1) == (proposed_start // 1)

                    ad_break['ads'].append({
                        "index": ad.index,
                        "arrival_time": ad.arrival_time,
                        "duration": time_to_add,
                        "full_addition": time_to_add == remaining_duration,
                        "immediately_added": immediately_added,
                    })
                    ad_break['current_time'] += time_to_add
                    self.ads.append(ad)

                    logging.info(
                        f"Ad {ad.index} placed in break starting at {ad_break['start']} for {time_to_add} minutes.")
                    return remaining_duration == time_to_add

            else:
                self.ads_not_ran += 1

        logging.info(f"Ad {ad.index} rejected due to lack of space.")
        return False


class Simulation:
    def __init__(self, num_breaks, price_per_min=300, cost_per_min=10,
                         speaking_time=16, ads_percent=0.1, erlang_shape=2, erlang_mean=20,
                         duration_low=2.5, duration_high=3.5,
                         partially_addition_coefficient=0.9, late_addition_coefficient=0.7,
                         is_fast_run=True):


        self.num_breaks = num_breaks
        self.price_per_min = price_per_min
        self.cost_per_min = cost_per_min
        self.speaking_time = speaking_time
        self.ads_percent = ads_percent
        self.erlang_shape = erlang_shape
        self.erlang_mean = erlang_mean
        self.duration_low = duration_low
        self.duration_high = duration_high
        self.partially_addition_coefficient = partially_addition_coefficient
        self.late_addition_coefficient = late_addition_coefficient
        self.is_fast_run = is_fast_run


        self.initial_cost = 1_000_000
        
        self.seed = None if st.secrets["seed"] == 'random' else st.secrets['seed']

    def run(self, iterations=1):
        stats_keys = ["not_added", "immediately_added", "not_immediately_added", "full_addition", "partial_addition"]
        total_stats = {key: [] for key in stats_keys}
        profits = []

        for _ in range(iterations):
            if self.is_fast_run:
                daily_profit, stats = self.simulate()
                yearly_profit = daily_profit * 365
                yearly_stats = {key: stats[key] * 365 for key in stats_keys}
            else:
                daily_profits = []
                yearly_stats = {key: 0 for key in stats_keys}

                for _ in range(365):
                    daily_profit, stats = self.simulate()
                    daily_profits.append(daily_profit)

                    for key in stats_keys:
                        yearly_stats[key] += stats[key]

                yearly_profit = sum(daily_profits)

            profits.append(yearly_profit)
            for key in stats_keys:
                total_stats[key].append(yearly_stats[key])

        avg_profit = mean(profits)
        avg_stats = {key: mean(values) for key, values in total_stats.items()}
        years_to_profit = (self.initial_cost // avg_profit) + 1 if avg_profit > 0 else float('inf')

        return avg_profit, years_to_profit, avg_stats

    def simulate(self):
        logging.info("Starting simulation.")
        ads = AdvertisementGenerator().generate_ads(self.speaking_time, self.erlang_shape, self.erlang_mean, self.duration_low, self.duration_high, self.seed)
        queue = Queue(hours=self.speaking_time, percent=self.ads_percent)
        queue.create_breaks(self.num_breaks)

        for ad in ads:
            queue.add_ad(ad)

        total_revenue = sum(self.revenue(ad) for ad_break in queue.breaks for ad in ad_break['ads'])
        total_ad_time = sum(ad['duration'] for ad_break in queue.breaks for ad in ad_break['ads'])
        daily_costs = self.speaking_time*60 * self.cost_per_min

        daily_profit = total_revenue - daily_costs
        logging.info(f"Daily Profit: {daily_profit}")

        stats = queue.do_stats()
        return daily_profit, stats

    def revenue(self, ad):
        money = ad['duration'] * self.price_per_min
        if not ad['full_addition']:
            money *= self.partially_addition_coefficient
        if not ad['immediately_added']:
            money *= self.late_addition_coefficient
        return money


def main():
    logging.basicConfig(filename='advertisement_simulation.log', level=logging.INFO)
    logging.info("Simulation started.")

    max_profit, best_breaks, years = 0, 0, 0

    for breaks in range(1, 10):
        simulation = Simulation(num_breaks=breaks, price_per_min=300, cost_per_min=20,
                                speaking_time=16, ads_percent=0.10, erlang_shape=2,
                                erlang_mean=20, duration_low=2.5, duration_high=3.5,
                                partially_addition_coefficient=0.9, late_addition_coefficient=0.7,
                                is_fast_run=True)
        total_profit, yrs, avg_stats = simulation.run()
        if total_profit > max_profit:
            max_profit, best_breaks, years = total_profit, breaks, yrs

    logging.info(f"Max profit of {max_profit} achieved with {best_breaks} breaks.")
    print(f"Max profit: {max_profit} with {best_breaks} breaks.")
    print(f"Years: {years}")

    logging.info("Simulation completed.")


if __name__ == "__main__":
    main()
