from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from accounts.forms import APIform, APIform2, APIform3, APIform4, APIform5, APIform6, APIform7, APIform8
import accounts.rates as MOIRA
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import pandas as pd
from django.utils.safestring import mark_safe

################ Home and Sign In Views ###############
class RegisterView(TemplateView):
    template_name = 'accounts/sign-up.html'

    def get(self, request):
        form = UserCreationForm()
        args = {'form':form}
        return render(request, self.template_name, args)

    def post(self, request):
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            template_name = 'accounts/index.html'
            form.save()
            return render(request, template_name)
        else:
            form = UserCreationForm()
            args = {'form':form}
            return render(request, self.template_name, args)
    
# MOIRA home page
class HomeView(TemplateView):
    
    template_name = 'accounts/index.html'

# Documentation page
class LabView(TemplateView):
    
    template_name = 'accounts/data-lab.html'
################## Documentation and Forum ############
class DocsView(TemplateView):
    
    template_name = 'accounts/documentation.html'

class ForumView(TemplateView):
    template_name = 'accounts/forum.html'
    

###################### Module Menus ###################
class TSGView(TemplateView):
    
    template_name = 'accounts/ts_groups.html'
class GeoMenuView(TemplateView):
    
    template_name = 'accounts/geo_menu.html'
    
###################### Module Views ###################
class RaceSexView(TemplateView):
    
    template_name = 'accounts/plotRS.html'
    
    def get(self, request):
        race_sex_form = APIform2()
        text = 'Plot mortality rates by race and sex over time'
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        args = {'race_sex_form':race_sex_form, 'text':text}
        return render(request, self.template_name, args)

    def post(self, request):
        race_sex_form = APIform2(request.POST)
        if race_sex_form.is_valid():
            form_data = race_sex_form.cleaned_data
            query, text, messages = MOIRA.get_rates(form_data, 'rs')
            if 'error' in text:
                alerts = "<div class=\"alert alert-brand\"><strong>Invalid Cause of Death Category</strong></div>"
            elif '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                alerts = "<div class=\"alert alert-brand\"><strong>Please Try Another Time Period</strong> - Thank you!</div>"
            else:
                text = MOIRA.rates_RStime(text)
                df, suptable = MOIRA.get_csv(text, RS = True)
                text = ""
                alerts = ""

            title = form_data['title_2']
            #df_rates, df_deaths = MOIRA.rates_RStime(text), MOIRA.deaths_RStime(text)
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
            

        else:
            text = "Invalid Submission"
    
        args = {'race_sex_form':race_sex_form, 'alerts':mark_safe(alerts), 'title':mark_safe(title), 'text':text, 'query':mark_safe(query), 'suptable':mark_safe(suptable)}
    
        return render(request, self.template_name, args)

    
#   MOIRA.get_csv(df_deaths, RS=True)
#   timePeriod = list(range(int(form_data['year1_2']),(int(form_data['year2_2'])+1)))
    
    
    
class SesView(TemplateView):
    template_name = 'accounts/plotSES.html'
    
    def get(self, request):
        ses_form = APIform4()
        text = 'Plot mortality rates by socioeconomic subgroup over time'
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        args = {'ses_form':ses_form, 'text':text}
        return render(request, self.template_name, args)

    def post(self, request):
        ses_form = APIform4(request.POST)
        if ses_form.is_valid():
            form_data = ses_form.cleaned_data
            query, messages, text = MOIRA.get_rates(form_data, 'ses')
            if 'error' in text:
                alerts = "<div class=\"alert alert-brand\"><strong>Invalid Cause of Death Category</strong></div>"
                suptable = ''
            elif '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                alerts = "<div class=\"alert alert-brand\"><strong>Your query returned too much data.</strong> Please Try a Shorter Time Period - Sorry!</div>"
                suptable = ''
                MOIRA.get_csv('{"temp":"temp"}', get=True)
            else:
                text = MOIRA.rates_SEStime(text)
                df, suptable = MOIRA.get_csv(text, SES = True)
                text = ""
                alerts = ""

            title = form_data['title_4']
            #df_rates, df_deaths = MOIRA.rates_RStime(text), MOIRA.deaths_RStime(text)
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
            

        else:
            text = "Invalid Submission"
            title = form_data['title_4']
            alerts = "<div class=\"alert alert-brand\"><strong>Please Try Another Time Period</strong> - Thank you!</div>" 
    
        args = {'ses_form':ses_form, 'alerts':mark_safe(alerts), 'title':mark_safe(title), 'text':query, 'suptable':mark_safe(suptable)}
    
        return render(request, self.template_name, args)
    
