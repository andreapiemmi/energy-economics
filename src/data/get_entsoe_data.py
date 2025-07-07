def get_entsoe_crossborder_flows(start_date: str, end_date: str, country_code: str): 
    import pandas as pd 
    import numpy as np
    from datetime import datetime
    from entsoe import EntsoePandasClient

    key_entsoe = "22d17cd2-0726-45db-b5b4-b19456fefee3"
    client = EntsoePandasClient(api_key=key_entsoe)
    df_NX_entsoe_API = (client.query_net_position("DE_LU", 
                                          start=pd.Timestamp("2014-01-01", tz="Europe/Berlin"), end=pd.Timestamp("2024-12-31", tz="Europe/Berlin")).
                                          to_frame(name = "DE_NX").groupby(lambda index: index.year)['DE_NX'].sum())
    
    # Load historical data from Excel file - however, this data measure is not explicit, cannot be used
    # as there is no clear explanation on the webside of what is being measured 
    df_NX_entsoe_archive = (pd.read_excel("data/History/additional/PEPF_data-2015-2019.xlsx").
            query("Year >= 2014 and Year <= 2018 and MeasureTime == 'Monthly Value' and MeasureItem == 'Physical Energy & Power Flows'").
            query("`Submitted By` == 'DE' or `Border with` == 'DE'").
            assign(Value = lambda df: np.where(
                df["Submitted By"] == "DE",
                df.Value * df.Direction.map({'Export': 1, 'Import': -1}), 
                df.Value * df.Direction.map({'Export': -1, 'Import': 1})   )
                   ).groupby("Year")["Value"].sum())
    return df_NX_entsoe_API

def get_entsoe_max_day_spread(start_date: str, end_date: str, country_code: str): 
    import pandas as pd 
    import numpy as np
    from datetime import datetime
    from entsoe import EntsoePandasClient

    key_entsoe = "22d17cd2-0726-45db-b5b4-b19456fefee3"
    client = EntsoePandasClient(api_key=key_entsoe)
    df = (client.query_day_ahead_prices("DE_LU", 
                                          start=pd.Timestamp("2014-01-01", tz="Europe/Berlin"),
                                          end=pd.Timestamp("2024-12-31", tz="Europe/Berlin")).to_frame(name = 'price').rename_axis("datetime").
                                          merge(
                                              client.query_load("DE_LU", 
                                                start=pd.Timestamp("2014-01-01", tz="Europe/Berlin"),
                                                end=pd.Timestamp("2024-12-31", tz="Europe/Berlin")).to_frame(name = 'load').rename_axis("datetime"),
                                          how = 'inner', on = ['datetime']
                                          ))