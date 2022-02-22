from pprint import pprint

import pandas as pd

stats = pd.read_csv('out.csv')
aggregate = stats.groupby('model').agg(one_step_avg=('one_step_time', 'mean'),
                                       permanent_avg=('permanent_time', 'mean'),
                                       temporary_avg=('temporary_time', 'mean'))
pd.set_option('display.max_columns', 500)
pprint(aggregate)
aggregate.to_csv('control_agg.csv')