class GeoView(TemplateView):

    template_name = 'accounts/plotGeo.html'
    def get(self, request):
        geo_form = APIform3()
        text = ''
        geoLVL = 'counties'
        args = {'geo_form':geo_form, 'text':text, 'geoLVL':geoLVL}
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        return render(request, self.template_name, args)
    
    def post(self, request):
        geo_form = APIform3(request.POST)
        
        if geo_form.is_valid():
            form_data = geo_form.cleaned_data
            query, messages, text = MOIRA.get_rates(form_data, 'geo')
            
            
            
            alerts= ""
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
                
            if form_data['plot'] == 'bubbles':
                bubbles = """const format = d3.format(",.0f")    
        
                        // Draw the bubble map
                        svg.append("path")
                          .datum(topojson.feature(us, us.objects.nation))
                          .attr("fill", "#ccc")
                          .attr("d", path);
                        svg.append("g")
                            .attr("fill", "brown")
                            .attr("fill-opacity", 0.5)
                            .attr("stroke", "#fff")
                            .attr("stroke-width", 0.5)
                            .selectAll("circle")
                            .data({{ geoLVL }}
                               .map(d => (d.value = bubble_data.get(d.id), d))
                               .sort((a, b) => b.value - a.value))
                            .join("circle")
                                .attr("transform", d => `translate(${path.centroid(d)})`)
                                .attr("r", d => radius(d.value)*bubbleradius)
                            //.attr("fill", d => color(data.get(d.id)))
                            .append("title")
                                .text(d => `${d.properties.name}, ${states.get(d.id.slice(0, 2)).name}
                ${format(bubble_data.get(d.id))}`);

                    """
                legend = """var blValues = [d3.quantile([...bubble_data.values()],0.25),d3.quantile([...bubble_data.values()],0.5),d3.quantile([...bubble_data.values()],0.75)].sort(d3.ascending),
            xCircle = 100,
            yCircle = 500,
            xLabel = 270;
            console.log(blValues)
            svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("circle")
            .attr("cx", function(d){ if(d==blValues[0]){return 50+xCircle}
            else if(d==blValues[1]){ return 100+xCircle }
            //else if(d==blValues[2]){ return 100+xCircle }
            //else if(d==blValues[3]){ return 150+xCircle }
            else{ return 150+xCircle } })
            .attr("cy", yCircle)
            .attr("r", function(d){ return radius(d)*bubbleradius})
            .style("fill", "none")
            .attr("stroke","black")
        /*svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("line")
            .attr("x1",function(d){ return xCircle + radius(d)})
            .attr("x2", function(d) { return xLabel - 10})
            .attr("y1", function(d){ return yCircle - radius(d)*1.05})
            .attr("y2", function(d){ return yCircle - radius(d)*1.05})
            .attr("stroke","black")
            .attr("stroke-dasharray",('2,2'))
        */
        svg
        .append("text")
            .attr('x', xLabel - xCircle)
            .attr('y', 450)
            .style("font-size", 10)
            .text(bubble_data.title)
        
        svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("text")
            .attr("x", function(d){ if(d==blValues[0]){return 50+xCircle}
            else if(d==blValues[1]){ return 100+xCircle }
            //else if(d==blValues[2]){ return 100+xCircle }
            //else if(d==blValues[3]){ return 150+xCircle }
            else{ return 150+xCircle } })
            .attr('y', yCircle-30)
            .text( function(d){ return d } )
            .style("font-size", 10)
            .attr('alignment-baseline', 'middle')
                            """
                
            else: 
                bubbles = ""
                legend = """svg.append("g")
            .attr("transform", "translate(90,440)")
            .append(() => legend({color, title: data.title, width: 200, tickFormat:".2f"}));
        """
            
            
            if form_data['title'] != 'Enter Map Title Here':
                title = form_data['title']
            else:
                title = 'Mortality Rates:' + query['timePeriod']
            
            if '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                geoLVL = 'counties'
                suptable = ''
                
            else:
                if form_data['geoLevel_3']=='State':
                    df, suptable = MOIRA.get_csv(text, state=True)
                    #MOIRA.get_csv(rs_text, state=True, rs=True)
                    geoLVL = 'states_'
                    bubbles = bubbles.replace("{400}","400").replace("bubbleradius","1.5")
                    legend = legend.replace("bubbleradius","1.5")

                else:
                    df, suptable = MOIRA.get_csv(text)
                    #MOIRA.get_csv(rs_text, rs=True)
                    geoLVL = 'counties'
                    bubbles = bubbles.replace("{400}","50").replace("bubbleradius",".25")
                    legend = legend.replace("bubbleradius",".25")

                text = ""
                bubbles = bubbles.replace("{{ geoLVL }}",geoLVL)
        else:
            text = "Invalid Submission"
        download = """
                   """
        
        
        
        args = {'geo_form':geo_form, 'alerts':mark_safe(alerts),'legend':mark_safe(legend),'text':text, 'bubbles':mark_safe(bubbles),'title':mark_safe(title), 'geoLVL':geoLVL, 'suptable':mark_safe(suptable), 'query':mark_safe(query)}

        return render(request, self.template_name, args)
        

