import pandas as pd
from io import StringIO
import numpy as np
import requests
import subprocess

def log_in(username, password):
    
    payload = "username="+username+"&password="+password
    headers = {'Host': "moira.pitt.edu",'Content-Type': "application/x-www-form-urlencoded"}

    response = requests.request("POST", "https://moira.pitt.edu/api/login", data=payload, headers=headers)

    x = response.json()
    token = "Bearer {}".format(x["token"])
    return token
def get_csv(data, get=False, state=False, RS=False, rs = False, SES=False, cluster=False, tempcluster=False, secondary_data='None'):

    if RS or SES or tempcluster:
        contents = data
        
        # run temporal clustering method
        if tempcluster:
            Routput = tempclustering(contents)
            if Routput == 'Error':
                contents.to_csv('accounts/static/temp_result.csv', index=False)
        else:
            contents.to_csv('accounts/static/temp_result.csv',index=False)
    else:
        # convert String to DataFrame
        contents = pd.read_csv(StringIO(data), sep=",")
        
        # clean FIPS codes
        if 'Formatted_FIPS' in contents.columns:
            fips = []
            for i in contents.Formatted_FIPS:
                if state == True:

                    if len(str(i)) == 4:
                        fips.append("0"+str(i)[:1])
                    else:
                        fips.append(str(i)[:2])
                else:
                    if len(str(i)) == 4:
                        fips.append("0"+str(i))
                    else:
                        fips.append(str(i))
        
            contents['Formatted_FIPS'] = fips
        
        # add secondary data
        if secondary_data != 'None':
            contents = add_unemployment(contents, secondary_data)
        # run clustering method
        if cluster==True:
            Routput = clustering(contents[['Formatted_FIPS','County','State','Deaths','Population','Age_Adjusted_Rate']])
            if Routput == 'Error':
                contents.to_csv('accounts/static/temp_result.csv',index=False)
        else:
        # save to static files
            contents.to_csv('accounts/static/temp_result.csv',index=False)
    
    if not get and not SES and not tempcluster:
        if cluster:
            supd = pd.read_csv('accounts/static/temp_result.csv').drop(columns=['Unnamed: 0'])
        else:
            supd = contents[contents.Deaths=='SUPPRESSED']
        
            if 'County' in supd.columns:
                supd = supd[['County','State']].drop_duplicates()
            elif 'State' in supd.columns:
                supd = supd[['State']].drop_duplicates()
            else:
                supd = supd.drop_duplicates()
            
        x = "<thead><tr>"
        for i in list(supd.columns):
            x = x+"<th>"+i+"</th>"
        x = x+"</tr></thead><tbody>"
        for i in supd.index:
            x = x+"<tr>"
            for col in list(supd.columns):
                x = x+"<td>"+str(supd[col][i])+"</td>"
            x = x+"</tr>"
    else:
        x = ""
    
    return contents, x
    



