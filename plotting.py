def plot_polar_aggregation(df, columns_of_interest, plotfunc='count'):
    """
    Generates and displays a polar plot for aggregated data from a DataFrame.

    This function groups the input DataFrame by month and calculates a specified
    aggregation (count, mean, or median) for the given columns. It then
    creates a polar plot for each of these columns, visualizing the
    aggregated data.

    Args:
        df (pd.DataFrame): The input DataFrame. It must contain a 'month'
            column and the columns specified in `columns_of_interest`.
        columns_of_interest (list of str): A list of column names for which to
            generate the plots.
        plotfunc (str, optional): The aggregation function to use.
            Can be 'count', 'mean', or 'median'. Defaults to 'count'.
    """
    # Define month labels for the angular axis
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for col in columns_of_interest:
        # --- 1. AGGREGATE DATA ---
        monthly = df.groupby('month')[col]

        if plotfunc == 'mean':
            monthly = monthly.mean().reset_index().sort_values('month')
        elif plotfunc == 'median':
            monthly = monthly.median().reset_index().sort_values('month')
        elif plotfunc == 'count':
            monthly = monthly.count().reset_index().sort_values('month')

        # --- 2. PREPARE DATA FOR PLOTTING ---
        values = monthly[col].values
        angles = np.linspace(0, 2 * np.pi, 12, endpoint=False)

        # Close the loop for a continuous plot
        values_closed = np.concatenate((values, [values[0]]))
        angles_closed = np.concatenate((angles, [angles[0]]))

        # --- 3. CREATE AND CUSTOMIZE THE PLOT ---
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

        ax.plot(angles_closed, values_closed, linewidth=2, linestyle='solid', label=f'{plotfunc.capitalize()} {col.capitalize()}')
        ax.fill(angles_closed, values_closed, alpha=0.25)

        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')

        ax.set_xticks(angles)
        ax.set_xticklabels(month_names, fontsize=12)

        if plotfunc == 'count':
          ax.set_title(f'Count by Month', fontsize=16, pad=20)
        else:
          ax.set_title(f'{col.capitalize()} {plotfunc.capitalize()} by Month', fontsize=16, pad=20)

        min_val = monthly[col].min()
        max_val = monthly[col].max()
        ax.set_rlim(min_val * 0.9, max_val * 1.1)

        plt.show()

        if plotfunc == 'count':
            break
