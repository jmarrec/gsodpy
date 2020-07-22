from gsodpy.epw_converter import clean_df, epw_convert
from gsodpy.constants import WEATHER_DIR
import os
import pandas as pd


class Output(object):
    """Class for output weather data into specific type """

    def __init__(self, args):

        self.type_of_output = args['type_of_output']
        self.hdd_threshold = args['hdd_threshold']
        self.cdd_threshold = args['cdd_threshold']

    def calculate_hdd(self, temp):
        """function to calculate hdd"""
        if temp <= self.hdd_threshold:
            return self.hdd_threshold - temp
        else:
            return 0

    def calculate_cdd(self, temp):
        """function to calculate cdd"""
        if temp >= self.cdd_threshold:
            return temp - self.cdd_threshold
        else:
            return 0

    def output_daily(self, df_hourly):
        """output daily data by grouping by daily
           used in output_files()
        """
        df_daily = df_hourly.groupby(by=df_hourly.index.date).mean()
        df_daily.index = pd.to_datetime(
            df_daily.index)  # reset index to datetime
        # remove unnecessary columns for daily
        df_daily.drop(
            columns=['AZIMUTH_ANGLE', 'ZENITH_ANGLE', 'WIND_DIRECTION'], inplace=True)
        # for col in ['AZIMUTH_ANGLE', 'ZENITH_ANGLE', 'WIND_DIRECTION']:
        #     if col in df_daily.columns:
        #         df_daily.drop(
        #             columns=col, inplace=True)

        df_daily['HDD_F'] = df_daily[
            'TEMP_F'].apply(self.calculate_hdd)
        df_daily['CDD_F'] = df_daily[
            'TEMP_F'].apply(self.calculate_cdd)

        return df_daily

    def output_monthly(self, df_hourly, df_daily):
        """output monthly data
           used in output_files()
        """
        df_monthly = df_hourly.groupby(by=df_hourly.index.month).mean()
        # remove unnecessary columns for daily
        df_monthly.drop(
            columns=['AZIMUTH_ANGLE', 'ZENITH_ANGLE', 'WIND_DIRECTION'], inplace=True)        
        # for col in ['AZIMUTH_ANGLE', 'ZENITH_ANGLE', 'WIND_DIRECTION']:
        #     if col in df_monthly.columns:
        #         df_daily.drop(
        #             columns=col, inplace=True)

        monthly_hdd = []
        monthly_cdd = []
        for month in range(1, 13):
            monthly_hdd.append(
                df_daily[df_daily.index.month == month]['HDD_F'].sum())
            monthly_cdd.append(
                df_daily[df_daily.index.month == month]['CDD_F'].sum())
        df_monthly['HDD_F'] = monthly_hdd
        df_monthly['CDD_F'] = monthly_cdd

        return df_monthly

    def output_files(self):
        """output epw, csv or json file for each weather data in the directory.

           epw: hourly

           csv: hourly, daily, monthly

           json: daily, monthly


        """
        for root, dirs, files in os.walk(WEATHER_DIR + '/isd_full'):
            for file in files:
                if file.endswith("xlsx"):
                    df_path = os.path.join(root, file)
                    df = pd.read_excel(df_path, index_col=0)
                    df = clean_df(df, file)

                    # hourly
                    hourly_file_name = os.path.join(
                        root, file[:-5] + '-hourly' + '.csv')
                    df.to_csv(hourly_file_name)
                    # df.to_json

                    # daily
                    df_daily = self.output_daily(df_hourly=df)
                    # monthly
                    df_monthly = self.output_monthly(
                        df_hourly=df, df_daily=df_daily)
                    # output files

                    # daily
                    daily_file_name = os.path.join(
                        root, file[:-5] + '-daily')

                    # monthly
                    monthly_file_name = os.path.join(
                        root, file[:-5] + '-monthly')

                    # epw
                    if self.type_of_output == 'EPW':
                        epw_convert(df, root, file)

                    # csv
                    if self.type_of_output == 'CSV':
                        df_daily.to_csv(daily_file_name + '.csv')
                        df_monthly.to_csv(monthly_file_name + '.csv')

                    # json
                    if self.type_of_output == 'JSON':
                        df_daily.to_json(daily_file_name + '.json')
                        df_monthly.to_json(monthly_file_name + '.json')