class RatesView(TemplateView):
    
    template_name = 'accounts/rates.html'
    # Render form 
    def get(self, request):
        
        form = APIform()
        race_sex_form = APIform2()
        text = "Get Mortality Rates..."
        args = {'form':form, 'race_sex_form':race_sex_form, 'text':text}
        return render(request, self.template_name, args)
    
    def post(self, request):
        
        form = APIform(request.POST)
        
        if form.is_valid():
            form_data = form.cleaned_data
            query, text, messages, age = MOIRA.get_rates(form_data, 'reg')

            #re_columns = list(df.columns)
            alerts = ""
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
            
            if '<!DOCTYPE html>' in text: 
                text = ''
                alerts = alerts + "<div class=\"alert alert-brand\"><strong>Invalid form submission:</strong> Please try again</div>"
            else:
                df, x = MOIRA.get_csv(text)
                
            
                text = "<thead><tr>"
                for i in list(df.columns):
                    text = text+"<th>"+i+"</th>"
                text = text+"</tr></thead><tbody>"
                for i in df.index:
                    text = text+"<tr>"
                    for col in list(df.columns):
                        text = text+"<td>"+str(df[col][i])+"</td>"
                    text = text+"</tr></tbody>"
                
                
        else:
            #alerts = "<div class=\"alert alert-brand\"><strong>Invalid form</strong></div><br>"
            text = "Invalid Submission"
        
        args = {'form':form, 'age':mark_safe(age),'query':mark_safe(query), 'text':mark_safe(text), 'alerts':mark_safe(alerts)}# 're_columns':re_columns}

        return render(request, self.template_name, args)

    
"""<strong>Selection Criteria:</strong>
                <li>Time Period: {{ years }}</li>
                <li>Geographic Detail: {{ geolvl }}</li>
                <li>States: {{ states }}</li>
                <li>Counties: {{ couFIPS }}</li>
                <li>CoD Category: {{ codcat }}</li>
                <li>CoD: {{ cods }}</li>
                <li>Age Group Category: {{ agecat }}</li>
                <li>Age Group: {{ ages }}</li>
                <li>Sex: {{ sex }}</li>
                <li>Race: {{ race }}</li>
                <li>HispanicOrigin: {{ hispOrg }}</li>
                <li>Group By: {{ groupby }}</li>
                <li>Age Adjustment: {{ ageadj }}</li>
                <li>Rate Per: {{ ratesPer }}</li>"""
    
    
    
    
    
    
