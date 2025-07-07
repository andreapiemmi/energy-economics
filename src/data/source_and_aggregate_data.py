def get_data_GDP_OECD():
    import requests
    import pandas as pd 
    from io import StringIO

    # Define API query URL (CSV with labels format)
    url = "https://sdmx.oecd.org/archive/rest/data/OECD,DF_EO114_LTB,/DEU.GDP..A?startPeriod=2024&endPeriod=2035&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    # Fetch data
    response = requests.get(url)
    # Long term forecast for Germany into pandas DataFrame
    df_forecast = (pd.read_csv(StringIO(response.text))[['Country','Scenario','TIME_PERIOD','OBS_VALUE']].
      query("Scenario == 'Baseline' and Country == 'Germany' and TIME_PERIOD > 2024").drop(columns=['Scenario','Country']).
      set_index('TIME_PERIOD').rename_axis('Year'))
    
    url = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE1_EXPENDITURE,2.0/A.DEU...B1GQ....XDC.V..?startPeriod=2008&endPeriod=2024&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    response = requests.get(url)
    #Observed GDP of Germany 
    df_observed = (pd.read_csv(StringIO(response.text))[['TIME_PERIOD','OBS_VALUE']].
             assign(OBS_VALUE = lambda df: df.OBS_VALUE * 1e6).set_index('TIME_PERIOD').rename_axis('Year'))
    # API blocks my requests after some time 
    df = (pd.concat([df_observed, df_forecast], axis=0).sort_index().
          assign(GDP_growth = lambda df: df.OBS_VALUE.pct_change())).rename(columns={'OBS_VALUE':'GDP'})
    df.query("Year<=2024").to_csv('data/History/GDP_series_observed.csv', index = True)
    df.query("Year>=2025").to_csv('data/Forecast/GDP_series_forecast.csv', index = True)
    return df

def get_data_benchmark_model(): 
    import pandas as pd
    import pandas_datareader as pdr
    import numpy as np
    eurusd = (pdr.get_data_fred("DEXUSEU", start = "2014-01-01", end = "2024-12-31").
              groupby(lambda index: index.year)["DEXUSEU"].mean().rename_axis("Year"))
    X=(pd.read_csv("data/History/History_Features.csv", sep = ";").set_index("Year").
       merge(pd.read_csv("data/History/History_Targets.csv", sep = ";").set_index("Year"), how = "right", on = ["Year"]).
       merge(eurusd, how = "left", on=["Year"]).
       assign(Coal_API2_Prices = lambda df: df["Coal_API2_Prices"]*df["DEXUSEU"]).drop(columns=["DEXUSEU"]))
    Y = X[['Power_Demand_DE_Industry']]
    return {'X':np.log(X.drop(columns=['Power_Demand_DE_Industry'])), 'Y':np.log(Y)}

def get_data_1st_stage_IPI():
    import pandas as pd 
    import numpy as np
    
    df=(pd.read_csv("data/History/History_Features.csv", sep = ";").set_index("Year").
       merge(pd.read_csv("data/History/History_Targets.csv", sep = ";").set_index("Year"), how = "right", on = ["Year"]).
       merge(pd.read_csv("data/History/GDP_series_observed.csv")[['Year','GDP_growth']], how='left', on=['Year']).
       set_index('Year'))
    X = (df[['GDP_growth','Gas_TTF_Prices','CO2_EUA_Prices']].
         pipe(lambda d: d.assign(**{col: np.log(d[col]) for col in d.columns if col != 'GDP_growth'})).
         assign(Dummy_22 = lambda df: (df.index >= 2022).astype(int)))
    Y = np.log(df[['Industrial_Production_Index_DE']])
    
    return {'X': X, 'Y': Y}

def get_data_1st_stage_Price(): 
    import pandas as pd 
    import numpy as np
    import pandas_datareader as pdr
    eurusd = (pdr.get_data_fred("DEXUSEU", start = "2014-01-01", end = "2024-12-31").
              groupby(lambda index: index.year)["DEXUSEU"].mean().rename_axis("Year"))
    df = (pd.read_csv("data/History/History_Features.csv", sep = ";").set_index("Year").
       merge(pd.read_csv("data/History/History_Targets.csv", sep = ";").set_index("Year"), how = "right", on = ["Year"]).
       merge(eurusd, how = "left", on=["Year"]).
       assign(Coal_API2_Prices = lambda df: df["Coal_API2_Prices"]*df["DEXUSEU"]).drop(columns=["DEXUSEU"]))
    
    X = (np.log(df[['Coal_API2_Prices','Gas_TTF_Prices','CO2_EUA_Prices']]).assign(Dummy_22 = lambda df: (df.index >= 2022).astype(int)).
         assign(Dummy_22_x_Coal_Price = lambda d: d.Dummy_22 * d.Coal_API2_Prices).drop(columns=['Dummy_22']))
    Y = np.log(df[["Power_DE_Prices"]])
    return {'X': X, 'Y': Y}


def get_data_2nd_Stage(): 
    import pandas as pd 
    import numpy as np
    from src.regression_models import run_1stStage_regression_IPI, run_1stStage_regression_Price

    df = (pd.read_csv("data/History/History_Features.csv", sep = ";").set_index("Year").
       merge(pd.read_csv("data/History/History_Targets.csv", sep = ";").set_index("Year"), how = "right", on = ["Year"]).
       drop(columns=["Coal_API2_Prices","Power_DE_Prices","Industrial_Production_Index_DE"]))
    X = (np.log(df.drop(columns=['Power_Demand_DE_Industry'])).
         merge(run_1stStage_regression_IPI()['fitted_values'].to_frame(name='Hat_Industrial_Production_Index_DE'),
               how = 'left', on = ['Year']).
         merge(run_1stStage_regression_Price()['fitted_values'].to_frame(name="Hat_Power_DE_Prices"),
               how = 'left', on = ['Year']).assign(Dummy_22 = lambda d: (d.index>=2022).astype(int)))
    Y = np.log(df[["Power_Demand_DE_Industry"]])

    return {'X':X, 'Y':Y}







