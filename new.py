import numpy as np
import logging


class AdvertisementGenerator:
    def __init__(self, seed=None):
        self.random = np.random.default_rng(seed)

    def erlang_interarrival(self, shape, mean, size=1):
        scale = mean / shape
        return self.random.gamma(shape, scale, size=size)

    def uniform_duration(self, low, high, size=1):
        return self.random.uniform(low, high, size=size)


class Advertisement:
    def __init__(self, index, arrival_time, duration):
        self.index = index
        self.arrival_time = arrival_time
        self.duration = duration

    def __str__(self):
        return f'Ad {self.index} at {self.arrival_time}; Duration: {self.duration}'


def generate_ads(number, erlang_shape=2, erlang_mean=20, duration_low=2.5, duration_high=3.5, seed=None):
    generator = AdvertisementGenerator(seed)
    interarrival_times = generator.erlang_interarrival(shape=erlang_shape, mean=erlang_mean, size=number)
    ad_durations = generator.uniform_duration(low=duration_low, high=duration_high, size=number)

    arrival_times = np.insert(np.cumsum(interarrival_times), 0, 0)[:-1]
    return [Advertisement(i, arrival_times[i], ad_durations[i]) for i in range(number)]



class AdQueue:
    def __init__(self):
        self.breaks = []
        self.ads = []

    def create_breaks(self, num_breaks):
        total_duration = 16 * 60
        break_duration = (1.6 * 60) / num_breaks
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

        logging.info(f"Ad {ad.index} rejected due to lack of space.")
        return False


def revenue(ad, partilally_addition_coeficiant, late_addition_coeficiant, price_per_min=300):
    money = ad['duration'] * price_per_min
    if not ad['full_addition']:
        money *= partilally_addition_coeficiant
    if not ad['immediately_added']:
        money *= late_addition_coeficiant
    return money


class Simulation:
    def __init__(self, num_breaks, price_per_min=300, cost_per_min=10, ads=57,
                         speaking_time=16, ads_percent=0.1, erlang_shape=2, erlang_mean=20,
                         duration_low=2.5, duration_high=3.5,
                         partially_addition_coefficient=0.9, late_addition_coefficient=0.7,
                         is_fast_run=True):


        self.num_breaks = num_breaks
        self.price_per_min = price_per_min
        self.cost_per_min = cost_per_min
        self.ads = ads
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
        self.seed =  None


    def run(self):
        if self.is_fast_run:
            profit = self.simulate()*365
        else:
            profit = sum(self.simulate() for _ in range(365))
        years_to_profit = (self.initial_cost // profit) + 1
        return profit, years_to_profit

    def simulate(self):
        logging.info("Starting simulation.")
        ads = generate_ads(self.ads, self.erlang_shape, self.erlang_mean, self.duration_low, self.duration_high, self.seed)
        queue = AdQueue()
        queue.create_breaks(self.num_breaks)

        for ad in ads:
            queue.add_ad(ad)

        total_revenue = sum(revenue(ad, self.partially_addition_coefficient, self.late_addition_coefficient, self.price_per_min) for ad_break in queue.breaks for ad in ad_break['ads'])
        total_ad_time = sum(ad['duration'] for ad_break in queue.breaks for ad in ad_break['ads'])
        daily_costs = self.speaking_time*60 * self.cost_per_min

        daily_profit = total_revenue - daily_costs
        logging.info(f"Daily Profit: {daily_profit}")
        return daily_profit


def main():
    logging.basicConfig(filename='advertisement_simulation.log', level=logging.INFO)
    logging.info("Simulation started.")

    max_profit, best_breaks, years = 0, 0, 0

    for breaks in range(1, 10):
        simulation = Simulation(num_breaks=breaks, price_per_min=300, cost_per_min=20, ads=60,
                                speaking_time=16, ads_percent=0.10, erlang_shape=2,
                                erlang_mean=20, duration_low=2.5, duration_high=3.5,
                                partially_addition_coefficient=0.9, late_addition_coefficient=0.7,
                                is_fast_run=True)
        total_profit, yrs = simulation.run()
        if total_profit > max_profit:
            max_profit, best_breaks, years = total_profit, breaks, yrs

    logging.info(f"Max profit of {max_profit} achieved with {best_breaks} breaks.")
    print(f"Max profit: {max_profit} with {best_breaks} breaks.")
    print(f"Years: {years}")

    logging.info("Simulation completed.")


if __name__ == "__main__":
    main()