class ClusteringView(TemplateView):
    template_name = 'accounts/clustering.html'
    
    def get(self, request):
        fc_form = APIform5()
        text = 'Locate Mortality Hotspots Across the United States'
        geoLVL = 'counties'
        projection = 'const projection = d3.geoAlbersUsa().scale(750).translate([350, 250])'
        args = {'fc_form':fc_form, 'text':text, 'geoLVL':geoLVL, 'projection':mark_safe(projection)}
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        return render(request, self.template_name, args)
    
    def post(self, request):
        fc_form = APIform5(request.POST)
        
        if fc_form.is_valid():
            form_data = fc_form.cleaned_data
            
            # get API query, results and alerts
            query, messages, text = MOIRA.get_rates(form_data, 'clustering')
            
            # get alerts
            alerts= ""
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert  
                    
            
            
            # 
            title = form_data['title_5']
            state = form_data['abbreviatedStates_5']
            STATES = [('AL','Alabama'),('AK','Alaska'),('AZ','Arizona'),('AR','Arkansas'),('CA','California'),('CO','Colorado'),('CT','Connecticut'),('DE','Delaware'),('DC','District of Columbia'),('FL','Florida'),('GA','Georgia'),('HI','Hawaii'),('ID','Idaho'),('IL','Illinois'),('IN','Indiana'),('IA','Iowa'),('KS','Kansas'),('KY','Kentucky'),('LA','Louisiana'),('ME','Maine'),('MD','Maryland'),('MA','Massachusetts'),('MI','Michigan'),('MN','Minnesota'),('MS','Mississippi'),('MO','Missouri'),('MT','Montana'),('NE','Nebraska'),('NV','Nevada'),('NH','New Hampshire'),('NJ','New Jersey'),('NM','New Mexico'),('NY','New York'),('NC','North Carolina'),('ND','North Dakota'),('OH','Ohio'),('OK','Oklahoma'),('OR','Oregon'),('PA','Pennsylvania'),('RI','Rhode Island'),('SC','South Carolina'),('SD','South Dakota'),('TN','Tennessee'),('TX','Texas'),('UT','Utah'),('VT','Vermont'),('VA','Virginia'),('WA','Washington'),('WV','West Virginia'),('WI','Wisconsin'),('WY','Wyoming')]        
            if len(state) == 1:
                for i in STATES:
                    if i[0] == state[0]:
                        state = i[1]
                        break
                state_filter = "else if (states.get(d.id.slice(0, 2)).name != \""+ state +"\") {return \"transparent\"}"
            #center = MOIRA.get_center(state)
            projection = 'const projection = d3.geoMercator().scale(750).translate([350, 250])'
            
            #projection = 'const projection = d3.geoAlbersUsa().scale(750).translate([350, 250])'
            #.attr("transform", d => `translate(${path.centroid(d)})`)
            
            #state_filter = "else if (states.get(d.id.slice(0, 2)).name != \""+ state +"\") {return \"#ffffff\"}"

            if '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                geoLVL = 'counties'
                suptable = ''

            else:
                df, suptable = MOIRA.get_csv(text, cluster=True)
                
            
                
        args = {'fc_form':fc_form, 'projection':mark_safe(projection), 'state_filter':mark_safe(state_filter), 'alerts':mark_safe(alerts),'text':text, 'title':mark_safe(title), 'suptable':mark_safe(suptable), 'query':mark_safe(query)}

        return render(request, self.template_name, args)
    
    
class MapboxView(TemplateView):
    template_name = 'accounts/plotGeo2.html'
    
    


class CountyTimeView(TemplateView):

    
    template_name = 'accounts/countytime.html'
    
    def get(self, request):
        county_time_form = APIform6()
        text = 'Plot mortality rates by county or state over time. Please limit queries to a small number of counties.'
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        args = {'county_time_form':county_time_form, 'text':text}
        return render(request, self.template_name, args)

    def post(self, request):
        county_time_form = APIform6(request.POST)
        if county_time_form.is_valid():
            form_data = county_time_form.cleaned_data
            query, text, messages = MOIRA.get_rates(form_data, 'countytime')
            if 'error' in text:
                alerts = "<div class=\"alert alert-brand\"><strong>Invalid Cause of Death Category</strong></div>"
            elif '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                alerts = "<div class=\"alert alert-brand\"><strong>Please Try Another Time Period</strong> - Thank you!</div>"
            else:
                text = MOIRA.rates_CTtime(text)
                df, suptable = MOIRA.get_csv(text, RS = True)
                text = ""
                alerts = ""

            title = form_data['title_6']

            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
            

        else:
            text = "Invalid Submission"
    
        args = {'county_time_form':county_time_form, 'alerts':mark_safe(alerts), 'title':mark_safe(title), 'text':text, 'query':mark_safe(query), 'suptable':mark_safe(suptable)}
    
        return render(request, self.template_name, args)

    
