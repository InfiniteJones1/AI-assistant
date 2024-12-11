import os
import getData
import normalizingData
import pandas as pd
import createStatistics
import matplotlib.pyplot as plt

stock_symbol = "NVDA"
epsilon = 1
getData.getSingleData(stock_symbol, 1, 1, 0)
filename = stock_symbol + '_historicals.csv'
path = os.path.join('.', 'data', filename)
data = pd.read_csv(path)
data = normalizingData.normalizeData(data, epsilon)
data.to_csv(path, index=False)
distribution = createStatistics.naiveEstimator(data)


def plot_distribution(estimated_distribution):
    lengths = list(estimated_distribution.keys())
    frequencies = list(estimated_distribution.values())
    plt.figure(figsize=(10, 5))
    plt.bar(lengths, frequencies, color='skyblue', edgecolor='black')
    plt.xlabel('Interval Length')
    plt.ylabel('Frequency')
    plt.title('Distribution of Interval Lengths:' + stock_symbol + " epsilon:" + str(epsilon))
    plt.show()


variance_normal, variance_price = createStatistics.normalizedVariance(data)
print("Variance of normalized data is: " + str(variance_normal))
print("Variance of close price data is: " + str(variance_price))
plot_distribution(distribution)
