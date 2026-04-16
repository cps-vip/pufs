from scipy.stats import binom

def find_bch_parameters(n_list, target_k, ber, target_failure_rate):
    print(f"{'n':<6} | {'k_req':<6} | {'t_req':<6} | {'Actual P_fail':<15}")
    print("-" * 45)
    
    for n in n_list:
        # We search for the smallest t that satisfies the failure rate
        found_t = None
        for t in range(1, n // 2):
            # Probability that errors > t
            # sf (survival function) is 1 - cdf
            p_fail = binom.sf(t, n, ber)
            if t == 64:
                print(f"n={n}, t={t}, p_fail={p_fail}")
            
            if p_fail <= target_failure_rate:
                found_t = t
                break
        
        if found_t:
            # Approximation for k: k >= n - m*t where m = log2(n+1)
            import math
            m = math.log2(n + 1)
            approx_k = n - (m * found_t)
            
            print(f"{n:<6} | {int(approx_k):<6} | {found_t:<6} | {p_fail:.2e}")

# --- Parameters ---
# n must be 2^m - 1 (e.g., 255, 511, 1023) // TODO: Probably automate this evenutally
block_sizes = [255, 511, 1023, 2047, 4095, 8191]
target_bits = 128
my_ber = 0.04
max_p_fail = 1e-6

find_bch_parameters(block_sizes, target_bits, my_ber, max_p_fail)