#   MOIRA.get_csv(df_deaths, RS=True)
#   timePeriod = list(range(int(form_data['year1_2']),(int(form_data['year2_2'])+1)))
    
class TempClusteringView(TemplateView): 
    template_name = 'accounts/temporal_clustering.html'
    
    def get(self, request):
        tc_form = APIform7()
        title = 'Create a time-series clustering heatmap... Please limit queries to a small number of counties.'
        # overwrite output file
        source1, source2 = '<!--', '-->'
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        args = {'tc_form':tc_form, 'title':title, 'source1':mark_safe(source1), 'source2':mark_safe(source2)}
        return render(request, self.template_name, args)

    def post(self, request):
        tc_form = APIform7(request.POST)
        if tc_form.is_valid():
            form_data = tc_form.cleaned_data
            query, text, messages = MOIRA.get_rates(form_data, 'timecluster')
            if 'error' in text:
                alerts = "<div class=\"alert alert-brand\"><strong>Invalid Cause of Death Category</strong></div>"
            elif '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                alerts = "<div class=\"alert alert-brand\"><strong>Please Try Another Time Period</strong> - Thank you!</div>"
            else:
                text = MOIRA.rates_TempClust(text, form_data['geoLevel_7'])
                df, suptable = MOIRA.get_csv(text, tempcluster=True)
                text = ""
                alerts = ""

            title = form_data['title_7']
            source1, source2 = '<iframe src=', '</iframe>'

            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert

        else:
            text = "Invalid Submission"
            alerts = "<div class=\"alert alert-brand\"><strong>Please Try Again</strong> - Thank you!</div>"
            
        
        args = {'tc_form':tc_form, 'alerts':mark_safe(alerts), 'title':mark_safe(title), 'text':text, 'query':mark_safe(query), 'source1':mark_safe(source1), 'source2':mark_safe(source2)}
    
        return render(request, self.template_name, args)
    
    
    