def get_rates(form_data, query):
    # CHANGE TO GLOBAL VARIABLES FROM USER LOGIN
    headers = {'Authorization': log_in("rgurewitsch", "Gnk8xZ0W8"),
               'Content-Type': "application/json",
               'Host': "moira.pitt.edu"}

    if query == 'reg':
        valid, payload, messages, age = validate_form(form_data)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)
        return payload, response.text, messages, age
    elif query == 'rs':
        valid, payload, messages = get_rs_payload(form_data)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)
        return payload, response.text, messages
    elif query == 'ses':
        valid, payload, messages = get_ses_payload(form_data)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)

        return payload, messages, response.text
    elif query == 'countytime':
        
        valid, payload, counties, messages = get_geo_payload(form_data, time=True)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)

        return payload, response.text, messages
    elif query == 'timecluster':
        
        valid, payload, counties, messages = get_geo_payload(form_data, clustering=True)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)

        return payload, response.text, messages
    elif query == 'clustering':
        valid, payload, messages = get_fc_payload(form_data)
        response = requests.request("POST", "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)
        return payload, messages, response.text 
    elif query == 'secondary':
        valid, payload, counties, messages = get_geo_payload(form_data, secondary_data=True)
        response = requests.request("POST", "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)
        return payload, messages, response.text 
    else: # query == 'geo'
        valid, payload, counties, messages = get_geo_payload(form_data)
        response = requests.request("POST", 
                                    "https://moira.pitt.edu/api/get_rate", 
                                    data=payload.replace("'","\""), 
                                    headers=headers)

        return payload, messages, response.text #, payload2, response2.text
    

def validate_time(year1, year2, states):
    messages = []
    if year1 > year2:
        form_valid = False
        message = "<strong>Invalid Time Period!</strong>Current time period: "+ year1 +"Input: " + str(year1) + ", " + str(year2)
        messages.append(message)
        timePeriod = [int(year1)]
    else:
        form_valid = True
        timePeriod = list(range(int(year1),(int(year2)+1)))
        
    # Identify time constraints:
    c68_99 = False # if true, HispanicOrigin not available, race = 'White/Black/Other only'
    if 1968 < min(timePeriod) < 1999 or 1968 < max(timePeriod) < 1999:
        c68_99 = True
        messages.append("<strong>Time Period Constraint:</strong> Hispanic Origin not available; Race: White/Black/Other only")
    pre79 = False # if true, codCategory = 63 only
    if min(timePeriod) < 1979:
        pre79 = True
    pre68 = False # if true, HispanicOrigin not available, race = 'White/Non-White only', ageGroupCategory = 12 only
    if min(timePeriod) < 1968:
        pre68 = True
        messages.append("<strong>Time Period Constraint:</strong> Hispanic Origin not available; Race: White/Non-White only; 12 Age Group Categories only")
    c62_63 = False # if true, no New Jersey data
    if 1962 in timePeriod or 1963 in timePeriod:
        c62_63 = True
        if 'NJ' in states:
            messages.append("<strong>Time Period Constraint:</strong> New Jersey data not available 1962-1963")
    pre62 = False # if true, only cancer-related deaths available
    if min(timePeriod) < 1962:
        pre62 = True
        messages.append("<strong>Time Period Constraint:</strong> Only cancer-related deaths available prior to 1962")
    pre60 = False # if true, no Alaska or Hawaii data
    if min(timePeriod) < 1960:
        pre60 = True
        if 'AK' in states or 'HI' in states:
            messages.append("<strong>Time Period Constraint:</strong> no data for Alaska/Hawaii prior to 1960")
    
    return timePeriod, form_valid, messages, c68_99, pre79, pre68, c62_63, pre62, pre60

def validate_cod(pre79, messages, cod63, cod113):
    cod_ints = []
    if pre79:
        if '0' in cod63 or cod63==[]:
            form_valid = False
            messages.append("<strong>Time Period Constraint:</strong> OCMAP 63 Cause of Death categories only prior to 1979; <strong>Current selection:</strong> All Causes of Death")
            pcodCat = '63'
            pcod = [1]
        else:
            for cd in cod63:
                cod_ints.append(int(cd))
            
            pcodCat = '63'    
            pcod = cod_ints
            
    else: 
        if '0' in cod113 or cod113 == []: 
            for cd in cod63:
                cod_ints.append(int(cd))
            pcodCat = '63'    
            pcod = cod_ints
            
        else:
            if '0' not in cod113:
                for cd in cod113:
                    cod_ints.append(int(cd))
                pcodCat = '113'    
                pcod = cod_ints
    
    return pcodCat, pcod, messages




def get_geo_payload(form_data, time=False, clustering=False, secondary_data=False):
    """    
    -----------------------------------------------------------------------------------------------------
    1. Validate time period selection
    """
    if time:
        o = '6' # FOR TIME SERIES PLOT
    elif clustering:
        o = '7'
    elif secondary_data:
        o = '8'
    else:
        o = '3' # FOR MAP
        
    timePeriod, form_valid, messages, c68_99, pre79, pre68, c62_63, pre62, pre60 = validate_time(form_data['year1_'+o], form_data['year2_'+o], form_data['abbreviatedStates_'+o])
    
    if form_valid:
        if time == False and clustering == False:
            timePeriod = [str(timePeriod[0])+" - "+str(timePeriod[len(timePeriod)-1])]
        
        payload = {'timePeriod':timePeriod}
    
    """
    set geoLevel
    """
    payload['geoLevel'] = form_data['geoLevel_'+o]
        
    if payload['geoLevel']== 'State':   
        payload['abbreviatedStates'] = form_data['abbreviatedStates_'+o]
        geos = []
    else:
        if not time:
            payload['allCounties'] = "true"
        payload['abbreviatedStates'] = form_data['abbreviatedStates_'+o]
        geos = [] # GEOS RETURNS SELECTED COUNTIES TO FILTER FROM D3 MAP
        for ST in form_data['abbreviatedStates_'+o]:
            state = ST+"select_"+o
            for FIPS in form_data[state]:
                if "[" in FIPS: 
                    for i in FIPS.replace("[","").replace("]","").replace("'","").split(", "):
                        geos.append(i)
                else:
                    geos.append(FIPS)
        payload['countyFIPS'] = geos   

    """
    All demographic groups:
    """
    payload["ageGroup"] = "All Default"
    payload["ageGroupCategory"] = "12"
    payload["race"], payload["sex"] = "All", "All"
 
    """
    -------------------------------------------------------------------------------------------------
    Validate Cause of Death
    """
    payload['codCategory'], payload['cod'], messages = validate_cod(pre79, messages, form_data['cod_'+o], form_data['cod113_'+o])
        
    payload['groupBy'] = ["timePeriod"]
    payload['ageAdjustment'] = "true"    

    return form_valid, str(payload), geos, messages



def get_rs_payload(form_data):
    """
    ---------------------------------------------------------------------------
    Validate form data
    """
    # get time period, alerts and time constraints from year1 and year2
    timePeriod, form_valid, messages, c68_99, pre79, pre68, c62_63, pre62, pre60 = validate_time(form_data['year1_2'], form_data['year2_2'], form_data['abbreviatedStates_2'])
    
    payload = {'timePeriod':timePeriod}
    
    """
    set geoLevel
    """
    payload['geoLevel'] = form_data['geoLevel_2']
    
    if form_data['geoLevel_2']== 'State':   
        payload['abbreviatedStates'] = form_data['abbreviatedStates_2']
        messages.append("Aggregated selected states: "+str(form_data['abbreviatedStates_2']).replace('[','').replace(']',''))
        payload['geoAggregate'] = "Aggregate Selected States"
        geos = []
    else:
        payload['abbreviatedStates'] = form_data['abbreviatedStates_2']
        geos = [] # GEOS RETURNS SELECTED COUNTIES TO FILTER FROM D3 MAP
        for ST in form_data['abbreviatedStates_2']:
            state = ST+"select_2"
            for FIPS in form_data[state]:
                if "[" in FIPS: 
                    for i in FIPS.replace("[","").replace("]","").replace("'","").split(", "):
                        geos.append(i)
                else:
                    geos.append(FIPS)
        payload['countyFIPS'] = geos
        if form_data['geoLevel_2']=='County':
            messages.append("Aggregated selected counties")
        payload['geoAggregate'] = "Aggregate Selected Counties"
    """
    All demographic groups:
    """
    payload["ageGroup"] = "All Default"
    payload["ageGroupCategory"] = "12"
    payload["race"], payload["sex"] = "All", "All"
    """
    -------------------------------------------------------------------------------------------------
    Validate Cause of Death
    """
    payload['codCategory'], payload['cod'], messages = validate_cod(pre79, messages, form_data['cod_2'], form_data['cod113_2'])
            
    payload['groupBy'] = ["timePeriod","race","sex"]
    payload['ageAdjustment'] = "true"    
    
    return form_valid, str(payload), messages



def get_ses_payload(form_data):
    """    
    -----------------------------------------------------------------------------------------------------
    Validate time period selection
    """
    timePeriod, form_valid, messages, c68_99, pre79, pre68, c62_63, pre62, pre60 = validate_time(form_data['year1_4'], form_data['year2_4'], ['NJ','HI','AK'])
    #if form_valid:
    #    timePeriod = [str(timePeriod[0])+" - "+str(timePeriod[len(timePeriod)-1])]
    
    payload = {'timePeriod':timePeriod}
    """
    set geoLevel
    """
    payload['geoLevel'] = 'County'
    payload['allCounties'] = 'true'
    payload['abbreviatedStates'] = ['AL', 'AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
    """
    All demographic groups:
    """
    payload["ageGroup"] = "All Default"
    payload["ageGroupCategory"] = "12"
    payload["race"], payload["sex"] = "All", "All"
 
    """
    -------------------------------------------------------------------------------------------------
    Validate Cause of Death
    """
    payload['codCategory'], payload['cod'], messages = validate_cod(pre79, messages, form_data['cod_4'], form_data['cod113_4'])
        
    payload['groupBy'] = ["timePeriod"]
    payload['ageAdjustment'] = "true"    
    
    return form_valid, str(payload), messages

    
def rates_RStime(text):
    
    df = pd.read_csv(StringIO(text),sep=",")
    if 'Detailed_Race_Label' in df.columns:  
        df['RaceSex'] = df['Detailed_Race_Label'].map(str) + " " + df['Sex_Label']
    else:
        df['RaceSex'] = df['Race_Label'].map(str) + " " + df['Sex_Label']
    df = df[['Time_Period_Label','RaceSex','Deaths','Population','Age_Adjusted_Rate']]
    #df_rate = df.pivot(index='Time_Period_Label', columns='RaceSex', values='Age_Adjusted_Rate').reset_index()
    
    return df

def rates_CTtime(text):
    
    df = pd.read_csv(StringIO(text), sep=",")
    return df

def rates_TempClust(text, geoLevel):
    df = pd.read_csv(StringIO(text), sep=",")
    df = df[df.Age_Adjusted_Rate!='SUPPRESSED']
    df['Time_Period_Label'] = df.Time_Period_Label.astype(str)
    try:
        df = df[[geoLevel,'Age_Adjusted_Rate','Time_Period_Label']].pivot(columns='Time_Period_Label',values='Age_Adjusted_Rate', index=geoLevel)
        df.dropna(inplace=True)
    except ValueError:
        df = df[['Formatted_FIPS','Age_Adjusted_Rate','Time_Period_Label']].pivot(columns='Time_Period_Label',values='Age_Adjusted_Rate', index='Formatted_FIPS')
        df.dropna(inplace=True)
    return df

def rates_SEStime(text):
    df = pd.read_csv('accounts/static/County-8Clusters.csv')
    output = StringIO(text)
    contents = pd.read_csv(output, sep=",")
    
    df = pd.merge(contents, df[['Formatted_FIPS','cluster.number','Group_Name']], on="Formatted_FIPS", how="inner")
    df = df[['Time_Period_Label','Group_Name','Deaths','Population','Age_Adjusted_Rate']]
    
    time = []
    group = []
    aar = []
    deaths = []
    for t in df.Time_Period_Label.unique():
        nndf = df[df['Time_Period_Label']==t]
        for g in nndf.Group_Name.unique():
            time.append(t)
            group.append(g)
            grp = nndf[nndf['Group_Name']==g]
            grp[['Deaths']] = grp['Deaths'].replace('SUPPRESSED',np.nan)
            grp[['Age_Adjusted_Rate']] = grp['Age_Adjusted_Rate'].replace('SUPPRESSED',np.nan)
            grp.dropna(subset=['Deaths', 'Age_Adjusted_Rate'], inplace=True)
            grp['Age_Adjusted_Rate'] = grp['Age_Adjusted_Rate'].astype(float)
            grp['Deaths'] = grp['Deaths'].astype(int)
            aar.append(grp['Age_Adjusted_Rate'].median())
            deaths.append(sum(grp['Deaths']))
            
    ndf = pd.DataFrame({'Time_Period_Label':time,'Group_Name':group,'Deaths':deaths,'Age_Adjusted_Rate':aar})

    return ndf

def deaths_RStime(text):
    
    df = pd.read_csv(StringIO(text),sep=",")
    
    df['RaceSex'] = df['Detailed_Race_Label'].map(str) + " " + df['Sex_Label']    
    df_deaths = df.pivot(index='Time_Period_Label', columns='RaceSex', values='Deaths').reset_index()
    
    return df_deaths

    
    
    
def validate_form(form_data):
    """
    Form validation for all queries:
    
    -----------------------------------------------------------------------------------------------------
    1. Validate time period selection
    """
    messages = []
    if form_data['year1'] > form_data['year2']:
        form_valid = False
        message = "<strong>Invalid Time Period!</strong>\n\nCurrent time period: "+ form_data['year1'] +"\n\nInput: " + str(form_data['year1']) + ", " + str(form_data['year2'])
        timePeriod = [form_data['year1']]
    else:
        form_valid = True
        timePeriod = list(range(int(form_data['year1']),(int(form_data['year2'])+1)))

    """
    Identify time constraints for other selection criteria
    """
    c68_99 = False # if true, HispanicOrigin not available, race = 'White/Black/Other only'
    if 1968 < min(timePeriod) < 1999 or 1968 < max(timePeriod) < 1999:
        c68_99 = True
        messages.append("<strong>Time Period Constraint:</strong> Hispanic Origin not available; Race: White/Black/Other only")

    pre79 = False # if true, codCategory = 63 only
    if min(timePeriod) < 1979:
        pre79 = True

    pre68 = False # if true, HispanicOrigin not available, race = 'White/Non-White only', ageGroupCategory = 12 only
    if min(timePeriod) < 1968:
        pre68 = True
        messages.append("<strong>Time Period Constraint:</strong> Hispanic Origin not available; Race: White/Non-White only; 12 Age Group Categories only")

    c62_63 = False # if true, no New Jersey data
    if 1962 in timePeriod or 1963 in timePeriod:
        c62_63 = True
        if 'NJ' in form_data['abbreviatedStates']:
            messages.append("<strong>Time Period Constraint:</strong> New Jersey data not available 1962-1963")
    pre62 = False # if true, only cancer-related deaths available
    if min(timePeriod) < 1962:
        pre62 = True
        messages.append("<strong>Time Period Constraint:</strong> Only cancer-related deaths available prior to 1962")
    pre60 = False # if true, no Alaska or Hawaii data
    if min(timePeriod) < 1960:
        pre60 = True
        if 'AK' in form_data['abbreviatedStates'] or 'HI' in form_data['abbreviatedStates']:
            messages.append("<strong>Time Period Constraint:</strong> no data for Alaska/Hawaii prior to 1960")

    """
    Check for 3, 5 or 10 year grouping
    """    
    if form_data['period'] == '3':
        t = []
        for i in range(0, len(timePeriod), 3): 
            try:
                t.append(str(timePeriod[i]) +"-" + str(timePeriod[i + 3]))
            except IndexError:
                if i != len(timePeriod)-1:
                    t.append(str(timePeriod[i]) +"-" + str(timePeriod[len(timePeriod)-1]))        
        timePeriod = t
    elif form_data['period'] == '5':
        t = []
        for i in range(0, len(timePeriod), 5): 
            try:
                t.append(str(timePeriod[i]) +"-" + str(timePeriod[i + 5]))
            except IndexError:
                if i != len(timePeriod)-1:
                    t.append(str(timePeriod[i]) +"-" + str(timePeriod[len(timePeriod)-1]))        
        timePeriod = t
    elif form_data['period'] == '10':
        t = []
        for i in range(0, len(timePeriod), 10): 
            try:
                t.append(str(timePeriod[i]) +"-" + str(timePeriod[i + 10]))
            except IndexError:
                if i != len(timePeriod)-1:
                    t.append(str(timePeriod[i]) +"-" + str(timePeriod[len(timePeriod)-1]))        
        timePeriod = t
    """
    set payload["timePeriod"]
    """  
    payload = {"timePeriod": timePeriod}

    """
    -------------------------------------------------------------------------------------------------
    2. Validate Geography -> payload[['geoLevel', 'abbreviatedStates', 'allCounties', 'countyFIPS']]

    """
    if form_data['geoLevel'] == 'National':
        payload['geoLevel'] = form_data['geoLevel']  

    elif form_data['geoLevel']== 'State':   
        payload['geoLevel'] = form_data['geoLevel']
        payload['abbreviatedStates'] = form_data['abbreviatedStates']
        payload['allCounties'] = 'true'

    else:
        if form_data['allCounties'] == 'True':
            payload['geoLevel'] = form_data['geoLevel']
            payload['abbreviatedStates'] = form_data['abbreviatedStates']
            payload['allCounties'] = 'true'

        else:
            fipslist = []
            for ST in form_data['abbreviatedStates']:
                state = ST+"select"
                for FIPS in form_data[state]:
                    if "[" in FIPS: 
                        for i in FIPS.replace("[","").replace("]","").replace("'","").split(", "):
                            fipslist.append(i)
                    else:
                        fipslist.append(FIPS)

            payload['geoLevel'] = form_data['geoLevel']
            payload['abbreviatedStates'] = form_data['abbreviatedStates']
            payload['countyFIPS'] = fipslist 
    """
    -------------------------------------------------------------------------------------------------
    3. Validate age group
    """   
    if pre68:
        if form_data['ageGroup12'] == ["All Default"]:
            payload['ageGroup'] = "All Default" 
        elif form_data['ageGroup12'] == []:
            payload['ageGroup'] = "All Default"
            messages.append("<strong>Time Period Constraint:</strong> 12 Age Group Categories only prior to 1968 - Current selection: All Default")
        else:
            payload['ageGroup'] = form_data['ageGroup12']
        payload['ageGroupCategory'] = '12'
    elif ~pre68 and form_data['ageGroup13'] == []:
        if form_data['ageGroup12'] == ["All Default"]:
            payload['ageGroup'] = "All Default" 
        elif form_data['ageGroup12'] == []:
            payload['ageGroup'] = "All Default"
            messages.append("<strong>All (12) Age Groups Selected</strong>")
        else:
            payload['ageGroup'] = form_data['ageGroup12']
        payload['ageGroupCategory'] = '12'
    else:
        if form_data['ageGroup13'] == ["All Default"]:
            payload['ageGroup'] = "All Default" 
        else:
            payload['ageGroup'] = form_data['ageGroup13']
        payload['ageGroupCategory'] = '13'
    
    """
    -------------------------------------------------------------------------------------------------
    4. Validate race
    """
    if pre68:
        if 'race' in form_data['groupBy']:  
            payload['race'] = 'All'
        else:
            if form_data['race'] not in ['White', 'All']:
                payload['race'] = 'All'
            else:
                payload['race'] = form_data['race']

    elif c68_99:
        if 'race' not in form_data['groupBy']:

            if form_data['race'] in ['White','Black','All']:

                payload['race'] = form_data['race']

            else:
                payload['race'] = 'All'
        else:
            payload['race'] = 'All'
    else:
        payload['race'] = form_data['race']

    """
    -------------------------------------------------------------------------------------------------
    5. Validate hispanicOrigin
    """
    if not pre68 and not c68_99:
        payload['hispanicOrigin'] = form_data['hispanicOrigin']

    """
    -------------------------------------------------------------------------------------------------
    6. Validate sex
    """                 
    payload['sex'] = form_data['sex']

    """
    -------------------------------------------------------------------------------------------------
    7. Validate Cause of Death
    """
    cod_ints = []
    if pre79:
        if '0' in form_data['cod']:#form_data['cod113_3'] != 0 or
            form_valid == False
            messages.append("<strong>Time Period Constraint:</strong> OCMAP 63 Cause of Death categories only prior to 1979\n\nCurrent selection: All Causes of Death")
            payload['codCategory'] = '63'
            payload['cod'] = [1]
        else:
            for cod in form_data['cod']:
                cod_ints.append(int(cod))
            payload['codCategory'] = '63'    
            payload['cod'] = cod_ints

    elif ~pre79 and '0' in form_data['cod113']: 
        for cod in form_data['cod']:
            cod_ints.append(int(cod))
        payload['codCategory'] = '63'    
        payload['cod'] = cod_ints
        payload2['codCategory'] = '63'    
        payload2['cod'] = cod_ints
    else:
        if '0' not in form_data['cod113']:
            for cod in form_data['cod113']:
                cod_ints.append(int(cod))
            payload['codCategory'] = '113'    
            payload['cod'] = cod_ints
    """
    -------------------------------------------------------------------------------------------------
    8. Validate group by
    """ 
    if form_data['groupBy'] == []:
        payload['groupBy'] = ['TimePeriod']
    else:
        payload['groupBy'] = form_data['groupBy']
    
    """
    --------------------------------------------------------------------------------------------------
    9. Age Adjustment & RatesPer    
    """
    if form_data['ageAdjustment']=="True": 
        if "ageGroup" in form_data['groupBy']:
            payload['ageAdjustment'] = 'false'
        else:
            payload['ageAdjustment'] = 'true'
    else:
        payload['ageAdjustment'] = 'false'
        
    payload['ratesPer'] = form_data['ratesPer']
    
    return form_valid, str(payload), messages, form_data['ageAdjustment']


def get_payload(form_data):

    cod_ints = []
    for cod in form_data['cod']:
        cod_ints.append(int(cod))

    if form_data['geoLevel'] == 'National':
        payload = {'timePeriod': list(range(int(form_data['year1']),(int(form_data['year2'])+1))),
                   'geoLevel': form_data['geoLevel'],   
                   "ageGroup": "All Default",
                   "ageGroupCategory": "12",
                   'race': form_data['race'], 
                   'hispanicOrigin': form_data['hispanicOrigin'], 
                   'sex': form_data['sex'], 
                   'codCategory': '113', 
                   'cod': cod_ints, 
                   'groupBy': form_data['groupBy'], 
                   'ageAdjustment': form_data['ageAdjustment'].lower()}

    else:   
        payload = {'timePeriod': list(range(int(form_data['year1']),(int(form_data['year2'])+1))),
                   'geoLevel': form_data['geoLevel'], 
                   'abbreviatedStates': form_data['abbreviatedStates'], 
                   'allCounties': 'true',  
                   "ageGroup": "All Default",
                   "ageGroupCategory": "12",
                   'race': form_data['race'], 
                   'hispanicOrigin': form_data['hispanicOrigin'], 
                   'sex': form_data['sex'], 
                   'codCategory': '113', 
                   'cod': cod_ints, 
                   'groupBy': form_data['groupBy'], 
                   'ageAdjustment': form_data['ageAdjustment'].lower()}


    if max(cod_ints) < 1999:
        del payload['hispanicOrigin']

    return str(payload)

def get_fc_payload(form_data):
    """    
    -----------------------------------------------------------------------------------------------------
    Validate time period selection
    """
    timePeriod, form_valid, messages, c68_99, pre79, pre68, c62_63, pre62, pre60 = validate_time(form_data['year1_5'], form_data['year2_5'], ['NJ','HI','AK'])
    if form_valid:
        timePeriod = [str(timePeriod[0])+" - "+str(timePeriod[len(timePeriod)-1])]
    
    payload = {'timePeriod':timePeriod}
    """
    set geoLevel
    """
    payload['geoLevel'] = 'County'
    payload['allCounties'] = 'true'
    payload['abbreviatedStates'] = form_data['abbreviatedStates_5']
    """
    All demographic groups:
    """
    payload["ageGroup"] = "All Default"
    payload["ageGroupCategory"] = "12"
    payload["race"], payload["sex"] = "All", "All"
 
    """
    -------------------------------------------------------------------------------------------------
    Validate Cause of Death
    """
    payload['codCategory'], payload['cod'], messages = validate_cod(pre79, messages, form_data['cod_5'], form_data['cod113_5'])
        
    payload['groupBy'] = ["timePeriod"]
    payload['ageAdjustment'] = "true"    
    
    return form_valid, str(payload), messages

def tempclustering(contents):
    contents.to_csv('accounts/static/clustering/test_query.csv')
    command = 'RScript'
    path2script = 'accounts/static/clustering/ts_clustering.R'
    
    cmd = [command, path2script]
    
    try:
        subprocess.check_output(cmd, universal_newlines=True)
        return 'Good'
    except:
        x = 'Error'
        return x

def clustering(contents):
    contents.to_csv('accounts/static/clustering/test_query.csv')
    command = 'RScript'
    path2script = 'accounts/static/clustering/clustering_updated.R'
    
    cmd = [command, path2script]
    
    try:
        subprocess.check_output(cmd, universal_newlines=True)
        return 'Good'
    except:
        x = 'Error'
        return x

def add_unemployment(moira_data, timePeriod):
    
    # get average year
    years = timePeriod.split('-')
    year = int((int(years[1].strip()) + int(years[0].strip())) / 2)
    year = str(year)[2:]
    unemployment = pd.read_csv('accounts/static/county_unemployment_'+year+'.csv')
    for df in unemployment, moira_data:
        df['Formatted_FIPS'] = df.Formatted_FIPS.astype(str)
        fips = []
        for i in df.Formatted_FIPS:
            if len(i) == 4:
                fips.append("0"+str(i))
            else:
                fips.append(str(i))
        df['Formatted_FIPS'] = fips
    moira_data = pd.merge(moira_data, unemployment, on='Formatted_FIPS', how='inner')
    

    
    return moira_data
    
def get_center(state):
    STATES = [('Alabama', '[-86.8287, 32.7794]'), ('Alaska', '[-152.2782, 64.0685]'), ('Arizona', '[-111.6602, 34.2744]'), ('Arkansas', '[-92.4426, 34.8938]'), ('California', '[-119.4696, 37.1841]'), ('Colorado', '[-105.5478, 38.9972]'), ('Connecticut', '[-72.7273, 41.6219]'), ('Delaware', '[-75.505, 38.9896]'), ('District of Columbia', '[-77.0147, 38.9101]'), ('Florida', '[-82.4497, 28.6305]'), ('Georgia', '[-83.4426, 32.6415]'), ('Hawaii', '[-156.3737, 20.2927]'), ('Idaho', '[-114.613, 44.3509]'), ('Illinois', '[-89.1965, 40.0417]'), ('Indiana', '[-86.2816, 39.8942]'), ('Iowa', '[-93.496, 42.0751]'), ('Kansas', '[-98.3804, 38.4937]'), ('Kentucky', '[-85.3021, 37.5347]'), ('Louisiana', '[-91.9968, 31.0689]'), ('Maine', '[-69.2428, 45.3695]'), ('Maryland', '[-76.7909, 39.055]'), ('Massachusetts', '[-71.8083, 42.2596]'), ('Michigan', '[-85.4102, 44.3467]'), ('Minnesota', '[-94.3053, 46.2807]'), ('Mississippi', '[-89.6678, 32.7364]'), ('Missouri', '[-92.458, 38.3566]'), ('Montana', '[-109.6333, 47.0527]'), ('Nebraska', '[-99.7951, 41.5378]'), ('Nevada', '[-116.6312, 39.3289]'), ('New Hampshire', '[-71.5811, 43.6805]'), ('New Jersey', '[-74.6728, 40.1907]'), ('New Mexico', '[-106.1126, 34.4071]'), ('New York', '[-75.5268, 42.9538]'), ('North Carolina', '[-79.3877, 35.5557]'), ('North Dakota', '[-100.4659, 47.4501]'), ('Ohio', '[-82.7937, 40.2862]'), ('Oklahoma', '[-97.4943, 35.5889]'), ('Oregon', '[-120.5583, 43.9336]'), ('Pennsylvania', '[-77.7996, 40.8781]'), ('Rhode Island', '[-71.5562, 41.6762]'), ('South Carolina', '[-80.8964, 33.9169]'), ('South Dakota', '[-100.2263, 44.4443]'), ('Tennessee', '[-86.3505, 35.858]'), ('Texas', '[-99.3312, 31.4757]'), ('Utah', '[-111.6703, 39.3055]'), ('Vermont', '[-72.6658, 44.0687]'), ('Virginia', '[-78.8537, 37.5215]'), ('Washington', '[-120.4472, 47.3826]'), ('West Virginia', '[-80.6227, 38.6409]'), ('Wisconsin', '[-89.9941, 44.6243]'), ('Wyoming', '[-107.5512, 42.9957]')]
    for i in STATES:
        if state == i[0]:
            center = i[1]
            break
    return center
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    