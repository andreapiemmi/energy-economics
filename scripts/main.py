import pandas as pd
import numpy as np
from src.regression_models import run_1stStage_regression_IPI, run_1stStage_regression_Price, run_2ndStage_regression_Demand
from src.regression_models import predict_IPI_OutOfSample, predict_Price_OutOfSample, predict_Demand_OutOfSample
from src.utils.utils import plot_time_series, MAPE
import plotly.io as pio
pio.renderers.default = 'browser'
import webbrowser


# 1st Stage Regression - logIPI over GDP growth, logGas Price, logCO2 EUA Price and Dummy_22 
IPI_1st_Stage  = run_1stStage_regression_IPI()
# 1st Stage Regression - logPrice over log Coal Price, log Gas Price, logCO2 EUA Price and Dummy_22*logCoalPrice 
Price_1st_Stage = run_1stStage_regression_Price()
#2nd Stage Regression - logDemand over logIPI_fitted, logPrice fitted and Dummy_22 
Demand_2nd_Stage = run_2ndStage_regression_Demand()

#Dictionary with model summaries 
model_summaries = {'IPI_1stStage': IPI_1st_Stage['model'].summary(), 
                   'Price_1stStage': Price_1st_Stage['model'].summary(), 
                   'Demand_2ndStage': Demand_2nd_Stage['model'].summary()}
html_content = ""

for name, summary in model_summaries.items():
    html_content += f"<h2>{name}</h2>"
    html_content += summary.as_html()

# Save to an HTML file
output_path = 'model_summaries.html'
with open(output_path, 'w') as f:
    f.write(html_content)

# Open in default browser
webbrowser.open(output_path)


print(model_summaries.values())
#Check that no direct impact of Gas Price and CO2 Price on Demand exists, other than 
#the effect channeled via Industrial Production and the effect channeled through Energy Prices
print(run_2ndStage_regression_Demand(include_controls=True)['model'].summary())
# See here, with controls included price elasticity is positive, i.e. more demand for a higher price, 
# and IPI coefficient is pulled towards 0. Thus, info overlapping with the latter (they were included
# in both IV regressions)


# Observed values - to estimate the model
df_hist= (pd.read_csv('data/History/History_Features.csv', sep = ';').set_index('Year').
          merge(pd. read_csv('data/History/History_Targets.csv', sep = ';').set_index('Year'), 
                how = 'inner', on = ['Year'])
                [['Power_DE_Prices','Power_Demand_DE_Industry','Industrial_Production_Index_DE']].
                reset_index().
                melt(id_vars=['Year'], var_name = 'indicator', value_name = 'value').
                assign(**{'label':'observed', 'origin':'given'}) )

# Forecasted values Out of Sample - i.e. final output of the Model
df_forecast = (pd.read_csv('data/Forecast/Foecast_Features.csv', sep = ';').set_index('Year').
               merge(np.exp(predict_IPI_OutOfSample()), how = 'inner', on = ['Year']).
               merge(np.exp(predict_Price_OutOfSample()), how = 'inner', on = ['Year']).
               merge(np.exp(predict_Demand_OutOfSample()), how = 'inner', on = ['Year']).
               filter(like = '_DE').reset_index().
               melt(id_vars=['Year'], var_name = 'indicator', value_name = 'value').
               assign(**{'label': 'prediction_out_of_sample'}).
               pipe(lambda df: df.assign(
                     origin = np.where(df.indicator.str.contains('Hat_'), 'computed', 'given'),
                     indicator = df['indicator'].str.replace('Hat_', '', regex=False))))

# In Sample predictions (fitted values - intermediate output)
df_insample_predictions = (np.exp(IPI_1st_Stage['fitted_values']).
                           to_frame(name = "Industrial_Production_Index_DE").
                           merge(np.exp(Price_1st_Stage['fitted_values']).
                                 to_frame(name = "Power_DE_Prices"),
                                 how = 'inner', on = ['Year']).
                            merge(np.exp(Demand_2nd_Stage['fitted_values']).
                                  to_frame(name = "Power_Demand_DE_Industry"),
                                  how = 'inner', on = ['Year']).reset_index().
                                  melt(id_vars=['Year'], var_name = 'indicator', value_name = 'value').
                                  assign(**{'label':'prediction_in_sample', 'origin':'computed'}))


df_series = pd.concat([df_hist, df_insample_predictions, df_forecast], axis = 0)

plots = plot_time_series(df_series)
plots['Power_Demand_DE_Industry'].show()
plots['Industrial_Production_Index_DE'].show()
plots['Power_DE_Prices'].show()

#Goodness of fit of all the insample predictions I did - Mean Absolute Percentage Error 
MAPE_in_sample = {var : 
                  MAPE(observed = df_series.query("label=='observed' and indicator == @var").sort_values('Year').value,
                       predicted  = df_series.query("label=='prediction_in_sample' and indicator == @var").sort_values('Year').value)
                  for var in df_series.indicator.unique()}