def MAPE(observed, predicted):
        import numpy as np
        y_true, y_pred = np.array(observed), np.array(predicted)
        # Avoid division by zero
        if np.any(y_true == 0):
              raise ValueError("y_true contains zero values, MAPE is undefined.")
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100



def plot_time_series(df_flat):
    import plotly.express as px 
    import pandas as pd 

    if not isinstance(df_flat, pd.DataFrame):
         raise TypeError("you must provide a flattened dataframe.")
    
    plots = {ind:
             px.line(df_flat.query("indicator == @ind").copy(),
                      x='Year',
                      y='value',
                      color='label',
                      line_dash='origin',
                      title=f'Time Series for {ind}',
                      template='plotly_white').update_xaxes(tickmode='linear', dtick=1).
                      update_layout(legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)) 
                      
                      for ind in df_flat.indicator.unique()}

    return plots 

       
