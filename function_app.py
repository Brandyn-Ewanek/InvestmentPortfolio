import logging

import pandas as pd
import azure.functions as func
import json
import time
from datetime import timedelta

import google.generativeai as genai
import yfinance as yf

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

logging.info('Done Imports')


app = func.FunctionApp()

# @app.schedule(schedule="30 16 * * 1 5", arg_name="myTimer", run_on_startup=True,
#                use_monitor=False) 
@app.schedule(schedule="*/5 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.info('Function started') 
    if myTimer.past_due:
        logging.info('The timer is past due!')

    # stock list
    ticker_name_list = [
    ("ADSK", "Autodesk, Inc."),
    ("AI", "C3.ai, Inc."),
    ("AMD", "Advanced Micro Devices, Inc."),
    ("AMZN", "Amazon.com, Inc."),
    ("ANET", "Arista Networks, Inc."),
    ("ASML", "ASML Holding N.V."),
    ("AVGO", "Broadcom Inc."),
    ("BIDU", "Baidu, Inc."),
    ("CNQ.TO", "Canadian Natural Resources Limited"),
    ("CRWD", "CrowdStrike Holdings, Inc."),
    ("CTSH", "Cognizant Technology Solutions Corporation"),
    ("DDOG", "Datadog, Inc."),
    ("DIS", "The Walt Disney Company"),
    ("DOL", "Dolby Laboratories, Inc."),
    ("DOL.TO", "Dollarama"),
    ("ENB", "Enbridge Inc."),
    ("GOOG", "Alphabet Inc."),
    ("GSY.TO", "Goeasy Ltd."),
    ("HIVE", "HIVE Blockchain Technologies Ltd."),
    ("INTC", "Intel Corporation"),
    ("LRCX", "Lam Research Corporation"),
    ("META", "Meta Platforms, Inc."),
    ("MRNA", "Moderna, Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("MU", "Micron Technology, Inc."),
    ("NIO", "NIO Inc."),
    ("NVDA", "NVIDIA Corporation"),
    ("NXPI", "NXP Semiconductors N.V."),
    ("PLTR", "Palantir Technologies Inc."),
    ("RBRK", "Berkshire Hathaway Inc. (Class B)"),
    ("SMCI", "Super Micro Computer, Inc."),
    ("TD.TO", "The Toronto-Dominion Bank"),
    ("TSM", "Taiwan Semiconductor Manufacturing Company Limited"),
    ("TXN", "Texas Instruments Incorporated"),
    ("V", "Visa Inc."),
    ("WCN", "Waste Connections, Inc."),
    ("SOL", "Renesola Ltd."),
    ("BDI.TO", "Bombardier Inc."),
    ("CEU.TO", "Cenovus Energy Inc."),
    ("CLS", "Celestica Inc."),
    ("XMTR", "Xometry, Inc."),
    ("PRLB", "Protolabs, Inc."),
    ("KXS.TO", "Kolibri Global Energy Inc."),
    ("FLPT", "Flexport, Inc."),
    ("CNVY", "Convoy, Inc."),
    ("P44", "Autobytel Inc."),
    ("CHRW", "C.H. Robinson Worldwide, Inc."),
    ("ALTI", "Altair Engineering Inc."),
    ("QCOM", "QUALCOMM Incorporated"),
    ("MRVL", "Marvell Technology, Inc."),
    ("SMH", "VanEck Semiconductor ETF"),
    ("RBC.TO", "Royal Bank of Canada"),
    ("CM.TO", "Canadian Imperial Bank of Commerce (CIBC)"),
    ("BNS.TO", "The Bank of Nova Scotia"),
    ("BMO.TO", "Bank of Montreal"),
    ("CAVA", "Cava Group, Inc."),
    ("BROS", "Dutch Bros Inc."),
    ("HOOD", "Robinhood Markets, Inc."),
    ("DND.TO", "Dundee Precious Metals Inc."),
    ("MG.TO", "Magna International Inc."),
    ("T.TO", "TELUS Corporation"),
    ("COST", "Costco Wholesale Corporation")]


    # Importing Data
    for i in range(8):
        try:
            date =  pd.Timestamp.today()
            date = date - timedelta(i)

            date_str = date.strftime('%Y-%m-%d')

            df = pd.read_csv(f'/content/drive/MyDrive/01. Projects/01. Experimental Playground/01. Algo Trading/10. YahooFinance/ {date_str} stock ratings.csv')
            break
        except Exception as e:
            logging.error(f"Error reading CSV from Blob Storage: {e}")
            pass




    # Importing Gemini
    genai.configure(api_key='AIzaSyBhhnyomY2QAQ8vOymKCDgL-al8MVPYDU0')

    model = genai.GenerativeModel('gemini-pro')

    # Company News Prompt
    company_news_prompt = '''Generate a Python Dictionary Keys being the Topic and Value being
        a Sentiment Prediction of the New of the company represented by the ticker {Company}
        Produce a sentiment evaluation from the past 24hrs of how it relates to
        Revenue, Managment, Legal, Technology and Financial.
        Use the exact names as the keys.
            Rating from 0 to 100. 0 Most negative, 100 Most positive.
        Display only the output as a python disctionary like this only as text
        {"Revenue": 75,
            "Management": 85,
            "Legal": 60,
            "Technology": 90,
            "Financial": 80}
        '''
    # Daily Global News Prompt
    daily_global_news_prompt = '''
        Generate a Python dictionary where keys are globally relevant news topics discussed 
        in the last 24 hours across major financial news sources worldwide. Values are sentiment
        scores on a scale of 0 to 100, where 0 is extremely negative and 100 is extremely positive.
        Include at least 10 of the most talked about topics, considering economic, political, 
        and social factors that could impact global markets.
        Display only the output as a python disctionary like this only as text as in the example below
        {"Topic1":65,
            "Topic2":75,
            "Topic3":85,
            "Topic4":95,
            "Topic5":100,
            "Topic6":90,
            "Topic7":80,
            "Topic8":70,
            "Topic9":60,
            "Topic10":50}
        }
        
        '''


    # Collection Loop
    dict_rating = {}
    dict_rating['date'] = pd.Timestamp.today().strftime('%Y-%m-%d')

    news_count = 0
    for (ticker, name) in ticker_name_list:
        print(ticker)
        stock = yf.Ticker(ticker)
        info = stock.info
        try:
            dict_rating[f'{ticker}_min_target'] = info['targetLowPrice']
            dict_rating[f'{ticker}_max_target'] = info['targetHighPrice']
            dict_rating[f'{ticker}_target_mean'] = info['targetMeanPrice']
            dict_rating[f'{ticker}_target_median'] = info['targetMedianPrice']
            dict_rating[f'{ticker}_number_analysts'] = info['numberOfAnalystOpinions']
            dict_rating[f'{ticker}_close'] = info['regularMarketPreviousClose']
            dict_rating[f'{ticker}_open'] = info['regularMarketOpen']
            dict_rating[f'{ticker}_high'] = info['regularMarketDayHigh']
            dict_rating[f'{ticker}_low'] = info['regularMarketDayLow']
            dict_rating[f'{ticker}_industry'] = info['industry']
            dict_rating[f'{ticker}_sector'] = info['sector']
            dict_rating[f'{ticker}_recommendationMean'] = info['recommendationMean']
            # new
            dict_rating[f'{ticker}_percent_from_mean'] = (info['targetMeanPrice'] - info['regularMarketPreviousClose']) / info['regularMarketPreviousClose'] * 100

        except:
            print('ERROR Reccomendations: ', ticker)
            pass

        try:
            dict_rating[f'{ticker}_heldPercentInsiders'] = info['heldPercentInsiders']
            dict_rating[f'{ticker}_heldPercentInstitutions'] = info['heldPercentInstitutions']
            dict_rating[f'{ticker}_trailingPE'] = info['trailingPE']
            dict_rating[f'{ticker}_forwardPE'] = info['forwardPE']
            dict_rating[f'{ticker}_earningsGrowth'] = info['earningsGrowth']
            dict_rating[f'{ticker}_revenueGrowth'] = info['revenueGrowth']
            dict_rating[f'{ticker}_grossMargins'] = info['grossMargins']
            dict_rating[f'{ticker}_ebitdaMargins'] = info['ebitdaMargins']
            dict_rating[f'{ticker}_operatingMargins'] = info['operatingMargins']
        except:
            print('ERROR Financial Metrics: ', ticker)
            pass


        try:

            prompt = company_news_prompt.replace('{Company}', name)
            response = model.generate_content(prompt)
            response_dict = json.loads(response.text)
            print(name)
            print(response.text)
            dict_rating[f'{ticker}_news_Revenue'] = response_dict['Revenue']
            dict_rating[f'{ticker}_news_Managment'] = response_dict['Management']
            dict_rating[f'{ticker}_news_Legal'] = response_dict['Legal']
            dict_rating[f'{ticker}_news_Technology'] = response_dict['Technology']
            dict_rating[f'{ticker}_news_Financial'] = response_dict['Financial']
        except:
            print('ERROR news prompt: ', name)
            news_count += 1
            pass
        time.sleep(2)

    try:
                
        response = model.generate_content(daily_global_news_prompt)
        response_dict = json.loads(response.text)
        for (t,s) in response_dict.items():
            # print(t, s)
            dict_rating[f'Daily_News_Topic_{t}_Sentiment'] = s
    except:
        print('Daily News FAILED')
    
    df_tmp = pd.DataFrame(dict_rating, index=[date_str])

    df_output = pd.concat([df, df_tmp])




    # Save File to blob
    connect_str = "DefaultEndpointsProtocol=https;AccountName=illumiastrategiesdata;AccountKey=1vH4GiLVmLWZRbDmFMq/bHQEPMXhcDm3lK7rj1c7q7RLeuHHVZMKfg6RydryJ3tXcGYTWI6TX6bw+AStwORDkQ==;EndpointSuffix=core.windows.net" 
    try:
        #  Create the BlobServiceClient object 
        blob_service_client = BlobServiceClient.from_connection_string(connect_str) 


        # Get a reference to the container
        container_name = "illuminadata"  
        container_client = blob_service_client.get_container_client(container_name)

        # Upload the Date CSV file
        blob_name = f"{date_str} stock ratings.csv"  # File name with the date
        blob_client = container_client.get_blob_client(container=container_name, blob=blob_name) #blob_service_client
        output = df_output.to_csv(index=False).encode('utf-8') 
        blob_client.upload_blob(output, overwrite=True)  

        # Upload the daily_data CSV file
        blob_name = f"daily_date.csv"  # File name with the date
        blob_client = container_client.get_blob_client(container=container_name, blob=blob_name) #blob_service_client
        output = df_output.to_csv(index=False).encode('utf-8') 
        blob_client.upload_blob(output, overwrite=True) 
    except Exception as e:
        logging.error(f"Error uploading CSV to Blob Storage: {e}")



logging.info('Python timer trigger function executed.')