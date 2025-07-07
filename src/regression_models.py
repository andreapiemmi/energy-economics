def run_1stStage_regression_IPI():
    import pandas as pd
    import statsmodels.api as sm
    from src.data.source_and_aggregate_data import get_data_1st_stage_IPI
    d_regression = get_data_1st_stage_IPI()
    df = d_regression['Y'].merge(d_regression['X'], how='inner', on=['Year'])
    X, Y = sm.add_constant(df.drop(columns=['Industrial_Production_Index_DE'])), df.Industrial_Production_Index_DE
    model_IPI = sm.OLS(Y,X).fit()
    return {'model':model_IPI, 'fitted_values' : model_IPI.fittedvalues}

def run_1stStage_regression_Price():
    import pandas as pd
    import statsmodels.api as sm
    from src.data.source_and_aggregate_data import get_data_1st_stage_Price
    d_regression = get_data_1st_stage_Price()
    df = d_regression['Y'].merge(d_regression['X'], how='inner', on=['Year'])
    X, Y = sm.add_constant(df.drop(columns=['Power_DE_Prices'])), df.Power_DE_Prices
    model_Price = sm.OLS(Y,X).fit()
    return {'model':model_Price, 'fitted_values' : model_Price.fittedvalues}

def run_2ndStage_regression_Demand(include_controls = False): 
    import pandas as pd
    import statsmodels.api as sm
    from src.data.source_and_aggregate_data import get_data_2nd_Stage

    drop_cols = ['Power_Demand_DE_Industry'] if include_controls else ['Power_Demand_DE_Industry','CO2_EUA_Prices','Gas_TTF_Prices']

    d_regression = get_data_2nd_Stage()
    df = d_regression['Y'].merge(d_regression['X'], how='inner', on=['Year'])
    X, Y = sm.add_constant(df.drop(columns=drop_cols)), df.Power_Demand_DE_Industry
    model_Demand = sm.OLS(Y,X).fit()
    return {'model': model_Demand, 'fitted_values': model_Demand.fittedvalues}

def predict_IPI_OutOfSample(): 
    from src.regression_models import run_1stStage_regression_IPI
    import pandas as pd 
    import numpy as np
    import statsmodels.api as sm
    df_gdp = pd.read_csv('data/Forecast/GDP_series_forecast.csv').drop(columns=['GDP']).set_index('Year')
    df = (np.log((pd.read_csv('data/Forecast/Foecast_Features.csv', sep = ';').drop(columns=['Power_DE_Prices','Coal_API2_Prices']).
          set_index('Year'))).merge(df_gdp, how = 'left', on=['Year']).
          assign(Dummy_22 = lambda d: (d.index >= 2022).astype(int)))
    X = df.assign(**{'const':1})
    Y = run_1stStage_regression_IPI()['model'].predict(X[['const','GDP_growth','Gas_TTF_Prices','CO2_EUA_Prices','Dummy_22']])
    #Y = X[['const','GDP_growth','Gas_TTF_Prices','CO2_EUA_Prices','Dummy_22']].values @ run_1stStage_regression_IPI()['model'].params.values 
    return Y.to_frame(name = 'Hat_Industrial_Production_Index_DE')

def predict_Price_OutOfSample(): 
    from src.regression_models import run_1stStage_regression_Price
    import pandas as pd 
    import numpy as np
    import statsmodels.api as sm
    eurusd = pd.DataFrame(data = [1.10]*11,index = pd.Index(range(2025, 2036),name='Year'),columns = ['DEXUSEU'])
    df = (pd.read_csv('data/Forecast/Foecast_Features.csv', sep = ';').set_index('Year').
          merge(eurusd, how = 'left', on = ['Year'] ).
        assign(Coal_API2_Prices = lambda df: df["Coal_API2_Prices"]*df["DEXUSEU"]).drop(columns=["DEXUSEU"]))
    X = sm.add_constant((np.log(df[['Coal_API2_Prices','Gas_TTF_Prices','CO2_EUA_Prices']]).
                         assign(Dummy_22 = lambda df: (df.index >= 2022).astype(int)).
                         assign(Dummy_22_x_Coal_Price = lambda d: d.Dummy_22 * d.Coal_API2_Prices).
                         drop(columns=['Dummy_22'])))
    Y = run_1stStage_regression_Price()['model'].predict(X[['const','Coal_API2_Prices','Gas_TTF_Prices','CO2_EUA_Prices','Dummy_22_x_Coal_Price']])
    benchmark = np.log(pd.read_csv('data/Forecast/Foecast_Features.csv', sep = ';')[['Power_DE_Prices']])

    return Y.to_frame(name = 'Hat_Power_DE_Prices')
    
def predict_Demand_OutOfSample(): 
    from src.regression_models import run_2ndStage_regression_Demand, predict_IPI_OutOfSample, predict_Price_OutOfSample
    import pandas as pd 
    import numpy as np
    import statsmodels.api as sm
    df= (predict_IPI_OutOfSample().merge(predict_Price_OutOfSample(), how = 'left', on = ['Year']).
        assign(Dummy_22 = lambda df: (df.index >= 2022).astype(int)).
        assign(**{'const':1}) )
    #if you assign const in this way (sm.add_constant sees dummy 22), then you must re-impose order manually 
    Y = run_2ndStage_regression_Demand()['model'].predict(df[['const','Hat_Industrial_Production_Index_DE','Hat_Power_DE_Prices','Dummy_22']])
    return Y.to_frame(name = 'Hat_Power_Demand_DE_Industry')