class SecondaryDataView(TemplateView):

    template_name = 'accounts/secondarydata.html'
    def get(self, request):
        geo_form = APIform8()
        text = ''
        geoLVL = 'counties'
        args = {'geo_form':geo_form, 'text':text, 'geoLVL':geoLVL}
        MOIRA.get_csv('{"temp":"temp"}', get=True)
        return render(request, self.template_name, args)
    
    def post(self, request):
        geo_form = APIform8(request.POST)
        
        if geo_form.is_valid():
            form_data = geo_form.cleaned_data
            query, messages, text = MOIRA.get_rates(form_data, 'secondary')
            
            
            
            alerts= ""
            if len(messages) > 0:
                for message in messages:
                    alert = "<div class=\"alert alert-brand\">"+message+"</div>" 
                    alerts = alerts + alert
                
            if form_data['plot'] == 'bubbles':
                bubbles = """const format = d3.format(",.0f")    
        
                        // Draw the bubble map
                        svg.append("path")
                          .datum(topojson.feature(us, us.objects.nation))
                          .attr("fill", "#ccc")
                          .attr("d", path);
                        svg.append("g")
                            .attr("stroke", "#fff")
                            .attr("stroke-width", 0.5)
                            .selectAll("circle")
                            .data({{ geoLVL }}
                               .map(d => (d.value = bubble_data.get(d.id), d))
                               .sort((a, b) => b.value - a.value))
                            .join("circle")
                                .attr("transform", d => `translate(${path.centroid(d)})`)
                                .attr("r", d => radius(d.value))
                            .attr("fill", function(d){
                                    if (data.get(d.id)){return color(data.get(d.id))}
                                    else {return "#d3d3d3"}
                                })
                            .attr("fill-opacity", 0.5)
                            //.attr("fill", d => color(data.get(d.id)))
                            .append("title")
                                .text(d => `${d.properties.name}, ${states.get(d.id.slice(0, 2)).name}
                ${format(bubble_data.get(d.id))}`);

                    """
                legend = """var blValues = [d3.quantile([...bubble_data.values()],0.25),d3.quantile([...bubble_data.values()],0.5),d3.quantile([...bubble_data.values()],0.75)].sort(d3.ascending),
            xCircle = 100,
            yCircle = 500,
            xLabel = 270;
            console.log(blValues)
            svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("circle")
            .attr("cx", function(d){ if(d==blValues[0]){return 50+xCircle}
            else if(d==blValues[1]){ return 100+xCircle }
            //else if(d==blValues[2]){ return 100+xCircle }
            //else if(d==blValues[3]){ return 150+xCircle }
            else{ return 150+xCircle } })
            .attr("cy", yCircle)
            .attr("r", function(d){ return radius(d)})
            .style("fill", "none")
            .attr("stroke","black")
        /*svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("line")
            .attr("x1",function(d){ return xCircle + radius(d)})
            .attr("x2", function(d) { return xLabel - 10})
            .attr("y1", function(d){ return yCircle - radius(d)*1.05})
            .attr("y2", function(d){ return yCircle - radius(d)*1.05})
            .attr("stroke","black")
            .attr("stroke-dasharray",('2,2'))
        */
        svg
        .append("text")
            .attr('x', xLabel - xCircle)
            .attr('y', 450)
            .style("font-size", 10)
            .text(bubble_data.title)
        
        svg
        .selectAll("legend")
        .data(blValues)
        .enter()
        .append("text")
            .attr("x", function(d){ if(d==blValues[0]){return 50+xCircle}
            else if(d==blValues[1]){ return 100+xCircle }
            //else if(d==blValues[2]){ return 100+xCircle }
            //else if(d==blValues[3]){ return 150+xCircle }
            else{ return 150+xCircle } })
            .attr('y', yCircle-30)
            .text( function(d){ return d } )
            .style("font-size", 10)
            .attr('alignment-baseline', 'middle')
            
        svg.append("g")
            .attr("transform", "translate(400,450)")
            .append(() => legend({color, title: data.title, width: 200, tickFormat:".2f"}));
       
                            """
                
            else: 
                bubbles = ""
                legend = """svg.append("g")
            .attr("transform", "translate(90,440)")
            .append(() => legend({color, title: data.title, width: 200, tickFormat:".2f"}));
        """
            
            
            if form_data['title'] != 'Enter Map Title Here':
                title = form_data['title']
            else:
                title = 'Mortality Rates:' + query['timePeriod']
            
            if '<!DOCTYPE html>' in text: # or '<!DOCTYPE html>' in rs_text:
                text = 'Please try another time period in your selection.'
                geoLVL = 'counties'
                suptable = ''
                
            else:
                timeperiod = str(form_data['year1_8']) + ' - ' + str(form_data['year2_8'])
                if form_data['geoLevel_8']=='State':
                    df, suptable = MOIRA.get_csv(text, state=True, secondary_data=timeperiod)
                    #MOIRA.get_csv(rs_text, state=True, rs=True)
                    geoLVL = 'states_'
                    bubbles = bubbles.replace("{400}","400").replace("bubbleradius","1.5")
                    legend = legend.replace("bubbleradius","1.5")

                else:
                    df, suptable = MOIRA.get_csv(text, secondary_data=timeperiod)
                    #MOIRA.get_csv(rs_text, rs=True)
                    geoLVL = 'counties'
                    bubbles = bubbles.replace("{400}","50").replace("bubbleradius",".25")
                    legend = legend.replace("bubbleradius",".25")

                text = ""
                bubbles = bubbles.replace("{{ geoLVL }}",geoLVL)
        else:
            text = "Invalid Submission"
        download = """
                   """
        
        
        
        args = {'geo_form':geo_form, 'alerts':mark_safe(alerts),'legend':mark_safe(legend),'text':text, 'bubbles':mark_safe(bubbles),'title':mark_safe(title), 'geoLVL':geoLVL, 'suptable':mark_safe(suptable), 'query':mark_safe(query)}

        return render(request, self.template_name, args)
    

    
    
    
    
    